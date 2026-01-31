# ai_assistant/utils/hotkey_manager.py (新建)

import keyboard
import threading
import time

class HotkeyManager:
    """
    一个在后台独立线程中运行的全局热键管理器。
    """
    def __init__(self, hotkey: str, callback):
        """
        初始化热键管理器。
        Args:
            hotkey (str): 要监听的热键组合, 例如 "ctrl+shift+s"。
            callback: 按下热键时要调用的函数。
        """
        self.hotkey = hotkey
        self.callback = callback
        self.running = False
        self.listener_thread = None

    def start_listener(self):
        """启动后台监听线程。"""
        if self.running:
            return
        
        print(f"热键管理器已启动，正在监听: {self.hotkey}")
        self.running = True
        
        # 注册热键和回调函数
        try:
            keyboard.add_hotkey(self.hotkey, self.callback)
        except Exception as e:
            print(f"错误: 注册热键 '{self.hotkey}' 失败。可能需要管理员权限运行程序。错误: {e}")
            self.running = False
            return
            
        # 启动一个守护线程，它的唯一目的就是保持程序运行，以便keyboard库能持续监听
        self.listener_thread = threading.Thread(target=self._keep_alive_loop)
        self.listener_thread.daemon = True
        self.listener_thread.start()

    def _keep_alive_loop(self):
        """一个简单的循环，以确保监听线程不会立即退出。"""
        while self.running:
            time.sleep(1) # 每秒检查一次状态

    def stop_listener(self):
        """停止监听并清理资源。"""
        if not self.running:
            return
        
        print("正在停止热键管理器...")
        self.running = False
        keyboard.remove_all_hotkeys() # 清理所有已注册的热键
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=1.0)
        print("热键管理器已停止。")