from flask import Flask, request, jsonify, redirect, url_for, session
from pymongo import MongoClient
import redis
import uuid
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Generate a secure secret key

# MongoDB setup
client = MongoClient('mongodb://172.17.0.4:27017/')
db = client['ikea_chatbot_db']
users_collection = db['users']
chat_collection = db['chat']  # New collection for storing chat history separately

# Redis setup
r = redis.StrictRedis(host='172.17.0.2', port=6379, db=0, decode_responses=True)

# Predefined FAQ responses
faq_responses = {
    "store hours": "Our store hours are from 9 AM to 9 PM.",
    "home delivery": "Yes, we offer home delivery for all our products.",
    "return product": "You can return a product within 90 days with the receipt.",
    "refund policy": "Refunds are processed within 7-10 business days.",
    "store locations": "We have stores globally. Please visit our website for details.",
    "track order": "You can track your order using the tracking number provided in your email.",
    "loyalty program": "Yes, our IKEA Family program offers discounts and benefits.",
    "modify order": "Orders can be modified within 24 hours of placement.",
    "payment methods": "We accept all major credit cards, PayPal, and IKEA gift cards.",
    "warranty policy": "We offer a 10-year warranty on many of our products."
}

@app.route('/')
def index():
    routes = {
        "Register": "/register",
        "Login": "/login/<username>/<password>",
        "Chat": "/chat"
    }
    return jsonify({"message": "Welcome to the IKEA Chatbot!", "available_routes": routes}), 200

@app.route('/register', methods=['POST'])
def register():
    try:
        username = request.json.get('username')
        if not username:
            return jsonify({'error': "No username provided"}), 400
        
        password = request.json.get('password')
        if not password:
            return jsonify({'error': "No password provided"}), 400

        if users_collection.find_one({"username": username}):
            return jsonify({"error": "User already exists. Please log in."}), 400

        users_collection.insert_one({
            "username": username,
            "password": password,
        })
        return jsonify({"message": "Registration successful. Please log in."}), 201
    
    except Exception as e:
        return jsonify({"error": "Unexpected error", "details": str(e)}), 500

@app.route('/login/<username>/<password>', methods=['GET'])
def login(username, password):
    user = users_collection.find_one({"username": username, "password": password})

    if not user:
        return jsonify({"error": "Invalid username or password."}), 401

    session['username'] = username
    session['chat_id'] = str(uuid.uuid4())
    
    # Initialize chat history in Redis
    r.delete(f"chat:{username}:{session['chat_id']}")  # Ensure no leftover data

    return redirect(url_for('chat'))

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'username' not in session:
        return jsonify({"error": "Please log in first."}), 401

    username = session['username']
    chat_id = session['chat_id']

    if request.method == 'POST':
        user_query = request.json.get('message').lower()
        
        # Handle logout command
        if user_query == "logout":
            return redirect(url_for('logout'))

        # Handle other queries
        response = handle_query(user_query, username, chat_id)
        
        # Store both user query and bot response in Redis as a list
        chat_key = f"chat:{username}:{chat_id}"
        r.rpush(chat_key, f"user_message:{user_query}")
        r.rpush(chat_key, f"response:{response}")

        return jsonify({"response": response}), 200

    # Initial chat greeting and insights
    welcome_message = f"Welcome, {username}! I'm the IKEA Chatbot. How can I assist you today?"
    insights = {
        "FAQ": list(faq_responses.keys()),
        "commands": ["logout"]
    }
    return jsonify({"message": welcome_message, "insights": insights}), 200

def handle_query(query, username, chat_id):
    if query in ["hi", "hello", "hey"]:
        return f"Hello, {username}! How can I assist you today?"

    for keyword in faq_responses.keys():
        if keyword in query:
            return faq_responses[keyword]

    # Default response for unknown queries
    return "I'm not sure how to help with that. Please ask something else or type 'logout' to end the session."

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    if 'username' not in session:
        return jsonify({"error": "You are not logged in."}), 401

    username = session['username']
    chat_id = session['chat_id']
    
    # Retrieve and save chat history to MongoDB
    chat_key = f"chat:{username}:{chat_id}"
    chat_history = r.lrange(chat_key, 0, -1)

    if chat_history:
        # Prepare chat history in the required format (ordered)
        chat_history_dict = {}
        for i in range(0, len(chat_history), 2):
            user_message = chat_history[i].replace("user_message:", "")
            response = chat_history[i+1].replace("response:", "")
            chat_history_dict[user_message] = response

        # Check if the username exists in the chat collection
        existing_chat = chat_collection.find_one({"username": username})

        if existing_chat:
            # Update existing document
            chat_collection.update_one(
                {"username": username},
                {"$set": {f"chathistory.{chat_id}": chat_history_dict}}
            )
        else:
            # Insert new document
            chat_collection.insert_one({
                "username": username,
                "chathistory": {chat_id: chat_history_dict}
            })

    # Clean up Redis and session
    r.delete(chat_key)
    session.pop('username', None)
    session.pop('chat_id', None)

    return jsonify({"message": "You have been logged out successfully."}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002,  debug=True)
