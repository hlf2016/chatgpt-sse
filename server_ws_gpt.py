import openai
import asyncio
import json
from websockets.server import serve
from utils import load_env

env_config = load_env()

openai.api_key = env_config.get('OPENAI_API_KEY')


async def echo(websocket):
    async for message in websocket:
        messages = [
            {'role': 'system', 'content': 'You\'re a helpful assistant named MacGPT. Provide clear and thorough answers but be concise'},
            {'role': 'user', 'content': message}
        ]
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=messages,
            temperature=0,
            stream=True  # this time, we set stream=True
        )
        for completion in response:
            delta = completion.get('choices')[0].get('delta')
            if delta.get('content') or delta.get('role'):
                await websocket.send(json.dumps(delta))


async def main():
    async with serve(echo, "localhost", 8765):
        await asyncio.Future()  # run forever

asyncio.run(main())
