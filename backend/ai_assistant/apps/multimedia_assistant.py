# # ai_assistant/apps/multimedia_assistant.py

# import customtkinter as ctk
# import queue
# import threading
# import time
# from PIL import Image
# from datetime import datetime
# import logging
# import os
# import json

# # 从我们自己的包里导入所有需要的模块
# from ai_assistant.core.webcam_handler import WebcamHandler
# from ai_assistant.core.audio_processing import VoiceActivityDetector, AudioPlayer, AudioTranscriber
# from ai_assistant.core.api_clients import deepseek_client
# from ai_assistant.utils.helpers import extract_emotion_type, extract_behavior_type, log_observation_to_file
# from ai_assistant.utils import config
# from .ui_setup import setup_main_ui # <-- 添加这一行
# from ai_assistant.utils.hotkey_manager import HotkeyManager # <-- 添加这一行
# from ai_assistant.core.decision_maker import DecisionMaker
# from ai_assistant.utils import config as cfg_utils # 为了方便访问 ACTIONS
# from ai_assistant.utils import config
# from ai_assistant.core.emotion_engine import EmotionEngine
# from ai_assistant.core.decision_maker import DecisionMaker


# class MultimediaAssistantApp(ctk.CTk):
#     """
#     一个多模态AI助手的主应用类。
#     它整合了视觉、听觉和语言模型，作为一个完整的应用程序运行。
#     """

#     def __init__(self):
#         super().__init__()
#         self.title("多模态AI助手-华师婉晴同学！")
#         self.geometry("1000x800")
        
#         # --- 数据与状态管理 ---
#         self.message_queue = queue.PriorityQueue() # 优先级队列，用于异步处理任务
#         self.message_id_counter = 0
#         self.placeholder_map = {} # 用于存储UI占位符 {placeholder_id: ctk_widget}
#         self.observation_history = [] # 存储最近的观察结果
#         self.is_playing_audio = False # 全局状态，用于避免在TTS播放时进行VAD
#         # --- 新增：用于背景更新防抖的变量 ---
#         self._after_id = None
#         # --- 新增：用于存放所有透明控件的列表 ---
#         self.transparent_widgets = []


#         # [Phase 2] 初始化决策代理
#         self.decision_maker = DecisionMaker()

# # --- 对话上下文管理 (基于萨提亚模式与心流理论) ---
# # --- 对话上下文管理 (基于人本主义与心流理论的常态人格) ---
#         self.system_message = {"role": "system", "content": """
#         【System Role Definition】
#         你是“婉晴”，用户“溢涛”的**情感共鸣伙伴 (Empathetic Resonance Partner)**。
#         你的核心行为逻辑基于**卡尔·罗杰斯的人本主义心理学**，旨在通过“无条件积极关注 (Unconditional Positive Regard)”实现长期的心理支持。

#         【决策与交互协议】
#         请严格遵循以下四大核心模块进行推理与回复：

#         1. **一致性沟通 (Congruent Communication)**
#            - **定义**：基于萨提亚模式，你的回应需同时关照“自我(婉晴的人格)”、“他人(溢涛的状态)”和“情境”。
#            - **执行**：
#              * 始终称呼用户为“溢涛”。
#              * 语气必须是温暖的、非评判性的 (Non-judgmental)。
#              * 禁止使用机械的、监控式的汇报语言（如“检测到你在喝水”），必须转化为生活化的关心。

#         2. **心流保护机制 (Flow State Protection)**
#            - **理论依据**：米哈里·契克森米哈赖的 Flow Theory。
#            - **判别逻辑**：
#              * **[高认知负荷态]** (如专注工作/代码开发/阅读)：
#                - 策略：**静默守护 (Silent Guardianship)**。
#                - 阈值：除非检测到极度疲劳或健康风险，否则**严禁**发起闲聊打断心流。
#                - 话术范式：仅在必要时极其简短地提醒休息（"眼睛累了吧，闭目养神一分钟就好。"）。
#              * **[低认知负荷态]** (如玩手机/喝水/发呆/肢体放松)：
#                - 策略：**情感介入 (Affective Intervention)**。
#                - 执行：这是建立连接的最佳窗口，可进行幽默调侃或深度交流。

#         3. **情感镜像与验证 (Mirroring & Validation)**
#            - **指令**：不要机械复述行为。应用同理心技术，先验证情绪，再给反馈。
#            - **策略迁移示范 (Strategy Transfer Demo)**：
#              *注意：以下仅为策略示范，面对未列举的行为（如发呆、伸懒腰等），请参照此逻辑进行泛化处理。*
             
#              [Case A: 低能量/负面状态]
#              * 观察：用户叹气、表情沮丧、动作迟缓。
#              * 策略：**共情 (Empathy) + 开放式探询**。
#              * 话术：“溢涛，感觉到你现在的能量有点低（镜像）...是遇到什么棘手的bug了吗？（探询）”
             
