import openai
import json
import uvicorn
import asyncio
import time
from redis import StrictRedis
from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from utils import load_env


app = FastAPI()

# 处理跨域
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

env_config = load_env()

rds = StrictRedis(host=env_config.get('REDIS_HOST', 'localhost'), port=env_config.get(
    'REDIS_PORT', 6379), db=env_config.get('REDIS_DB', 0), decode_responses=True)

STREAM_DELAY = 1  # second
RETRY_TIMEOUT = 25000  # milisecond
openai.api_key = env_config.get('OPENAI_API_KEY')


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/stream")
async def message_stream(request: Request, msg: str, name: str):
    messages = [
        {'role': 'system', 'content': 'You\'re a helpful assistant named MacGPT. Provide clear and thorough answers but be concise'}
    ]
    msg_tm = time.time()
    # redis 中 key 的命名规则
    messages_key = f'{name}_messages'
    rds.zadd(messages_key, {json.dumps(
        {'msg': {'role': 'user', 'content': msg}, 'tm': msg_tm}): msg_tm})
    # 倒序获取 messages_key 对应的 value
    pre_messages = rds.zrange(messages_key, -6, -1)
    if pre_messages:
        # pre_messages.reverse()
        # `extend()` 方法用于将一个列表中的元素添加到另一个列表的末尾
        messages.extend([json.loads(msg).get('msg') for msg in pre_messages])
    # print(messages)
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=messages,
        temperature=0,
        stream=True  # this time, we set stream=True
    )

    async def event_generator():
        # If client closes connection, stop sending events
        if await request.is_disconnected():
            print('disconnected')
        # gpt消息的组装
        gpt_msg = ''
        # Checks for new messages and return them to client if any
        for completion in response:
            delta = completion.get('choices')[0].get('delta')
            finish_reason = completion.get(
                'choices')[0].get('finish_reason')
            if delta:
                if delta.get('content'):
                    gpt_msg += delta.get('content')
                yield json.dumps(delta)

            if finish_reason == 'stop':
                # 将回复内容存入 redis
                gpt_msg_tm = time.time()
                rds.zadd(messages_key, {json.dumps(
                    {'msg': {'role': 'assistant', 'content': gpt_msg}, 'tm': gpt_msg_tm}): gpt_msg_tm
                })
                yield 'stop'

            # await asyncio.sleep(STREAM_DELAY)
    return EventSourceResponse(event_generator())
    # return StreamingResponse(event_generator())

if __name__ == "__main__":
    uvicorn.run('main:app', host="0.0.0.0", port=8000, reload=True)
