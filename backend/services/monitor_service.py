# backend/services/monitor_service.py
import asyncio
import base64
import threading
from io import BytesIO
from PIL import Image
from datetime import datetime

# 导入原来的底层核心
from ai_assistant.core.webcam_handler import WebcamHandler
from ai_assistant.core.emotion_engine import EmotionEngine
# 导入通信管家实例


from socket_manager import manager
from services.memory_service import memory_service
from services.decision_service import decision_service

class MonitorService:
    """
    【视觉与感知服务】
    原身份: bridge.py / HeadlessApp
    职责: 连接底层硬件摄像头与 Web 通信层，负责视频推流与感知结果分发。
    """
    def __init__(self):
        self.status_text = "初始化中..."
        # 初始化情感引擎 (学术数学模型)
        self.emotion_engine = EmotionEngine()
        # 初始化摄像头处理器，并把自己作为 app 传入 (Adapter Pattern)
        self.webcam_handler = WebcamHandler(self)
        self.main_loop = None # 用于跨线程通信的句柄

    def start(self, loop):
        """由主线程启动服务"""
        self.main_loop = loop
        print("📸 [MonitorService] 启动摄像头捕获线程...")
        # 延迟 1 秒启动，确保事件循环已完全稳定
        threading.Timer(1.0, self.webcam_handler.start).start()

    # --- 兼容性接口: 欺骗 WebcamHandler 的回调 ---
    
    def update_status(self, text: str):
        """模拟原 Tkinter 的状态栏更新"""
        print(f"👁️ [Perception Status] {text}")

    def after(self, delay_ms, func, *args):
        """模拟原 Tkinter 的定时任务"""
        def wrapper():
            try: func(*args)
            except Exception as e: print(f"❌ 后台任务出错: {e}")
        t = threading.Timer(delay_ms / 1000.0, wrapper)
        t.daemon = True
        t.start()

    # --- 核心数据分发接口 ---

    def broadcast_frame(self, image: Image.Image):
        """
        [快车道] 实时视频流
        由 WebcamHandler 在其独立线程中高频调用 (约 20fps)
        """
        if not self.main_loop: return
        
        try:
            # 1. 压缩图像以提升 B/S 传输速度
            buffered = BytesIO()
            img_resized = image.resize((640, 360)) 
            img_resized.save(buffered, format="JPEG", quality=50) # 50%质量足够预览
            
            # 2. 转为 Base64 字符串
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            payload = {
                "type": "video_frame",
                "data": f"data:image/jpeg;base64,{img_str}"
            }
            
            # 3. 线程安全地扔进 Socket 管理器的队列中
            self.main_loop.call_soon_threadsafe(manager.broadcast, payload)
        except Exception:
            pass # 视频流允许少量掉帧，不报错

    def handle_analysis_result(self, timestamp, analysis_text, 
                               behavior_num, behavior_desc, 
                               emotion, screenshot,
                               complex_emotion=None, 
                               emotion_vector=None):
        """
        [慢车道] AI 分析结果
        当 Qwen-VL 完成分析后调用
        """
        print(f"🚀 [视觉分析完成] 行为:{behavior_desc} | 情绪:{emotion}")

         # === [新增] 每一轮分析结果出来后，立即存入本地日志 ===
        observation_data = {
            "timestamp": timestamp,
            "behavior_num": behavior_num,
            "behavior_desc": behavior_desc,
            "emotion": emotion,
            "complex_emotion": complex_emotion,
            "vector": emotion_vector,
            "analysis": analysis_text
        }
        memory_service.save_log(observation_data)
        # ===============================================
        #后期会改变应该？
        arousal = self.emotion_engine.get_arousal_level()
        
        # 异步启动决策任务 (不阻塞主循环)
        if self.main_loop:
            asyncio.run_coroutine_threadsafe(
                decision_service.process_new_observation(
                    behavior_desc, emotion, complex_emotion, arousal
                ), 
                self.main_loop
            )



        # 处理截图
        img_str = ""
        if screenshot:
            buffered = BytesIO()
            screenshot.save(buffered, format="JPEG", quality=70)
            img_str = base64.b64encode(buffered.getvalue()).decode()

        # 打包感知数据
        payload = {
            "type": "perception_update",
            "data": {
                "timestamp": timestamp.isoformat(),
                "behavior": behavior_desc,
                "emotion": emotion,
                "complex_emotion": complex_emotion,
                "vector": emotion_vector,
                "analysis": analysis_text,
                "image": f"data:image/jpeg;base64,{img_str}"
            }
        }
        
        # 同样放入队列发送
        if self.main_loop:
            self.main_loop.call_soon_threadsafe(manager.broadcast, payload)

# 单例导出
monitor_service = MonitorService()