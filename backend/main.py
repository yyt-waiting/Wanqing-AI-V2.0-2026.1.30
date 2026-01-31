# backend/main.py
import sys
import os
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

# 路径修复
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from socket_manager import manager
from services.monitor_service import monitor_service
from api.websocket import handle_websocket # 导入刚才写的分发器

app = FastAPI(title="Wanqing AI MVC-Ready")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def startup_event():
    print("⚡ [System] 系统正在启动...")
    loop = asyncio.get_running_loop()
    # 1. 启动唯一的发货员
    manager.start_sender_worker()
    # 2. 启动视觉服务
    monitor_service.start(loop)
    print("✅ [System] 核心服务初始化完毕")

@app.get("/")
async def index():
    return {"status": "online", "arch": "MVC-BS"}

# 极简的 WebSocket 入口
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # 直接把连接扔给 api 层的 handle_websocket 处理
    await handle_websocket(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)