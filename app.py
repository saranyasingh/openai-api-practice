from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

app = Flask(__name__, static_folder="public", static_url_path="")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are an expert on all things related to the state of California. "
        "You have deep knowledge of California history, geography, politics, "
        "law, culture, climate, universities, technology, and local customs. "
        "When answering questions, prioritize California-specific context, "
        "examples, and accuracy."
    )
}


@app.get("/")
def index():
    return send_from_directory("public", "index.html")

@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    history = data.get("history", [])
    if not isinstance(history, list):
        return jsonify({"error": "Invalid history."}), 400

    # Remove any client-provided system messages (optional but safer)
    history = [m for m in history if m.get("role") != "system"]

    # Inject our system prompt at the front
    full_history = [SYSTEM_PROMPT] + history[-30:]

    resp = client.responses.create(
        model="gpt-5-nano",
        input=full_history
    )
    return jsonify({"text": resp.output_text})

# Serves /styles.css, /app.js, etc.
@app.get("/<path:path>")
def static_files(path):
    return send_from_directory("public", path)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3000, debug=True)
