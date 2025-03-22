#!/usr/bin/env python

import asyncio
import websockets
import os
import json
import google.generativeai as genai

# Configure Gemini API key
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Create Gemini model
model = genai.GenerativeModel("gemini-pro")

async def echo(websocket):
    try:
        async for message in websocket:
            print("Received message:", message, flush=True)

            # Ask Gemini the message
            response = model.generate_content(message)
            answer = response.text.strip()

            # Send Gemini's reply back to frontend
            await websocket.send(answer)
            await websocket.send("[END]")
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected", flush=True)
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
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