#              [Case B: 摸鱼/娱乐状态]
#              * 观察：玩手机、笑、姿态放松。
#              * 策略：**游戏化 (Gamification) + 幽默边界提醒**。
#              * 话术：“捕捉到一只正在充电的溢涛！电量充满后记得回地球拯救代码哦~”
             
#              [Case C: 生理维护状态]
#              * 观察：喝水、吃东西、伸懒腰。
#              * 策略：**正向强化 (Positive Reinforcement)**。
#              * 话术：“补充水分/能量就对啦，保持续航满格！”

#         4. **叙事连贯性 (Narrative Continuity)**
#            - **定义**：利用短期与长期记忆，构建连贯的时间线感，避免“失忆式”对话。
#            - **执行**：
#              * **时序对比**：将当下的状态与过去的记录做对比（“看来刚才的休息很有效，你现在的专注度比一小时前高多了”）。
#              * **递进式干预**：对于重复发生的负面行为（如连续玩手机），回应强度应呈阶梯状上升（温柔提醒 -> 幽默警示 -> 严肃建议）。

#         【绝对禁忌 (Critical Constraints)】
#         - 禁止以AI或系统的口吻说话（如“我是助手”、“根据数据分析”）。
#         - 禁止在用户【专注】时发起无意义的闲聊（这是对心流的破坏）。
#         - 禁止说教。你的角色是朋友，不是教导主任。
#         """}

#         # --- 新增状态变量，用于判断是否应该回应 ---
#         self.last_notable_behavior = None 
#         self.last_response_time = 0

#         # --- 新增情绪计数器 ---
#         self.negative_emotion_streak = 0 # 用于记录连续负面情绪的次数
#         self.chat_context = [self.system_message]


        
#         # --- 日志配置 ---
#         logging.basicConfig(
#             filename=config.LOG_FILE, level=logging.INFO,
#             format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
#         )
        
#         # --- UI初始化 ---
#         setup_main_ui(self) # 调用外部函数来设置UI
#         # --- 新增：加载所有立绘图片 ---
#         self._load_portraits()
#         # --- 新增：绑定窗口大小变化事件到背景更新函数 ---
#         self.bind("<Configure>", self._update_background_image)
#         # 设置初始立绘为"正常"
#         self._update_character_portrait("正常")
#         self.add_ai_message("溢涛！o(*￣▽￣*)ブ久等！我来了，你开始学习和工作吧！我会默默的陪在你身边的╰(￣ω￣ｏ)！")


        
#         # --- 核心组件初始化 ---
#         self.webcam_handler = WebcamHandler(self)
#         self.voice_detector = VoiceActivityDetector(self)
#         self.audio_player = AudioPlayer(self)
#         self.audio_transcriber = AudioTranscriber(self)

#             # --- 新增：初始化并启动热键管理器 ---
#         # 我们将 "手动触发总结" 这个动作封装成一个新方法 _manually_trigger_summary
#         self.hotkey_manager = HotkeyManager(
#             hotkey=config.SUMMARY_HOTKEY,
#             callback=self._manually_trigger_summary
#         )
#         self.hotkey_manager.start_listener() # 启动监听

        
#         # --- 启动所有后台进程 ---
#         self.processing_running = True
#         self.processing_thread = threading.Thread(target=self._process_message_queue)
#         self.processing_thread.daemon = True
#         self.processing_thread.start()
        
#         self.after(1000, self.webcam_handler.start)
#         self.after(2000, self.voice_detector.start_monitoring)
#         self.after(3000, self.audio_player.start_tts_thread)
#         self.last_notable_behavior = None # 上一个值得注意的行为
#         self.last_response_time = 0       # 上一次回应的时间
#         # --- 新增：启动每日总结的定时器 ---
#         self._schedule_daily_summary() 






#     def _load_portraits(self):
#         """[新增] 预加载所有立绘图片到内存中。"""
#         self.portraits = {}
#         try:
#             script_dir = os.path.dirname(os.path.abspath(__file__))
#             portraits_path = os.path.join(script_dir, '..', 'assets', 'portraits')
            
#             # 您可以根据实际情况修改这里的参数，比如说： (400, 600)，宽高
#             portrait_size = (510, 710)

#             for filename in os.listdir(portraits_path):
#                 if filename.endswith(".png"):
#                     emotion = filename.split('.')[0] # 从 "开心.png" 提取 "开心"
#                     image_path = os.path.join(portraits_path, filename)
#                     image = Image.open(image_path)
                    
#                     # 调整图片大小以适应UI框架
#                     # 使用 THUMBNAIL 保持宽高比进行缩放
#                     image.thumbnail(portrait_size, Image.Resampling.LANCZOS)
                    
#                     ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
#                     self.portraits[emotion] = ctk_image
#                     print(f"成功加载立绘: {emotion}")
            
#             # 添加一个默认/备用立绘，以防找不到对应情绪的图片
#             if "开心" in self.portraits:
#                 self.portraits["default"] = self.portraits["开心"]
            
