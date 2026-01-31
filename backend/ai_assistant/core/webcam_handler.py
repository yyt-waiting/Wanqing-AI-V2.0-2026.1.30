# ai_assistant/core/webcam_handler.py
import cv2
import time
import io
import threading
from PIL import Image
from datetime import datetime
import logging
import oss2
import json


# 从我们自己的包里导入所需模块
from ai_assistant.core.api_clients import qwen_client, oss_bucket
from ai_assistant.utils.helpers import extract_behavior_type, extract_emotion_type
#这个导入可能是不需要的！需要注意删除
#from ai_assistant.ui.camera_window import CameraWindow
#CameraWindow 这个类我们暂时不需要
from ai_assistant.utils import config
from ai_assistant.core.emotion_engine import EmotionEngine

from ai_assistant.utils.helpers import parse_model_response

class WebcamHandler:
    """
    处理摄像头捕获、图像分析和与主应用通信的核心类。
    它作为一个独立的引擎，通过回调函数与主应用解耦。
    """
    def __init__(self, app):
        """
        初始化WebcamHandler。
        Args:
            app: 主应用的实例。它必须实现 handle_analysis_result 和 update_status 方法。
        """
        self.app = app
        self.running = False
        self.paused = False
        self.processing = False
        self.cap = None
        self.webcam_thread = None
        self.last_webcam_image = None
        #self.camera_window = None 不需要了
        # [Phase 1.2 新增] 初始化情感引擎
        self.emotion_engine = EmotionEngine()

    def start(self) -> bool:
        """启动摄像头捕获进程，并开始后台分析循环。"""
        if self.running:
            return True
        try:
            # 尝试打开默认摄像头 (ID=0)
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.app.update_status("错误: 无法打开摄像头")
                return False
            
            self.running = True
            self.create_camera_window()
            
            # 启动一个后台守护线程来持续读取摄像头帧
            self.webcam_thread = threading.Thread(target=self._process_webcam_frames)
            self.webcam_thread.daemon = True
            self.webcam_thread.start()
            
            # 延迟2秒后，启动第一次图像分析
            self.app.after(2000, self.trigger_next_capture)
            return True
        except Exception as e:
            self.app.update_status(f"启动摄像头出错: {e}")
            return False

    def stop(self):
        """安全地停止所有线程和摄像头硬件。"""
        self.running = False
        if self.webcam_thread and self.webcam_thread.is_alive():
            self.webcam_thread.join(timeout=1.0) # 等待线程结束
        if self.cap:
            self.cap.release() # 释放摄像头资源
        if self.camera_window and self.camera_window.winfo_exists():
            self.camera_window.destroy()
        self.camera_window = None
        print("WebcamHandler 已成功停止。")

    def _process_webcam_frames(self):
        """[后台线程] 持续从摄像头读取帧并更新UI窗口。"""
        last_ui_update_time = 0
        ui_update_interval = 0.05  # 20 FPS

        while self.running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                
                # 转换颜色格式 (OpenCV: BGR -> PIL: RGB)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                self.last_webcam_image = img # 缓存最新一帧
                
                # === [新增] 调用快车道，发送视频流 ===
                # 只要 app 有 broadcast_frame 这个方法，就调用它
                if hasattr(self.app, 'broadcast_frame'):
                    self.app.broadcast_frame(img)






                # # 控制UI更新频率，避免过度消耗资源
                # current_time = time.time()
                # if self.camera_window and not self.camera_window.is_closed and \
                #    (current_time - last_ui_update_time) >= ui_update_interval:
                #     self.camera_window.update_frame(img)
                #     last_ui_update_time = current_time
                




                time.sleep(0.01) # 稍微让出CPU
            except Exception as e:
                print(f"摄像头处理循环错误: {e}")
                time.sleep(1)

    def trigger_next_capture(self):
        """
        [主线程调用] 触发下一次图像分析的入口点。
        检查所有状态标志，确保不会重复或在不当的时机执行分析。
        """
        if self.running and not self.paused and not self.processing:
            print(f"[{time.strftime('%H:%M:%S')}] 触发新一轮图像分析")
            
            # 将耗时的分析任务放入一个新线程，以防阻塞UI
            analysis_thread = threading.Thread(target=self._capture_and_analyze_pipeline)
            analysis_thread.daemon = True
            analysis_thread.start()





