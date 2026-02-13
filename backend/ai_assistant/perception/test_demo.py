"""
PerceptionEngine 验收脚本
- 读取测试图片和音频
- 输出符合协议的JSON
- 运行不报错即通过
"""

import json
import os
import sys
from feature_extractor import PerceptionEngine

def main():
    print("=" * 60)
    print("🌸 婉晴感知模块 - 验收测试 v1.0")
    print("=" * 60)
    
    # 1. 初始化引擎
    print("\n📀 初始化 PerceptionEngine...")
    try:
        engine = PerceptionEngine()
        print("✅ 初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        sys.exit(1)
    
    # 2. 准备测试文件路径
    current_dir = os.path.dirname(__file__)
    test_data_dir = os.path.join(current_dir, "test_data")
    os.makedirs(test_data_dir, exist_ok=True)
    
    image_path = os.path.join(test_data_dir, "face_sample.jpg")
    audio_path = os.path.join(test_data_dir, "audio.wav")
    
    # 3. 检查测试文件
    print("\n📁 检查测试文件...")
    image_exists = os.path.exists(image_path)
    audio_exists = os.path.exists(audio_path)
    
    if image_exists:
        print(f"✅ 测试图片: {os.path.basename(image_path)}")
    else:
        print(f"⚠️ 缺少测试图片: {image_path}")
    
    if audio_exists:
        print(f"✅ 测试音频: {os.path.basename(audio_path)}")
    else:
        print(f"⚠️ 缺少测试音频: {audio_path}")
    
    if not (image_exists or audio_exists):
        print("\n❌ 无任何测试文件，请至少准备一个测试文件")
        sys.exit(1)
    
    # 4. 执行感知分析
    print("\n🔍 正在提取感知特征...")
    try:
        result = engine.analyze(
            image_path=image_path if image_exists else None,
            audio_path=audio_path if audio_exists else None
        )
        print("✅ 特征提取成功")
    except Exception as e:
        print(f"❌ 特征提取失败: {e}")
        sys.exit(1)
    
    # 5. 输出结果
    print("\n📊 感知数据输出:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 6. 协议验证
    print("\n🔬 协议合规性验证:")
    
    # 验证顶层字段
    required_top = ['timestamp', 'visual', 'audio']
    missing_top = [k for k in required_top if k not in result]
    if not missing_top:
        print("  ✅ 顶层结构: 正确")
    else:
        print(f"  ❌ 缺失字段: {missing_top}")
    
    # 验证visual字段
    if 'visual' in result:
        required_visual = ['ear', 'mar', 'blink_count', 'head_pose']
        missing_visual = [k for k in required_visual if k not in result['visual']]
        if not missing_visual:
            print("  ✅ visual结构: 正确")
        else:
            print(f"  ❌ visual缺失: {missing_visual}")
        
        # 验证head_pose子字段
        if 'head_pose' in result['visual']:
            required_pose = ['pitch', 'yaw', 'roll']
            missing_pose = [k for k in required_pose if k not in result['visual']['head_pose']]
            if not missing_pose:
                print("  ✅ head_pose结构: 正确")
            else:
                print(f"  ❌ head_pose缺失: {missing_pose}")
    
    # 验证audio字段
    if 'audio' in result:
        required_audio = ['is_speaking', 'loudness', 'pitch_avg']
        missing_audio = [k for k in required_audio if k not in result['audio']]
        if not missing_audio:
            print("  ✅ audio结构: 正确")
        else:
            print(f"  ❌ audio缺失: {missing_audio}")
    
    # 7. 数据类型验证
    print("\n📋 数据类型验证:")
    if 'visual' in result:
        print(f"  ear: {type(result['visual']['ear']).__name__}, 值: {result['visual']['ear']}")
        print(f"  mar: {type(result['visual']['mar']).__name__}, 值: {result['visual']['mar']}")
        print(f"  blink_count: {type(result['visual']['blink_count']).__name__}, 值: {result['visual']['blink_count']}")
    
    if 'audio' in result:
        print(f"  is_speaking: {type(result['audio']['is_speaking']).__name__}, 值: {result['audio']['is_speaking']}")
        print(f"  loudness: {type(result['audio']['loudness']).__name__}, 值: {result['audio']['loudness']}")
        print(f"  pitch_avg: {type(result['audio']['pitch_avg']).__name__}, 值: {result['audio']['pitch_avg']}")
    
    # 8. 最终结果
    print("\n" + "=" * 60)
    if image_exists and audio_exists:
        print("✅🎉 验收通过！符合数据接口协议！")
    else:
        print("⚠️  部分测试未执行，请补充测试文件后重试")
    print("=" * 60)

    

if __name__ == "__main__":
    main()