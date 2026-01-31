# backend/services/decision_service.py
import asyncio
from ai_assistant.core.decision_maker import DecisionMaker
from ai_assistant.utils import config
from services.chat_service import chat_service

class DecisionService:
    """
    【决策与主动关怀服务】
    职责：
    1. 实例化核心决策引擎 (DecisionMaker)。
    2. 接收来自视觉服务的感官数据，评估是否需要介入。
    3. 如果决策结果非“静默”，则指挥 ChatService 发起主动关怀。
    """
    def __init__(self):
        # 1. 实例化你图片中的那个核心算法类
        self.engine = DecisionMaker()
        print("🧠 [DecisionService] 决策引擎已加载，开始实时监控状态...")

    async def process_new_observation(self, behavior_desc, ui_emotion, complex_emotion, arousal):
        """
        [核心逻辑] 每当 MonitorService 完成一轮 AI 分析，都会调用这里。
        """
        # 1. 构造算法需要的状态快照
        current_state = {
            "ui_emotion": ui_emotion,
            "complex_emotion": complex_emotion,
            "arousal": arousal
        }

        # 2. 调用核心算法进行效用评估 (Argmax U)
        # 这个方法内部包含了你图片里的 R_static, R_arousal, C_cost 等计算
        action = self.engine.evaluate_action_value(current_state, behavior_desc)

        # 3. 根据决策结果执行动作
        if action == config.ACTIONS.WAIT:
            print(f"🤫 [Decision] 决策结果: 【{action}】。当前不干扰溢涛。")
            return

        # 4. 如果是 LIGHT_CARE 或 DEEP_INTERVENTION，主动触发对话
        is_deep = (action == config.ACTIONS.DEEP_INTERVENTION)
        mode_text = "深度干预(CBT)" if is_deep else "轻度关怀"
        
        print(f"❤️ [Decision] 触发主动动作: 【{action}】 ({mode_text})")
        
        # 5. 调用 ChatService 发起主动关怀
        # 我们传入一个特殊的标志位，让 ChatService 知道这是 AI 主动发起的
        await chat_service.handle_proactive_care(
            behavior=behavior_desc, 
            emotion=ui_emotion, 
            is_cbt=is_deep
        )

# 单例导出
decision_service = DecisionService()