# ai_assistant/core/webcam_handler.py

    def _capture_and_analyze_pipeline(self):
        """[分析线程] 执行完整的“捕获->上传->分析->回调”流程。"""
        self.processing = True
        try:
            self.app.update_status("正在捕捉图像...")
            screenshots, current_screenshot = self._capture_screenshots()
            if not screenshots:
                raise ValueError("未能捕获有效截图")
                
            self.app.update_status("正在上传图像...")
            screenshot_urls = self._upload_screenshots(screenshots)
            if not screenshot_urls:
                raise ValueError("上传截图失败")

            self.app.update_status("正在分析图像...")
            
            # 1. 获取并解析 AI 原始数据
            raw_response = self._get_image_analysis(screenshot_urls)
            if not raw_response:
                raise ValueError("图像分析返回空结果")
            
            # 引入解析器 (防止未导入报错)
            from ai_assistant.utils.helpers import parse_model_response
            parsed_data = parse_model_response(raw_response)
            
            # 2. 提取基础信息
            behavior_info = parsed_data.get("behavior", {})
            behavior_num = str(behavior_info.get("id", "0"))
            behavior_desc = behavior_info.get("description", "未识别")
            analysis_text = parsed_data.get("analysis", "无详细分析")
            
            # 3. [关键修正] 注入情感引擎 (Academic Engine Upgrade)
            raw_emotion_vector = parsed_data.get("emotions", config.DEFAULT_EMOTION_VECTOR)
            
            # A. 更新引擎内部状态 (EMA 平滑)
            self.emotion_engine.update(raw_emotion_vector)
            
            # B. 计算复合情绪 (使用新方法名: compute_complex_emotions)
            # 旧代码调用的是 get_complex_label，这里必须改！
            complex_label = self.emotion_engine.compute_complex_emotions()
            
            # C. 获取 UI 情绪 (使用新方法名: get_ui_emotion_by_similarity)
            # 旧代码是查表，现在是计算余弦相似度
            ui_emotion = self.emotion_engine.get_ui_emotion_by_similarity()
            
            # D. 获取用于日志的字典数据
            smoothed_vector_dict = self.emotion_engine.get_current_state_dict()

            # 4. 日志记录
            timestamp = datetime.now()
            log_msg = f"ANALYSIS | 行为:{behavior_desc} | UI:{ui_emotion} | 复合:{complex_label} | 向量:{json.dumps(smoothed_vector_dict, ensure_ascii=False)}"
            logging.info(log_msg)
            
            # 5. 回调主应用
            self.app.handle_analysis_result(
                timestamp, 
                analysis_text, 
                behavior_num, 
                behavior_desc, 
                ui_emotion, 
                current_screenshot,
                complex_emotion=complex_label, # 传参
                emotion_vector=smoothed_vector_dict # 传参
            )

        except Exception as e:
            error_msg = f"捕获与分析流程出错: {e}"
            print(error_msg)
            import traceback
            traceback.print_exc() # 打印详细报错方便调试
            self.app.update_status(error_msg)
        finally:
            self.processing = False
            delay_ms = int(config.ANALYSIS_INTERVAL_SECONDS * 1000)
            self.app.after(delay_ms, self.trigger_next_capture)







    def _capture_screenshots(self, num_shots=4, interval=0.1) -> tuple:
        """[分析线程] 从摄像头捕获多张连续截图以模拟动态信息。"""
        screenshots = []
        # --- 关键修正：直接从摄像头硬件读取，确保每一帧都是新的 ---
        for _ in range(num_shots):
            if not self.cap or not self.cap.isOpened():
                break # 如果摄像头关闭了，则停止捕获
            ret, frame = self.cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                screenshots.append(Image.fromarray(frame_rgb))
            time.sleep(interval)
        
        return screenshots, self.last_webcam_image

    def _upload_screenshots(self, screenshots: list) -> list:
        """[分析线程] 将截图列表上传到OSS并返回URLs。"""
        oss_urls = []
        for i, img in enumerate(screenshots):
            # 将PIL Image对象转换为内存中的JPEG字节流
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG')
            buffer.seek(0)
            
            object_key = f"screenshots/{int(time.time())}_{i}.jpg"
            result = oss_bucket.put_object(object_key, buffer)
            
            if result.status == 200:
                url = f"https://{config.OSS_BUCKET}.{config.OSS_ENDPOINT}/{object_key}"
                oss_urls.append(url)
        return oss_urls


