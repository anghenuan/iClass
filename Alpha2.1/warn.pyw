import datetime
import ctypes

#获取时间
now = datetime.datetime.now()
current_time = now.time()

def log_message(message):
    """将消息追加到日志文件"""
    with open("warn.log", "a", encoding="utf-8") as log_file:
        log_file.write(f"[{now}]:{message}\n")

def check_time_period():
    """检查当前时间是否在关机时段内"""
    
    # 定义关机时段
    evening_start = datetime.time(21, 20)  # 21:20
    morning_end = datetime.time(7, 30)     # 07:30
    noon_start = datetime.time(12, 35)     # 12:35
    noon_end = datetime.time(13, 50)       # 13:50
    
    # 检查是否在关机时段内
    if current_time >= evening_start or current_time <= morning_end:
        return True
    if current_time >= noon_start and current_time <= noon_end:
        return True
    return False

def show_warning():
        #定义提示
    message = "当日21:20至次日07:30及12:35至13:50为关机时段，在本时间内打开电脑将会在开机后10秒内关机。"
    
    """显示警告"""

    # 使用Windows的消息框显示警告
    try:
        ctypes.windll.user32.MessageBoxW(0, message + "\n\n系统将在10秒后关机。", "关机警告", 0x30)
    except:
        pass
   
def main():
    
    # 检查是否在关机时段内
    if check_time_period():
        log_message("检测到在关机时段内开机，即将显示警告")

        #使用一般模式启动
        show_warning()
    else:
        log_message("当前不在关机时段内，程序退出")

if __name__ == "__main__":
    main()
