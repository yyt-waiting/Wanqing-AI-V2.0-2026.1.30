# backend/api/websocket.py
import json
from fastapi import WebSocket, WebSocketDisconnect
from socket_manager import manager

# 导入业务服务层
from services.chat_service import chat_service
from services.monitor_service import monitor_service

async def handle_websocket(websocket: WebSocket):
    """
    【WebSocket 路由分发器】
    职责：负责接收前端原始消息，并根据 type 分发给不同的 Service。
    """
    # 1. 建立连接
    success = await manager.connect(websocket)
    if not success:
        return

    try:
        while True:
            # 2. 等待接收前端消息
            data = await websocket.receive_text()
            
            try:
                msg_obj = json.loads(data)
                msg_type = msg_obj.get("type")
                
                # --- 路由分发逻辑 ---
                
                # A. 聊天类型 -> 交给 ChatService
                if msg_type == "chat":
                    user_text = msg_obj.get("text")
                    # 我们用 await 调用 ChatService 的异步处理方法
                    # 这样 main.py 就不需要关心 DeepSeek 怎么调了
                    await chat_service.handle_user_message(user_text)
                
                # B. 指令类型 -> 交给 MonitorService (比如控制摄像头开关)
                elif msg_type == "instruction":
                    action = msg_obj.get("action")
                    if action == "toggle_camera":
                        monitor_service.toggle_camera()
                
                # C. 以后可以扩展的心跳检测或其他功能
                elif msg_type == "ping":
                    manager.broadcast({"type": "pong"})
                
                
                elif msg_type == "request_summary":
                    await chat_service.generate_daily_summary()

            except json.JSONDecodeError:
                print("⚠️ [WS] 收到非 JSON 格式数据")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"❌ [WS 路由异常] {e}")
        manager.disconnect(websocket)