"""
基于Chromium的开源浏览器 - 修复主页链接跳转
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtGui import *
from new_tab import NewTabPage
from script_injector import ScriptInjector

# 设置高DPI支持（必须在QApplication创建之前）
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

class BrowserBridge(QObject):
    """JavaScript与Python通信的桥梁"""
    
    # 定义信号
    navigateRequested = pyqtSignal(str)
    
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
    
    @pyqtSlot(str)
    def navigate(self, url):
        """从JavaScript调用导航"""
        print(f"JavaScript请求导航到: {url}")
        self.navigateRequested.emit(url)

class Browser(QMainWindow):
    """主浏览器窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rick浏览器")
        self.setGeometry(100, 100, 1400, 900)
        
        # 设置应用图标
        self.setWindowIcon(QIcon(self.get_icon_path("browser.png")))
        
        # 创建脚本注入器
        self.script_injector = ScriptInjector()
        
        # 存储新标签页的引用
        self.new_tab_pages = {}
        
        # 创建浏览器桥梁
        self.browser_bridge = BrowserBridge(self)
        self.browser_bridge.navigateRequested.connect(self.handle_navigation_request)
        
        # 初始化UI
        self.init_ui()
        
        # 应用主题
        self.apply_theme("light")
        
        # 打开主页
        self.open_home_page()
        
    def init_ui(self):
        """初始化用户界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建垂直布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建导航栏
        nav_bar = self.create_navigation_bar()
        main_layout.addWidget(nav_bar)
        
        # 创建标签页部件
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.tab_changed)
        main_layout.addWidget(self.tabs)
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 添加快捷键
        self.setup_shortcuts()
        
    def create_navigation_bar(self):
        """创建导航工具栏"""
        nav_bar = QToolBar()
        nav_bar.setMovable(False)
        
        # 后退按钮
        self.back_btn = QAction(QIcon(self.get_icon_path("back.png")), "后退", self)
        self.back_btn.triggered.connect(self.navigate_back)
        nav_bar.addAction(self.back_btn)
        
        # 前进按钮
        self.forward_btn = QAction(QIcon(self.get_icon_path("forward.png")), "前进", self)
        self.forward_btn.triggered.connect(self.navigate_forward)
        nav_bar.addAction(self.forward_btn)
        
        # 刷新按钮
        self.refresh_btn = QAction(QIcon(self.get_icon_path("refresh.png")), "刷新", self)
        self.refresh_btn.triggered.connect(self.refresh_page)
        nav_bar.addAction(self.refresh_btn)
        
        # 主页按钮
        self.home_btn = QAction(QIcon(self.get_icon_path("home.png")), "主页", self)
        self.home_btn.triggered.connect(self.open_home_page)
        nav_bar.addAction(self.home_btn)
        
        nav_bar.addSeparator()
        
        # 地址栏
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_bar.addWidget(self.url_bar)
        
        # 搜索按钮
        self.search_btn = QAction(QIcon(self.get_icon_path("search.png")), "搜索", self)
        self.search_btn.triggered.connect(self.search_with_bing)
        nav_bar.addAction(self.search_btn)
        
        nav_bar.addSeparator()
        
        # 新标签页按钮
        self.new_tab_btn = QAction(QIcon(self.get_icon_path("add_tab.png")), "新标签页", self)
        self.new_tab_btn.triggered.connect(self.open_new_tab)
        nav_bar.addAction(self.new_tab_btn)
        
        # 菜单按钮
        self.menu_btn = QAction(QIcon(self.get_icon_path("menu.png")), "菜单", self)
        self.menu_btn.triggered.connect(self.show_menu)
        nav_bar.addAction(self.menu_btn)
        
        # 画中画按钮
        self.pip_btn = QAction(QIcon(self.get_icon_path("pip.png")), "画中画", self)
        self.pip_btn.triggered.connect(self.toggle_picture_in_picture)
        nav_bar.addAction(self.pip_btn)
        self.pip_btn.setVisible(False)
        
        return nav_bar
    
    def create_web_view(self, url=None):
        """创建网页视图，配置HTML5播放器支持"""
        web_view = QWebEngineView()
        
        # 获取页面对象
        page = web_view.page()
        
        # 启用HTML5功能
        settings = page.settings()
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.AllowWindowActivationFromJavaScript, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        
        # 设置用户代理
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # 设置缓存路径以避免权限问题
        cache_dir = os.path.join(tempfile.gettempdir(), "browser_cache")
        os.makedirs(cache_dir, exist_ok=True)
        profile.setCachePath(cache_dir)
        profile.setPersistentStoragePath(cache_dir)
        
        # 设置初始URL
        if url:
            web_view.setUrl(QUrl(url))
        
        # 连接信号
        web_view.urlChanged.connect(self.update_url_bar)
        web_view.loadStarted.connect(self.page_loading_started)
        web_view.loadFinished.connect(self.page_loading_finished)
        
        # 连接全屏信号
        page.fullScreenRequested.connect(self.handle_fullscreen_request)
        
        return web_view
    
    def add_tab(self, web_view=None, title="新标签页", url=None):
        """添加新标签页"""
        if not web_view:
            web_view = self.create_web_view(url)
        
        # 设置页面为标签页
        tab_index = self.tabs.addTab(web_view, title)
        self.tabs.setCurrentIndex(tab_index)
        
        # 如果是新标签页，设置特殊处理
        if title == "新标签页" and not url:
            self.setup_new_tab(web_view)
        
        return web_view
    
    def setup_new_tab(self, web_view):
        """设置新标签页"""
        # 生成新标签页HTML
        new_tab_page = NewTabPage()
        html_content = new_tab_page.generate_html()
        
        # 将HTML内容加载到web_view中
        web_view.setHtml(html_content, QUrl("data:text/html;charset=utf-8,"))
        
        # 为页面设置WebChannel
        self.setup_web_channel(web_view.page())
        
        # 为新标签页注入链接处理脚本
        self.inject_new_tab_script(web_view.page())
        
        # 记录这是新标签页
        self.new_tab_pages[id(web_view)] = True
        
        # 连接URL变化信号
        web_view.urlChanged.connect(lambda url, view=web_view: self.handle_new_tab_navigation(view, url))
    
    def setup_web_channel(self, page):
        """为页面设置WebChannel"""
        # 创建WebChannel
        channel = QWebChannel(page)
        
        # 注册JavaScript对象
        channel.registerObject("browser", self.browser_bridge)
        
        # 将WebChannel设置为页面的通信通道
        page.setWebChannel(channel)
    
    def inject_new_tab_script(self, page):
        """为新标签页注入JavaScript来处理链接点击"""
        script = """
        // 等待页面加载完成
        document.addEventListener('DOMContentLoaded', function() {
            console.log('新标签页加载完成，初始化链接处理器...');
            
            // 初始化WebChannel
            if (typeof QWebChannel !== 'undefined') {
                console.log('初始化WebChannel...');
                new QWebChannel(qt.webChannelTransport, function(channel) {
                    console.log('WebChannel连接成功');
                    window.browser = channel.objects.browser;
                    
                    // 现在可以安全地初始化链接处理器
                    initializeLinkHandlers();
                });
            } else {
                console.log('QWebChannel未定义，使用备用方案');
                // 备用方案：使用window.open
                initializeLinkHandlers();
            }
        });
        
        function initializeLinkHandlers() {
            console.log('初始化链接处理器...');
            
            // 处理所有链接点击
            document.addEventListener('click', function(e) {
                let target = e.target;
                
                // 查找最近的链接元素
                while (target && target.tagName !== 'A') {
                    target = target.parentElement;
                }
                
                if (target && target.tagName === 'A' && target.href) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const url = target.href;
                    console.log('点击链接:', url);
                    
                    // 使用WebChannel导航
                    if (window.browser && window.browser.navigate) {
                        console.log('使用WebChannel导航');
                        window.browser.navigate(url);
                    } else {
                        // 备用方案：使用window.open
                        console.log('使用window.open导航');
                        window.open(url, '_self');
                    }
                    return false;
                }
            }, true);
            
            // 处理搜索框
            const searchInput = document.getElementById('searchInput');
            const searchButton = document.getElementById('searchButton');
            
            if (searchInput && searchButton) {
                console.log('初始化搜索处理器...');
                
                // 搜索按钮点击
                searchButton.addEventListener('click', function() {
                    const query = searchInput.value.trim();
                    if (query) {
                        handleSearch(query);
                    }
                });
                
                // 搜索框回车
                searchInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        const query = searchInput.value.trim();
                        if (query) {
                            handleSearch(query);
                        }
                    }
                });
            }
            
            // 处理快速链接
            document.querySelectorAll('.quick-link').forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const url = this.getAttribute('data-url');
                    if (url) {
                        console.log('点击快速链接:', url);
                        
                        // 使用WebChannel导航
                        if (window.browser && window.browser.navigate) {
                            window.browser.navigate(url);
                        } else {
                            // 备用方案：使用window.open
                            window.open(url, '_self');
                        }
                    }
                });
            });
            
            function handleSearch(query) {
                console.log('处理搜索:', query);
                
                // 检查是否是URL
                let url;
                if (query.startsWith('http://') || query.startsWith('https://') || 
                    query.startsWith('file://') || (query.includes('.') && !query.includes(' '))) {
                    url = query;
                    if (!url.startsWith('http://') && !url.startsWith('https://') && !url.startsWith('file://')) {
                        url = 'https://' + url;
                    }
                } else {
                    // 使用Bing搜索
                    url = 'https://www.bing.com/search?q=' + encodeURIComponent(query);
                }
                
                console.log('导航到:', url);
                
                // 使用WebChannel导航
                if (window.browser && window.browser.navigate) {
                    window.browser.navigate(url);
                } else {
                    // 备用方案：使用window.open
                    window.open(url, '_self');
                }
            }
            
            console.log('链接处理器初始化完成');
        }
        """
        
        # 创建并注入脚本
        web_script = QWebEngineScript()
        web_script.setSourceCode(script)
        web_script.setInjectionPoint(QWebEngineScript.DocumentCreation)
        web_script.setWorldId(QWebEngineScript.MainWorld)
        web_script.setRunsOnSubFrames(True)
        page.scripts().insert(web_script)
    
    def handle_navigation_request(self, url):
        """处理JavaScript的导航请求"""
        print(f"处理导航请求: {url}")
        current_web_view = self.tabs.currentWidget()
        if current_web_view:
            # 检查是否是新标签页
            if id(current_web_view) in self.new_tab_pages:
                # 从新标签页中移除，因为现在要导航到实际网站
                del self.new_tab_pages[id(current_web_view)]
            
            # 更新标签页标题
            index = self.tabs.indexOf(current_web_view)
            if index >= 0:
                self.tabs.setTabText(index, "加载中...")
            
            # 导航到URL
            current_web_view.setUrl(QUrl(url))
    
    def handle_new_tab_navigation(self, web_view, url):
        """处理新标签页的导航"""
        # 如果是新标签页的内部导航，忽略
        url_str = url.toString()
        if url_str.startswith("data:text/html") or url_str in ["about:blank", ""]:
            return
        
        # 检查是否是新标签页
        if id(web_view) in self.new_tab_pages:
            # 从新标签页中移除，因为现在要导航到实际网站
            del self.new_tab_pages[id(web_view)]
            
            # 更新标签页标题
            index = self.tabs.indexOf(web_view)
            if index >= 0:
                self.tabs.setTabText(index, "加载中...")
    
    def inject_scripts_to_page(self, page):
        """注入脚本到页面"""
        try:
            self.script_injector.inject_to_page(page)
        except Exception as e:
            print(f"注入脚本时出错: {e}")
    
    def open_home_page(self):
        """打开主页（新标签页）"""
        self.open_new_tab()
    
    def open_new_tab(self):
        """打开新标签页"""
        self.add_tab(title="新标签页")
    
    def close_tab(self, index):
        """关闭标签页"""
        if self.tabs.count() > 1:
            web_view = self.tabs.widget(index)
            web_view_id = id(web_view)
            if web_view_id in self.new_tab_pages:
                del self.new_tab_pages[web_view_id]
            self.tabs.removeTab(index)
        else:
            self.close()
    
    def tab_changed(self, index):
        """标签页切换"""
        if index >= 0:
            web_view = self.tabs.widget(index)
            if web_view:
                self.update_url_bar(web_view.url())
                # 检查是否有视频
                self.check_for_video(web_view)
    
    def check_for_video(self, web_view):
        """检查页面是否有视频元素"""
        script = """
        var videos = document.getElementsByTagName('video');
        return videos.length > 0;
        """
        
        web_view.page().runJavaScript(script, self.handle_video_check_result)
    
    def handle_video_check_result(self, has_video):
        """处理视频检查结果"""
        self.pip_btn.setVisible(bool(has_video))
    
    def navigate_back(self):
        """后退"""
        current_web_view = self.tabs.currentWidget()
        if current_web_view:
            current_web_view.back()
    
    def navigate_forward(self):
        """前进"""
        current_web_view = self.tabs.currentWidget()
        if current_web_view:
            current_web_view.forward()
    
    def refresh_page(self):
        """刷新页面"""
        current_web_view = self.tabs.currentWidget()
        if current_web_view:
            current_web_view.reload()
    
    def navigate_to_url(self):
        """导航到地址栏中的URL"""
        url_text = self.url_bar.text()
        
        if not url_text:
            return
            
        # 如果不是以http/https开头，添加https://
        if not url_text.startswith(("http://", "https://", "file://")):
            url_text = "https://" + url_text
            
        current_web_view = self.tabs.currentWidget()
        if current_web_view:
            current_web_view.setUrl(QUrl(url_text))
    
    def search_with_bing(self):
        """使用Bing搜索"""
        search_text = self.url_bar.text()
        if search_text:
            # 如果是URL，直接导航
            if search_text.startswith(("http://", "https://", "file://")):
                self.navigate_to_url()
            else:
                # 使用Bing搜索
                search_url = f"https://www.bing.com/search?q={search_text}"
                current_web_view = self.tabs.currentWidget()
                if current_web_view:
                    current_web_view.setUrl(QUrl(search_url))
    
    def update_url_bar(self, url):
        """更新地址栏"""
        current_web_view = self.tabs.currentWidget()
        if current_web_view and current_web_view.url() == url:
            self.url_bar.setText(url.toString())
            
            # 更新标签页标题
            page_title = current_web_view.page().title()
            if page_title:
                index = self.tabs.currentIndex()
                self.tabs.setTabText(index, page_title[:20] + "..." if len(page_title) > 20 else page_title)
    
    def page_loading_started(self):
        """页面开始加载"""
        self.status_bar.showMessage("加载中...")
    
    def page_loading_finished(self, success):
        """页面加载完成"""
        if success:
            self.status_bar.showMessage("完成")
            
            # 注入脚本到当前页面（除了新标签页）
            current_web_view = self.tabs.currentWidget()
            if current_web_view and id(current_web_view) not in self.new_tab_pages:
                self.inject_scripts_to_page(current_web_view.page())
                
                # 检查是否有视频
                self.check_for_video(current_web_view)
        else:
            self.status_bar.showMessage("加载失败")
    
    def handle_fullscreen_request(self, request):
        """处理全屏请求"""
        request.accept()
        web_view = self.tabs.currentWidget()
        
        if request.toggleOn():
            # 进入全屏
            self.showFullScreen()
            if web_view:
                web_view.setParent(None)
                web_view.showFullScreen()
                self.fullscreen_view = web_view
        else:
            # 退出全屏
            self.showNormal()
            if hasattr(self, 'fullscreen_view') and self.fullscreen_view:
                self.tabs.currentWidget().layout().addWidget(self.fullscreen_view)
                self.fullscreen_view.showNormal()
    
    def toggle_picture_in_picture(self):
        """切换画中画模式"""
        current_web_view = self.tabs.currentWidget()
        if current_web_view:
            script = """
            var videos = document.getElementsByTagName('video');
            if (videos.length > 0) {
                var video = videos[0];
                if (video !== document.pictureInPictureElement) {
                    video.requestPictureInPicture();
                } else {
                    document.exitPictureInPicture();
                }
            }
            """
            current_web_view.page().runJavaScript(script)
    
    def apply_theme(self, theme_name):
        """应用主题"""
        if theme_name == "dark":
            # 深色主题
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #202124;
                }
                QToolBar {
                    background-color: #2d2d30;
                    border: none;
                    padding: 2px;
                }
                QLineEdit {
                    background-color: #3c3c3c;
                    color: white;
                    border: 1px solid #5c5c5c;
                    border-radius: 3px;
                    padding: 5px;
                }
                QTabWidget::pane {
                    background-color: #202124;
                    border: none;
                }
                QTabBar::tab {
                    background-color: #2d2d30;
                    color: white;
                    padding: 8px 15px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #202124;
                    border-bottom: 2px solid #0078d4;
                }
            """)
        else:
            # 浅色主题（默认）
            self.setStyleSheet("""
                QToolBar {
                    background-color: #f3f3f3;
                    border: none;
                    padding: 2px;
                }
                QLineEdit {
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    padding: 5px;
                }
                QTabWidget::pane {
                    border: none;
                }
                QTabBar::tab {
                    background-color: #f3f3f3;
                    padding: 8px 15px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: white;
                    border-bottom: 2px solid #0078d4;
                }
            """)
        
        # 保存主题设置
        self.current_theme = theme_name
    
    def show_menu(self):
        """显示菜单"""
        menu = QMenu(self)
        
        # 开发者工具
        dev_tools_action = QAction("开发者工具", self)
        dev_tools_action.triggered.connect(self.open_dev_tools)
        menu.addAction(dev_tools_action)
        
        menu.addSeparator()
        
        # 主题菜单
        theme_menu = menu.addMenu("主题")
        
        light_theme_action = QAction("浅色主题", self)
        light_theme_action.triggered.connect(lambda: self.apply_theme("light"))
        theme_menu.addAction(light_theme_action)
        
        dark_theme_action = QAction("深色主题", self)
        dark_theme_action.triggered.connect(lambda: self.apply_theme("dark"))
        theme_menu.addAction(dark_theme_action)
        
        menu.addSeparator()
        
        # 脚本管理
        script_action = QAction("管理脚本", self)
        script_action.triggered.connect(self.manage_scripts)
        menu.addAction(script_action)
        
        menu.addSeparator()
        
        # 关于
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about_dialog)
        menu.addAction(about_action)
        
        # 退出
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        menu.addAction(exit_action)
        
        menu.exec_(self.menu_btn.parentWidget().mapToGlobal(
            self.menu_btn.parentWidget().rect().bottomLeft()
        ))
    
    def open_dev_tools(self):
        """打开开发者工具"""
        current_web_view = self.tabs.currentWidget()
        if current_web_view:
            current_web_view.page().triggerAction(QWebEnginePage.InspectElement)
    
    def manage_scripts(self):
        """管理脚本对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("脚本管理")
        dialog.setGeometry(200, 200, 600, 400)
        
        layout = QVBoxLayout(dialog)
        
        # 脚本列表
        script_list = QListWidget()
        scripts = self.script_injector.get_script_list()
        for script in scripts:
            script_list.addItem(script)
        
        layout.addWidget(QLabel("当前脚本文件夹中的脚本:"))
        layout.addWidget(script_list)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        open_folder_btn = QPushButton("打开脚本文件夹")
        open_folder_btn.clicked.connect(self.open_scripts_folder)
        btn_layout.addWidget(open_folder_btn)
        
        refresh_btn = QPushButton("刷新列表")
        refresh_btn.clicked.connect(lambda: self.refresh_script_list(script_list))
        btn_layout.addWidget(refresh_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.exec_()
    
    def open_scripts_folder(self):
        """打开脚本文件夹"""
        scripts_path = self.script_injector.scripts_dir
        if os.path.exists(scripts_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(scripts_path))
    
    def refresh_script_list(self, script_list):
        """刷新脚本列表"""
        script_list.clear()
        scripts = self.script_injector.get_script_list()
        for script in scripts:
            script_list.addItem(script)
    
    def show_about_dialog(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于", 
            "基于Chromium的开源浏览器\n\n"
            "版本: 5.0.0\n"
            "使用PyQt5 WebEngine (基于Chromium)\n\n"
            "修复的问题:\n"
            "• 主页链接跳转\n"
            "• 时间、天气信息显示\n"
            "• HTML5视频播放\n"
            "• localStorage权限问题\n\n"
            "© 2025 Rick浏览器")
    
    def setup_shortcuts(self):
        """设置快捷键"""
        # Ctrl+T - 新标签页
        new_tab_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        new_tab_shortcut.activated.connect(self.open_new_tab)
        
        # Ctrl+W - 关闭标签页
        close_tab_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_tab_shortcut.activated.connect(
            lambda: self.close_tab(self.tabs.currentIndex())
        )
        
        # Ctrl+R - 刷新
        refresh_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        refresh_shortcut.activated.connect(self.refresh_page)
        
        # F5 - 刷新
        refresh_f5_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_f5_shortcut.activated.connect(self.refresh_page)
        
        # Ctrl+L - 聚焦地址栏
        focus_url_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        focus_url_shortcut.activated.connect(self.url_bar.setFocus)
        
        # F11 - 全屏
        fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
        fullscreen_shortcut.activated.connect(self.toggle_fullscreen)
        
        # Ctrl+Shift+P - 画中画
        pip_shortcut = QShortcut(QKeySequence("Ctrl+Shift+P"), self)
        pip_shortcut.activated.connect(self.toggle_picture_in_picture)
        
        # Ctrl+Shift+I - 开发者工具
        devtools_shortcut = QShortcut(QKeySequence("Ctrl+Shift+I"), self)
        devtools_shortcut.activated.connect(self.open_dev_tools)
    
    def toggle_fullscreen(self):
        """切换全屏模式"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def get_icon_path(self, icon_name):
        """获取图标路径"""
        # 首先检查icons文件夹
        icon_path = os.path.join("icons", icon_name)
        if os.path.exists(icon_path):
            return icon_path
        
        # 如果不存在，返回空字符串
        return ""
    
    def closeEvent(self, event):
        """关闭事件"""
        event.accept()

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用名称（使用英文避免路径问题）
    app.setApplicationName("ChromiumBrowser")
    app.setApplicationVersion("5.0.0")
    
    # 设置组织名称（使用英文避免路径问题）
    app.setOrganizationName("ChromiumBrowser")
    
    browser = Browser()
    browser.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
