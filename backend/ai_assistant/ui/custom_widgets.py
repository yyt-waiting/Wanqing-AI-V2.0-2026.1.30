# # ai_assistant/ui/custom_widgets.py (新建)

# import customtkinter as ctk
# from PIL import Image, ImageEnhance

# class TransparentFrame(ctk.CTkFrame):
#     """
#     一个自定义的Frame控件，能够通过截取和处理父窗口的背景来实现伪透明效果。
#     """
#     def __init__(self, *args, transparency: float = 0.85, **kwargs):
#         super().__init__(*args, **kwargs)
        
#         # 将自身的背景设置为完全透明，这样底下的背景标签才能显示出来
#         self.configure(fg_color="transparent") 
        
#         self.transparency = transparency
#         self._background_label = ctk.CTkLabel(self, text="", image=None)
#         self._background_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        
#         # 提升子控件的层级，确保它们显示在背景标签之上
#         self._background_label.lower()

#     def update_background(self, root_bg_image: Image.Image):
#         """
#         根据父窗口的背景图和自身的位置，更新自己的背景。
#         """
#         if not self.winfo_exists() or self.winfo_width() <= 1 or self.winfo_height() <= 1:
#             return

#         # 获取控件相对于主窗口的绝对位置
#         abs_x = self.winfo_rootx() - self.winfo_toplevel().winfo_rootx()
#         abs_y = self.winfo_rooty() - self.winfo_toplevel().winfo_rooty()
        
#         # 从主背景图中裁剪出对应位置的区域
#         box = (abs_x, abs_y, abs_x + self.winfo_width(), abs_y + self.winfo_height())
#         cropped_image = root_bg_image.crop(box)

#         # 应用 "深色玻璃" 效果
#         # 通过降低亮度来实现，transparency 值越小，效果越暗
#         enhancer = ImageEnhance.Brightness(cropped_image)
#         darkened_image = enhancer.enhance(self.transparency)

#         # 创建CTkImage并应用到背景标签上
#         ctk_image = ctk.CTkImage(light_image=darkened_image, dark_image=darkened_image,
#                                  size=(self.winfo_width(), self.winfo_height()))
        
#         self._background_label.configure(image=ctk_image)
#         self._background_label.image = ctk_image # 保持引用