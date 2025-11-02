import streamlit as st
import requests
import random

# --- Config ---
RASA_API_URL = "http://localhost:5005/webhooks/rest/webhook"
BOT_AVATAR = "🤖"
USER_AVATAR = "🙂"

st.set_page_config(page_title="Wellness Chatbot", page_icon=BOT_AVATAR)
st.title("Wellness Chatbot")
st.caption("Your non-diagnostic health assistant 🩺")

# --- Session State ---
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm your wellness assistant. You can ask me about symptoms, first-aid, or general wellness tips."}
    ]

# --- Helper Function ---
def get_rasa_response(message):
    """Send message to Rasa and get a response."""
    try:
        payload = {"sender": str(random.randint(1, 1000)), "message": message}
        response = requests.post(RASA_API_URL, json=payload)
        response.raise_for_status() # Raise an exception for bad status codes
        
        rasa_responses = response.json()
        if rasa_responses:
            # Return the text from the first response
            return rasa_responses[0].get("text", "Sorry, I didn't understand that.")
        return "I'm not sure how to respond to that."
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to the Rasa server. Are both Rasa servers running?"
    except Exception as e:
        print(f"Rasa API Error: {e}")
        return "Sorry, I'm having technical difficulties."

# --- Chat Interface ---

# Display chat messages from history
for message in st.session_state.messages:
    avatar = BOT_AVATAR if message["role"] == "assistant" else USER_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What's up?"):
    # 1. Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # 2. Display user message
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    # 3. Get bot response
    with st.spinner("Thinking..."):
        bot_response = get_rasa_response(prompt)
    
    # 4. Add bot response to history
    st.session_state.messages.append({"role": "assistant", "content": bot_response})
    # 5. Display bot response
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        st.markdown(bot_response)