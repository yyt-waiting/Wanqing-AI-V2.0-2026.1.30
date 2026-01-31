# check_env.py
import sys
import os

print("="*30)
print("🔍 开始环境自检程序...")
print("="*30)

# 1. 检查第三方库
try:
    import fastapi
    print("✅ FastAPI 已安装")
    import uvicorn
    print("✅ Uvicorn 已安装")
    import numpy as np
    print("✅ Numpy 已安装")
    import cv2
    print("✅ OpenCV (视觉) 已安装")
    import dashscope
    print("✅ Dashscope (DeepSeek/Qwen依赖) 已安装")
    import funasr
    print("✅ FunASR (语音识别) 已安装")
except ImportError as e:
    print(f"❌ 严重错误：缺少依赖库 -> {e}")
    print("请重新运行 pip install 命令安装缺失的库。")
    sys.exit(1)

# 2. 检查项目路径和配置
try:
    # 尝试导入我们的核心配置
    from ai_assistant.utils import config
    print("✅ 本地模块 ai_assistant 路径正常")
    
    # 检查 Phase X 的数学配置是否存在
    if hasattr(config, 'BASIS_VECTORS') and hasattr(config, 'REWARD_CONFIG'):
        print("✅ 配置文件完整 (包含 Phase X 数学内核)")
    else:
        print("⚠️ 警告：配置文件可能版本过旧，缺少数学定义")

except Exception as e:
    print(f"❌ 项目结构错误：找不到代码模块 -> {e}")
    print("请确认 ai_assistant 文件夹是否完整复制过来了。")
    sys.exit(1)

# 3. 检查情感引擎 (数学运算测试)
try:
    print("Testing 情感引擎初始化...")
    from ai_assistant.core.emotion_engine import EmotionEngine
    engine = EmotionEngine()
    
    # 模拟输入一个开心的数据，看是否报错
    test_input = {"喜悦": 8.0, "信任": 5.0}
    engine.update(test_input)
    arousal = engine.get_arousal_level()
    
    print(f"✅ 情感引擎运算正常 (模拟唤醒度: {arousal})")
    print("✅ Phase X 数学逻辑验证通过")

except Exception as e:
    print(f"❌ 情感引擎崩溃 -> {e}")
    sys.exit(1)

print("="*30)
print("🎉 恭喜！环境完美，可以开始重构后端了！")
print("="*30)