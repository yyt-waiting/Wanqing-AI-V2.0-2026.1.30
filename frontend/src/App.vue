<template>
  <!-- 全局沉浸式背景 -->
  <div 
    class="relative w-screen h-screen overflow-hidden transition-colors duration-[2000ms] ease-in-out font-sans"
    :class="bgGradientClass"
  >
    <!-- 背景光晕 -->
    <div class="absolute inset-0 opacity-40 blur-[120px] animate-pulse-slow bg-gradient-to-tr from-white/10 to-transparent pointer-events-none"></div>

    <!-- 主布局 -->
    <div class="relative z-10 flex h-full w-full max-w-[1600px] mx-auto p-6 gap-6">
      
      <!-- === 左侧区域 === -->
      <div class="w-2/5 flex flex-col gap-6">
        
        <!-- 立绘展示区 -->
        <div class="flex-1 relative rounded-3xl border border-white/10 bg-white/5 backdrop-blur-sm overflow-hidden flex items-center justify-center group">
          <img 
            :src="currentPortraitPath" 
            class="h-[90%] object-contain drop-shadow-[0_0_15px_rgba(255,255,255,0.2)] animate-float transition-all duration-700"
            alt="Role Portrait"
          />
          <!-- 状态标签 -->
          <div class="absolute top-4 left-4 px-3 py-1 rounded-full bg-black/30 border border-white/10 text-xs text-white/70 backdrop-blur-md flex flex-col gap-1">
            <span>状态: {{ currentEmotion }}</span>
            <span class="text-[10px] text-slate-400">行为: {{ currentBehavior }}</span>
          </div>
        </div>

        <!-- 多功能视窗 -->
        <div class="h-64 rounded-3xl border border-white/10 bg-black/20 backdrop-blur-md flex flex-col overflow-hidden relative">
          <!-- 切换按钮 -->
          <div class="absolute top-3 right-3 flex bg-black/40 rounded-lg p-1 z-20">
            <button @click="viewMode = 'radar'" class="px-3 py-1 text-xs rounded-md transition-all" :class="viewMode === 'radar' ? 'bg-cyan-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'">情感雷达</button>
            <button @click="viewMode = 'camera'" class="px-3 py-1 text-xs rounded-md transition-all" :class="viewMode === 'camera' ? 'bg-cyan-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'">视觉信号</button>
          </div>

          <!-- 雷达图容器 -->
          <div v-show="viewMode === 'radar'" class="flex-1 w-full h-full" ref="radarChartRef"></div>

          <!-- 摄像头容器 -->
          <div v-show="viewMode === 'camera'" class="flex-1 bg-black flex items-center justify-center relative w-full h-full overflow-hidden">
             <!-- 这里的 img src 绑定了 videoFrameData -->
             <img v-if="videoFrameData" :src="videoFrameData" class="w-full h-full object-cover opacity-90" />
             <div v-else class="text-slate-600 text-xs animate-pulse">等待视觉信号...</div>
             <!-- 扫描线特效 -->
             <div class="absolute inset-0 bg-gradient-to-b from-transparent via-cyan-500/10 to-transparent h-full w-full animate-scan pointer-events-none"></div>
          </div>
        </div>
      </div>

      <!-- === 右侧聊天区域 === -->
      <div class="w-3/5 rounded-3xl border border-white/10 bg-gradient-to-b from-white/10 to-black/40 backdrop-blur-xl flex flex-col overflow-hidden shadow-2xl">
        <!-- 顶部栏 -->
        <div class="h-16 border-b border-white/5 flex items-center px-6 justify-between bg-black/20">
          <div class="flex items-center gap-3">
             <div class="w-2 h-2 rounded-full animate-pulse" :class="isConnected ? 'bg-green-500' : 'bg-red-500'"></div>
             <span class="text-lg font-medium text-slate-200 tracking-wider">WANQING <span class="text-xs text-slate-500 ml-2">LIVE</span></span>
          </div>
          <div class="text-xs text-slate-500">{{ isConnected ? '实时连接中' : '连接断开' }}</div>
        </div>

        <!-- 聊天记录 -->
        <div class="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide" id="chat-container">
          <div v-for="(msg, index) in chatHistory" :key="index" class="flex gap-4" :class="msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'">
            <div class="w-10 h-10 rounded-full bg-slate-700 overflow-hidden border border-white/20 flex-shrink-0">
               <img :src="msg.role === 'user' ? '/portraits/user_avatar.png' : '/portraits/ai_avatar.png'" class="w-full h-full object-cover" @error="handleImgError" />
            </div>
            <div class="max-w-[70%] px-5 py-3 rounded-2xl text-sm leading-relaxed shadow-lg backdrop-blur-sm transition-all"
              :class="msg.role === 'user' ? 'bg-cyan-600/80 text-white rounded-tr-sm' : 'bg-white/10 text-slate-200 border border-white/5 rounded-tl-sm'">
              {{ msg.text }}
            </div>
          </div>
        </div>

        <!-- 输入栏 -->
        <div class="p-6 bg-black/20 border-t border-white/5">
          <div class="relative flex items-end gap-3 bg-white/5 border border-white/10 rounded-2xl p-2 focus-within:bg-white/10 focus-within:border-cyan-500/50">
            <textarea v-model="inputMessage" @keydown.enter.prevent="sendMessage" placeholder="与婉晴对话..." class="w-full bg-transparent border-none text-slate-200 text-sm p-2 max-h-32 focus:ring-0 resize-none placeholder-slate-500" rows="1"></textarea>
            <button @click="sendMessage" class="mb-1 p-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg active:scale-95">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" /></svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