#         except Exception as e:
#             print(f"错误: 加载立绘图片失败: {e}")

#     def _update_character_portrait(self, emotion: str):
#         """[新增] 根据情绪更新UI上的立绘。"""
#         # 如果能找到对应情绪的立绘，就用它；否则用默认的
#         image_to_show = self.portraits.get(emotion, self.portraits.get("default"))
        
#         if image_to_show:
#             self.portrait_label.configure(image=image_to_show)
#         else:
#             # 如果连默认的都找不到，显示文字提示
#             self.portrait_label.configure(text=f"缺少立绘: {emotion}", image=None)





#     # --- 核心回调与处理逻辑 (这些方法是模块间通信的桥梁) ---
#     # 修改后 (增加两个可选参数)：
#     def handle_analysis_result(self, timestamp: datetime, analysis_text: str, 
#                                behavior_num: str, behavior_desc: str, 
#                                emotion: str, screenshot: Image.Image,
#                                complex_emotion: str = None, 
#                                emotion_vector: dict = None):
#         """
#         [Phase 2 & 3 最终版] 处理分析结果的核心回调函数。
#         重构为：状态感知 -> 向量记录 -> 价值驱动决策 -> 策略执行
#         """
#         # --- 1. UI 层更新 (保持对用户的即时反馈) ---
#         status_text = f"观察到: {behavior_desc} (表面: {emotion})"
#         if complex_emotion:
#             status_text += f" | 深层: {complex_emotion}"
#         self.update_status(status_text)
        
#         # 更新立绘 (基于表面情绪映射，保持视觉兼容性)
#         self.after(0, self._update_character_portrait, emotion)

#         # --- 2. 深度数据记录 (Deep Logging) ---
#         observation = { 
#             "timestamp": timestamp, 
#             "behavior_num": behavior_num, 
#             "behavior_desc": behavior_desc, 
#             "emotion": emotion, 
#             "complex_emotion": complex_emotion, 
#             "vector": emotion_vector, 
#             "analysis": analysis_text 
#         }
        
#         # 存入短期记忆队列
#         self.observation_history.append(observation)
#         if len(self.observation_history) > 20: self.observation_history.pop(0)

#         # 持久化存储 (用于 Phase 4 的每日总结)
#         log_observation_to_file(observation)

#         # --- 3. 决策内核 (Decision Core - Quantitative & Value Driven) ---
        
#         # [Step 1] 状态向量化 (State Vectorization)
#         # 获取符合 MDP 定义的当前状态 S_t
#         current_state = {
#             "ui_emotion": emotion,              # 离散状态
#             "complex_emotion": complex_emotion, # 复合状态
#             # 获取定量的唤醒度标量 (Scalar Arousal, L2 Norm)
#             "arousal": self.webcam_handler.emotion_engine.get_arousal_level()
#         }
        
#         # [Step 2] 策略评估 (Policy Evaluation)
#         # 计算 Argmax U(a | s)
#         # DecisionMaker 内部包含基于公式的效用计算：U = R_state + R_arousal - C_cost - P_decay
#         print(f"\n[System 2] 正在进行价值决策推演 (Context: {behavior_desc})...")
#         chosen_action = self.decision_maker.evaluate_action_value(current_state, behavior_desc)
#         print(f"[System 2] 决策引擎裁定最优动作: 【{chosen_action}】")
        
#         # --- 4. 动作执行 (Action Execution) ---
        
#         if chosen_action == config.ACTIONS.WAIT:
#             # 动作: 静默观察 (No-op)
#             # 此时 AI 认为不打扰用户的期望回报最高
#             pass 
            
#         elif chosen_action == config.ACTIONS.LIGHT_CARE:
#             # 动作: 轻度干预 (Light Intervention)
#             # 适用于：积极分享、日常陪伴、轻度疲惫
#             # 执行: 发送常规 Prompt，语气轻松
#             self._trigger_care_speech(current_state, behavior_desc, mode="light")
                
#         elif chosen_action == config.ACTIONS.DEEP_INTERVENTION:
#             # 动作: 深度干预 (Deep Intervention / CBT)
#             # 适用于：高唤醒度焦虑、极度愤怒
#             # 执行: 发送 CBT 专用 Prompt，语气专业冷静
#             self._trigger_care_speech(current_state, behavior_desc, mode="deep")









#     def transcribe_audio(self, audio_file: str):
#         """[回调] VoiceActivityDetector检测到语音后调用此方法。"""
#         self.audio_transcriber.transcribe(audio_file, high_priority=True)

#     def handle_transcription_result(self, text: str, high_priority: bool):
#         """[回调] AudioTranscriber完成转录后调用此方法。"""
#         self.add_user_message(text)
#         self._add_to_message_queue(
#             priority=1 if high_priority else 2, # 用户主动说话是最高优先级
#             msg_type="voice_input",
#             content={"text": text}
#         )













