🌸 WANQING-AI V2.0：主动式桌面情感智能体

开发者： 阳溢涛及其“Book思议”小组
版本说明： 本版本为 B/S (Browser/Server) 架构重构版，旨在提供更美观、平滑的交互体验。

📂 项目结构一览 (小白必看)

本项目分为“大脑”和“脸面”两部分，请在开发时分清目录：

backend/ (后端 - 婉晴的大脑)

main.py: 总开关，负责启动服务器。

api/: 处理网络连接的“分拣中心”。

services/: 初级业务逻辑层（对话、视觉、记忆、决策、语音都在这）。

ai_assistant/core/: 核心算法层（数学模型、底层驱动，非必要不修改）。

storage/logs/: 婉晴的“日记本”，存放所有观察日志。

frontend/ (前端 - 婉晴的脸面)

基于 Vue 3 渲染的精美网页，负责立绘显示、对话框、情感雷达图。

🛠️ 技术栈清单

前端：Vue 3, Vite, Tailwind CSS (美化), ECharts (雷达图)

后端：FastAPI (异步框架), WebSocket (实时通信)

AI 核心：

语言：DeepSeek-V3 (对话引擎)

视觉：Qwen-VL-Max (行为与表情识别)

语音：阿里云 DashScope (TTS), 本地 FunASR (ASR)

算法：Plutchik 8维情感模型, POMDP 决策逻辑

🚀 快速开始 (新手安装指南)
1. 环境准备 (就像买食材)

在开始之前，请确保你的电脑安装了以下两个基础软件：

Python 3.10+  (勾选 "Add Python to PATH")

Node.js (LTS版本)  (一路点击“下一步”安装即可)

2. 下载与安装 (把锅架起来)
a. 克隆本项目

打开终端（CMD 或 PowerShell），输入：

git clone [你的GitHub仓库地址]

b. 后端：创建虚拟环境 (建立独立小厨房)

为了防止依赖冲突，我们给后端开辟独立空间：


cd backend
# 创建虚拟环境
python -m venv venv
# 激活虚拟环境 (Windows)
.\venv\Scripts\activate
# 激活成功后，你的命令行开头会出现 (venv) 字样
c. 安装后端依赖 (买齐调料)

注意：这一步由于包含语音模型，下载量约 2GB，请保持网络畅通。不要开梯子


pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

d. 前端：安装依赖 

新开一个终端窗口，进入 frontend 文件夹：


cd frontend
npm install
3. 核心配置 (注入灵魂)

这是最重要的一步，必须配置 API Key 婉晴才能“活”过来。

a. 找到配置文件：
打开 backend/ai_assistant/utils/config.py。

b. 填写你的 API 密钥：


# 找到以下变量并替换为你自己的 Key
DEEPSEEK_API_KEY = '你的密钥'
QWEN_API_KEY = '你的密钥'
OSS_ACCESS_KEY_ID = '你的OSS ID'
OSS_ACCESS_KEY_SECRET = '你的OSS Secret'
OSS_BUCKET = '你的Bucket名'
OSS_ENDPOINT = 'oss-cn-beijing.aliyuncs.com'

c. (可选) 调整婉晴的脾气：
在同一个 config.py 文件中，你可以修改以下参数：

ANALYSIS_INTERVAL_SECONDS = 15 : 婉晴每隔 15 秒观察你一次。

AROUSAL_THRESHOLD_HIGH = 7.5 : 压力值超过 7.5 时，婉晴会触发 CBT 专业干预。

4. 运行项目 (开火做饭！)

你需要同时运行后端和前端。

第一步：启动后端 (启动大脑)

在 backend 终端运行：

python main.py

当看到 Uvicorn running on http://0.0.0.0:8000 时，说明大脑已联机。

第二步：启动前端 (打开脸面)

在 frontend 终端运行：

npm run dev

点击终端显示的链接 http://localhost:5173。

💡 给队员的小贴士 (FAQ)

进网页后没声音？

浏览器为了不吵到你，默认静音。请在进入网页后随便点一下页面，婉晴才能开口说话。

摄像头黑屏？

检查摄像头是否被其他软件（微信、会议软件）占用了。

运行 python main.py 报找不到包？

检查你是否激活了虚拟环境（命令行前有没有 (venv) 字样）。

修改了代码怎么生效？

后端修改后需要 Ctrl + C 停止并重启；前端修改后会自动刷新网页。

📜 版权声明

本项目归阳溢涛及其小组所有，仅限内部学术交流。严谨未授权的商业扩散。
