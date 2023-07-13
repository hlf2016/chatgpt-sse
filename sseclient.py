import asyncio
import json
from websockets.server import serve
import requests
# pip install sseclient-py
import sseclient

api_key = ''


async def echo(websocket):
    async for message in websocket:
        messages = [
            {'role': 'system', 'content': 'You\'re a helpful assistant named MacGPT. Provide clear and thorough answers but be concise'},
            {'role': 'user', 'content': message}
        ]
        url = ""
        payload = json.dumps({
            "max_tokens": 1200,
            "model": "gpt-3.5-turbo",
            "temperature": 0.8,
            "top_p": 1,
            "presence_penalty": 1,
            "stream": True,
            "messages":messages
        })
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
            'Authorization': 'Bearer '+api_key
        }
        response = requests.post(url, headers=headers, data=payload, stream=True)
        sseClient = sseclient.SSEClient(response)
        for event in  sseClient.events():
            if event.data != '[DONE]':
                print(event.data)
                await websocket.send(json.dumps(json.loads(event.data)['choices'][0]['delta']))
async def main():
    async with serve(echo, "0.0.0.0", 8888):
        await asyncio.Future()  # run forever

asyncio.run(main())