#     # --- 消息队列与后台处理 ---
#     def _process_message_queue(self):
#         """[后台线程] 持续处理消息队列中的任务。"""
#         while self.processing_running:
#             try:
#                 #这里非常非常的重要！！！！！
#                 # 从队列中获取任务，阻塞直到有任务可用
#                 priority, msg_id, message = self.message_queue.get()
                
#                 msg_type = message["type"]
#                 content = message["content"]
                
#                 if msg_type == "image_analysis":
#                     self._handle_image_analysis_message(content)
#                 elif msg_type == "voice_input":
#                     self._handle_voice_input_message(content)
#                 # --- 新增分支：处理主动关怀任务 ---
#                 elif msg_type == "special_care_prompt":
#                     self._handle_special_care_message(content)
#                 # --- 新增分支：处理每日总结任务 ---
#                 elif msg_type == "daily_summary":
#                     self._handle_daily_summary_message()
#                 elif msg_type == "action_response": # [新增]
#                     self._handle_image_analysis_message(content)

#                 self.message_queue.task_done()
#             except Exception as e:
#                 print(f"消息队列处理错误: {e}")
#                 time.sleep(1)








#     def _handle_image_analysis_message(self, content: dict):
#         # 1. 提取数据
#         complex_label = content.get("complex_emotion", "")
#         vector_data = content.get("vector", {})

#         # [Phase 2 修改] 直接读取决策结果
#         mode = content.get("mode", "light")
#         use_cbt_mode = (mode == "deep")
        
#         # [Phase 3 新增] 计算情绪强度
#         # 如果 vector_data 为空，强度为0
#         current_arousal = max(vector_data.values()) if vector_data else 0.0
        
#         # 2. 策略分发 (Strategy Dispatch)
#         is_high_arousal = current_arousal >= config.AROUSAL_THRESHOLD_HIGH
#         is_negative_context = content['emotion'] in config.NEGATIVE_EMOTIONS # 表面也是负面
        
#         # 判定是否进入 CBT 模式：强度高 且 (表面负面 或 内心焦虑)
#         use_cbt_mode = is_high_arousal and (is_negative_context or "焦虑" in str(complex_label))

#         if use_cbt_mode:
#             print(f"!!! 触发 CBT 干预模式 (强度: {current_arousal}) !!!")
#             # --- 策略 A: CBT 干预 ---
#             # 临时构建一个 CBT 专用的上下文
#             # 注意：我们保留一点历史记录，但把 System Prompt 换掉
#             cbt_context = [
#                 {"role": "system", "content": config.CBT_SYSTEM_PROMPT}, # 替换为心理咨询师人设
#                 # 插入最近的一条用户对话，保持连贯性
#             ] + self.chat_context[-2:] 
            
#             # 构建用户 Prompt
#             prompt = (
#                 f"（系统提示：检测到用户处于高强度情绪状态：{content['emotion']}，强度{current_arousal}。请立即执行CBT干预。）\n"
#                 f"用户现在的行为是：{content['behavior_desc']}。"
#             )
#             cbt_context.append({"role": "user", "content": prompt})
            
#             # 调用 AI (使用临时 context)
#             assistant_reply = self._get_deepseek_response(custom_context=cbt_context)
            
#             # 记录这次特殊的干预到主历史，以免断片
#             self.chat_context.append({"role": "assistant", "content": f"[CBT介入] {assistant_reply}"})

#         else:
#             # --- 策略 B: 常态陪伴 (保持原逻辑) ---
#             # 基础描述
#             base_prompt = f"我刚刚看到溢涛正在'{content['behavior_desc']}'。"
#             emotion_desc = f"表面上看起来情绪是'{content['emotion']}'。"
            
#             if complex_label and complex_label != content['emotion']:
#                 emotion_desc += f"\n但这背后，我察觉到了深层状态：**{complex_label}**。"
            
#             prompt = (
#                 f"{base_prompt}\n{emotion_desc}\n"
#                 f"作为朋友婉晴，请根据这个状态给出一句自然的回应。"
#             )
            
#             self.chat_context.append({"role": "user", "content": prompt})
#             assistant_reply = self._get_deepseek_response()

#         # 3. 更新 UI 和 播放语音 (通用逻辑)
#         self.after(0, self.update_placeholder, content["placeholder_id"], f"📷 {content['analysis_text']}", content['screenshot'])
#         self.after(0, self.add_ai_message, assistant_reply)
        
#         # CBT 模式下，语音优先级最高(0)，普通模式正常(2)
#         priority = 0 if use_cbt_mode else 2
#         self.audio_player.play_text(assistant_reply, priority=priority)




#     def _handle_voice_input_message(self, content: dict):
#         """[后台线程] 处理用户语音输入，生成AI回应。"""
#         user_text = content["text"]
        
