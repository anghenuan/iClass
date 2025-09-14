import sys
import json
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QMenu, QAction, QColorDialog, QHBoxLayout)
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QFont, QColor, QMouseEvent

class TimetableWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # 初始化变量
        self.drag_position = QPoint()
        self.font_color = QColor(255, 255, 255)  # 默认白色字体
        self.bg_alpha = 180  # 默认背景透明度
        
        # 设置窗口属性
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置初始位置和大小
        self.setGeometry(0, 0, 300, 500)
        
        # 创建UI
        self.init_ui()
        
        # 加载课程表数据
        self.load_timetable()
        
        # 更新显示
        self.update_display()
        
        # 设置定时器，每天更新
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_display)
        self.timer.start(60000)  # 每分钟检查一次
        
    def init_ui(self):
        # 主布局
        layout = QVBoxLayout()
        
        # 标题栏
        self.title_bar = QLabel("课程表")
        self.title_bar.setAlignment(Qt.AlignCenter)
        self.title_bar.setStyleSheet("background-color: rgba(60, 60, 60, 180); color: white; border-radius: 5px;")
        self.title_bar.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        self.title_bar.mousePressEvent = self.title_press
        self.title_bar.mouseMoveEvent = self.title_move
        
        # 内容区域
        self.content = QLabel()
        self.content.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.content.setStyleSheet("background-color: rgba(40, 40, 40, 180); color: white; padding: 10px; border-radius: 5px;")
        self.content.setFont(QFont("Microsoft YaHei", 9))
        self.content.setWordWrap(True)
        
        # 添加到布局
        layout.addWidget(self.title_bar)
        layout.addWidget(self.content)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.setLayout(layout)
        
    def title_press(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPos())
            
    def title_move(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
            
    def show_context_menu(self, pos):
        menu = QMenu(self)
        
        color_action = QAction("字体颜色", self)
        color_action.triggered.connect(self.change_font_color)
        menu.addAction(color_action)
        
        alpha_action = QAction("透明度", self)
        alpha_action.triggered.connect(self.change_background_alpha)
        menu.addAction(alpha_action)
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close_application)
        menu.addAction(exit_action)
        
        menu.exec_(pos)
        
    def change_font_color(self):
        color = QColorDialog.getColor(self.font_color, self, "选择字体颜色")
        if color.isValid():
            self.font_color = color
            self.update_display()
            
    def change_background_alpha(self):
        # 简化实现：在160-220之间循环切换
        self.bg_alpha = 160 if self.bg_alpha >= 220 else self.bg_alpha + 20
        self.update_style()
        
    def close_application(self):
        self.close()
        
    def load_timetable(self):
        try:
            with open('timetable.json', 'r', encoding='utf-8') as f:
                self.timetable_data = json.load(f)
        except FileNotFoundError:
            # 创建示例数据文件
            sample_data = [
                {
                    "day": "Monday",
                    "class": ["语文", "数学", "地理", "体育", "英语", "英语", "午休", "物理", "语文", "班团", "校本课程", "晚饭", "数学"]
                },
                {
                    "day": "Tuesday",
                    "class": ["英语", "语文", "语文", "道法", "数学", "数学", "午休", "英语", "体育", "物理", "英语", "晚饭", "英语"]
                },
                {
                    "day": "Wednesday",
                    "class": ["语文", "音乐", "体育", "生物", "数学", "语文", "午休", "数学", "英语", "历史", "语文", "晚饭", "语文/物理"]
                },
                {
                    "day": "Thursday",
                    "class": ["英语", "英语", "地理", "物理", "历史", "数学", "午休", "生物", "语文", "体育", "数学", "晚饭", "语文/物理"]
                },
                {
                    "day": "Friday",
                    "class": ["语文", "语文", "生物/地理", "英语", "美术", "物理", "午休", "体育", "道法", "信息科技", "数学/心理/物理", "无", "无"]
                },
                {
                    "day": "Saturday",
                    "class": ["周末休息", "", "", "", "", "", "", "", "", "", "", "", ""]
                },
                {
                    "day": "Sunday",
                    "class": ["周末休息", "", "", "", "", "", "", "", "", "", "", "", ""]
                }
            ]
            
            with open('timetable.json', 'w', encoding='utf-8') as f:
                json.dump(sample_data, f, ensure_ascii=False, indent=2)
                
            self.timetable_data = sample_data
            
    def update_display(self):
        # 获取当前星期几
        today = datetime.now().strftime("%A")
        
        # 中文星期映射
        week_map = {
            "Monday": "Monday",
            "Tuesday": "Tuesday",
            "Wednesday": "Wednesday",
            "Thursday": "Thursday",
            "Friday": "Friday",
            "Saturday": "Saturday",
            "Sunday": "Sunday"
        }
        
        # 查找今天的课程
        today_classes = None
        for day_data in self.timetable_data:
            if day_data["day"] == week_map[today]:
                today_classes = day_data["class"]
                break
                
        if today_classes is None:
            self.content.setText("今天没有课程安排")
            return
            
        # 构建显示文本
        class_times = ["早读", "第一节", "第二节", "第三节", "第四节", "第五节", 
                      "午休", "第六节", "第七节", "第八节", "课后分层", "晚饭", "晚自习"]

        if today == "Monday":
            today_new = "周一"
        if today == "Tuesday":
            today_new = "周二"
        if today == "Wednesday":
            today_new = "周三"
        if today == "Thursday":
            today_new = "周四"
        if today == "Friday":
            today_new = "周五"
        if today == "Saturday":
            today_new = "周六"
        if today == "Sunday":
            today_new = "周日"
        display_text = f"<h3>{today_new} 课程表</h3><hr>"
        for i, (time, class_name) in enumerate(zip(class_times, today_classes)):
            if class_name.strip():  # 只显示有课程的时段
                display_text += f"<b>{time}:</b> {class_name}<br>"
        
        self.content.setText(display_text)
        self.update_style()
        
    def update_style(self):
        # 更新样式表
        color_str = f"rgba({self.font_color.red()}, {self.font_color.green()}, {self.font_color.blue()}, 255)"
        bg_color = f"rgba(40, 40, 40, {self.bg_alpha})"
        
        self.content.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {color_str};
                padding: 10px;
                border-radius: 5px;
            }}
        """)
        
    def adjust_position(self):
        # 调整到右上角
        screen_geo = QApplication.desktop().availableGeometry()
        widget_geo = self.frameGeometry()
        x = screen_geo.width() - widget_geo.width() - 20
        y = 20
        self.move(x, y)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    widget = TimetableWidget()
    widget.show()
    widget.adjust_position()
    
    sys.exit(app.exec_())
