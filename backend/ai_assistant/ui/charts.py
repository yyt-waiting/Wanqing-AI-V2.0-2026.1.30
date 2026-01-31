# # ai_assistant/ui/charts.py

# import customtkinter as ctk
# from matplotlib.figure import Figure
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# import matplotlib.dates as mdates
# from datetime import datetime
# import threading
# import time
# import numpy as np
# from ai_assistant.utils import config

# class BehaviorVisualizer:
#     """
#     [Phase 2.5 可视化升级] 多模态数据看板。
#     Layout:
#     [ 行为时间轴 (Line) ]  [                 ]
#     [ ----------------- ]  [ 情感雷达 (Radar) ]
#     [ 情绪时间轴 (Line) ]  [                 ]
#     """
    
#     def __init__(self, parent_frame):
#         self.parent_frame = parent_frame
        
#         # --- 映射定义 ---
#         # 行为映射 (Y轴 1-7)
#         self.behavior_map = {
#             "1": "专注", "2": "进食", "3": "喝水", "4": "饮料",
#             "5": "手机", "6": "睡觉", "7": "其他", "0": "未知"
#         }
#         # 情绪映射 (Y轴 1-8, 对应 Plutchik 维度)
#         self.emotion_labels = config.PLUTCHIK_EMOTIONS # ["喜悦", "信任", ...]
#         self.emotion_map_y = {label: i+1 for i, label in enumerate(self.emotion_labels)}
        
#         # --- 数据存储 ---
#         self.behavior_history = [] # [(time, y_val)]
#         self.emotion_history = []  # [(time, y_val)]
#         self.current_emotion_vector = config.DEFAULT_EMOTION_VECTOR.copy()
        
#         self.data_lock = threading.Lock()
        
#         self._setup_charts_ui()
        
#         self.running = True
#         self.update_thread = threading.Thread(target=self._update_charts_loop)
#         self.update_thread.daemon = True
#         self.update_thread.start()

#     def _setup_charts_ui(self):
#         """创建 3 个图表的布局"""
#         # 使用 Grid 布局分割左右
#         charts_frame = ctk.CTkFrame(self.parent_frame, fg_color="transparent")
#         charts_frame.pack(fill="both", expand=True)
#         charts_frame.grid_columnconfigure(0, weight=3) # 左侧 (折线图)
#         charts_frame.grid_columnconfigure(1, weight=2) # 右侧 (雷达图)
#         charts_frame.grid_rowconfigure(0, weight=1) # 左上
#         charts_frame.grid_rowconfigure(1, weight=1) # 左下

#         # --- 1. 左上：行为折线图 ---
#         self.fig_beh = Figure(figsize=(6, 2.5), dpi=100) # 高度减小
#         self.fig_beh.patch.set_facecolor('#242424')
#         self.ax_beh = self.fig_beh.add_subplot(111, facecolor='#242424')
#         self.canvas_beh = FigureCanvasTkAgg(self.fig_beh, master=charts_frame)
#         self.canvas_beh.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=(0, 5))

#         # --- 2. 左下：情绪折线图 ---
#         self.fig_emo = Figure(figsize=(6, 2.5), dpi=100)
#         self.fig_emo.patch.set_facecolor('#242424')
#         self.ax_emo = self.fig_emo.add_subplot(111, facecolor='#242424')
#         self.canvas_emo = FigureCanvasTkAgg(self.fig_emo, master=charts_frame)
#         self.canvas_emo.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=(0, 5), pady=(5, 0))

#         # --- 3. 右侧：雷达图 (跨两行) ---
#         self.fig_radar = Figure(figsize=(4, 5), dpi=100)
#         self.fig_radar.patch.set_facecolor('#242424')
#         self.ax_radar = self.fig_radar.add_subplot(111, polar=True, facecolor='#242424')
#         self.canvas_radar = FigureCanvasTkAgg(self.fig_radar, master=charts_frame)
#         self.canvas_radar.get_tk_widget().grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(5, 0), pady=0)
        
#         self._redraw_charts()

#     def add_behavior_data(self, timestamp: datetime, behavior_num: str):
#         """添加行为数据"""
#         with self.data_lock:
#             # 简单清洗数据
#             if behavior_num not in self.behavior_map: behavior_num = "0"
#             y_val = int(behavior_num)
            
#             self.behavior_history.append((timestamp, y_val))
#             if len(self.behavior_history) > 50: self.behavior_history.pop(0)

#     def update_emotion_data(self, emotion_vector: dict):
#         """添加情绪数据 (同时更新雷达图和情绪历史)"""
#         if not emotion_vector: return
        
#         with self.data_lock:
#             self.current_emotion_vector = emotion_vector
            
