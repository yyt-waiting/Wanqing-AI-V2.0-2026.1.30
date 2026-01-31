# ai_assistant/utils/helpers.py

import re
import json
from typing import Tuple
from datetime import datetime
from . import config

def extract_emotion_type(analysis_text: str) -> str:
    """
    从分析文本中提取情感类型（如开心、沮丧、专注等）。
    """
    emotion_keywords = {
        "开心": ["开心", "微笑", "愉悦", "兴奋"],
        "沮丧": ["沮丧", "皱眉", "低落", "失落"],
        "专注": ["专注", "认真", "投入", "凝神"],
        "疲惫": ["疲惫", "困倦", "乏力", "打哈欠"],
        "生气": ["生气", "愤怒", "烦躁", "不满"],
        "平静": ["平静", "放松", "平和"]
    }
    for emotion, keywords in emotion_keywords.items():
        for kw in keywords:
            if kw in analysis_text:
                return emotion
    return "未知"

def extract_language_emotion_content(text: str) -> str:
    """
    从ASR（语音识别）的原始输出中提取干净的对话内容。
    """
    match = re.search(r'>\s*([^>]*)$', text)
    if match:
        return match.group(1).strip()
    return text.strip()

def log_observation_to_file(observation: dict):
    """
    将单条观察记录以JSON格式追加到每日日志文件中。
    """
    if 'timestamp' in observation and isinstance(observation['timestamp'], datetime):
        observation['timestamp'] = observation['timestamp'].isoformat()
        
    today_str = datetime.now().strftime('%Y-%m-%d')
    log_file_path = f'observation_log_{today_str}.jsonl'
    
    try:
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(observation, ensure_ascii=False) + '\n')
    except Exception as e:
        print(f"写入观察日志文件时出错: {e}")

def extract_behavior_type(analysis_text: str) -> Tuple[str, str]:
    """
    从AI分析文本中提取行为类型编号和描述。
    """
    pattern = r'(\d+)\s*[.、:]?\s*(认真专注工作|吃东西|用杯子喝水|喝饮料|玩手机|睡觉|其他)'
    match = re.search(pattern, analysis_text)
    
    if match:
        behavior_num = match.group(1)
        behavior_desc = match.group(2)
        return behavior_num, behavior_desc
    
    fallback_patterns = [
        ('认真专注工作', '1'),
        ('吃东西', '2'),
        ('用杯子喝水', '3'),
        ('喝饮料', '4'),
        ('玩手机', '5'),
        ('睡觉', '6'),
        ('其他', '7')
    ]
    
    for desc, num in fallback_patterns:
        if re.search(desc, analysis_text):
            return num, desc
            
    return "0", "未识别"

# ==========================================
# Phase 1.1 新增函数 (必须顶格写，不能缩进)
# ==========================================
def parse_model_response(response_text: str) -> dict:


    
    """
    解析 Qwen-VL 返回的 JSON 数据。
    这是连接感知（API）和决策（代码逻辑）的关键桥梁。
    """
    try:
        # 1. 清洗数据
        cleaned_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()
        if cleaned_text.lower().startswith("json"):
            cleaned_text = cleaned_text[4:].strip()
        
        # 2. 解析 JSON
        data = json.loads(cleaned_text)
        
        # 3. 数据完整性兜底
        if "emotions" not in data:
            data["emotions"] = config.DEFAULT_EMOTION_VECTOR
            
        if "behavior" not in data:
            data["behavior"] = {"id": "0", "description": "未知行为"}
            
        return data

    except Exception as e:
        print(f"解析 JSON 失败: {e} | 原始返回: {response_text[:50]}...")
        # 返回安全结构
        return {
            "behavior": {"id": "0", "description": "识别错误"},
            "emotions": config.DEFAULT_EMOTION_VECTOR,
            "analysis": "视觉分析数据解析失败"
        }




# ======================================================
# Phase 3.3 安全熔断机制
# ======================================================

# 危机关键词库 (可扩展)
CRISIS_KEYWORDS = [
    "不想活", "自杀", "去死", "结束生命", "毫无意义", 
    "绝望", "毁灭", "割腕", "跳楼", "遗书"
]



#我当然不会哈哈！是指用户啦，当然我觉得有些貌似不太吉利？
# 危机干预硬编码回复 (不经过 LLM，确保绝对安全)
CRISIS_RESPONSE = """
我听到了你内心极其痛苦的声音。
请立刻停下来，深呼吸。你现在处于非常危险的情绪风暴中，但请相信这只是暂时的。
我恳请你立刻寻求专业帮助：
1. 请拨打心理援助热线：400-161-9995
2. 或者联系你最信任的朋友/家人。
我一直在这里陪着你，直到风暴过去。
"""

def check_safety_fuse(text: str) -> bool:
    """
    [安全熔断] 检测文本中是否包含危机关键词。
    Returns: True 表示触发熔断（危险），False 表示安全。
    """
    if not text:
        return False
        
    for kw in CRISIS_KEYWORDS:
        if kw in text:
            return True
    return False