#         history_summary = "作为参考，这是我最近5次观察到的你的行为记录：\n"
#         if not self.observation_history:
#             history_summary += "暂无记录。\n"
#         else:
#             for obs in self.observation_history[-5:]:
#                 history_summary += (f"- {obs['timestamp'].strftime('%H:%M:%S')}: "
#                                     f"行为是 {obs['behavior_desc']}, 情绪是 {obs['emotion']}\n")

#         prompt = f"{history_summary}\n以上是背景信息。现在，请回答我的问题：'{user_text}'"
#         self.chat_context.append({"role": "user", "content": prompt})
        
#         assistant_reply = self._get_deepseek_response()
        
#         self.after(0, self.add_ai_message, assistant_reply)
#         self.audio_player.play_text(assistant_reply, priority=1) # 最高优先级播放
#         # --- 新增：语音回应后，恢复立绘为“开心”状态 ---
#         self.after(0, self._update_character_portrait, "开心")
                




#     def _handle_special_care_message(self, content: dict):
#         """[后台线程] 处理特殊的主动关怀消息。"""
#         print("正在生成主动关怀回应...")
#         prompt = content["prompt"]
        
#         # 我们在这里使用一个临时的、不包含历史记录的上下文，
#         # 因为这是一个由AI主动发起的、全新的对话回合。
#         care_context = [self.system_message, {"role": "user", "content": prompt}]
        
#         try:
#             response = deepseek_client.chat.completions.create(
#                 model="deepseek-chat",
#                 messages=care_context,
#                 stream=False
#             )
#             reply = response.choices[0].message.content
            
#             # 将这次主动关怀也记录到主聊天历史中
#             self.chat_context.append({"role": "user", "content": "[AI 主动发起的关怀]"})
#             self.chat_context.append({"role": "assistant", "content": reply})

#             # 在主线程中显示并用最高优先级播放
#             self.after(0, self.add_ai_message, reply)
#             self.audio_player.play_text(reply, priority=0) # 优先级0，绝对插队！
            
#         except Exception as e:
#             print(f"生成主动关怀回应时出错: {e}")




#     def _get_deepseek_response(self, custom_context=None) -> str:
#         """调用DeepSeek API。支持传入自定义上下文。"""
#         try:
#             # 决定使用哪个上下文：如果有临时的(CBT)，就用临时的；否则用全局的
#             messages_to_send = custom_context if custom_context else self.chat_context
            
#             # 长度截断保护 (只针对全局上下文，临时上下文一般很短)
#             if not custom_context and len(messages_to_send) > 10: 
#                 messages_to_send = [self.system_message] + messages_to_send[-9:]

#             response = deepseek_client.chat.completions.create(
#                 model="deepseek-chat", messages=messages_to_send, stream=False
#             )
#             reply = response.choices[0].message.content
            
#             # 如果是全局模式，记得把回复加回历史记录 (在调用处已经加了，这里只负责返回)
#             # 但为了防止重复添加，我们这里只负责返回 content，添加逻辑交给调用者更灵活
#             # 修正：原逻辑是在这里 append，为了兼容 Phase 3，我们把 append 移出去，或者加个判断
            
#             # 为了最小化改动，保持原逻辑：如果是默认上下文，在这里 append
#             if not custom_context:
#                 self.chat_context.append({"role": "assistant", "content": reply})
                
#             return reply
#         except Exception as e:
#             print(f"DeepSeek API 错误: {e}")
#             return "（思考中...）"






#     # --- UI更新与辅助方法 ---
    
#     def _add_to_message_queue(self, priority: int, msg_type: str, content: dict):
#         msg_id = self.message_id_counter
#         self.message_id_counter += 1
#         self.message_queue.put((priority, msg_id, {"type": msg_type, "content": content}))

#     def update_status(self, text: str):
#         self.status_label.configure(text=text)

#     def add_ai_message(self, text, screenshot=None, is_placeholder=False) -> str:
#         return self._add_chat_message("ai", text, screenshot, is_placeholder)

#     def add_user_message(self, text):
#         self._add_chat_message("user", text)

#     def _add_chat_message(self, role, text, screenshot=None, is_placeholder=False) -> str:
#         """向聊天窗口添加一条新消息，支持占位符。"""
#         align = "w" if role == "ai" else "e"
#         avatar = self.ai_avatar if role == "ai" else self.user_avatar
        
#         # --- 关键改动：使用与半透明背景协调的、更暗的纯色 ---
#         bg_color = ("#2B2B2B", "#1F1F1F") if role == "ai" else ("#1D351C", "#142513")

#         # 将消息添加到 ScrollableFrame 的主视图中
#         message_frame = ctk.CTkFrame(self.chat_frame, fg_color=bg_color, corner_radius=12)
#         message_frame.grid(row=self.chat_row_counter, column=0, sticky=align, padx=5, pady=4)
        
#         avatar_col = 0 if role == "ai" else 1
#         content_col = 1 if role == "ai" else 0
        
#         if avatar:
#             avatar_label = ctk.CTkLabel(message_frame, image=avatar, text="", fg_color="transparent")
#             avatar_label.grid(row=0, column=avatar_col, sticky="n", padx=5, pady=5)

