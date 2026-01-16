from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client
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
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding

def semantic_search(query_text: str, k: int = 5) -> list[dict]:
    q_emb = embed_query(query_text)
    res = sb.rpc("match_chunks", {"query_embedding": q_emb, "match_count": k}).execute()
    rows = res.data or []
    print("RAG OUTPUT:", rows)  # console.log equivalent
    return rows


@app.get("/")
def index():
    return send_from_directory("public", "index.html")

@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "")

    # conduct semantic search to get the rows 
    rag_rows = semantic_search(user_message, k=5)


    # implement context
    context = "\n\n".join(
        f"[Source {i+1} | sim={row.get('similarity'):.3f}]\n{row.get('content','')}"
        for i, row in enumerate(rag_rows)
    )

    # system prompt this message
    rag_message = {
        "role": "system",
        "content": (
            "Use the retrieved context below to answer. If it doesn't contain the answer, say so.\n\n"
            f"RETRIEVED CONTEXT:\n{context if context else '(no matches)'}"
        ),
    }

    # wrap user message
    full_user_message = {
        "role": "user",
        "content": user_message,
    }

    full_message = [SYSTEM_PROMPT, full_user_message, rag_message]

    resp = client.responses.create(
        model="gpt-5-nano",
        input=full_message
    )
    return jsonify({"text": resp.output_text})

# Serves /styles.css, /app.js, etc.
@app.get("/<path:path>")
def static_files(path):
    return send_from_directory("public", path)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3000, debug=True)
