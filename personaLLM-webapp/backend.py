#!/usr/bin/env python

import asyncio
import websockets
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import shutil

load_dotenv()  # this reads .env and sets environment variables

# Configure Gemini API key
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")

# Store chat sessions and their memory contexts
sessions = {}

# Global flag and content for uploaded file
has_uploaded_file = False
MEMORY_CONTEXT = ""

# FastAPI app for file uploads
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global has_uploaded_file, MEMORY_CONTEXT
    upload_dir = "data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    with open(file_path, "r", encoding="utf-8") as f:
        MEMORY_CONTEXT = f.read()
        has_uploaded_file = True

    return {"status": "success", "filename": file.filename}

async def echo(websocket):
    try:
        # Start a new Gemini chat session for this connection
        chat = model.start_chat()
        sessions[websocket] = chat

        async for message in websocket:
            print("Received message:", message, flush=True)

            # Reset session if user types 'reset'
            if message.strip().lower() == "reset":
                chat = model.start_chat()
                sessions[websocket] = chat
                await websocket.send("Session reset.")
                await websocket.send("[END]")
                continue

            # Use context only if file has been uploaded
            if has_uploaded_file and MEMORY_CONTEXT.strip():
                prompt = f"""
Below is context from a recently uploaded document:
{MEMORY_CONTEXT}

User's question:
{message}

Please answer the question based on the provided context.
"""
            else:
                prompt = message

            # Use existing session for contextual memory
            chat = sessions[websocket]
            response = chat.send_message(prompt)
            answer = response.text.strip()

            await websocket.send(answer)
            await websocket.send("[END]")

    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected", flush=True)
        sessions.pop(websocket, None)  # Clean up session
    except Exception as e:
        print(f"Error: {e}", flush=True)

from uvicorn import Config, Server

async def main():
    print("Starting backend servers...", flush=True)

    # Create FastAPI server
    config = Config(app=app, host="0.0.0.0", port=8000, log_level="info")
    fastapi_server = Server(config)

    # Start WebSocket and FastAPI server concurrently
    async with websockets.serve(echo, "0.0.0.0", int(os.environ.get("PORT", 8090))):
        print("WebSocket server running on port 8090", flush=True)
        await fastapi_server.serve()

        
if __name__ == "__main__":
    asyncio.run(main())