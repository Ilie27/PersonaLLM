# AI Memory Keeper 🧠

A minimalist, Gemini-powered chatbot that remembers.  
Upload notes, WhatsApp conversations, or journal entries — then ask questions like “When am I meeting with Alex?” or “What did I say to Victoria last week?”

Built using `chatbot-ui` as the frontend, and a custom Python backend that connects to Google's Gemini API, with vector search-based memory.

---

Upload notes, WhatsApp conversations, or journal entries — then ask natural questions like:  
> "When am I meeting with Alex?"  
> "What did I say to Victoria last week?"  
> "Who confirmed for the meeting?"

## ✨ Features

- ✅ Chat interface powered by Gemini 1.5 (via WebSocket)
- 🧠 Context-aware answers using your uploaded files
- 📎 Upload `.txt` or `.md` files (notes, WhatsApp chats, etc.)
- 💬 Real-time WebSocket responses with `[END]` signal
- 🗃️ FAISS vector search for memory retrieval
- 🧾 Markdown + multi-turn conversation support
- 🔁 Session memory (remembers past messages)
- 🔧 Easy to self-host and extend

---# PersonaLLM 🧠  


## 🛠️ Getting Started

Clone the project and move into the app folder:

```bash
git clone https://github.com/Ilie27/personaLLM.git
to run:
cd personaLLM-webapp

# also create your .env file here, example:
# export GEMINI_API_KEY="API_KEY"
# PORT=8090

Backend:
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python backend.py

Frontend:
npm i
npm start dev