// === 状态 ===
const viewMode = ref('radar') 
const currentEmotion = ref('平静')
const currentBehavior = ref('初始化中...')
const inputMessage = ref('')
const isConnected = ref(false)
const videoFrameData = ref(null)
const chatHistory = ref([{ role: 'ai', text: '正在建立感知连接...' }])

// WebSocket 实例
let socket = null
// ECharts 实例
let myChart = null
const radarChartRef = ref(null)

// Plutchik 8维标签
const emotionLabels = ["喜悦", "信任", "恐惧", "惊讶", "悲伤", "厌恶", "愤怒", "期待"]
const currentVector = ref([0,0,0,0,0,0,0,0]) // 初始数据

// === 计算属性 ===
const currentPortraitPath = computed(() => {
  const map = {
    '开心': '/portraits/开心.png', '喜悦': '/portraits/开心.png',
    '生气': '/portraits/生气.png', '愤怒': '/portraits/生气.png',
    '悲伤': '/portraits/无奈.png', '无奈': '/portraits/无奈.png',
    '焦虑': '/portraits/害怕.png', '害怕': '/portraits/害怕.png',
    '恐惧': '/portraits/害怕.png', '惊讶': '/portraits/惊讶.png',
    '好奇': '/portraits/好奇.png', '害羞': '/portraits/害羞.png',
  }
  return map[currentEmotion.value] || '/portraits/正常.png'
})

const bgGradientClass = computed(() => {
  const map = {
    '开心': 'bg-slate-900', '喜悦': 'bg-slate-900',
    '生气': 'bg-red-950',   '愤怒': 'bg-red-950',
    '悲伤': 'bg-blue-950',  '无奈': 'bg-blue-950',
    '焦虑': 'bg-stone-900', '恐惧': 'bg-stone-900',
  }
  return map[currentEmotion.value] || 'bg-slate-950'
})

// === ECharts 初始化与更新 ===
const initChart = () => {
  if (!radarChartRef.value) return
  myChart = echarts.init(radarChartRef.value)
  updateChartOption()
  
  // 监听窗口大小变化
  window.addEventListener('resize', () => myChart.resize())
}

