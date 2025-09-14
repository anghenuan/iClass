import pygame
import sys
import time
import argparse
import os

# 初始化 Pygame
pygame.init()

# 解析命令行参数
parser = argparse.ArgumentParser(description='倒计时程序')
parser.add_argument('-m', '--minutes', type=int, default=0, help='设置分钟数')
parser.add_argument('-s', '--seconds', type=int, default=0, help='设置秒数')
args = parser.parse_args()

# 计算总秒数
total_seconds = args.minutes * 60 + args.seconds
if total_seconds <= 0:
    print("错误：请设置有效的倒计时时间（使用 -m 和 -s 参数）")
    sys.exit(1)

# 计算警告阈值（总时长的五分之一）
warning_threshold = total_seconds // 5

# 获取屏幕尺寸
screen_info = pygame.display.Info()
screen_width, screen_height = screen_info.current_w, screen_info.current_h

# 初始窗口设置
window_width, window_height = 300, 150
window_x = screen_width - window_width - 20
window_y = 20

# 创建窗口
screen = pygame.display.set_mode((window_width, window_height), pygame.NOFRAME)
pygame.display.set_caption("倒计时程序")

# 设置窗口位置
os.environ['SDL_VIDEO_WINDOW_POS'] = f"{window_x},{window_y}"

# 尝试设置窗口置顶（可能不适用于所有系统）
try:
    import ctypes
    hwnd = pygame.display.get_wm_info()["window"]
    ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)
except:
    print("警告：无法设置窗口置顶，此功能可能不支持当前系统")

# 字体设置
font_large = pygame.font.SysFont('Arial', 60)
font_small = pygame.font.SysFont('Arial', 30)

# 颜色定义
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

# 加载铃声
try:
    pygame.mixer.music.load("bell.mp3")
except:
    print("警告：无法加载 bell.mp3 文件")

# 倒计时状态
start_time = time.time()
is_fullscreen = False
is_finished = False

# 主循环
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and is_finished:  # 鼠标点击
                running = False
    
    # 计算剩余时间
    elapsed_time = time.time() - start_time
    remaining_time = max(0, total_seconds - elapsed_time)
    
    # 检查是否需要切换到全屏
    if not is_fullscreen and remaining_time <= warning_threshold:
        screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
        is_fullscreen = True
    
    # 检查是否倒计时结束
    if remaining_time <= 0 and not is_finished:
        is_finished = True
        try:
            pygame.mixer.music.play()
        except:
            pass
    
    # 清空屏幕
    screen.fill(BLACK)
    
    # 格式化时间显示
    minutes = int(remaining_time) // 60
    seconds = int(remaining_time) % 60
    time_str = f"{minutes:02d}:{seconds:02d}"
    
    # 选择颜色
    color = RED if is_fullscreen else WHITE
    
    if is_finished:
        # 显示结束信息
        text = font_small.render("Time Is Over!", True, color)
        text_rect = text.get_rect(center=(screen.get_width()//2, screen.get_height()//2))
        screen.blit(text, text_rect)
        
        # 显示退出提示
        if is_fullscreen:
            hint = font_small.render("Keydown left mouse button to exit.", True, color)
            hint_rect = hint.get_rect(center=(screen.get_width()//2, screen.get_height()//2 + 50))
            screen.blit(hint, hint_rect)
    else:
        # 显示倒计时
        text = font_large.render(time_str, True, color)
        text_rect = text.get_rect(center=(screen.get_width()//2, screen.get_height()//2))
        screen.blit(text, text_rect)
    
    # 更新显示
    pygame.display.flip()
    
    # 控制帧率
    pygame.time.delay(50)

# 退出程序
pygame.quit()
sys.exit()
