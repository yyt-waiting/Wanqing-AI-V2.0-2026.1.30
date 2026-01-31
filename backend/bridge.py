# # backend/bridge.py
#过度文件使用，已废弃


# import threading
# import time
# import asyncio
# import base64
# from io import BytesIO
# from PIL import Image

# from ai_assistant.core.webcam_handler import WebcamHandler
# from ai_assistant.core.emotion_engine import EmotionEngine
# from socket_manager import manager

# # === [新增] 全局变量，用于存放主线程的事件循环 ===
# global_main_loop = None

# class HeadlessApp:
#     def __init__(self):
#         print("初始化无头适配器...")
#         self.status_text = "初始化中..."
#         self.emotion_engine = EmotionEngine() 
#         self.webcam_handler = WebcamHandler(self) 
#         self.after(1000, self.webcam_handler.start)

#     def after(self, delay_ms, func, *args):
#         def wrapper():
#             try:
#                 func(*args)
#             except Exception as e:
#                 print(f"后台任务出错: {e}")
#         t = threading.Timer(delay_ms / 1000.0, wrapper)
#         t.daemon = True
#         t.start()

#     def update_status(self, text: str):
#         print(f"[STATUS] {text}")

#     def broadcast_frame(self, image: Image.Image):
#         """
#         [修复版] 实时视频流通道
#         使用 run_coroutine_threadsafe 跨线程发送
#         """
#         try:
#             # 1. 如果主循环没准备好，就先不发
#             if not global_main_loop:
#                 return

#             # 2. 图片压缩
#             buffered = BytesIO()
#             img_resized = image.resize((640, 360)) 
#             img_resized.save(buffered, format="JPEG", quality=50)
#             img_str = base64.b64encode(buffered.getvalue()).decode()
            
#             payload = {
#                 "type": "video_frame",
#                 "data": f"data:image/jpeg;base64,{img_str}"
#             }
            
#             # 3. [核心修复] 线程安全发送！
#             # 告诉主线程的 Loop：“嘿，帮我执行一下 manager.broadcast”
#             asyncio.run_coroutine_threadsafe(manager.broadcast(payload), global_main_loop)
            
#         except Exception as e:
#             pass

#     def handle_analysis_result(self, timestamp, analysis_text, 
#                                behavior_num, behavior_desc, 
#                                emotion, screenshot,
#                                complex_emotion=None, 
#                                emotion_vector=None):
#         print(f"🚀 [分析完成] 行为:{behavior_desc} | 情绪:{emotion}")
        
#         # 处理截图用于展示
#         img_str = ""
#         if screenshot:
#             buffered = BytesIO()
#             screenshot.save(buffered, format="JPEG", quality=70)
#             img_str = base64.b64encode(buffered.getvalue()).decode()

#         payload = {
#             "type": "perception_update",
#             "data": {
#                 "timestamp": timestamp.isoformat(),
#                 "behavior": behavior_desc,
#                 "emotion": emotion,
#                 "complex_emotion": complex_emotion,
#                 "vector": emotion_vector,
#                 "analysis": analysis_text,
#                 "image": f"data:image/jpeg;base64,{img_str}"
#             }
#         }
        
#         # 分析结果频率低，也可以用同样的方式安全发送
#         if global_main_loop:
#              asyncio.run_coroutine_threadsafe(manager.broadcast(payload), global_main_loop)

# # 全局单例
# headless_wanqing = HeadlessApp()