const updateChartOption = () => {
  if (!myChart) return
  const option = {
    backgroundColor: 'transparent',
    radar: {
      center: ['50%', '55%'], // [新增] 手动居中
      radius: '65%',          // [新增] 放大半径 (原来默认可能只有 40% 显得很小)
      indicator: emotionLabels.map(name => ({ name, max: 10 })),
      shape: 'circle',
      splitNumber: 4,
      axisName: { color: '#94a3b8', fontSize: 10 },
      splitLine: { lineStyle: { color: ['rgba(255,255,255,0.05)', 'rgba(255,255,255,0.1)'] } },
      splitArea: { show: false },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }
    },
    series: [{
      type: 'radar',
      data: [{ value: currentVector.value }],
      symbol: 'none',
      lineStyle: { width: 2, color: '#06b6d4' }, // cyan-500
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(6,182,212,0.6)' }, { offset: 1, color: 'rgba(6,182,212,0.1)' }]) }
    }]
  }
  myChart.setOption(option)
}

// === WebSocket 逻辑 ===
const connectWebSocket = () => {
  // 注意：这里连接后端的 8000 端口
  socket = new WebSocket('ws://localhost:8000/ws')

  socket.onopen = () => {
    console.log('✅ WebSocket Connected')
    isConnected.value = true
    chatHistory.value.push({ role: 'ai', text: '感知系统已联机。' })
  }

  socket.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)
      
      // 1. 处理视频帧 (快车道)
      if (msg.type === 'video_frame') {
        videoFrameData.value = msg.data
      }
      
      // 2. 处理感知更新 (慢车道 - AI分析结果)
      else if (msg.type === 'perception_update') {
        const data = msg.data
        
        // 更新情绪和行为文本
        currentEmotion.value = data.emotion || '平静'
        currentBehavior.value = data.behavior || '未知'
        
        // 更新雷达图
        if (data.vector) {
          // 将字典转为数组顺序 [喜悦, 信任...]
          currentVector.value = emotionLabels.map(label => data.vector[label] || 0)
          updateChartOption()
        }
        
        // 如果有分析文本，AI 说话 (模拟)
        if (data.analysis && data.analysis !== "无详细分析") {
           // 这里我们只取分析文本的前一句作为简短反馈，避免刷屏
           // 实际对话逻辑应该在后端处理并通过专门的 chat 消息发送
        }
      }
      
      // 3. 处理后端发来的对话 (如果有)
      else if (msg.type === 'chat_message') {
         chatHistory.value.push({ role: 'ai', text: msg.data })
         scrollToBottom()
      }

      // 4. 处理语音播放 (新增)
      else if (msg.type === 'voice_play') {
        console.log('🎵 收到语音流，准备播放...')
        // 创建一个临时的音频对象并播放
        const audio = new Audio(msg.data)
        // 可以根据需要设置音量
        audio.volume = 0.8 
        audio.play().catch(e => {
            console.warn('播放失败，可能是浏览器权限限制，请点击页面任意处激活', e)
        })
      }

    } catch (e) {
      console.error('WS Parse Error:', e)
    }
  }

  socket.onclose = () => {
    console.log('❌ WebSocket Disconnected')
    isConnected.value = false
    // 断线重连
    setTimeout(connectWebSocket, 3000)
  }
}

// === 辅助方法 ===
const sendMessage = () => {
  if (!inputMessage.value.trim() || !socket) return
  
  const text = inputMessage.value
  chatHistory.value.push({ role: 'user', text })
  inputMessage.value = ''
  
  // 发送给后端
  socket.send(JSON.stringify({ type: 'chat', text }))
  scrollToBottom()
}

const scrollToBottom = () => {
  nextTick(() => {
    const container = document.getElementById('chat-container')
    if (container) container.scrollTop = container.scrollHeight
  })
}

const handleImgError = (e) => { e.target.src = 'https://via.placeholder.com/40' }

// === 生命周期 ===
onMounted(() => {
  initChart()
  connectWebSocket()
})

// 监听 viewMode 变化，如果切回雷达图，强制重绘一次
watch(viewMode, (newVal) => {
  if (newVal === 'radar') {
    nextTick(() => {
      myChart && myChart.resize()
    })
  }
})

onUnmounted(() => {
  if (socket) socket.close()
  if (myChart) myChart.dispose()
})
</script>

<style>
.scrollbar-hide::-webkit-scrollbar { display: none; }
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
</style>