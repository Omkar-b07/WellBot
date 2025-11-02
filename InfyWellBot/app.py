import os
import requests

from flask import Flask, request, jsonify, render_template, redirect, url_for

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    create_access_token, get_jwt_identity, jwt_required,
    JWTManager, set_access_cookies, unset_jwt_cookies
)
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)


db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'project.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


app.config["JWT_SECRET_KEY"] = "your-super-secret-key-please-change-me" 

app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies"]

app.config["JWT_COOKIE_CSRF_PROTECT"] = False
jwt = JWTManager(app)

# --- Database Setup ---
db = SQLAlchemy(app)

# --- Database Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    preferred_language = db.Column(db.String(10), default='en', nullable=False) # Make non-nullable
    age_group = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f'<User {self.email}>'

@app.route('/')
def index():
    """Redirects base URL to the login page if not logged in, else chat."""

    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
    try:
        
        verify_jwt_in_request(optional=True, locations=["cookies"])
        if get_jwt_identity():
            return redirect(url_for('chat_page')) 
    except Exception as e:
        print(f"Error checking JWT at index: {e}") 
        pass
    return redirect(url_for('login_page'))

@app.route('/login_page')
def login_page():
    """Serves the login HTML page."""
    return render_template('login.html')

@app.route('/register_page')
def register_page():
    """Serves the register HTML page."""
    return render_template('register.html')

# Protect the chat page route - only accessible if logged in via cookie
@app.route('/chat_page')
@jwt_required(locations=["cookies"]) # Check if user has a valid login cookie
def chat_page():
    """Serves the main chat HTML page."""
    return render_template('chat.html')

@app.route('/profile_page')
@jwt_required(locations=["cookies"]) # Protect this page
def profile_page():
    """Serves the profile editing HTML page."""
    return render_template('profile.html')



# Handles missing/invalid token for @jwt_required routes
@jwt.unauthorized_loader
def unauthorized_render_callback(error_string):
    print(f"Unauthorized access detected: {error_string}")

    rule = request.url_rule
    if rule and not rule.endpoint.endswith(('_page', 'index')): # Crude check if it's an API route
        print("-> Responding with JSON error")
        return jsonify(msg="Missing or invalid token"), 401
    else:
        print("-> Redirecting to login page")
        return redirect(url_for('login_page'))

# Handles expired tokens specifically
@jwt.expired_token_loader
def expired_token_render_callback(jwt_header, jwt_payload):
    print("Expired token detected")
    # Similar check for HTML vs JSON response
    rule = request.url_rule
    if rule and not rule.endpoint.endswith(('_page', 'index')):
        print("-> Responding with JSON error")
        return jsonify(msg="Token has expired"), 401
    else:
        print("-> Redirecting to login page")
        # Maybe add a flash message here later
        return redirect(url_for('login_page'))


# --- API Endpoints (These handle JSON requests from JavaScript/PowerShell) ---

@app.route('/register', methods=['POST'])
def register():
    """Registers a new user including age and language (API endpoint)."""
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Missing JSON in request"}), 400

    email = data.get('email')
    password = data.get('password')
    age_group = data.get('age_group')
    preferred_language = data.get('preferred_language', 'en')

    if not email or not password:
        return jsonify({"msg": "Email and password are required"}), 400
    if preferred_language not in ['en', 'hi']:
        return jsonify({"msg": "Invalid preferred language"}), 400
    # Add age group validation if needed

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Email already exists"}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(
        email=email,
        password_hash=hashed_password,
        age_group=age_group,
        preferred_language=preferred_language
    )
    try:
        db.session.add(new_user)
        db.session.commit()
        print(f"User registered: {email}, Lang: {preferred_language}, Age: {age_group}")
        return jsonify({"msg": "User created successfully"}), 201
    except Exception as e:
        db.session.rollback()
        print(f"!!! DB Error during registration: {e}")
        return jsonify({"msg": "Database error during registration"}), 500


@app.route('/login', methods=['POST'])
def login():
    """Logs in a user via API, returns JWT token, AND sets an HTTP-only cookie."""
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Missing JSON in request"}), 400
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"msg": "Email and password required"}), 400

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password_hash, password):
        access_token = create_access_token(identity=str(user.id))
        response = jsonify(access_token=access_token) # Also return token for potential API clients
        # Set the JWT in an HTTP-only cookie for secure browser sessions
        set_access_cookies(response, access_token)
        print(f"Login successful for {email}, cookie set.") # Debug print
        return response

    print(f"Login failed for {email}.") # Debug print
    return jsonify({"msg": "Bad email or password"}), 401

@app.route('/logout', methods=['POST'])
def logout():
    """Logs out user by clearing the JWT cookie (API endpoint)."""
    response = jsonify({"msg": "Logout successful"})
    unset_jwt_cookies(response)
    print("User logged out, cookie unset.") # Debug print
    return response


