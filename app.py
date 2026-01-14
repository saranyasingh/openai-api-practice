from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

app = Flask(__name__, static_folder="public", static_url_path="")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Supabase (use service role on backend)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

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

def embed_query(text: str) -> list[float]:
    """
    Generate an embedding for a user query using OpenAI.
    Returns a list of floats (the embedding vector).
    """
    if not text or not isinstance(text, str):
        raise ValueError("Text to embed must be a non-empty string")

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding



@app.get("/")
def index():
    return send_from_directory("public", "index.html")

@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    history = data.get("history", [])
    if not isinstance(history, list):
        return jsonify({"error": "Invalid history."}), 400
    
    # Get the latest user message
    user_message = next(
        (m["content"] for m in reversed(history) if m.get("role") == "user"),
        None,
    )
    if not user_message:
        return jsonify({"error": "No user message found"}), 400

    # 🔹 Embed the user query
    query_embedding = embed_query(user_message)



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
