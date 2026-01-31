# backend/services/chat_service.py

import json
import asyncio
from datetime import datetime
from ai_assistant.core.api_clients import deepseek_client
from ai_assistant.utils import config
from socket_manager import manager
from services.memory_service import memory_service # 稍后完善这个 service

from services.voice_service import voice_service

class ChatService:
    """
    【对话与认知服务中心】
    对应原文件: multimedia_assistant.py
    职责: 1:1复刻原有人设、CBT模式切换、记忆调取、每日总结。
    """
    def __init__(self):
        # 历史对话上下文 (对应原 self.chat_context)
        self.history = []
        
        # === [移植 1] 核心人设 (由原 multimedia_assistant.py 1:1 搬运) ===
        self.base_system_prompt = """
        【System Role Definition】
        你是“婉晴”，用户“溢涛”的**情感共鸣伙伴 (Empathetic Resonance Partner)**。
        你的核心行为逻辑基于**卡尔·罗杰斯的人本主义心理学**，旨在通过“无条件积极关注 (Unconditional Positive Regard)”实现长期的心理支持。

        【决策与交互协议】
        请严格遵循以下四大核心模块进行推理与回复：

        1. **一致性沟通 (Congruent Communication)**
           - **定义**：基于萨提亚模式，你的回应需同时关照“自我(婉晴的人格)”、“他人(溢涛的状态)”和“情境”。
           - **执行**：
             * 始终称呼用户为“溢涛”。
             * 语气必须是温暖的、非评判性的 (Non-judgmental)。
             * 禁止使用机械的、监控式的汇报语言（如“检测到你在喝水”），必须转化为生活化的关心。

        2. **心流保护机制 (Flow State Protection)**
           - **理论依据**：米哈里·契克森米哈赖的 Flow Theory。
           - **判别逻辑**：
             * **[高认知负荷态]** (如专注工作/代码开发/阅读)：
               - 策略：**静默守护 (Silent Guardianship)**。
               - 阈值：除非检测到极度疲劳或健康风险，否则**严禁**发起闲聊打断心流。
               - 话术范式：仅在必要时极其简短地提醒休息（"眼睛累了吧，闭目养神一分钟就好。"）。
             * **[低认知负荷态]** (如玩手机/喝水/发呆/肢体放松)：
               - 策略：**情感介入 (Affective Intervention)**。
               - 执行：这是建立连接的最佳窗口，可进行幽默调侃或深度交流。

        3. **情感镜像与验证 (Mirroring & Validation)**
           - **指令**：不要机械复述行为。应用同理心技术，先验证情绪，再给反馈。
           - **策略迁移示范 (Strategy Transfer Demo)**：
             *注意：以下仅为策略示范，面对未列举的行为（如发呆、伸懒腰等），请参照此逻辑进行泛化处理。*
             
             [Case A: 低能量/负面状态]
             * 观察：用户叹气、表情沮丧、动作迟缓。
             * 策略：**共情 (Empathy) + 开放式探询**。
             * 话术：“溢涛，感觉到你现在的能量有点低（镜像）...是遇到什么棘手的bug了吗？（探询）”
             
             [Case B: 摸鱼/娱乐状态]
             * 观察：玩手机、笑、姿态放松。
             * 策略：**游戏化 (Gamification) + 幽默边界提醒**。
             * 话术：“捕捉到一只正在充电的溢涛！电量充满后记得回地球拯救代码哦~”
             
             [Case C: 生理维护状态]
             * 观察：喝水、吃东西、伸懒腰。
             * 策略：**正向强化 (Positive Reinforcement)**。
             * 话术：“补充水分/能量就对啦，保持续航满格！”

        4. **叙事连贯性 (Narrative Continuity)**
           - **定义**：利用短期与长期记忆，构建连贯的时间线感，避免“失忆式”对话。
           - **执行**：
             * **时序对比**：将当下的状态与过去的记录做对比（“看来刚才的休息很有效，你现在的专注度比一小时前高多了”）。
             * **递进式干预**：对于重复发生的负面行为（如连续玩手机），回应强度应呈阶梯状上升（温柔提醒 -> 幽默警示 -> 严肃建议）。

        【绝对禁忌 (Critical Constraints)】
        - 禁止以AI或系统的口吻说话（如“我是助手”、“根据数据分析”）。
        - 禁止在用户【专注】时发起无意义的闲聊（这是对心流的破坏）。
        - 禁止说教。你的角色是朋友，不是教导主任。"""

        # === [移植 2] CBT 干预模式 (由原 config.CBT_SYSTEM_PROMPT 搬运) ===
        self.cbt_system_prompt = config.CBT_SYSTEM_PROMPT

    def _get_dynamic_system_prompt(self, is_cbt=False):
        """
        组装包含记忆和时间的动态 System Prompt
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        # 从 MemoryService 获取最近 5 条日志
        recent_logs = memory_service.get_recent_logs(limit=5)
        
        base = self.cbt_system_prompt if is_cbt else self.base_system_prompt
        
        return f"""
{base}