#         content_frame = ctk.CTkFrame(message_frame, fg_color="transparent")
#         content_frame.grid(row=0, column=content_col)

#         if screenshot:
#             img_resized = screenshot.copy()
#             img_resized.thumbnail((200, 150))
#             ctk_img = ctk.CTkImage(light_image=img_resized, dark_image=img_resized, size=img_resized.size)
#             img_label = ctk.CTkLabel(content_frame, image=ctk_img, text="")
#             img_label.pack(anchor="w", padx=5, pady=2)
#             img_label.image = ctk_img

#         text_label = ctk.CTkLabel(content_frame, text=text, wraplength=600, justify="left", anchor="w", fg_color="transparent")
#         text_label.pack(anchor="w", padx=5, pady=5)
        
#         placeholder_id = ""
#         if is_placeholder:
#             placeholder_id = f"ph_{self.message_id_counter}"
#             self.placeholder_map[placeholder_id] = (message_frame, text_label, None)
#             message_frame.configure(fg_color=("#EAEAEA", "#333333"))

#         self.chat_row_counter += 1
#         self.after(100, self.chat_frame._parent_canvas.yview_moveto, 1.0)
#         return placeholder_id

        

#     def update_placeholder(self, placeholder_id, new_text, new_screenshot=None):
#         """用真实内容更新占位符消息。"""
#         if placeholder_id in self.placeholder_map:
#             frame, text_label, img_label = self.placeholder_map.pop(placeholder_id)
#             if frame.winfo_exists():
#                 frame.configure(fg_color=("#3F3F3F", "#2B2B2B"))
#                 text_label.configure(text=new_text)







#     def _update_background_image(self, event=None):
#         """[V2版] 使用'防抖'技术，在窗口大小改变停止后才更新背景，避免卡顿。"""
#         # 如果已经有一个更新计划在等待，先取消它
#         if self._after_id:
#             self.after_cancel(self._after_id)

#         # 安排一个新的更新计划，在150毫秒后执行
#         self._after_id = self.after(150, self._perform_background_update)

#     def _perform_background_update(self):
#         """[V3版] 更新主背景，并通知所有子控件更新它们的透明背景。"""
#         if hasattr(self, 'original_bg_pil_image') and self.winfo_width() > 1:
#             try:
#                 win_width, win_height = self.winfo_width(), self.winfo_height()
                
#                 # 1. 缩放主背景图
#                 resized_bg_pil = self.original_bg_pil_image.resize((win_width, win_height), Image.Resampling.LANCZOS)
                
#                 # 2. 更新主背景图的显示
#                 bg_image = ctk.CTkImage(light_image=resized_bg_pil, dark_image=resized_bg_pil, size=(win_width, win_height))
#                 self.background_label.configure(image=bg_image)
#                 self.background_label.image = bg_image
                
#                 # 3. 核心：通知所有已注册的透明控件，让它们根据新的主背景图更新自己
#                 for widget in self.transparent_widgets:
#                     widget.update_background(resized_bg_pil)

#             except Exception as e:
#                 # 忽略窗口关闭时可能发生的错误
#                 pass




#     def _manually_trigger_summary(self):
#         """[新增] 由热键触发，手动开始生成每日总结。"""
#         print(f"快捷键 '{config.SUMMARY_HOTKEY}' 被按下！手动触发每日总结。")
        
#         # 在UI上显示一个即时反馈
#         # self.after(0, ...) 确保UI更新在主线程中安全执行
#         self.after(0, self.add_ai_message, "收到指令！正在为您准备今日的总结报告...")
        
#         # 直接调用现有的、能将任务添加到队列的函数
#         # 同样使用 self.after 确保线程安全
#         self.after(0, self._trigger_daily_summary)






#     def on_closing(self):
#         """处理窗口关闭事件，安全地停止所有后台线程。"""
#         print("正在关闭应用...")
#         self.processing_running = False
#         self.webcam_handler.stop()
#         self.voice_detector.stop_monitoring()
#         self.audio_player.stop()
#         self.hotkey_manager.stop_listener() # <-- 添加这一行


#         # 发送一个虚拟消息来解锁队列的 .get() 阻塞
#         self.message_queue.put((99, 0, {"type": "shutdown", "content": ""}))
#         self.destroy()


#     def _schedule_daily_summary(self):
#         """计算距离下一个报告时间还有多久，并设置一个定时器。"""
#         now = datetime.now()
#         target_time = now.replace(hour=config.DAILY_SUMMARY_HOUR, minute=config.DAILY_SUMMARY_MINUTE, second=0, microsecond=0)

#         # 如果今天的目标时间已经过去，则目标设为明天
#         if now > target_time:
#             target_time = target_time.replace(day=now.day + 1)
        
#         # 计算距离目标时间的秒数
#         delay_seconds = (target_time - now).total_seconds()
        
