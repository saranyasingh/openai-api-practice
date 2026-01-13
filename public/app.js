const chat = document.getElementById("chat");
const form = document.getElementById("form");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");

// This is what we send to the backend each time:
const history = [];

function addMessage(text, who) {
  const div = document.createElement("div");
  div.className = `msg ${who}`;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}

async function sendMessage(message) {
  sendBtn.disabled = true;
  input.disabled = true;

  addMessage(message, "user");
  history.push({ role: "user", content: message });

  const thinking = addMessage("…", "bot");

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ history }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data?.error || "Request failed");

    const botText = data.text || "(no response)";
    thinking.textContent = botText;
    history.push({ role: "assistant", content: botText });
  } catch (err) {
    thinking.textContent = `Error: ${err.message}`;
  } finally {
    sendBtn.disabled = false;
    input.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message) return;
  input.value = "";
  sendMessage(message);
});

// Optional: greet AND include it in history so the bot “remembers” it.
const greeting = "Hi! Ask me anything.";
addMessage(greeting, "bot");
history.push({ role: "assistant", content: greeting });
