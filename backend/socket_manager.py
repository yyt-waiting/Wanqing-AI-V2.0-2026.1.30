# backend/socket_manager.py
import asyncio
from fastapi import WebSocket
from typing import List
import json
import traceback

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.broadcast_queue = asyncio.Queue()
        self.sender_task = None

    def start_sender_worker(self):
        print("🚦 [Socket] 启动广播队列发货员...")
        self.sender_task = asyncio.create_task(self._broadcast_worker())

    async def _broadcast_worker(self):
        while True:
            try:
                message = await self.broadcast_queue.get()
                json_str = json.dumps(message, ensure_ascii=False)
                for connection in list(self.active_connections):
                    try:
                        await connection.send_text(json_str)
                    except Exception:
                        self.disconnect(connection) 
                self.broadcast_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception:
                traceback.print_exc()
                await asyncio.sleep(1)

    async def connect(self, websocket: WebSocket):
        """[修改] 内部处理 accept，如果失败则不加入列表"""
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            print(f"✅ [Socket] 连接成功。当前在线: {len(self.active_connections)}")
            return True
        except Exception as e:
            print(f"❌ [Socket] 握手阶段失败: {e}")
            return False

    def disconnect(self, websocket: WebSocket):
        """[核心修复] 安全移除，防止 ValueError 导致程序崩溃"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"❌ [Socket] 连接已断开。剩余在线: {len(self.active_connections)}")

    def broadcast(self, message: dict):
        """[注意] 这是同步函数，不加 await"""
        self.broadcast_queue.put_nowait(message)

manager = ConnectionManager()