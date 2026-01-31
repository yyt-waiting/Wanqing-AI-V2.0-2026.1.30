# backend/services/voice_service.py
import base64
import json
import asyncio
from dashscope.audio.tts_v2 import SpeechSynthesizer
from ai_assistant.utils import config
from socket_manager import manager

class VoiceService:
    """
    【语音合成服务】
    职责：将文字转化为生动的语音流，并通过 WebSocket 发送至前端播放。
    """
    def __init__(self):
        # 从配置中读取模型和音色
        # 推荐音色：'shanshuo' (活泼女声), 'zhichu' (温柔女声)
        self.model = config.TTS_MODEL or "cosyvoice-v1"
        self.voice = config.TTS_VOICE or "shanshuo" 

    async def speak(self, text: str):
        """
        核心方法：文字 -> 语音 -> WebSocket 广播
        """
        if not text:
            return

        print(f"🎙️ 婉晴准备说话: {text[:20]}...")

        try:
            # 1. 在线程池中运行同步的 TTS 合成，防止阻塞主循环
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(None, self._synthesize, text)

            if audio_data:
                # 2. 将二进制 MP3 数据转为 Base64 字符串
                audio_b64 = base64.b64encode(audio_data).decode('utf-8')

                # 3. 通过 WebSocket 发送
                # 这里的 type 为 'voice_play'，前端会识别并播放
                manager.broadcast({
                    "type": "voice_play",
                    "data": f"data:audio/mp3;base64,{audio_b64}"
                })
                print("✅ 语音数据已下发")
            else:
                print("❌ TTS 返回数据为空")

        except Exception as e:
            print(f"❌ 语音合成失败: {e}")

    def _synthesize(self, text):
        """同步合成逻辑 (供线程池调用)"""
        try:
            synthesizer = SpeechSynthesizer(model=self.model, voice=self.voice)
            return synthesizer.call(text)
        except Exception as e:
            print(f"Dashscope TTS 底层错误: {e}")
            return None

# 单例导出
voice_service = VoiceService()