#             # 找出当前的主导情绪，用于画折线图
#             dominant_emotion = max(emotion_vector, key=emotion_vector.get)
#             y_val = self.emotion_map_y.get(dominant_emotion, 0)
            
#             self.emotion_history.append((datetime.now(), y_val))
#             if len(self.emotion_history) > 50: self.emotion_history.pop(0)

#     def _update_charts_loop(self):
#         while self.running:
#             time.sleep(1.0)
#             try:
#                 if self.parent_frame.winfo_exists():
#                     self.parent_frame.after(0, self._redraw_charts)
#                 else:
#                     break
#             except:
#                 break

#     def _redraw_charts(self):
#         with self.data_lock:
#             self._plot_timeline(self.ax_beh, self.fig_beh, self.canvas_beh, 
#                               self.behavior_history, self.behavior_map, "行为流", '#4CAF50')
            
#             # 构建反向映射用于Y轴标签: {1: "喜悦", 2: "信任"...}
#             emo_y_map = {v: k for k, v in self.emotion_map_y.items()}
#             self._plot_timeline(self.ax_emo, self.fig_emo, self.canvas_emo,
#                               self.emotion_history, emo_y_map, "情绪流", '#2196F3')
            
#             self._plot_radar(self.current_emotion_vector)

#     def _plot_timeline(self, ax, fig, canvas, history, y_map, title, color):
#         """
#         [修复版] 通用的折线图绘制函数。
#         修复了 KeyError: 0 问题，兼容 int 和 str 类型的字典键。
#         """
#         ax.clear()
#         ax.set_title(title, color='white', fontsize=9, pad=2)
        
#         # 样式设置
#         ax.tick_params(axis='x', colors='gray', labelsize=7)
#         ax.tick_params(axis='y', colors='white', labelsize=7)
#         for spine in ax.spines.values(): spine.set_edgecolor('#444444')
#         ax.grid(True, linestyle='--', alpha=0.1, color='gray')

#         # Y轴标签设置 (修复核心逻辑)
#         if y_map:
#             # 1. 获取所有有效的 Y 值 (转换为 int 进行排序，确保轴是从下到上)
#             # 过滤掉非数字的键
#             y_vals = sorted([int(k) for k in y_map.keys() if str(k).isdigit()])
            
#             if y_vals:
#                 ax.set_yticks(y_vals)
                
#                 # 2. 安全地获取标签 (关键修复)
#                 labels_list = []
#                 for k in y_vals:
#                     # 尝试直接用 int 获取 (针对 emotion_map)
#                     # 如果失败，尝试转 str 获取 (针对 behavior_map)
#                     # 如果都失败，直接显示数字 k
#                     label = y_map.get(k, y_map.get(str(k), str(k)))
#                     labels_list.append(label)
                
#                 ax.set_yticklabels(labels_list)
                
#                 # 设置 Y 轴范围，稍微留点余地让点不要压线
#                 ax.set_ylim(min(y_vals)-0.5, max(y_vals)+0.5)

#         # 绘图逻辑
#         if history:
#             times, values = zip(*history)
#             ax.plot(times, values, color=color, linewidth=1.5, marker='.', markersize=4)
#             ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
#             # 只显示最近的几个时间标签，防止重叠
#             ax.xaxis.set_major_locator(mdates.SecondLocator(interval=30)) 
#             fig.autofmt_xdate(rotation=0, ha='center')

#         fig.tight_layout()
#         canvas.draw()



#     def _plot_radar(self, vector):
#         """绘制雷达图"""
#         self.ax_radar.clear()
        
#         labels = config.PLUTCHIK_EMOTIONS
#         values = [vector.get(l, 0) for l in labels]
        
#         # 闭环
#         values += values[:1]
#         angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
#         angles += angles[:1]
        
#         # 绘图
#         self.ax_radar.set_facecolor('#242424')
#         self.ax_radar.grid(color='#444444')
        
#         # 动态颜色：根据总能量改变颜色 (Arousal越高越红)
#         arousal = max(values)
#         line_color = '#FF5722' if arousal > 7 else '#00BCD4'
        
#         self.ax_radar.plot(angles, values, color=line_color, linewidth=2)
#         self.ax_radar.fill(angles, values, color=line_color, alpha=0.3)
        
#         self.ax_radar.set_yticklabels([])
#         self.ax_radar.set_xticks(angles[:-1])
#         self.ax_radar.set_xticklabels(labels, color='white', fontsize=8)
#         self.ax_radar.set_ylim(0, 10)
#         self.ax_radar.set_title("实时情感态势", color='white', y=1.08, fontsize=10)
        
#         self.canvas_radar.draw()

#     def stop(self):
#         self.running = False
#         if self.update_thread.is_alive():
#             self.update_thread.join(timeout=1.0)