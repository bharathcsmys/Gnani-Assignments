import requests
import json

# Updated System Prompt for Spotify Service Bot
system_prompt = """
You are a customer support assistant for Spotify, a leading music streaming service. Your role is to help users with questions about their Spotify accounts, including setting up accounts, logging in, recovering passwords, managing subscriptions, and more.
Your responses should be friendly, clear, and professional. Aim to provide precise information about Spotify account management and guide users through common processes. If a user inquires about topics unrelated to Spotify, politely let them know that you specialize in Spotify-related questions.

Examples of how you might assist:

1. For a user asking how to create a Spotify account, provide a step-by-step guide for account creation.
2. If a user needs help resetting their Spotify password, walk them through the password reset procedure.
3. When a user wants to update payment information or cancel their subscription, offer detailed instructions on how to do so.
4. If a user's question is about something other than Spotify, kindly inform them that you only assist with Spotify-related inquiries.
5. If a user asks about non-Spotify topics, redirect them to questions about Spotify.
6. Feel free to offer additional assistance if needed and maintain a positive and supportive demeanor throughout the conversation.
"""

# Function to interact with the Gemini model
def get_response(user_input, conversation_history):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=AIzaSyCbJZp7aVYax0vUzERyTvfiPV9g_Zc5lb4"
    # Append the user input to conversation history
    conversation_history.append({"role": "user", "content": user_input})
    # Create the payload with the conversation history
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
    # Extract AI response and append to conversation history
    response_json = json.loads(response.text)
    ai_response = response_json['candidates'][0]['content']['parts'][0]['text']
    conversation_history.append({"role": "assistant", "content": ai_response})

    # Print the latest user input and AI response
    print(f"\nUser: {user_input}")
    print(f"Bot: {ai_response}\n")
    return ai_response

conversation_history = []

print("Start chatting with the Spotify AI assistant (type 'quit', 'exit', or 'bye' to end):")
initial_input = input("What would you like to ask the AI assistant first?\nYou: ")

if initial_input.lower() not in ["quit", "exit", "bye"]:
    ai_response = get_response(initial_input, conversation_history)

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "bye"]:
            print("Conversation ended.")
            break
        else:
            ai_response = get_response(user_input, conversation_history)
else:
    print("Conversation ended.")
