import os

# 定义基础路径
BASE_DIR = "backend"

# 定义文件结构和初始内容
structure = {
    "api": {
        "__init__.py": "",
        "websocket.py": """
from fastapi import WebSocket, WebSocketDisconnect
from socket_manager import manager
import json
import asyncio

# 导入各个服务实例
from services.chat_service import chat_service
from services.monitor_service import monitor_service
# from services.voice_service import voice_service (后续实现)

async def handle_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg_obj = json.loads(data)
                msg_type = msg_obj.get("type")

                # 路由分发
                if msg_type == "chat":
                    # 调用对话服务
                    await chat_service.handle_user_message(msg_obj.get("text"))
                
                elif msg_type == "toggle_camera":
                    # 调用监控服务
                    monitor_service.toggle_camera()

            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WS Error: {e}")
        manager.disconnect(websocket)
"""
    },
    "services": {
        "__init__.py": "",
        "chat_service.py": """
import json
from datetime import datetime
from ai_assistant.core.api_clients import deepseek_client
from socket_manager import manager
from services.memory_service import memory_service

class ChatService:
    def __init__(self):
        self.history = [] # 短期记忆

    def build_system_prompt(self):
        # 从 MemoryService 获取日志
        recent_logs = memory_service.get_recent_logs()
        current_time = datetime.now().strftime("%H:%M")
        
        # 你的核心人设 (从 multimedia_assistant.py 搬运)
        return f\"\"\"
【System Role Definition】
你是“婉晴”，用户“溢涛”的**情感共鸣伙伴**。
当前时间：{current_time}
最近观察：
{recent_logs}
\"\"\"

    async def handle_user_message(self, user_text: str):
        # 1. 组装 Prompt
        sys_prompt = self.build_system_prompt()
        messages = [{"role": "system", "content": sys_prompt}] + self.history[-10:] + [{"role": "user", "content": user_text}]
        
        # 2. 调用 DeepSeek
        print("🤔 婉晴正在思考...")
        try:
            response = deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                stream=False
            )
            reply = response.choices[0].message.content
            
            # 3. 更新历史
            self.history.append({"role": "user", "content": user_text})
            self.history.append({"role": "assistant", "content": reply})
            
            # 4. 发送回前端
            await manager.broadcast({
                "type": "chat_message",
                "data": reply
            })
            
            # TODO: 调用 VoiceService 说话
            
        except Exception as e:
            print(f"DeepSeek Error: {e}")

chat_service = ChatService()
""",
        "monitor_service.py": """
import asyncio
import base64
from io import BytesIO
from PIL import Image
import threading

# 引用核心算法库
from ai_assistant.core.webcam_handler import WebcamHandler
from ai_assistant.core.emotion_engine import EmotionEngine
from socket_manager import manager

# 这是一个升级版的 Bridge
class MonitorService:
    def __init__(self):
        self.emotion_engine = EmotionEngine()
        # 将自己传入 WebcamHandler，以便接收回调
        self.webcam_handler = WebcamHandler(self)
        self.main_loop = None # 主线程 Loop

    def start(self, loop):
        self.main_loop = loop
        # 延迟启动摄像头
        threading.Timer(1.0, self.webcam_handler.start).start()

    # --- 核心回调接口 ---
    def update_status(self, text):
        print(f"[Monitor] {text}")

    def broadcast_frame(self, image: Image.Image):
        # 视频流快车道
        if not self.main_loop: return
        try:
            buffered = BytesIO()
            image.resize((640, 360)).save(buffered, format="JPEG", quality=50)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            payload = {"type": "video_frame", "data": f"data:image/jpeg;base64,{img_str}"}
            asyncio.run_coroutine_threadsafe(manager.broadcast(payload), self.main_loop)
        except: pass

    def handle_analysis_result(self, timestamp, analysis_text, behavior_num, behavior_desc, emotion, screenshot, complex_emotion=None, emotion_vector=None):
        # AI 分析慢车道
        # 1. 保存日志 (调用 MemoryService)
        # from services.memory_service import memory_service
        # memory_service.save_log(...)
        
        # 2. 推送给前端
        if self.main_loop:
            payload = {
                "type": "perception_update",
                "data": {
                    "emotion": emotion,
                    "behavior": behavior_desc,
                    "vector": emotion_vector,
                    "analysis": analysis_text
                }
            }
            asyncio.run_coroutine_threadsafe(manager.broadcast(payload), self.main_loop)

monitor_service = MonitorService()
""",
        "memory_service.py": """
import os
import json
from datetime import datetime

class MemoryService:
    def get_recent_logs(self, limit=5):
        today = datetime.now().strftime('%Y-%m-%d')
        # 假设 logs 存在 storage 目录下
        # 此处需要根据实际路径调整
        return "（暂无日志，记忆模块连接中...）"

    def save_log(self, data):
        # 将观察结果写入 jsonl
        pass

memory_service = MemoryService()
""",
        "decision_service.py": """
import asyncio
# from ai_assistant.core.decision_maker import DecisionMaker

class DecisionService:
    def __init__(self):
        # self.engine = DecisionMaker()
        self.running = False

    async def start_monitoring(self):
        self.running = True
        while self.running:
            # 每 5 秒思考一次是否需要主动关怀
            await asyncio.sleep(5)
            # logic...

decision_service = DecisionService()
""",
        "voice_service.py": """
# 这里将处理 TTS
class VoiceService:
    def speak(self, text):
        pass
        
voice_service = VoiceService()
"""
    },
    "storage": {
        "logs": {} # 空文件夹
    }
}

def create_structure(base, struct):
    for name, content in struct.items():
        path = os.path.join(base, name)
        
        if isinstance(content, dict):
            # 是文件夹
            if not os.path.exists(path):
                os.makedirs(path)
                print(f"📁 创建目录: {path}")
            create_structure(path, content)
        else:
            # 是文件
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content.strip())
                print(f"📄 创建文件: {path}")
            else:
                print(f"⚠️ 跳过已存在: {path}")

if __name__ == "__main__":
    if not os.path.exists(BASE_DIR):
        print(f"❌ 错误：找不到 {BASE_DIR} 目录，请确保脚本在 Wanqing 根目录下运行。")
    else:
        print("🚀 开始构建 MVC 架构...")
        create_structure(BASE_DIR, structure)
        
        # 最后，我们需要更新 main.py 来使用新架构
        print("\n✅ 架构生成完毕！")
        print("下一步：请手动修改 backend/main.py，引入 api.websocket 并启动 services。")