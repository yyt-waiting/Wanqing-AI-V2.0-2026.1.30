# ai_assistant/utils/config.py

import os
import numpy as np # [学术重构] 引入 Numpy 进行向量计算

# ==============================================================================
# 1. 基础服务配置 (API & Storage)
# ==============================================================================

# --- OSS (对象存储) 配置 ---
OSS_ACCESS_KEY_ID = ''      # <--- 你的 Access Key ID 在这里
OSS_ACCESS_KEY_SECRET = '' # <--- 你的 Secret 在这里
OSS_ENDPOINT = 'oss-cn-beijing.aliyuncs.com'
OSS_BUCKET = 'camera-vedio-place'

# --- Deepseek API 配置 (大脑) ---
DEEPSEEK_API_KEY = '' # <--- 你的 DeepSeek Key 在这里
DEEPSEEK_BASE_URL = 'https://api.deepseek.com'

# --- Qwen-VL (通义千问视觉语言模型) API 配置 ---
QWEN_API_KEY = ""   # <--- 你的 Qwen/Dashscope Key 在这里
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# --- TTS & ASR 配置 ---
# (注意：TTS 和 ASR 通常也使用 QWEN_API_KEY)
TTS_MODEL = "cosyvoice-v1"
TTS_VOICE = "longwan"
ASR_MODEL_DIR = "iic/SenseVoiceSmall"


# 音频录制参数
AUDIO_CHUNK = 1024
AUDIO_FORMAT = 16
AUDIO_CHANNELS = 1
AUDIO_RATE = 16000
AUDIO_WAVE_OUTPUT_FILENAME = "output.wav"

# ==============================================================================
# 2. Phase X: 情感计算数学模型 (Perception & Math Core)
# ==============================================================================

# 图像分析频率 (秒)
ANALYSIS_INTERVAL_SECONDS = 15

# Plutchik 8种基础情绪维度 (学术标准)
PLUTCHIK_EMOTIONS = [
    "喜悦", "信任", "恐惧", "惊讶", 
    "悲伤", "厌恶", "愤怒", "期待"
]

# 默认零向量
DEFAULT_EMOTION_VECTOR = {k: 0.0 for k in PLUTCHIK_EMOTIONS}

# --- [学术重构] 向量空间定义 ---

# 1. Plutchik 空间的基向量 (Basis Vectors, 8维正交基)
BASIS_VECTORS = {
    "喜悦": np.array([1, 0, 0, 0, 0, 0, 0, 0]),
    "信任": np.array([0, 1, 0, 0, 0, 0, 0, 0]),
    "恐惧": np.array([0, 0, 1, 0, 0, 0, 0, 0]),
    "惊讶": np.array([0, 0, 0, 1, 0, 0, 0, 0]),
    "悲伤": np.array([0, 0, 0, 0, 1, 0, 0, 0]),
    "厌恶": np.array([0, 0, 0, 0, 0, 1, 0, 0]),
    "愤怒": np.array([0, 0, 0, 0, 0, 0, 1, 0]),
    "期待": np.array([0, 0, 0, 0, 0, 0, 0, 1]),
}

# 2. UI 状态质心向量 (Centroids of UI States)
UI_CENTROIDS = {
    "开心": np.array([0.8, 0.2, 0, 0, 0, 0, 0, 0]),
    "惊讶": np.array([0, 0, 0.5, 0.8, 0, 0, 0, 0]),
    "沮丧": np.array([0, 0, 0, 0, 0.9, 0, 0, 0]),
    "生气": np.array([0, 0, 0, 0, 0, 0.4, 0.8, 0]),
    "专注": np.array([0, 0.1, 0, 0, 0, 0, 0, 0.9]),
    "平静": np.array([0, 0, 0, 0, 0, 0, 0, 0]),
}

# --- [Phase X.2 新增] 基于大五人格 (OCEAN) 的参数映射 ---

# 定义数字生命的人格特质 (0.0 - 1.0)
PERSONALITY_PROFILE = {
    "O": 0.5, # 开放性
    "C": 0.8, # 尽责性
    "E": 0.6, # 外向性
    "A": 0.9, # 宜人性
    "N": 0.4  # 神经质
}

# 动态计算惯性系数 (Inertia)
# N越高，情绪越容易波动(惯性小)
def get_derived_inertia():
    N = PERSONALITY_PROFILE["N"]
    return max(0.1, 0.8 - 0.5 * N)

EMOTION_INERTIA = get_derived_inertia()

# 动态计算稳态衰减率 (Homeostatic Decay Rate)
# 模拟能量耗散，E越高恢复越快
def get_derived_decay_rate():
    E = PERSONALITY_PROFILE["E"]
    return 0.05 + 0.05 * E

HOMEOSTATIC_DECAY = get_derived_decay_rate()

