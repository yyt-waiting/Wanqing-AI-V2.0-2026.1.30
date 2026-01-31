# ai_assistant/core/decision_maker.py

import time
import math
import numpy as np
from ai_assistant.utils import config

class DecisionMaker:
    """
    [Phase X 最终版] 自适应效用决策引擎 (Adaptive Utility Decision Engine)。
    集成特征：
    1. 确定性效用计算 (Deterministic Utility)
    2. 在线反馈学习 (Online Feedback Learning) - 根据用户反应动态调整策略权重
    """
    def __init__(self):
        self.last_action_time = {} 
        self.last_state_snapshot = None # 记录上一次决策时的状态，用于对比
        self.last_action_taken = None   # 记录上一次采取的动作
        
        # 动态权重调整矩阵 (Memory)
        # 用于存储对 REWARD_CONFIG 的修正值 (Delta)
        # 格式: { (state_key, action): delta_score }
        self.adaptive_weights = {} 

    def evaluate_action_value(self, current_state: dict, behavior: str) -> str:
        """
        Step 1: 评估并决策
        """
        # --- [新增] 反馈学习环节 ---
        # 在做新决策前，先看一眼上一次决策的效果好不好
        if self.last_state_snapshot and self.last_action_taken != config.ACTIONS.WAIT:
            self._learn_from_feedback(self.last_state_snapshot, current_state, self.last_action_taken)

        # --- 决策环节 (保持不变，但增加了 adaptive_weights 的考量) ---
        ui_emotion = current_state.get('ui_emotion')
        complex_e = current_state.get('complex_emotion')
        arousal = current_state.get('arousal', 0.0)
        
        state_key = "焦虑" if (complex_e and "焦虑" in complex_e) else ui_emotion
        
        best_action = config.ACTIONS.WAIT
        max_score = -float('inf') 
        
        print(f"\n[System 2] 决策计算 | State:{state_key} | Arousal:{arousal:.2f}")
        
        for action in [config.ACTIONS.WAIT, config.ACTIONS.LIGHT_CARE, config.ACTIONS.DEEP_INTERVENTION]:
            score = self._calculate_utility(state_key, action, behavior, arousal)
            
            # 打印包含学习权重的得分
            learned_bias = self.adaptive_weights.get((state_key, action), 0.0)
            print(f"   - {action:4s} | Base:{score-learned_bias:.1f} + Learn:{learned_bias:.1f} = {score:.2f}")
            
            if score > max_score:
                max_score = score
                best_action = action
                
        # 更新状态快照
        if best_action != config.ACTIONS.WAIT:
            self.last_action_time[best_action] = time.time()
            self.last_state_snapshot = current_state # 存下当前状态，等下一轮来看看有没有变好
            self.last_action_taken = best_action
        else:
            # 如果是静默，通常不进行强反馈学习，以免噪音干扰
            self.last_state_snapshot = None
            
        return best_action

    def _calculate_utility(self, emotion_key: str, action: str, behavior: str, arousal: float) -> float:
        """
        [学术重构] 效用函数 U(a) = R_static + R_adaptive + R_bias - C - P_decay
        """
        # 1. R_static: 静态先验知识 (Expert Knowledge)
        r_static = config.REWARD_CONFIG.get((emotion_key, action), config.DEFAULT_REWARD)
        
        # 2. [新增] R_adaptive: 自适应学习权重 (Learned Preference)
        # 这是 Agent 通过交互"学"到的偏好
        r_adaptive = self.adaptive_weights.get((emotion_key, action), 0.0)

        # 行为上下文修正
        if "专注" in behavior and action == config.ACTIONS.DEEP_INTERVENTION:
            r_static -= 50.0 

        # 3. R_arousal_bias: 唤醒度偏差
        r_arousal = 0.0
        if action == config.ACTIONS.DEEP_INTERVENTION:
            if arousal > 6.0: 
                r_arousal = (arousal - 6.0) * 2.0

        # 4. C_cost: 固有成本
        c_cost = 0.0
        if action != config.ACTIONS.WAIT:
            c_cost = 2.0 

        # 5. P_time_decay: 时间衰减
        p_penalty = 0.0
        last_time = self.last_action_time.get(action, 0)
        if last_time > 0:
            time_diff = time.time() - last_time
            if action == config.ACTIONS.LIGHT_CARE:
                p_penalty = 50.0 * math.exp(-0.05 * time_diff)
            elif action == config.ACTIONS.DEEP_INTERVENTION:
                p_penalty = 100.0 * math.exp(-0.01 * time_diff)

        # === 总效用 ===
        return r_static + r_adaptive + r_arousal - c_cost - p_penalty

    def _learn_from_feedback(self, prev_state: dict, curr_state: dict, action: str):
        """
        [学术重构] 基于情感反馈的参数更新 (Delta Learning Rule).
        如果介入后用户状态改善 -> 增加权重
        如果介入后用户状态恶化 -> 减少权重
        """
        # 提取关键指标
        prev_arousal = prev_state.get('arousal', 0.0)
        curr_arousal = curr_state.get('arousal', 0.0)
        
        # 简单的改善指标: 唤醒度(压力)是否下降?
        # Delta < 0 表示压力减轻 (Good)
        # Delta > 0 表示压力上升 (Bad)
        delta_arousal = curr_arousal - prev_arousal
        
        # 定义学习率 (Learning Rate)
        alpha = 0.5 
        
        # 确定 Reward Signal (反馈信号)
        # 如果压力下降了，给予正反馈；反之负反馈
        # 我们希望 delta_arousal 越负越好 -> reward = -delta
        feedback_signal = -delta_arousal 
        
        # 状态键
        ui_emotion = prev_state.get('ui_emotion')
        complex_e = prev_state.get('complex_emotion')
        state_key = "焦虑" if (complex_e and "焦虑" in complex_e) else ui_emotion
        
        key = (state_key, action)
        current_weight = self.adaptive_weights.get(key, 0.0)
        
        # 更新公式: W_new = W_old + alpha * (Feedback)
        # 为了防止权重无限发散，可以加一个衰减项或者限制范围，这里简化处理
        if abs(feedback_signal) > 0.1: # 只有显著变化才学习，忽略噪音
            new_weight = current_weight + alpha * feedback_signal
            
            # 限制学习范围 (-20 到 +20)，防止过拟合
            new_weight = max(-20.0, min(20.0, new_weight))
            
            self.adaptive_weights[key] = new_weight
            
            print(f"[自适应学习] Action '{action}' 后，压力变化 {delta_arousal:.2f}。权重修正: {current_weight:.2f} -> {new_weight:.2f}")