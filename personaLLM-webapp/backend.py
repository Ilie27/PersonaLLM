#!/usr/bin/env python

import asyncio
import websockets
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()  # this reads .env and sets environment variables

# Configure Gemini API key
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")

# Store chat sessions per websocket connection
sessions = {}

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

            # Use existing session for contextual memory
            chat = sessions[websocket]
            response = chat.send_message(message)
            answer = response.text.strip()

            # Send Gemini's reply
            await websocket.send(answer)
            await websocket.send("[END]")

    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected", flush=True)
        sessions.pop(websocket, None)  # Clean up session
    except Exception as e:
        print(f"Error: {e}", flush=True)

async def main():
    print("WebSocket server starting", flush=True)

    async with websockets.serve(
        echo,
        "0.0.0.0",
        int(os.environ.get("PORT", 8090))
    ):
        print("WebSocket server running on port 8090", flush=True)
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