# -----------------------------------------------------

COMPOUND_THRESHOLD = 5.0    # 复合情绪激活阈值
FUZZY_SIGMOID_SLOPE = 2.0   # Sigmoid 斜率
FUZZY_SIGMOID_OFFSET = 5.0  # Sigmoid 中点

# 负面情绪列表 (用于兼容)
NEGATIVE_EMOTIONS = ["沮丧", "生气", "疲惫"] 
EMOTION_TRIGGER_THRESHOLD = 1

# ==============================================================================
# 3. Phase 2: 决策内核配置 (POMDP / Utility Function)
# ==============================================================================

class ACTIONS:
    WAIT = "静默观察"
    LIGHT_CARE = "轻度关怀"
    DEEP_INTERVENTION = "深度干预"

REWARD_CONFIG = {
    ("专注", ACTIONS.WAIT): 5.0,
    ("专注", ACTIONS.LIGHT_CARE): -5.0,
    ("专注", ACTIONS.DEEP_INTERVENTION): -20.0,

    ("焦虑", ACTIONS.WAIT): -10.0,
    ("焦虑", ACTIONS.LIGHT_CARE): 5.0,
    ("焦虑", ACTIONS.DEEP_INTERVENTION): 10.0,

    ("沮丧", ACTIONS.WAIT): -2.0,
    ("沮丧", ACTIONS.LIGHT_CARE): 8.0,
    ("沮丧", ACTIONS.DEEP_INTERVENTION): 2.0,

    ("开心", ACTIONS.WAIT): 2.0,
    ("开心", ACTIONS.LIGHT_CARE): 6.0,
    ("开心", ACTIONS.DEEP_INTERVENTION): -5.0
}

DEFAULT_REWARD = 0.0

# ==============================================================================
# 4. Phase 3: 认知行为疗法 (CBT) 与交互配置
# ==============================================================================

AROUSAL_THRESHOLD_HIGH = 7.5

CBT_SYSTEM_PROMPT = """
【指令】
你已切换至**“认知行为疗法 (CBT) 临床干预模式”**。
当前系统检测到用户的心理唤醒度 (Arousal Level) 超过阈值，且伴随显著的负面情绪图谱。
你的目标是通过结构化的对话，协助用户降低情绪强度 (De-escalation) 并识别认知扭曲。

【干预流程 (基于 ABC 模型)】
请严格按照以下逻辑推进对话，但保持语言的自然与温暖：

1. **A (Activating Event) - 锚定当下**：
   - 目标：帮助用户从情绪风暴中通过“着地技术 (Grounding)”回到当下。
   - 话术策略：使用接纳承诺疗法 (ACT) 的技巧。“我感觉到一股强烈的情绪正在流过。溢涛，先停一下，跟我一起深呼吸...”

2. **B (Beliefs) - 苏格拉底式探询 (Socratic Questioning)**：
   - 目标：引导用户识别导致情绪的“自动化思维”。不要直接给建议！要提问！
   - 关键问题示例：
     * “刚才脑海里闪过的第一个念头是什么？”
     * “这个想法完全是事实吗？还是包含了一些我们的猜测？”
     * “如果最好的朋友遇到这种情况，你会怎么对他/她说？”

3. **C (Consequences) - 认知解离与重构**：
   - 目标：将“想法”与“事实”分离，寻找替代性的、更具适应性的思维方式。
   - 策略：提供一个新的视角，或者建议一个微小的行为改变（Behavioral Activation）。

【语气约束】
- **专业且抱持 (Holding)**：像一个稳重的心理咨询师，提供安全感。
- **降维打击**：不要试图一次解决所有问题，专注于降低当下的情绪浓度。
- **避免有毒积极性**：不要说“开心点”、“没事的”，这是否定用户感受。要说“这确实很难，我陪着你”。
"""

SUMMARY_HOTKEY = "ctrl+shift+s"
LOG_FILE = "behavior_log.txt"

# [Phase 4 补全] 每日总结调度配置
DAILY_SUMMARY_HOUR = 17   # 下午 5 点
DAILY_SUMMARY_MINUTE = 30 # 30 分

# ==============================================================================
# 5. UI 与 字体配置
# ==============================================================================
try:
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    
    chinese_fonts = ['SimHei', 'Microsoft YaHei', 'SimSun', 'NSimSun', 'FangSong', 'KaiTi']
    chinese_font = None
    
    for font_name in chinese_fonts:
        try:
            font_path = fm.findfont(fm.FontProperties(family=font_name))
            if os.path.exists(font_path):
                chinese_font = font_name
                break
        except:
            continue
    
    if chinese_font:
        plt.rcParams['font.sans-serif'] = [chinese_font, 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
except Exception as e:
    print(f"Font loading error: {e}")