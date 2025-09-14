import tkinter as tk
from tkinter import font
import time
import threading
from datetime import datetime, timedelta

class HourlyNotifier:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("整点报时")
        
        # 设置窗口属性
        self.root.overrideredirect(True)  # 无边框
        self.root.attributes("-topmost", True)  # 始终在最前
        self.root.attributes("-alpha", 0.9)  # 透明度
        self.root.configure(bg='black')
        
        # 设置字体
        self.custom_font = font.Font(family="Arial", size=24, weight="bold")
        
        # 创建标签
        self.label = tk.Label(
            self.root, 
            text="", 
            font=self.custom_font, 
            fg="white", 
            bg="black",
            padx=20,
            pady=10
        )
        self.label.pack()
        
        # 初始隐藏窗口
        self.root.withdraw()
        
        # 设置窗口位置
        self.set_window_position()
        
        # 启动时间检查线程
        self.check_time_thread()
        
    def set_window_position(self):
        # 更新窗口以确保获取正确的尺寸
        self.root.update_idletasks()
        
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 获取窗口尺寸
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # 设置位置（右下角，距离边缘50像素）
        x = screen_width - window_width - 100
        y = screen_height - window_height - 50  # 与任务栏保持距离
        
        self.root.geometry(f"+{x}+{y}")
    
    def show_notification_o(self, current_time):
        # 更新标签文本
        self.label.config(text=f"{current_time:02d}:00")
        
        # 显示窗口
        self.root.deiconify()
        
        # 10秒后隐藏窗口
        self.root.after(10000, self.root.withdraw)

    def show_notification_h(self, current_time):
        # 更新标签文本
        self.label.config(text=f"{current_time:02d}:30")
        
        # 显示窗口
        self.root.deiconify()
        
        # 10秒后隐藏窗口
        self.root.after(10000, self.root.withdraw)

    def check_time(self):
        while True:
            now = datetime.now()
            # 如果是整点且分钟和秒都为0（考虑到可能的延迟，可以稍微放宽条件）
            if now.minute == 0 and now.second < 2:
                self.show_notification_o(now.hour)
                time.sleep(10)
            if now.minute == 30 and now.second < 2:
                self.show_notification_h(now.hour)
                # 显示后等待一段时间再继续检查，避免重复触发
                time.sleep(10)
            time.sleep(1)  # 每秒检查一次
    
    def check_time_thread(self):
        # 在单独线程中运行时间检查
        thread = threading.Thread(target=self.check_time, daemon=True)
        thread.start()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = HourlyNotifier()
    app.run()