@app.route('/profile', methods=['GET', 'PUT'])
@jwt_required() # Checks header OR cookie automatically based on config
def profile():
    """Gets or updates the logged-in user's profile (API endpoint)."""
    current_user_id = get_jwt_identity() # Works with header or cookie (returns string ID)
    # Use db.session.get for primary key lookup, converting ID to int if necessary
    user = db.session.get(User, int(current_user_id))
    if not user:
        return jsonify({"msg": "User not found"}), 404

    if request.method == 'GET':
        print(f"GET /profile for User ID: {current_user_id}")
        return jsonify(
            email=user.email,
            preferred_language=user.preferred_language,
            age_group=user.age_group
        )

    if request.method == 'PUT':
        data = request.get_json()
        if not data:
            return jsonify({"msg": "Missing JSON in request"}), 400
        print(f"PUT /profile for User ID: {current_user_id} with data: {data}")

        updated = False
        if 'preferred_language' in data:
             lang = data['preferred_language']
             if lang in ['en', 'hi']:
                 user.preferred_language = lang
                 updated = True
             else:
                  return jsonify({"msg": "Invalid language code"}), 400
        if 'age_group' in data:
             # Add validation for age_group if needed
             user.age_group = data.get('age_group') # Allow setting age_group to null/empty
             updated = True

        if updated:
            try:
                db.session.commit()
                print("Profile update successful.")
                return jsonify({"msg": "Profile updated successfully"})
            except Exception as e:
                db.session.rollback()
                print(f"!!! DB Error updating profile: {e}")
                return jsonify({"msg": "Database error during profile update"}), 500
        else:
             return jsonify({"msg": "No profile fields provided for update"}), 400


@app.route('/chat', methods=['POST'])
@jwt_required() # Checks header OR cookie
def chat():
    """Handles chat messages (API endpoint), gets user lang, forwards to Rasa."""
    print("\n--- FLASK /chat Endpoint Hit ---")
    current_user_id = get_jwt_identity() # String user ID
    user = db.session.get(User, int(current_user_id))
    if not user:
         print(f"!!! ERROR: User ID {current_user_id} not found in DB for chat.")
         return jsonify({"error": "User authentication error"}), 404 # Use 404 or 401

    user_language = user.preferred_language # Get 'en' or 'hi'
    print(f"User ID: {current_user_id}, Language: {user_language}")

    try:
        data = request.get_json()
        if not data:
             print("!!! ERROR: No JSON data in chat request.")
             return jsonify({"error": "Missing JSON data"}), 400

        message = data.get('message')
        print(f"Received message: {message}")
        if not message:
            print("!!! ERROR: No message provided.")
            return jsonify({"error": "No message provided"}), 400

        # Use 127.0.0.1 for potentially better reliability than localhost
        RASA_API_URL = "http://127.0.0.1:5005/webhooks/rest/webhook"
        payload = {
            "sender": current_user_id, # Use user ID as sender ID for Rasa
            "message": message,
            "metadata": {"user_language": user_language} # Pass language to action server
        }
        print(f"Payload to send to Rasa: {payload}")

        print(f"Attempting to send request to Rasa at {RASA_API_URL}...")
        try:
            # Send request to Rasa
            rasa_response = requests.post(RASA_API_URL, json=payload, timeout=10)
            rasa_response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            print("Successfully received response from Rasa.")

            bot_messages = rasa_response.json()
            print(f"Rasa raw response: {bot_messages}")

            if bot_messages and isinstance(bot_messages, list) and len(bot_messages) > 0:
                # Extract text from the first message object
                bot_reply = bot_messages[0].get("text", "Sorry, I received an unexpected format from the bot.")
            else:
                bot_reply = "Sorry, the bot didn't provide a response."
                print("Warning: Rasa returned an empty or invalid response.")

            print(f"Extracted bot reply: {bot_reply}")
            print("--- FLASK /chat Endpoint Success ---")
            return jsonify({"reply": bot_reply})

        # --- Specific Error Handling for Rasa Connection ---
        except requests.exceptions.ConnectionError:
            print("!!! ConnectionError: Could not connect to Rasa server. Is it running?")
            return jsonify({"error": "Could not connect to the chatbot server"}), 503 # Service Unavailable
        except requests.exceptions.Timeout:
            print("!!! TimeoutError: Connection to Rasa server timed out.")
            return jsonify({"error": "Chatbot server connection timed out"}), 504 # Gateway Timeout
        except requests.exceptions.RequestException as e:
            # Includes HTTPError raised by raise_for_status()
            print(f"!!! RequestException: Error during request to Rasa: {e}")
            error_msg = f"Error communicating with Rasa: {e}"
            status_code = 500 # Internal Server Error
            if e.response is not None:
                status_code = e.response.status_code
                try:
                    rasa_error = e.response.json()
                    print(f"Rasa returned error status {status_code}: {rasa_error}")
                    error_msg = f"Rasa error ({status_code}): {rasa_error.get('message', str(rasa_error))}"
                except ValueError: # If Rasa error response wasn't JSON
                    error_msg = f"Rasa returned non-JSON error ({status_code}): {e.response.text}"
            return jsonify({"error": error_msg}), status_code if status_code >= 500 else 500 # Return 5xx

    # --- General Error Handling ---
    except Exception as e:
        print(f"!!! General Exception in /chat: {type(e).__name__} - {e}")
        # Log the full traceback for debugging if needed
        import traceback
        traceback.print_exc()
        return jsonify({"error": "An internal server error occurred"}), 500


# --- Run the App ---
if __name__ == '__main__':
    print(f"Database path: {db_path}") # Print DB path on startup
    with app.app_context():
        # Create tables if they don't exist based on the models defined
        db.create_all()
        print("Database tables checked/created.")
    print(f"Starting Flask server on http://0.0.0.0:5000...")
    # Listen on all available network interfaces
    app.run(debug=True, port=5000, host='0.0.0.0')

