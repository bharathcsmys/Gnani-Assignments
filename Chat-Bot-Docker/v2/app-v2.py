from flask import Flask, request, jsonify, redirect, url_for, session
from pymongo import MongoClient
import redis
import uuid
import secrets
import re
from datetime import datetime
from bson import ObjectId

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  

client = MongoClient('mongodb://172.17.0.4:27017/')
db = client['ikea_chatbot_db']
users_collection = db['users']
chat_collection = db['chat'] 

r = redis.StrictRedis(host='172.17.0.2', port=6379, db=0, decode_responses=True)

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
        "Chat": "/chat",
        "Statistics": "/statistics"
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

    r.delete(f"chat:{username}:{session['chat_id']}") 

    return redirect(url_for('chat'))

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'username' not in session:
        return jsonify({"error": "Please log in first."}), 401

    username = session['username']
    chat_id = session['chat_id']

    if request.method == 'POST':
        user_query = request.json.get('message').lower()
        
        if user_query == "logout":
            return redirect(url_for('logout'))

        response = handle_query(user_query, username)

        chat_key = f"chat:{username}:{chat_id}"
        r.rpush(chat_key, f"user_message:{user_query}")
        r.rpush(chat_key, f"response:{response}")

        return jsonify({"response": response}), 200
    
    welcome_message = f"Welcome, {username}! I'm the IKEA Chatbot. How can I assist you today?"
    insights = {
        "FAQ": list(faq_responses.keys()),
        "commands": ["logout"]
    }
    return jsonify({"message": welcome_message, "insights": insights}), 200

def handle_query(query, username):
    if re.search(r'\b(hi|hello|hey)\b', query, re.IGNORECASE):
        return f"Hello, {username}! How can I assist you today?"

    responses = []
    matched_keywords = []
    date_key = datetime.now().strftime('%Y-%m-%d')

    for keyword, answer in faq_responses.items():
        if re.search(rf"\b{keyword}\b", query, re.IGNORECASE):
            responses.append(answer)
            matched_keywords.append(keyword)

    if responses:
        update_chat_history_and_queries(username, matched_keywords, query, " ".join(responses), date_key)
        return " ".join(responses)
    
    return "I'm not sure how to help with that. Please ask something else or type 'logout' to end the session."

def update_chat_history_and_queries(username, matched_keywords, user_query, bot_response, date_key):
    user_doc = chat_collection.find_one({"username": username})
    
    chat_collection.update_one(
        {"username": username},
        {"$push": {f"chathistory.{date_key}": {"user_query": user_query, "bot_response": bot_response}}},
        upsert=True
    )

    existing_keywords = user_doc.get("user_queries", {}).get(date_key, []) if user_doc else []
    new_keywords = list(set(matched_keywords) - set(existing_keywords))
    
    if new_keywords:
        chat_collection.update_one(
            {"username": username},
            {"$push": {f"user_queries.{date_key}": {"$each": new_keywords}}},
            upsert=True
        )

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    if 'username' not in session:
        return jsonify({"error": "You are not logged in."}), 401

    username = session['username']
    chat_id = session['chat_id']
    
    chat_key = f"chat:{username}:{chat_id}"
    chat_history = r.lrange(chat_key, 0, -1)

    if chat_history:
        chat_history_list = []
        for i in range(0, len(chat_history), 2):
            user_message = chat_history[i].replace("user_message:", "")
            response = chat_history[i+1].replace("response:", "")
            chat_history_list.append({"user_query": user_message, "bot_response": response})

        date_key = datetime.now().strftime('%Y-%m-%d')

        existing_chat = chat_collection.find_one({"username": username, f"chathistory.{date_key}": {"$exists": True}})

        if existing_chat:
            chat_collection.update_one(
                {"username": username, f"chathistory.{date_key}": {"$exists": True}},
                {"$push": {f"chathistory.{date_key}": {"$each": chat_history_list}}}
            )
        else:
            chat_collection.update_one(
                {"username": username},
                {"$set": {f"chathistory.{date_key}": chat_history_list}},
                upsert=True
            )

    r.delete(chat_key)
    session.pop('username', None)
    session.pop('chat_id', None)

    return jsonify({"message": "You have been logged out successfully."}), 200

@app.route('/statistics', methods=['GET'])
def statistics():
    keyword_stats = {}

    for user_doc in chat_collection.find({}):
        for date, keywords in user_doc.get("user_queries", {}).items():
            for keyword in keywords:
                if keyword not in keyword_stats:
                    keyword_stats[keyword] = 0
                keyword_stats[keyword] += 1

    stats_list = [{"keyword": k, "count": v} for k, v in keyword_stats.items()]
    return jsonify({"statistics": stats_list}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