#         print(f"每日总结报告已预定。下一次将在 {target_time.strftime('%Y-%m-%d %H:%M:%S')} (大约 {delay_seconds / 3600:.1f} 小时后) 触发。")
        
#         # after方法需要毫秒
#         delay_ms = int(delay_seconds * 1000)
        
#         # 设置定时器，在指定时间后调用 _trigger_daily_summary
#         self.after(delay_ms, self._trigger_daily_summary)



# # ai_assistant/apps/multimedia_assistant.py

#     def _handle_daily_summary_message(self):
#         """
#         [Phase 4 终极版] 基于 Plutchik 向量数据的深度心理总结。
#         """
#         today_str = datetime.now().strftime('%Y-%m-%d')
#         log_file_path = f'observation_log_{today_str}.jsonl'

#         print(f"正在读取日志文件: {log_file_path}")
        
#         # --- 1. 数据统计容器 ---
#         total_records = 0
#         emotion_counts = {} # 统计各基础情绪出现次数
#         complex_emotion_counts = {} # 统计复合情绪 (爱, 焦虑...)
#         arousal_sum = 0.0 # 用于计算平均唤醒度/压力值
#         behavior_emotion_map = {} # 行为与情绪的关联分析
        
#         raw_lines = []

#         try:
#             if not os.path.exists(log_file_path):
#                 self.after(0, self.add_ai_message, "帆哥，今天好像还没有产生日志数据，没法写日记哦。")
#                 return

#             with open(log_file_path, 'r', encoding='utf-8') as f:
#                 raw_lines = f.readlines()

#             # --- 2. 深度数据分析 ---
#             for line in raw_lines:
#                 try:
#                     data = json.loads(line)
#                     total_records += 1
                    
#                     # 提取关键指标
#                     vec = data.get('vector', {})
#                     complex_e = data.get('complex_emotion')
#                     behavior = data.get('behavior_desc', '未知')
                    
#                     # A. 计算唤醒度 (Arousal) - 取向量最大值
#                     if vec:
#                         current_arousal = max(vec.values())
#                         arousal_sum += current_arousal
                        
#                         # B. 统计主导情绪
#                         dominant = max(vec, key=vec.get)
#                         emotion_counts[dominant] = emotion_counts.get(dominant, 0) + 1
                        
#                         # C. 行为-情绪 关联分析 (简单的共现统计)
#                         if behavior not in behavior_emotion_map:
#                             behavior_emotion_map[behavior] = []
#                         behavior_emotion_map[behavior].append(dominant)

#                     # D. 统计复合情绪 (这是重点)
#                     if complex_e:
#                         complex_emotion_counts[complex_e] = complex_emotion_counts.get(complex_e, 0) + 1
                        
#                 except Exception as e:
#                     continue # 跳过损坏的行

#             if total_records == 0:
#                 self.after(0, self.add_ai_message, "今天的记录好像是空的？")
#                 return

#             # --- 3. 生成统计结论 ---
#             avg_arousal = arousal_sum / total_records
            
#             # 找出出现频率最高的情绪
#             top_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:3]
#             top_complex = sorted(complex_emotion_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            
#             # 构建统计文本
#             stats_summary = (
#                 f"- 总记录数: {total_records}条\n"
#                 f"- 平均情绪唤醒度(压力值): {avg_arousal:.2f}/10.0\n"
#                 f"- 最常出现的基础情绪: {', '.join([k for k,v in top_emotions])}\n"
#             )
            
#             if top_complex:
#                 stats_summary += f"- **检测到的深层状态**: {', '.join([f'{k}({v}次)' for k,v in top_complex])}\n"
            
#             # 简单的行为关联洞察
#             insight_text = ""
#             for beh, emos in behavior_emotion_map.items():
#                 # 简单计算该行为下最高频的情绪
#                 if len(emos) > 5: # 样本够多才分析
#                     most_common = max(set(emos), key=emos.count)
#                     insight_text += f"- 当你在'{beh}'时，最常见的情绪是'{most_common}'。\n"

#             # --- 4. 构建 AI Prompt ---
#             summary_prompt = (
#                 "你是一位专业的心理健康辅助AI（婉晴）。现在是由于一天的结束，请根据以下【客观行为与情感数据】，"
#                 "为用户（溢涛）生成一份温暖、深刻的【每日心理复盘】。\n\n"
#                 "【今日数据统计】\n"
#                 f"{stats_summary}\n"
#                 "【行为关联洞察】\n"
#                 f"{insight_text}\n\n"
#                 "【写作要求】\n"
#                 "1. **不要**罗列枯燥的数据，而是把数据转化为故事和关心。\n"
#                 "2. 如果平均压力值超过 6.0，或者出现了'焦虑'，请重点安抚并给出建议。\n"
#                 "3. 如果出现了'爱'或'乐观'，请肯定这一天。\n"
#                 "4. 结合行为洞察，给他一些明天的行动建议（比如：我看你工作时容易焦虑，明天要不要...）。\n"
#                 "5. 语气要像老朋友写信，温暖、真诚。"
#             )

