from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client
import os
from collections import deque

load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
print(os.environ.get("OPENAI_API_KEY"))

# Keep history bounded so you don't blow context/tokens
MAX_TURNS = 20  # each "turn" is one message; 20 means up to 20 messages stored
CHAT_ONE_HISTORY = deque(maxlen=MAX_TURNS)
CHAT_TWO_HISTORY = deque(maxlen=MAX_TURNS)

# Supabase (use service role on backend)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
sb1 = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
sb2 = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are an expert on all things related to the state of California. "
        "You have deep knowledge of California history, geography, politics, "
        "law, culture, climate, universities, technology, and local customs. "
        "When answering questions, prioritize California-specific context, "
        "examples, and accuracy. "
        "Additionally, you are talking to another chatbot. This means that if conversation "
        "stalls, you must generate questions to continue the conversation. Be eager to talk about California "
        "but also engage in the other bot's interests. Always repeat the question you are asked."
        "I will also pass in a chat history, just for context. This is NOT the question you are being asked, "
        "it is just context from previous conversations."

    )
}

def embed_query(text: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def semantic_search(query_text: str, sb_client, k: int = 5) -> list[dict]:
    q_emb = embed_query(query_text)
    res = sb_client.rpc("match_chunks", {"query_embedding": q_emb, "match_count": k}).execute()
    rows = res.data or []
    print("RAG OUTPUT:", rows)
    return rows

def build_rag_message(user_message, sb_client) -> dict:
    rag_rows = semantic_search(user_message, sb_client, k=5)

    context = "\n\n".join(
        f"[Source {i+1} | sim={row.get('similarity'):.3f}]\n{row.get('content','')}"
        for i, row in enumerate(rag_rows)
    )

    return {
        "role": "system",
        "content": (
            "Use the retrieved context below to answer. If it doesn't contain the answer, say so.\n\n"
            f"RETRIEVED CONTEXT:\n{context if context else '(no matches)'}"
        ),
    }

def run_bot(user_message, history, sb_client) -> str:
    # RAG should be based on the latest message (simple + works well)
    rag_message = build_rag_message(user_message, sb_client)

    user_msg = {"role": "user", "content": user_message}

    messages = [
        SYSTEM_PROMPT,
        *list(history),
        rag_message,
        user_msg    # latest user input
    ]

    resp = client.responses.create(
        model="gpt-5-nano",
        input=messages
    )
    assistant_text = resp.output_text


    # Save turns to that bot's local history
    history.append({"role": "user", "content": "This is history of previous user messages" + user_message})
    history.append({"role": "assistant", "content": "This is history of your previous answers" + assistant_text})

    return assistant_text

def chatone(user_message: str) -> str:
    return run_bot(user_message, CHAT_ONE_HISTORY, sb1)

def chattwo(user_message: str) -> str:
    return run_bot(user_message, CHAT_TWO_HISTORY, sb2)

def chat_communication():
    output = chatone("Tell me about a fun fact, then ask a question to the other chatbot related to the fun fact to get started.")
    print("BOT ONE SAYS:\n" + output + "\n")

    for _ in range(10):
        output = chattwo("Respond directly to the question in the message below.\n\n" + output)
        print("BOT TWO SAYS:\n" + output + "\n")

        output = chatone("Respond directly to the question in the message below.\n\n" + output)
        print("BOT ONE SAYS:\n" + output + "\n")

chat_communication()
