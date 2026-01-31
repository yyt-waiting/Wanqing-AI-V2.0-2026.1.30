# ai_assistant/core/emotion_engine.py

import numpy as np
import math
from ai_assistant.utils import config

class EmotionEngine:
    """
    [学术重构版] 情感计算引擎。
    核心算法：
    1. 状态空间：8维 Plutchik 向量空间。
    2. 平滑算法：指数移动平均 (EMA)。
    3. 复杂情绪：基于模糊逻辑 (Fuzzy Logic) 的合成。
    4. UI映射：基于余弦相似度 (Cosine Similarity) 的最近邻分类。
    """
    def __init__(self):
        # 内部状态维持为 numpy 数组，方便线性代数计算
        self.current_vector = np.zeros(8, dtype=float) 
        self.labels = config.PLUTCHIK_EMOTIONS
        
        # 复合情绪的模糊隶属度记录
        self.complex_emotions_fuzzy = {} 

    def update(self, new_observation: dict) -> np.ndarray:
        """
        [学术重构] 状态更新方程。
        结合了 观测输入(Input)、惯性(Inertia) 和 稳态衰减(Homeostasis)。
        
        System Equation:
        S_t = [ alpha * S_{t-1} + (1 - alpha) * O_t ] * (1 - decay)
        
        其中:
        - alpha (Inertia): 由人格特质 Neuroticism 决定
        - decay (Homeostasis): 由人格特质 Extraversion 决定
        """
        # 1. 观测向量化
        obs_vector = np.array([new_observation.get(label, 0.0) for label in self.labels])
        
        # 2. 惯性更新 (EMA)
        alpha = config.EMOTION_INERTIA
        smoothed_input = self.current_vector * alpha + obs_vector * (1.0 - alpha)
        
        # 3. [新增] 稳态调节 (Homeostatic Regulation)
        # 模拟生物情绪的自然消退/能量耗散
        # 如果没有持续的外部刺激 O_t，S_t 最终会收敛到 0 (平静)
        decay_rate = config.HOMEOSTATIC_DECAY
        
        # 确保不会衰减成负数（虽然理论上不会，但工程上做个保护）
        self.current_vector = smoothed_input * (1.0 - decay_rate)
        
        # 极小值截断 (防止浮点数拖尾)
        self.current_vector[self.current_vector < 0.01] = 0.0
        
        return self.current_vector

    def get_arousal_level(self) -> float:
        """
        计算 L2 范数 (欧几里得范数) 作为唤醒度。
        """
        return float(np.linalg.norm(self.current_vector))

    def compute_complex_emotions(self) -> str:
        """
        [算法核心] 使用模糊逻辑 (Fuzzy Logic) 计算复合情绪。
        不使用 if > 5 这种硬阈值，而是计算隶属度。
        
        Formula:
        mu_High(x) = 1 / (1 + exp(-k * (x - x0)))  [Sigmoid 隶属度函数]
        mu_Compound(A, B) = min(mu_High(A), mu_High(B)) [Zadeh算子 / T-norm]
        """
        # 辅助函数：计算单维度的隶属度 (Membership Degree)
        def fuzzy_membership(value):
            k = config.FUZZY_SIGMOID_SLOPE
            x0 = config.FUZZY_SIGMOID_OFFSET
            # Sigmoid 函数
            return 1.0 / (1.0 + np.exp(-k * (value - x0)))

        # 获取当前向量的字典形式
        current_dict = dict(zip(self.labels, self.current_vector))
        
        # 定义复合规则 (可以扩展)
        # 规则: Key = (Component A, Component B), Value = Name
        rules = [
            (("喜悦", "信任"), "爱 (Love)"),
            (("恐惧", "期待"), "焦虑 (Anxiety)"),
            (("期待", "喜悦"), "乐观 (Optimism)"),
            (("惊讶", "悲伤"), "失望 (Disapproval)")
        ]
        
        max_degree = 0.0
        dominant_complex = None
        
        self.complex_emotions_fuzzy = {}

        for (emo_a, emo_b), name in rules:
            val_a = current_dict.get(emo_a, 0)
            val_b = current_dict.get(emo_b, 0)
            
            # 计算各自的"高"隶属度
            mu_a = fuzzy_membership(val_a)
            mu_b = fuzzy_membership(val_b)
            
            # 计算复合情绪的隶属度 (取交集，即 Min)
            mu_complex = min(mu_a, mu_b)
            
            self.complex_emotions_fuzzy[name] = mu_complex
            
            # 记录最显著的复合情绪
            if mu_complex > max_degree:
                max_degree = mu_complex
                dominant_complex = name
        
        # 只有当隶属度超过一定置信度 (比如 0.6) 时才返回，否则认为没有显著复合情绪
        if max_degree > 0.6:
            return dominant_complex
        return None

    def get_ui_emotion_by_similarity(self) -> str:
        """
        [算法核心] 使用余弦相似度决定 UI 展示。
        计算当前向量与所有 UI 质心向量的相似度，取最大者。
        """
        max_sim = -1.0
        best_ui = "平静" # 默认
        
        # 防止除以零
        norm_current = np.linalg.norm(self.current_vector)
        if norm_current < 0.1:
            return "平静"

        for ui_name, centroid in config.UI_CENTROIDS.items():
            norm_centroid = np.linalg.norm(centroid)
            if norm_centroid == 0: continue
            
            # 余弦相似度公式: (A . B) / (||A|| * ||B||)
            similarity = np.dot(self.current_vector, centroid) / (norm_current * norm_centroid)
            
            if similarity > max_sim:
                max_sim = similarity
                best_ui = ui_name
                
        return best_ui
    
    def get_current_state_dict(self):
        """返回字典格式供日志使用"""
        return dict(zip(self.labels, self.current_vector))






