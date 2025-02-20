import json
import google.generativeai as genai
import wikipediaapi  # Replace wikipedia with wikipedia-api
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Load your personal data
with open("mumbere_darius_profile.json", "r") as file:
    personal_data = json.load(file)

# Directly set your API key here
api_key = "AIzaSyAN23PVrXsIBkYO43JVrXa69hdbRvBqkoY"  # Replace with your actual key

# Configure Gemini API
genai.configure(api_key=api_key)

# Initialize Wikipedia API
wiki_wiki = wikipediaapi.Wikipedia(
    language='en',  # Language of Wikipedia
    user_agent='MyApp/1.0 (myemail@example.com)'  # User agent string
)

# Initialize conversation history
conversation_history = []

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Function to generate AI responses with context
def ask_gemini(question, history):
    model = genai.GenerativeModel("gemini-pro")
    prompt = (
        "You are a helpful assistant. You have access to the following personal data:\n"
        f"{personal_data_to_string(personal_data)}\n\n"
        "If the user's question is related to the above data, use it to answer. "
        "If the question is unrelated, use your general knowledge to answer.\n\n"
        "Format your responses clearly.\n\n"
    )
    if history:
        prompt += "Conversation History:\n"
        for turn in history:
            prompt += f"User: {turn['user']}\nAI: {turn['ai']}\n"
    prompt += f"Question: {question}\nAnswer:"

    try:
        response = model.generate_content(prompt)
        if response:
            return format_response(response.text)
        else:
            return None  # Return None if Gemini fails
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return None

# Wikipedia Integration using wikipedia-api
def search_wikipedia(query):
    page = wiki_wiki.page(query)
    if page.exists():
        return page.summary  # Return the summary of the page
    else:
        return "Sorry, I couldn't find relevant information on Wikipedia."

def personal_data_to_string(data):
    def flatten(d, parent_key="", sep="_"):
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    items.extend(flatten({str(i): item}, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    flat_data = flatten(data)
    return "\n".join([f"{k}: {v}" for k, v in flat_data.items()])

def format_response(response):
    lines = response.split("\n")
    formatted_response = ""
    for line in lines:
        line = line.strip()
        if line.startswith(("* ", "- ", "1. ", "2. ", "3. ")):
            formatted_response += f"{line}\n"
        elif line.endswith(":"):
            formatted_response += f"**{line}**\n\n"
        elif line:
            formatted_response += f"{line}\n\n"
    return formatted_response.strip()

# Flask API
app = Flask(__name__)
CORS(app)

@app.route("/ask", methods=["POST"])
def ask_question():
    user_question = request.json.get("question")
    if not user_question:
        return jsonify({"error": "No question provided"}), 400
    
    # First try to get an answer from Gemini
    answer = ask_gemini(user_question, conversation_history)
    
    # If Gemini fails, try Wikipedia
    if not answer:
        answer = search_wikipedia(user_question)
    
    # If both Gemini and Wikipedia fail, provide a default response
    if not answer:
        answer = "Sorry, I couldn't find an answer to your question."
    
    conversation_history.append({"user": user_question, "ai": answer})
    if len(conversation_history) > 5:
        conversation_history.pop(0)

    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)