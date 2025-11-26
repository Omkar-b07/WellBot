import os
import requests
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    create_access_token, get_jwt_identity, jwt_required,
    JWTManager, set_access_cookies, unset_jwt_cookies
)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from sqlalchemy import func # <-- IMPT: Needed for charts

# --- App Initialization ---
app = Flask(__name__)

# --- Database Configuration ---
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'project.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SECRET_KEY"] = "your-admin-session-secret-key"

# --- JWT Configuration ---
app.config["JWT_SECRET_KEY"] = "3ae0710d88e55092c2cde9d5b597d0c1d51fae8fa54481b9f2c83bb4139e0243"
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
    preferred_language = db.Column(db.String(10), default='en', nullable=False)
    age_group = db.Column(db.String(20), nullable=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<User {self.email}>'

class HealthKnowledge(db.Model):
    __tablename__ = 'health_knowledge'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    intent = db.Column(db.String(100), nullable=False)
    entity = db.Column(db.String(100), nullable=False)
    response_en = db.Column(db.Text, nullable=False)
    response_hi = db.Column(db.Text, nullable=False)

class UserWellnessData(db.Model):
    __tablename__ = 'user_wellness_data'
    UserID = db.Column(db.String, primary_key=True)
    Date = db.Column(db.String, primary_key=True)
    Steps = db.Column(db.String)
    CaloriesBurned = db.Column(db.String)
    DistanceKm = db.Column(db.String)
    SleepHours = db.Column(db.String)
    HeartRate = db.Column(db.String)
    FoodItem = db.Column(db.String)
    CaloriesIntake = db.Column(db.String)
    Protein_g = db.Column(db.String)
    Fat_g = db.Column(db.String)
    Carbs_g = db.Column(db.String)
    WaterIntake_L = db.Column(db.String)
    Mood = db.Column(db.String)
    Recommendation = db.Column(db.Text)

class ChatFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(36), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    rating = db.Column(db.String(10), nullable=False)
    comment = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# --- Admin Decorator ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# --- HTML Serving Routes ---
@app.route('/')
def index():
    return redirect(url_for('login_page'))

@app.route('/login_page')
def login_page():
    return render_template('login.html')

@app.route('/register_page')
def register_page():
    return render_template('register.html')

@app.route('/chat_page')
@jwt_required(locations=["cookies"])
def chat_page():
    """Serves the main chat HTML page, passing current language."""
    current_user_id = get_jwt_identity()
    user = db.session.get(User, int(current_user_id))
    
    current_language = user.preferred_language if user else 'en'
    
    return render_template('chat.html', current_language=current_language)

@app.route('/profile_page')
@jwt_required(locations=["cookies"])
def profile_page():
    return render_template('profile.html')

# --- JWT Error Handlers ---
@jwt.unauthorized_loader
def unauthorized_callback(error_string):
    if request.accept_mimetypes.accept_html:
        return redirect(url_for('login_page'))
    return jsonify(msg="Missing or invalid token"), 401

@jwt.expired_token_loader
def expired_token_render_callback(jwt_header, jwt_payload):
    if request.accept_mimetypes.accept_html:
        return redirect(url_for('login_page'))
    return jsonify(msg="Token has expired"), 401

# --- API Endpoints ---
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    age_group = data.get('age_group')
    preferred_language = data.get('preferred_language', 'en')

    if not email or not password:
        return jsonify({"msg": "Email and password are required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Email already exists"}), 400

    hashed_password = generate_password_hash(password)
    is_first_user = User.query.count() == 0
    new_user = User(
        email=email,
        password_hash=hashed_password,
        age_group=age_group,
        preferred_language=preferred_language,
        is_admin=is_first_user
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"msg": "User created successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password_hash, password):
        access_token = create_access_token(identity=str(user.id))
        response = jsonify(access_token=access_token)
        set_access_cookies(response, access_token)
        return response
    return jsonify({"msg": "Bad email or password"}), 401

@app.route('/logout', methods=['POST'])
def logout():
    response = jsonify({"msg": "Logout successful"})
    unset_jwt_cookies(response)
    return response

@app.route('/profile', methods=['GET', 'PUT'])
@jwt_required()
def profile():
    current_user_id = get_jwt_identity()
    user = db.session.get(User, int(current_user_id))
    if not user:
        return jsonify({"msg": "User not found"}), 404

    if request.method == 'GET':
        return jsonify(email=user.email, preferred_language=user.preferred_language, age_group=user.age_group)

    if request.method == 'PUT':
        data = request.get_json()
        if 'preferred_language' in data:
             user.preferred_language = data['preferred_language']
        if 'age_group' in data:
             user.age_group = data.get('age_group')
        db.session.commit()
        return jsonify({"msg": "Profile updated successfully"})

@app.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    current_user_id = get_jwt_identity()
    user = db.session.get(User, int(current_user_id))
    if not user:
         return jsonify({"error": "User authentication error"}), 404

    user_language = user.preferred_language
    data = request.get_json()
    message = data.get('message')
    if not message:
        return jsonify({"error": "No message provided"}), 400

    RASA_API_URL = "http://127.0.0.1:5005/webhooks/rest/webhook"
    payload = {
        "sender": current_user_id,
        "message": message,
        "metadata": {"user_language": user_language}
    }
    
    try:
        rasa_response = requests.post(RASA_API_URL, json=payload, timeout=10)
        rasa_response.raise_for_status()
        bot_messages = rasa_response.json()
        
        bot_reply = "Rasa returned an empty response."
        if bot_messages and isinstance(bot_messages, list) and len(bot_messages) > 0:
            bot_reply = bot_messages[0].get("text", "Error parsing Rasa reply.")
        
        return jsonify({"reply": bot_reply, "user_message": message})

    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Could not connect to the chatbot server"}), 503
    except Exception as e:
        print(f"!!! General Exception in /chat: {e}")
        return jsonify({"error": "An internal error occurred"}), 500

@app.route('/feedback', methods=['POST'])
@jwt_required()
def feedback():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    user_message = data.get('user_message')
    bot_response = data.get('bot_response')
    rating = data.get('rating')
    comment = data.get('comment', '')

    if not all([user_message, bot_response, rating]):
        return jsonify({"msg": "Missing data"}), 400
    
    try:
        new_feedback = ChatFeedback(
            user_id=current_user_id,
            user_message=user_message,
            bot_response=bot_response,
            rating=rating,
            comment=comment
        )
        db.session.add(new_feedback)
        db.session.commit()
        return jsonify({"msg": "Feedback saved"}), 201
    except Exception as e:
        db.session.rollback()
        print(f"!!! Error saving feedback: {e}")
        return jsonify({"msg": "Error saving feedback"}), 500

# --- ADMIN DASHBOARD ROUTES ---

@app.route('/admin', methods=['GET'])
def admin_index_redirect():
    return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password) and user.is_admin:
            session['admin_logged_in'] = True
            session['admin_email'] = user.email
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials or not an admin.', 'error')
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_email', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Shows the main admin dashboard with analytics."""

    # --- 1. Calculate Statistics ---
    total_users = User.query.count()
    total_tips = HealthKnowledge.query.count()
    total_feedback = ChatFeedback.query.count()

    positive_feedback = ChatFeedback.query.filter_by(rating='good').count()
    if total_feedback > 0:
        satisfaction_rate = round((positive_feedback / total_feedback) * 100)
    else:
        satisfaction_rate = 0

    # --- 2. Prepare Feedback Chart Data ---
    negative_feedback = total_feedback - positive_feedback
    chart_feedback_data = {
        'labels': ['Positive', 'Negative'],
        'data': [positive_feedback, negative_feedback]
    }

    # --- 3. Intent Count Chart ---
    intent_counts = db.session.query(
        HealthKnowledge.intent,
        func.count(HealthKnowledge.intent)
    ).group_by(HealthKnowledge.intent).all()

    chart_intent_labels = [item[0].replace('_', ' ').title() for item in intent_counts]
    chart_intent_data = [item[1] for item in intent_counts]

    # --- 4. Activity Chart (Queries Per Day) ---
    daily_counts = db.session.query(
        func.strftime("%Y-%m-%d", ChatFeedback.timestamp),
        func.count(ChatFeedback.id)
    ).group_by(func.strftime("%Y-%m-%d", ChatFeedback.timestamp)).all()

    if daily_counts:
        chart_activity_labels = [row[0] for row in daily_counts]
        chart_activity_data = [row[1] for row in daily_counts]
    else:
        # Fallback if no data exists
        chart_activity_labels = ["No Data"]
        chart_activity_data = [0]

    # --- 5. Fetch Tables ---
    try:
        knowledge_base = HealthKnowledge.query.order_by(
            HealthKnowledge.intent,
            HealthKnowledge.entity
        ).all()
    except Exception:
        knowledge_base = []

    try:
        feedback_logs = ChatFeedback.query.order_by(
            ChatFeedback.timestamp.desc()
        ).limit(50).all()
    except Exception:
        feedback_logs = []

    try:
        user_logs = UserWellnessData.query.limit(50).all()
    except Exception:
        user_logs = []

    # --- 6. Render Template ---
    return render_template(
        'admin_dashboard.html',
        total_users=total_users,
        total_tips=total_tips,
        total_feedback=total_feedback,
        satisfaction_rate=satisfaction_rate,
        chart_feedback_data=chart_feedback_data,
        chart_intent_labels=chart_intent_labels,
        chart_intent_data=chart_intent_data,
        chart_activity_labels=chart_activity_labels,
        chart_activity_data=chart_activity_data,
        knowledge=knowledge_base,
        user_logs=user_logs,
        feedback_logs=feedback_logs
    )
    

@app.route('/admin/add_tip', methods=['POST'])
@admin_required
def admin_add_tip():
    try:
        intent = request.form['intent']
        entity = request.form['entity']
        response_en = request.form['response_en']
        response_hi = request.form['response_hi']

        if not all([intent, entity, response_en, response_hi]):
            flash("All fields are required.", "error")
            return redirect(url_for('admin_dashboard'))

        new_tip = HealthKnowledge(
            intent=intent,
            entity=entity.lower(),
            response_en=response_en,
            response_hi=response_hi
        )
        db.session.add(new_tip)
        db.session.commit()
        flash("Health tip added successfully!", "success")
    except Exception as e:
        db.session.rollback()
        print(f"Error adding tip: {e}")
        flash("Error adding tip to database.", "error")
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_tip/<int:id>', methods=['POST'])
@admin_required
def admin_delete_tip(id):
    try:
        tip = db.session.get(HealthKnowledge, id)
        if tip:
            db.session.delete(tip)
            db.session.commit()
            flash("Health tip deleted successfully.", "success")
        else:
            flash("Tip not found.", "error")
    except Exception as e:
        db.session.rollback()
        flash("Error deleting tip.", "error")
        
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000, host='0.0.0.0')