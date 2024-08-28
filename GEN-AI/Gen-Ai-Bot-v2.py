import requests
import json
from pymongo import MongoClient
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client['spotify_bot']
users_collection = db['users']
chat_collection = db['chat']
recommendation_collection = db['recommendation']

def get_user_data(phone):
    user_data = users_collection.find_one({"phone": phone})
    data = recommendation_collection.find_one()
    recommendation_data = {
    "kannada": data.get("kannada", []),
    "tamil": data.get("tamil", []),
    "telugu": data.get("telugu", []),
    "malayalam": data.get("malayalam", []),
    "hindi": data.get("hindi", [])
    }
    return user_data, recommendation_data

def register_user():
    while True:
        phone = input("Enter your phone number (10 digits): ")
        if len(phone) == 10 and phone.isdigit():
            existing_user = users_collection.find_one({"phone": phone})
            if existing_user:
                print("This phone number is already registered.")
                continue
            else:
                full_name = input("Enter your full name: ")
                languages = input("Enter preferred languages (comma-separated): ").split(',')
                languages = [lang.strip() for lang in languages]
      
                user_data = {
                    "phone": phone,
                    "full_name": full_name,
                    "language": languages
                }

                users_collection.insert_one(user_data)
                
                print(f"User registered successfully! Your phone number is {phone}.")
                return phone
        else:
            print("Invalid phone number. Please enter a valid 10-digit phone number.")


def build_system_prompt(user_data, recommendation_data):
    system_prompt = f"""
    You are a customer support assistant for Spotify, a leading music streaming service. Your role is to help users with questions about their Spotify accounts, including setting up accounts, logging in, recovering passwords, managing subscriptions, and more.

    User's full name: {user_data['full_name']}
    Preferred languages: {', '.join(user_data['language'])}
    Recommendation playlist data: {recommendation_data}

    Instructions for assistance:
    - Welcome message : "Hello {user_data['full_name']}, welcome. I'm virtual spotify assistant. Let me know how can i help you. If you want to log out of the chat, just say "bye bye!".
    - Execute the welcome message only for one time at the begining of the chat and then proceed with further chat of assistance.
    - Provide Spotify-related assistance only. If the user asks about non-Spotify topics, politely redirect them to Spotify-related inquiries.
    - Recommendations should be based on the provided playlist data. If a user requests a playlist in a specific language and it is available in the Recommendation playlist data, recommend it, even if the language is not in the user's preferred languages.
    - Only recommend one playlist link per query, and the next time user asks send another link of from the language user previously asked.
    - If the requested playlist is not found in the Recommendation playlist data, guide the user on how to search for it on Spotify.
    - Logout/goodbye message : bye bye!
        - If user's query context is like getting out of the chat like saying something bye bye then execute goodbye message, and strictly it should be goodbye message only.

    Scenarios:
    1. Suppose user asks a question like creating spotify account, Provide a step-by-step guide in response
    2. If asked about personal information, only state the user’s name and explain that no other information can be accessed due to security policy.
    3. If asked for recommendations without specifying a language, recommend a playlist in one of the user’s preferred languages and if the language not found help the user with gudielines how can he find those.
    4. If the user repeatedly asks for recommendations in a specific language, send a different link from the same language.
    5. If the user asks for a playlist in a language not in the provided data, explain that no recommendations are available and guide them step by step them on how to search for playlists in that language.

    """
    return system_prompt

def get_response(user_input, conversation_history, system_prompt):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=API_KEY"
    conversation_history.append({"role": "user", "content": user_input})
    payload = json.dumps({
        "contents": [
            {
                "parts": [
                    {
                       "text": f"""{system_prompt}\n\n{' '.join([f"{entry['role']}: {entry['content']}" for entry in conversation_history])}"""
                    }
                ]
            }
        ]
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)

    try:
        response_json = json.loads(response.text)
        ai_response = response_json['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError):
        ai_response = "I'm sorry, there seems to be an issue with processing your request. Please try again later."

    conversation_history.append({"role": "assistant", "content": ai_response})

    print(f"\nUser: {user_input}")
    print(f"Bot: {ai_response}\n")
    return ai_response


def start_chat(phone):
    user_data, recommendation_data = get_user_data(phone)
    if user_data:
        system_prompt = build_system_prompt(user_data, recommendation_data)
        print(f"Hello {user_data['full_name']}! You can start chating now.")
        conversation_history = []
        while True:
            user_input = input("You: ")

            ai_response = get_response(user_input, conversation_history, system_prompt)
            date_str = datetime.now().strftime("%Y-%m-%d")
            chat_collection.update_one(
                {"phone": phone},
                {"$push": {f"chat.{date_str}": {"User": user_input, "Bot": ai_response}}},
                upsert=True
            )

            if ai_response.strip().lower() == "bye bye!":
                print("Logging out..........,")
                break
    else:
        print("This phone number is not registered. Please register to start chatting.")

def main():
    print("Welcome to the Spotify AI assistant!")
    while True:
        phone = input("Please enter your phone number to start chatting or type 'register' to create a new account: ")
        if phone.lower() == 'register':
            phone = register_user()
            start_chat(phone)
            break
        elif len(phone) == 10 and phone.isdigit():
            if users_collection.find_one({"phone": phone}):
                start_chat(phone)
                break
            else:
                print("This phone number is not registered. Please register to start chatting.")
        else:
            print("Invalid input. Please enter a valid 10-digit phone number or type 'register'.")

if __name__ == "__main__":
    main()