# url = f"https://{config.OSS_BUCKET}.{config.OSS_ENDPOINT}/{object_key}"
# 这是在做什么？
# 这行代码是根据OSS的规则，拼接出一个完整的、可以通过互联网访问的公开URL地址。

    def _get_image_analysis(self, image_urls: list) -> str:
        """[分析线程] 调用Qwen-VL API分析图像，同时获取行为和情感。"""
        # 定义严格的输出结构
        json_template = {
            "behavior": {"id": "行为编号(1-7)", "description": "描述"},
            "emotions": {k: "0-10分" for k in config.PLUTCHIK_EMOTIONS}, # 动态引用配置
            "analysis": "简短的心理学观察总结(50字内)"
        }

        system_prompt = (
            "你是一位精通‘情感计算(Affective Computing)’与‘面部动作编码系统(FACS)’的视觉分析专家。\n"
            "你的任务是基于输入画面，进行高精度的行为识别与情感量化分析。\n\n"
            "### 理论基础\n"
            "1. **Plutchik 情感轮模型**：将情感解析为8个正交维度的混合向量。\n"
            "2. **FACS (Facial Action Coding System)**：通过眉毛、眼睛、嘴角的肌肉运动单元(AU)来推断情绪。\n\n"
            "### 核心分析步骤 (Chain of Thought)\n"
            "请在内部进行以下思维推演，并最终输出结果：\n"
            "1. **环境与行为上下文扫描**：通过肢体姿态(Body Pose)和物体交互(Object Interaction)确定当前行为。\n"
            "   - 识别手部动作（如持杯、敲击键盘、握持手机）。\n"
            "   - 识别头部姿态（如低头、后仰、侧倾）。\n"
            "2. **面部微表情解码**：\n"
            "   - 观察眉间纹（AU4）：判断是否存在焦虑、专注或愤怒。\n"
            "   - 观察眼睑开合度（AU5/AU7）：判断是否存在惊恐或疲惫。\n"
            "   - 观察嘴角拉伸（AU12/AU15）：判断愉悦或悲伤。\n"
            "3. **情感维度量化**：基于上述特征，为 Plutchik 的8个维度打分 (0-10)。\n"
            "   - 注意：'期待(Anticipation)' 维度通常表现为注意力高度集中、身体前倾。\n"
            "   - 注意：'信任(Trust)' 维度通常表现为面部肌肉放松、眼神柔和。\n\n"
            "### 任务输出定义\n"
            "1. **行为分类 (Behavior Classification)**：\n"
            "   必须从以下互斥集合中选择最精确的一项：\n"
            "   [1.认真专注工作, 2.吃东西, 3.用杯子喝水, 4.喝饮料, 5.玩手机, 6.睡觉, 7.其他]\n"
            "2. **情感量化 (Emotion Quantification)**：\n"
            "   输出 JSON 格式的 8 维向量，禁止全0，必须捕捉细微情绪。\n\n"
            "### 输出格式约束\n"
            "严格输出标准 JSON 字符串，不包含 Markdown 标记，不包含任何解释性文字。"
        )
        
        user_prompt = f"分析画面并严格按此JSON格式返回：{json.dumps(json_template, ensure_ascii=False)}"
        
        messages = [
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {
                "role": "user", 
                "content": [
                    {"type": "video", "video": image_urls},
                    {"type": "text", "text": user_prompt}
                ]
            }
        ]
        
        completion = qwen_client.chat.completions.create(
            model="qwen-vl-max",
            messages=messages,
        )
        return completion.choices[0].message.content

    def toggle_pause(self):
        """[主线程调用] 切换分析循环的暂停/恢复状态。"""
        self.paused = not self.paused
        status = "已暂停分析" if self.paused else "已恢复分析"
        self.app.update_status(status)
        # 如果是恢复，则立即尝试触发一次分析
        if not self.paused:
            self.app.after(500, self.trigger_next_capture)
            




    # def toggle_camera_window(self):
    #     # """[主线程调用] 显示或隐藏摄像头窗口。"""
    #     # if self.camera_window and not self.camera_window.is_closed:
    #     #     self.camera_window.on_closing()
    #     # else:
    #     #     self.create_camera_window()
    #     pass
    # #禁止切换窗口
    







    def create_camera_window(self):
        #"""[主线程调用] 创建或显示摄像头窗口。"""
        # if not self.camera_window or self.camera_window.is_closed:
        #     self.camera_window = CameraWindow(self.app)
        #     self.camera_window.is_closed = False
        # else:
        #     self.camera_window.deiconify() # Toplevel窗口隐藏后用deiconify来显示

        # # 将窗口定位在主窗口下方，增加一些偏移以防重叠
        # self.app.update() # 确保主窗口位置信息是最新的
        # main_x = self.app.winfo_x()
        # main_y = self.app.winfo_y()
        # main_height = self.app.winfo_height()
        # self.camera_window.geometry(f"640x480+{main_x}+{main_y + main_height + 40}")
        pass
    #禁止创建窗口


