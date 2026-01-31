
# import customtkinter as ctk
# from PIL import Image
# import os
# from ai_assistant.ui.custom_widgets import TransparentFrame

# def setup_main_ui(app):
#     """
#     配置主窗口UI布局 (V7版)
#     """
#     # ... (背景图片设置部分保持不变) ...
#     try:
#         script_dir = os.path.dirname(os.path.abspath(__file__))
#         assets_path = os.path.join(script_dir, '..', 'assets')
#         bg_path = os.path.join(assets_path, 'background.png')
#         app.original_bg_pil_image = Image.open(bg_path)
#         app.background_label = ctk.CTkLabel(app, text="")
#         app.background_label.place(relx=0, rely=0, relwidth=1, relheight=1)
#     except Exception as e:
#         print(f"警告: 加载背景图片失败: {e}")

#     app.grid_columnconfigure(0, weight=1)
#     app.grid_rowconfigure(0, weight=1)
#     main_frame = ctk.CTkFrame(app, fg_color="transparent")
#     main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
#     main_frame.grid_columnconfigure(0, weight=1)
#     main_frame.grid_columnconfigure(1, weight=3)
#     main_frame.grid_rowconfigure(0, weight=1)

#     # --- 1. 左侧立绘区域 (已修正) ---
#     app.portrait_frame = TransparentFrame(main_frame, corner_radius=10, transparency=0.7)
#     app.portrait_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=0)
    
#     # 配置 portrait_frame 内部的 grid, 让其子控件可以填充
#     app.portrait_frame.grid_columnconfigure(0, weight=1)
#     app.portrait_frame.grid_rowconfigure(0, weight=1)
#     # 创建真正用于显示立绘的 Label 控件
#     app.portrait_label = ctk.CTkLabel(app.portrait_frame, text="", fg_color="transparent")
#     app.portrait_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)


#     # --- 2. 右侧交互区域 (保持 V6 的稳定 pack 布局) ---
#     right_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
#     right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)
    
#     # 2.1 校徽 (放在最上面)
#     emblem_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
#     emblem_frame.pack(side="top", fill="x", pady=(0, 5))
#     try:
#         # ... (校徽加载代码不变) ...
#         script_dir = os.path.dirname(os.path.abspath(__file__))
#         assets_path = os.path.join(script_dir, '..', 'assets')
#         emblem_path = os.path.join(assets_path, 'school_emblem.png')
#         emblem_original_image = Image.open(emblem_path)
#         original_width, original_height = emblem_original_image.size
#         target_height = 50
#         aspect_ratio = original_width / original_height
#         target_width = int(target_height * aspect_ratio)
#         app.school_emblem_img = ctk.CTkImage(light_image=emblem_original_image, dark_image=emblem_original_image, size=(target_width, target_height))
#         emblem_label = ctk.CTkLabel(emblem_frame, image=app.school_emblem_img, text="")
#         emblem_label.pack(side="right", padx=10)
#     except Exception as e:
#         print(f"警告: 加载校徽失败: {e}")

#     # 2.4 状态栏 (放在最下面)
#     app.status_frame = TransparentFrame(right_frame, corner_radius=0, transparency=0.8)
#     app.status_frame.pack(side="bottom", fill="x", pady=(5, 0))
#     app.status_label = ctk.CTkLabel(app.status_frame, text="正在初始化...", anchor="w", fg_color="transparent")
#     app.status_label.pack(side="left", padx=10, pady=5)

#     # 2.3 聊天输入区 (放在状态栏的上面)
#     chat_input_frame = TransparentFrame(right_frame, corner_radius=10, transparency=0.8)
#     chat_input_frame.pack(side="bottom", fill="x", pady=(5, 0))
#     chat_input_frame.grid_columnconfigure(0, weight=1)
#     app.chat_entry = ctk.CTkEntry(chat_input_frame, placeholder_text="在这里输入你想说的话...", height=40)
#     app.chat_entry.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
#     app.send_button = ctk.CTkButton(chat_input_frame, text="发送", width=80, height=40, command=app._on_send_text_message)
#     app.send_button.grid(row=0, column=1, sticky="e", padx=(0, 10), pady=10)
#     app.chat_entry.bind("<Return>", lambda event: app.send_button.invoke())

#     # 2.2 对话记录区 (最后填充所有剩余空间)
#     app.chat_frame = ctk.CTkScrollableFrame(right_frame, label_text="对话记录", fg_color="transparent")
#     app.chat_frame_background = TransparentFrame(app.chat_frame, corner_radius=10, transparency=0.85)
#     app.chat_frame_background.place(relx=0, rely=0, relwidth=1, relheight=1)
#     app.chat_frame.pack(side="top", fill="both", expand=True)

#     # 加载头像
#     try:
#         script_dir = os.path.dirname(os.path.abspath(__file__))
#         assets_path = os.path.join(script_dir, '..', 'assets')
#         ai_avatar_path = os.path.join(assets_path, 'ai_avatar.png')
#         user_avatar_path = os.path.join(assets_path, 'user_avatar.png')
        
#         if not os.path.exists(ai_avatar_path) or not os.path.exists(user_avatar_path):
#             raise FileNotFoundError("头像文件未在 assets 目录中找到。")
            
#         app.ai_avatar = ctk.CTkImage(Image.open(ai_avatar_path), size=(40, 40))
#         app.user_avatar = ctk.CTkImage(Image.open(user_avatar_path), size=(40, 40))
#         print("头像文件加载成功。")

#     except Exception as e:
#         print(f"警告: 加载头像文件失败: {e}。将不显示头像。")
#         # 即使失败，也要创建变量并设为None，防止程序崩溃
#         app.ai_avatar = None
#         app.user_avatar = None




#     app.chat_row_counter = 0

#     app.transparent_widgets = [
#         app.portrait_frame,
#         app.chat_frame_background,
#         chat_input_frame,
#         app.status_frame
#     ]