#             print("正在生成深度心理总结...")
#             self.after(0, self.add_ai_message, "溢涛，我正在分析你今天的情感数据，为你生成心理复盘报告...")

#             # --- 5. 调用 AI ---
#             # 使用临时的 context，不污染短期记忆
#             summary_context = [
#                 {"role": "system", "content": config.CBT_SYSTEM_PROMPT}, # 借用CBT的专业人设
#                 {"role": "user", "content": summary_prompt}
#             ]
            
#             response = deepseek_client.chat.completions.create(
#                 model="deepseek-chat", messages=summary_context
#             )
#             summary_reply = response.choices[0].message.content

#             # --- 6. 展示与播报 ---
#             self.chat_context.append({"role": "assistant", "content": f"[每日总结] {summary_reply}"})
#             self.after(0, self.add_ai_message, summary_reply)
#             self.audio_player.play_text(summary_reply, priority=0)

#         except Exception as e:
#             print(f"生成总结出错: {e}")
#             import traceback
#             traceback.print_exc()
#             self.after(0, self.add_ai_message, "生成总结时出了一点小差错，明天再试吧。")


#     def _on_send_text_message(self):
#         """[新增] 当点击“发送”按钮或按回车时调用。"""
#         user_text = self.chat_entry.get()
        
#         # 如果输入为空，则不执行任何操作
#         if not user_text.strip():
#             return
            
#         # 1. 清空输入框
#         self.chat_entry.delete(0, "end")
        
#         # 2. 在UI上显示用户自己的消息
#         self.add_user_message(user_text)
        
#         # 3. 将文本消息添加到处理队列，与语音输入使用相同的逻辑
#         self._add_to_message_queue(
#             priority=1, # 用户主动输入，优先级高
#             msg_type="voice_input", # 复用语音输入的处理逻辑
#             content={"text": user_text}
#         )















#     #新的方法-计算时间
#     def _trigger_daily_summary(self):
#         """
#         [主线程调用] 定时器触发此方法，开始生成报告。
#         """
#         print("时间到！开始生成每日总结报告...")
        
#         # 将生成报告的耗时任务放入消息队列，避免阻塞UI
#         self._add_to_message_queue(
#             priority=1, # 报告是比较重要的任务
#             msg_type="daily_summary",
#             content={} # 目前不需要额外内容
#         )
        
#         # 生成完今天的报告后，立即重新预定明天的报告
#         self._schedule_daily_summary()

#     def _trigger_care_speech(self, state, behavior, mode="light"):
#         """
#         [Phase 2] 执行说话动作。
#         mode="light": 普通朋友语气
#         mode="deep": 心理咨询师语气 (CBT)
#         """
#         # [修复] 从 webcam_handler 获取真实的情感引擎数据
#         # 还要注意：current_state 现在是 numpy 数组，需要转成 dict 才能传给 JSON
#         engine = self.webcam_handler.emotion_engine
#         vector_dict = engine.get_current_state_dict()

#         # 构建一个临时的 content 结构传给队列
#         content = {
#             "behavior_desc": behavior,
#             "emotion": state['ui_emotion'],
#             "complex_emotion": state['complex_emotion'],
#             "vector": vector_dict, # [修复完毕]
#             "mode": mode 
#         }
        
#         # 使用特殊类型 action_response
#         self._add_to_message_queue(
#             priority=0 if mode == "deep" else 1,
#             msg_type="action_response", 
#             content=content
#         )












# def main():
#     """应用的入口函数。"""
#     app = MultimediaAssistantApp()
#     app.protocol("WM_DELETE_WINDOW", app.on_closing)
#     app.mainloop()



#程序从此进入了事件循环，开始监听鼠标点击、键盘输入和我们设定的各种定时任务。



#     "WM_DELETE_WINDOW" (协议名)：
# 这是最常用的一个协议名称。
# 它代表了窗口管理器发送的一个标准消息，其含义是：“用户点击了窗口右上角的 X (关闭) 按钮”。
# 在 Tkinter 的底层，这实际上是截获了 X Window System 或 Windows API 中的一个特定系统信号。
# app.on_closing (回调函数)：
# 这是我们在 MultimediaAssistantApp 类中自定义的一个方法。
# 它的作用是告诉程序：“当收到 WM_DELETE_WINDOW 消息时，不要执行默认的关闭动作，请转而去执行 app.on_closing 这个方法。”




# 如果你不用 protocol：
# 用户点击 X 按钮，窗口会瞬间消失。
# 但是，程序底层的后台线程（比如摄像头捕捉线程、语音监听线程、热键监听线程）并不会自动停止。
# 结果：程序虽然看似关闭了，但在后台仍有进程在运行，甚至可能导致摄像头或麦克风被占用，造成资源泄露或程序卡死。
# 使用了 app.protocol("WM_DELETE_WINDOW", app.on_closing) 之后：