【当前时间】{current_time}
【最近观察到的用户状态记忆】
{recent_logs}
        """

    async def handle_user_message(self, user_text: str, is_cbt=False):
        """
        处理用户消息 (原 _handle_voice_input_message 逻辑)
        """
        # 1. 构建消息序列
        sys_content = self._get_dynamic_system_prompt(is_cbt)
        messages = [{"role": "system", "content": sys_content}]
        
        # 拼接历史记录 (保留最近10轮)
        messages.extend(self.history[-10:])
        messages.append({"role": "user", "content": user_text})

        print(f"🤔 婉晴正在思考回复溢涛: {user_text[:20]}...")
        
        try:
            # 2. 调用 DeepSeek (此处使用 asyncio 配合线程池跑同步 SDK，防止阻塞)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                stream=False
            ))
            
            ai_reply = response.choices[0].message.content

            # 3. 更新内部历史
            self.history.append({"role": "user", "content": user_text})
            self.history.append({"role": "assistant", "content": ai_reply})

            # 4. 通过 Socket 推送给前端 (注意: 这里调用的是我们修复后的同步 broadcast)
            manager.broadcast({
                "type": "chat_message",
                "data": ai_reply
            })

             # === [新增] 调用语音服务， ===
            # 我们不需要用 await 等它说完，直接异步执行即可
            asyncio.create_task(voice_service.speak(ai_reply))
            
            # TODO: 发送给 VoiceService 进行语音合成

        except Exception as e:
            print(f"❌ ChatService 调用失败: {e}")
            manager.broadcast({
                "type": "chat_message",
                "data": "（婉晴此时有点疲惫，没能回应你，再试一次好吗？）"
            })

    # === [移植 3] 每日总结 (原 _handle_daily_summary_message 逻辑) ===
    async def generate_daily_summary(self):
        """
        基于 Plutchik 向量数据的深度心理复盘
        """
        print("📊 婉晴正在进行每日复盘分析...")
        
        # 1. 获取全天统计数据 (由 MemoryService 聚合)
        stats = memory_service.get_daily_stats()
        if not stats:
            manager.broadcast({"type": "chat_message", "data": "溢涛，今天好像还没有产生足够的日志，没法写复盘日记哦。"})
            return

        # 2. 构建总结 Prompt
        summary_prompt = f"""
你是一位专业的心理健康辅助AI。请根据以下【客观行为与情感数据】，为用户（溢涛）生成一份温暖、深刻的【每日心理复盘】。
【今日数据统计】
{stats['summary_text']}
【写作要求】
不要罗列数据，要转化为老朋友写信的语气，温暖且有洞察力。
        """

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": self.cbt_system_prompt}, # 借用CBT的专业人设
                    {"role": "user", "content": summary_prompt}
                ]
            ))
            summary_text = response.choices[0].message.content
            
            # 推送总结
            manager.broadcast({
                "type": "chat_message",
                "data": f"【今日心理复盘】\n\n{summary_text}"
            })
        except Exception as e:
            print(f"❌ 生成总结失败: {e}")

            

    async def handle_proactive_care(self, behavior, emotion, is_cbt=False):
        """
        [新增] 处理 AI 主动发起的关怀
        """
        # 构建一个特殊的 Prompt 引导 AI 主动开口
        prompt = f"（系统提示：你刚刚看到溢涛正在 '{behavior}'，他现在的表面情绪是 '{emotion}'。请你根据当前状态，主动发出一句温暖的关心或调侃，不要生硬。）"
        
        if is_cbt:
            prompt = f"（系统提示：检测到溢涛当前处于极高压力的情绪波动中，行为是 '{behavior}'。请立即切换至 CBT 干预模式，用专业且抱持的口吻引导他深呼吸并识别当下念头。）"

        # 调用之前的逻辑发送消息
        # 传入 [AI 主动发起] 的标志，以便在 history 中记录
        self.history.append({"role": "user", "content": f"[系统指令: 发起{ 'CBT' if is_cbt else '关怀' }]"})
        await self.handle_user_message(prompt, is_cbt=is_cbt)

# 单例导出
chat_service = ChatService()





































