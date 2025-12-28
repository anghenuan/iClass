"""
基于Chromium的开源浏览器 - 增强视频播放与界面美化版
"""

import os
import sys
import json
import tempfile
import time
from datetime import datetime
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
    videoDetected = pyqtSignal(bool)
    
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
    
    @pyqtSlot(str)
    def navigate(self, url):
        """从JavaScript调用导航"""
        print(f"JavaScript请求导航到: {url}")
        self.navigateRequested.emit(url)
    
    @pyqtSlot(bool)
    def videoStatus(self, has_video):
        """从JavaScript报告视频状态"""
        self.videoDetected.emit(has_video)

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
        
        # 视频播放器状态
        self.video_player = None
        self.video_detected = False
        
        # 书签和历史记录
        self.bookmarks = []
        self.history = []
        self.load_bookmarks()
        self.load_history()
        
        # 下载管理
        self.downloads = []
        self.current_download = None
        
        # 创建浏览器桥梁
        self.browser_bridge = BrowserBridge(self)
        self.browser_bridge.navigateRequested.connect(self.handle_navigation_request)
        self.browser_bridge.videoDetected.connect(self.handle_video_detected)
        
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
        
        # 创建视频播放器容器（隐藏，按需显示）
        self.video_container = QWidget()
        self.video_container.setLayout(QVBoxLayout())
        self.video_container.hide()
        main_layout.addWidget(self.video_container)
        
        # 创建标签页部件
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.tab_changed)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f5f5f5, stop:1 #e8e8e8);
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f0f0f0, stop:1 #e0e0e0);
                border: 1px solid #c0c0c0;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 16px;
                margin-right: 2px;
                color: #333;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f0f0f0);
                border-bottom: 2px solid #2196F3;
                color: #2196F3;
            }
            QTabBar::tab:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f8f8, stop:1 #e8e8e8);
            }
            /* 使用CSS绘制关闭按钮（"×"符号） */
            QTabBar::close-button {
                image: none;
                subcontrol-position: right;
                subcontrol-origin: padding;
                width: 16px;
                height: 16px;
                margin: 2px;
            }
            QTabBar::close-button::after {
                content: "×";
                color: #777;
                font-size: 12px;
                font-weight: bold;
                line-height: 16px;
            }
            QTabBar::close-button:hover::after {
                content: "×";
                color: white;
                background-color: #ff4444;
                border-radius: 2px;
                padding: 1px;
            }
            /* 为标签页添加关闭按钮间距 */
            QTabBar::tab {
                padding-right: 30px;
            }
        """)
        main_layout.addWidget(self.tabs)
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f5f5f5, stop:1 #e8e8e8);
                border-top: 1px solid #c0c0c0;
                color: #666;
            }
        """)
        self.setStatusBar(self.status_bar)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # 添加快捷键
        self.setup_shortcuts()
        
        # 创建系统托盘
        self.create_system_tray()
        
        # 创建视频播放器
        self.create_video_player()
        
    def create_navigation_bar(self):
        """创建导航工具栏"""
        nav_bar = QToolBar()
        nav_bar.setMovable(False)
        nav_bar.setIconSize(QSize(24, 24))
        nav_bar.setStyleSheet("""
            QToolBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f8f8, stop:1 #e0e0e0);
                border-bottom: 1px solid #c0c0c0;
                spacing: 5px;
                padding: 5px;
            }
            QToolButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 5px;
            }
            QToolButton:hover {
                background: rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(0, 0, 0, 0.2);
            }
            QToolButton:pressed {
                background: rgba(0, 0, 0, 0.15);
            }
            QToolButton:disabled {
                color: #999;
            }
        """)
        
        # 后退按钮
        self.back_btn = QAction(QIcon(self.get_icon_path("back.png")), "后退", self)
        self.back_btn.triggered.connect(self.navigate_back)
        self.back_btn.setShortcut(QKeySequence.Back)
        nav_bar.addAction(self.back_btn)
        
        # 前进按钮
        self.forward_btn = QAction(QIcon(self.get_icon_path("forward.png")), "前进", self)
        self.forward_btn.triggered.connect(self.navigate_forward)
        self.forward_btn.setShortcut(QKeySequence.Forward)
        nav_bar.addAction(self.forward_btn)
        
        # 刷新按钮
        self.refresh_btn = QAction(QIcon(self.get_icon_path("refresh.png")), "刷新", self)
        self.refresh_btn.triggered.connect(self.refresh_page)
        self.refresh_btn.setShortcut(QKeySequence.Refresh)
        nav_bar.addAction(self.refresh_btn)
        
        # 主页按钮
        self.home_btn = QAction(QIcon(self.get_icon_path("home.png")), "主页", self)
        self.home_btn.triggered.connect(self.open_home_page)
        nav_bar.addAction(self.home_btn)
        
        nav_bar.addSeparator()
        
        # 地址栏
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("输入网址或搜索内容...")
        self.url_bar.setClearButtonEnabled(True)
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.url_bar.setStyleSheet("""
            QLineEdit {
                border: 2px solid #ddd;
                border-radius: 20px;
                padding: 8px 15px;
                background: white;
                font-size: 14px;
                selection-background-color: #2196F3;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
                background: #f8fdff;
            }
            QLineEdit:hover {
                border: 2px solid #bbb;
            }
        """)
        nav_bar.addWidget(self.url_bar)
        
        # 搜索按钮
        self.search_btn = QAction(QIcon(self.get_icon_path("search.png")), "搜索", self)
        self.search_btn.triggered.connect(self.search_with_bing)
        nav_bar.addAction(self.search_btn)
        
        nav_bar.addSeparator()
        
        # 书签按钮
        self.bookmark_btn = QAction(QIcon(self.get_icon_path("bookmark.png")), "书签", self)
        self.bookmark_btn.triggered.connect(self.toggle_bookmark)
        nav_bar.addAction(self.bookmark_btn)
        
        # 下载按钮
        self.download_btn = QAction(QIcon(self.get_icon_path("download.png")), "下载", self)
        self.download_btn.triggered.connect(self.show_downloads)
        nav_bar.addAction(self.download_btn)
        
        # 历史按钮
        self.history_btn = QAction(QIcon(self.get_icon_path("history.png")), "历史", self)
        self.history_btn.triggered.connect(self.show_history)
        nav_bar.addAction(self.history_btn)
        
        nav_bar.addSeparator()
        
        # 新标签页按钮
        self.new_tab_btn = QAction(QIcon(self.get_icon_path("add_tab.png")), "新标签页", self)
        self.new_tab_btn.triggered.connect(self.open_new_tab)
        self.new_tab_btn.setShortcut(QKeySequence.AddTab)
        nav_bar.addAction(self.new_tab_btn)
        
        # 视频播放器按钮
        self.video_toggle_btn = QAction(QIcon(self.get_icon_path("video.png")), "视频播放器", self)
        self.video_toggle_btn.triggered.connect(self.toggle_video_player)
        self.video_toggle_btn.setCheckable(True)
        self.video_toggle_btn.setVisible(False)
        nav_bar.addAction(self.video_toggle_btn)
        
        # 画中画按钮
        self.pip_btn = QAction(QIcon(self.get_icon_path("pip.png")), "画中画", self)
        self.pip_btn.triggered.connect(self.toggle_picture_in_picture)
        self.pip_btn.setVisible(False)
        nav_bar.addAction(self.pip_btn)
        
        # 菜单按钮
        self.menu_btn = QAction(QIcon(self.get_icon_path("menu.png")), "菜单", self)
        self.menu_btn.triggered.connect(self.show_menu)
        nav_bar.addAction(self.menu_btn)
        
        return nav_bar
    
    def create_video_player(self):
        """创建独立视频播放器"""
        video_widget = QWidget()
        layout = QVBoxLayout(video_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 视频控制工具栏
        video_toolbar = QToolBar()
        video_toolbar.setMovable(False)
        
        # 播放/暂停按钮
        self.play_btn = QAction(QIcon(self.get_icon_path("play.png")), "播放", self)
        self.play_btn.triggered.connect(self.video_play_pause)
        video_toolbar.addAction(self.play_btn)
        
        # 停止按钮
        self.stop_btn = QAction(QIcon(self.get_icon_path("stop.png")), "停止", self)
        self.stop_btn.triggered.connect(self.video_stop)
        video_toolbar.addAction(self.stop_btn)
        
        # 音量控制
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self.set_video_volume)
        video_toolbar.addWidget(QLabel("音量:"))
        video_toolbar.addWidget(self.volume_slider)
        
        # 进度条
        self.video_progress = QSlider(Qt.Horizontal)
        self.video_progress.sliderMoved.connect(self.seek_video)
        video_toolbar.addWidget(self.video_progress)
        
        # 时间显示
        self.time_label = QLabel("00:00 / 00:00")
        video_toolbar.addWidget(self.time_label)
        
        layout.addWidget(video_toolbar)
        
        # 视频显示区域
        self.video_widget = QWebEngineView()
        layout.addWidget(self.video_widget)
        
        self.video_container.layout().addWidget(video_widget)
    
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
        settings.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
        settings.setAttribute(QWebEngineSettings.FocusOnNavigationEnabled, True)
        
        # 设置用户代理
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0")
        
        # 设置缓存路径
        cache_dir = os.path.join(tempfile.gettempdir(), "browser_cache")
        os.makedirs(cache_dir, exist_ok=True)
        profile.setCachePath(cache_dir)
        profile.setPersistentStoragePath(cache_dir)
        
        # 设置下载处理
        profile.downloadRequested.connect(self.handle_download_request)
        
        # 设置初始URL
        if url:
            web_view.setUrl(QUrl(url))
        
        # 连接信号
        web_view.urlChanged.connect(self.update_url_bar)
        web_view.loadStarted.connect(self.page_loading_started)
        web_view.loadFinished.connect(self.page_loading_finished)
        web_view.loadProgress.connect(self.update_progress_bar)
        
        # 连接全屏信号
        page.fullScreenRequested.connect(self.handle_fullscreen_request)
        
        # 连接标题变化信号
        page.titleChanged.connect(self.update_tab_title)
        
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
        web_view.setHtml(html_content, QUrl("about:blank"))
        
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
        
        # 注入视频检测脚本
        self.inject_video_detection_script(page)
    
    def inject_video_detection_script(self, page):
        """注入视频检测脚本"""
        script = """
        // 检测页面中的视频元素
        function detectVideos() {
            const videos = document.querySelectorAll('video');
            const hasVideo = videos.length > 0;
            
            if (window.browser && window.browser.videoStatus) {
                window.browser.videoStatus(hasVideo);
            }
            
            // 为视频添加增强控制
            videos.forEach((video, index) => {
                if (!video.dataset.enhanced) {
                    video.dataset.enhanced = 'true';
                    
                    // 添加右键菜单支持
                    video.addEventListener('contextmenu', function(e) {
                        e.preventDefault();
                        // 可以在这里添加自定义右键菜单
                    });
                    
                    // 监听播放状态
                    video.addEventListener('play', function() {
                        console.log('视频开始播放:', this.src);
                    });
                    
                    video.addEventListener('pause', function() {
                        console.log('视频暂停');
                    });
                    
                    video.addEventListener('ended', function() {
                        console.log('视频播放结束');
                    });
                }
            });
        }
        
        // 初始检测
        detectVideos();
        
        // 监听DOM变化
        const observer = new MutationObserver(function(mutations) {
            detectVideos();
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        """
        
        web_script = QWebEngineScript()
        web_script.setSourceCode(script)
        web_script.setInjectionPoint(QWebEngineScript.DocumentCreation)
        web_script.setWorldId(QWebEngineScript.MainWorld)
        web_script.setRunsOnSubFrames(True)
        page.scripts().insert(web_script)
    
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
    
    def handle_video_detected(self, has_video):
        """处理视频检测结果"""
        self.video_detected = has_video
        self.video_toggle_btn.setVisible(has_video)
        self.pip_btn.setVisible(has_video)
    
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
        self.handle_video_detected(bool(has_video))
    
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
            
        # 添加到历史记录
        self.add_to_history(url_text)
        
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
            # 添加到历史记录
            self.add_to_history(f"搜索: {search_text}")
            
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
    
    def update_tab_title(self, title):
        """更新标签页标题"""
        current_web_view = self.tabs.currentWidget()
        if current_web_view:
            index = self.tabs.indexOf(current_web_view)
            if index >= 0:
                # 限制标题长度
                if len(title) > 30:
                    title = title[:27] + "..."
                self.tabs.setTabText(index, title)
    
    def update_progress_bar(self, progress):
        """更新进度条"""
        self.progress_bar.setValue(progress)
        self.progress_bar.setVisible(progress < 100)
    
    def page_loading_started(self):
        """页面开始加载"""
        self.status_bar.showMessage("加载中...")
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
    
    def page_loading_finished(self, success):
        """页面加载完成"""
        if success:
            self.status_bar.showMessage("完成")
            self.progress_bar.setVisible(False)
            
            # 注入脚本到当前页面（除了新标签页）
            current_web_view = self.tabs.currentWidget()
            if current_web_view and id(current_web_view) not in self.new_tab_pages:
                self.inject_scripts_to_page(current_web_view.page())
                
                # 检查是否有视频
                self.check_for_video(current_web_view)
        else:
            self.status_bar.showMessage("加载失败")
            self.progress_bar.setVisible(False)
    
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
    
    def toggle_video_player(self):
        """切换视频播放器显示"""
        if self.video_container.isVisible():
            self.video_container.hide()
            self.video_toggle_btn.setChecked(False)
        else:
            self.video_container.show()
            self.video_toggle_btn.setChecked(True)
            # 提取当前页面的视频
            self.extract_video()
    
    def extract_video(self):
        """提取当前页面的视频"""
        current_web_view = self.tabs.currentWidget()
        if current_web_view:
            script = """
            var videos = document.getElementsByTagName('video');
            if (videos.length > 0) {
                return videos[0].src;
            }
            return null;
            """
            
            current_web_view.page().runJavaScript(script, self.load_video_to_player)
    
    def load_video_to_player(self, video_url):
        """加载视频到独立播放器"""
        if video_url:
            self.video_widget.setUrl(QUrl(video_url))
    
    def video_play_pause(self):
        """视频播放/暂停"""
        script = """
        var videos = document.getElementsByTagName('video');
        if (videos.length > 0) {
            var video = videos[0];
            if (video.paused) {
                video.play();
                return 'playing';
            } else {
                video.pause();
                return 'paused';
            }
        }
        return 'no_video';
        """
        
        current_web_view = self.tabs.currentWidget()
        if current_web_view:
            current_web_view.page().runJavaScript(script, self.handle_play_pause_result)
    
    def handle_play_pause_result(self, result):
        """处理播放/暂停结果"""
        if result == 'playing':
            self.play_btn.setIcon(QIcon(self.get_icon_path("pause.png")))
            self.play_btn.setText("暂停")
        elif result == 'paused':
            self.play_btn.setIcon(QIcon(self.get_icon_path("play.png")))
            self.play_btn.setText("播放")
    
    def video_stop(self):
        """视频停止"""
        script = """
        var videos = document.getElementsByTagName('video');
        if (videos.length > 0) {
            var video = videos[0];
            video.pause();
            video.currentTime = 0;
        }
        """
        
        current_web_view = self.tabs.currentWidget()
        if current_web_view:
            current_web_view.page().runJavaScript(script)
            self.play_btn.setIcon(QIcon(self.get_icon_path("play.png")))
            self.play_btn.setText("播放")
    
    def set_video_volume(self, volume):
        """设置视频音量"""
        script = f"""
        var videos = document.getElementsByTagName('video');
        if (videos.length > 0) {{
            videos[0].volume = {volume / 100};
        }}
        """
        
        current_web_view = self.tabs.currentWidget()
        if current_web_view:
            current_web_view.page().runJavaScript(script)
    
    def seek_video(self, position):
        """视频跳转"""
        script = f"""
        var videos = document.getElementsByTagName('video');
        if (videos.length > 0) {{
            var video = videos[0];
            video.currentTime = video.duration * ({position} / 100);
        }}
        """
        
        current_web_view = self.tabs.currentWidget()
        if current_web_view:
            current_web_view.page().runJavaScript(script)
    
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
    
    def toggle_bookmark(self):
        """切换书签"""
        current_web_view = self.tabs.currentWidget()
        if current_web_view:
            url = current_web_view.url().toString()
            title = current_web_view.page().title()
            
            # 检查是否已收藏
            for bookmark in self.bookmarks:
                if bookmark['url'] == url:
                    self.bookmarks.remove(bookmark)
                    self.save_bookmarks()
                    self.status_bar.showMessage("已从书签移除", 3000)
                    return
            
            # 添加书签
            bookmark = {
                'url': url,
                'title': title,
                'time': time.time()
            }
            self.bookmarks.append(bookmark)
            self.save_bookmarks()
            self.status_bar.showMessage("已添加到书签", 3000)
    
    def load_bookmarks(self):
        """加载书签"""
        bookmark_file = Path("bookmarks.json")
        if bookmark_file.exists():
            try:
                with open(bookmark_file, 'r', encoding='utf-8') as f:
                    self.bookmarks = json.load(f)
            except:
                self.bookmarks = []
    
    def save_bookmarks(self):
        """保存书签"""
        bookmark_file = Path("bookmarks.json")
        try:
            with open(bookmark_file, 'w', encoding='utf-8') as f:
                json.dump(self.bookmarks, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def load_history(self):
        """加载历史记录"""
        history_file = Path("history.json")
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except:
                self.history = []
    
    def save_history(self):
        """保存历史记录"""
        history_file = Path("history.json")
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def add_to_history(self, url):
        """添加到历史记录"""
        history_item = {
            'url': url,
            'time': time.time(),
            'title': url
        }
        self.history.insert(0, history_item)
        
        # 限制历史记录数量
        if len(self.history) > 100:
            self.history = self.history[:100]
        
        self.save_history()
    
    def show_bookmarks(self):
        """显示书签对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("书签")
        dialog.setGeometry(200, 200, 600, 400)
        
        layout = QVBoxLayout(dialog)
        
        # 书签列表
        bookmark_list = QListWidget()
        for bookmark in self.bookmarks:
            item = QListWidgetItem(bookmark['title'])
            item.setData(Qt.UserRole, bookmark['url'])
            bookmark_list.addItem(item)
        
        layout.addWidget(bookmark_list)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        open_btn = QPushButton("打开")
        open_btn.clicked.connect(lambda: self.open_bookmark(bookmark_list, dialog))
        btn_layout.addWidget(open_btn)
        
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(lambda: self.delete_bookmark(bookmark_list))
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.exec_()
    
    def open_bookmark(self, bookmark_list, dialog):
        """打开选中的书签"""
        current_item = bookmark_list.currentItem()
        if current_item:
            url = current_item.data(Qt.UserRole)
            self.add_tab(url=url)
            dialog.close()
    
    def delete_bookmark(self, bookmark_list):
        """删除选中的书签"""
        current_item = bookmark_list.currentItem()
        if current_item:
            url = current_item.data(Qt.UserRole)
            for bookmark in self.bookmarks:
                if bookmark['url'] == url:
                    self.bookmarks.remove(bookmark)
                    break
            
            self.save_bookmarks()
            row = bookmark_list.row(current_item)
            bookmark_list.takeItem(row)
    
    def show_history(self):
        """显示历史记录对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("历史记录")
        dialog.setGeometry(200, 200, 700, 400)
        
        layout = QVBoxLayout(dialog)
        
        # 历史记录表格
        history_table = QTableWidget()
        history_table.setColumnCount(3)
        history_table.setHorizontalHeaderLabels(["标题", "网址", "访问时间"])
        history_table.setRowCount(len(self.history))
        
        for i, item in enumerate(self.history):
            title = item.get('title', '未知')
            url = item.get('url', '')
            visit_time = datetime.fromtimestamp(item.get('time', time.time())).strftime("%Y-%m-%d %H:%M:%S")
            
            history_table.setItem(i, 0, QTableWidgetItem(title))
            history_table.setItem(i, 1, QTableWidgetItem(url))
            history_table.setItem(i, 2, QTableWidgetItem(visit_time))
        
        history_table.resizeColumnsToContents()
        layout.addWidget(history_table)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        open_btn = QPushButton("打开")
        open_btn.clicked.connect(lambda: self.open_history_item(history_table, dialog))
        btn_layout.addWidget(open_btn)
        
        clear_btn = QPushButton("清空历史")
        clear_btn.clicked.connect(lambda: self.clear_history(history_table))
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.exec_()
    
    def open_history_item(self, history_table, dialog):
        """打开选中的历史记录"""
        current_row = history_table.currentRow()
        if current_row >= 0:
            url = history_table.item(current_row, 1).text()
            self.add_tab(url=url)
            dialog.close()
    
    def clear_history(self, history_table):
        """清空历史记录"""
        reply = QMessageBox.question(self, "确认", "确定要清空所有历史记录吗？",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.history.clear()
            self.save_history()
            history_table.setRowCount(0)
    
    def handle_download_request(self, download):
        """处理下载请求"""
        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(self, "保存文件", 
                                                  os.path.basename(download.path()))
        if file_path:
            download.setPath(file_path)
            download.accept()
            
            # 添加到下载列表
            download_item = {
                'path': file_path,
                'url': download.url().toString(),
                'start_time': time.time(),
                'status': '下载中'
            }
            self.downloads.append(download_item)
            
            # 连接下载信号
            download.downloadProgress.connect(
                lambda bytes_received, bytes_total: 
                self.update_download_progress(download, bytes_received, bytes_total)
            )
            download.finished.connect(
                lambda: self.download_finished(download)
            )
            
            self.current_download = download
            self.status_bar.showMessage(f"开始下载: {os.path.basename(file_path)}")
    
    def update_download_progress(self, download, bytes_received, bytes_total):
        """更新下载进度"""
        if bytes_total > 0:
            progress = int((bytes_received / bytes_total) * 100)
            self.progress_bar.setValue(progress)
            self.progress_bar.setVisible(True)
            
            # 更新下载列表中的状态
            for item in self.downloads:
                if item['url'] == download.url().toString():
                    item['progress'] = progress
                    item['received'] = bytes_received
                    item['total'] = bytes_total
                    break
    
    def download_finished(self, download):
        """下载完成"""
        self.progress_bar.setVisible(False)
        
        # 更新下载状态
        for item in self.downloads:
            if item['url'] == download.url().toString():
                item['status'] = '已完成'
                item['end_time'] = time.time()
                break
        
        self.status_bar.showMessage("下载完成", 3000)
        self.current_download = None
    
    def show_downloads(self):
        """显示下载管理对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("下载管理")
        dialog.setGeometry(200, 200, 700, 400)
        
        layout = QVBoxLayout(dialog)
        
        # 下载列表
        download_table = QTableWidget()
        download_table.setColumnCount(5)
        download_table.setHorizontalHeaderLabels(["文件名", "状态", "进度", "大小", "时间"])
        download_table.setRowCount(len(self.downloads))
        
        for i, item in enumerate(self.downloads):
            filename = os.path.basename(item['path'])
            status = item.get('status', '未知')
            progress = item.get('progress', 0)
            received = item.get('received', 0)
            total = item.get('total', 0)
            
            # 格式化大小
            if total > 0:
                size = f"{received/(1024*1024):.1f}MB / {total/(1024*1024):.1f}MB"
            else:
                size = "未知"
            
            # 格式化时间
            if 'start_time' in item:
                time_str = datetime.fromtimestamp(item['start_time']).strftime("%H:%M:%S")
            else:
                time_str = "未知"
            
            download_table.setItem(i, 0, QTableWidgetItem(filename))
            download_table.setItem(i, 1, QTableWidgetItem(status))
            
            # 进度条单元格
            progress_widget = QWidget()
            progress_layout = QHBoxLayout(progress_widget)
            progress_bar = QProgressBar()
            progress_bar.setValue(progress)
            progress_layout.addWidget(progress_bar)
            progress_layout.setContentsMargins(0, 0, 0, 0)
            download_table.setCellWidget(i, 2, progress_widget)
            
            download_table.setItem(i, 3, QTableWidgetItem(size))
            download_table.setItem(i, 4, QTableWidgetItem(time_str))
        
        download_table.resizeColumnsToContents()
        layout.addWidget(download_table)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        open_btn = QPushButton("打开文件")
        open_btn.clicked.connect(lambda: self.open_downloaded_file(download_table))
        btn_layout.addWidget(open_btn)
        
        open_folder_btn = QPushButton("打开文件夹")
        open_folder_btn.clicked.connect(lambda: self.open_download_folder(download_table))
        btn_layout.addWidget(open_folder_btn)
        
        clear_btn = QPushButton("清空列表")
        clear_btn.clicked.connect(lambda: self.clear_downloads(download_table))
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.exec_()
    
    def open_downloaded_file(self, download_table):
        """打开下载的文件"""
        current_row = download_table.currentRow()
        if current_row >= 0 and current_row < len(self.downloads):
            file_path = self.downloads[current_row]['path']
            if os.path.exists(file_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
    
    def open_download_folder(self, download_table):
        """打开下载文件所在文件夹"""
        current_row = download_table.currentRow()
        if current_row >= 0 and current_row < len(self.downloads):
            file_path = self.downloads[current_row]['path']
            folder_path = os.path.dirname(file_path)
            if os.path.exists(folder_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))
    
    def clear_downloads(self, download_table):
        """清空下载列表"""
        reply = QMessageBox.question(self, "确认", "确定要清空下载列表吗？",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.downloads.clear()
            download_table.setRowCount(0)
    
    def apply_theme(self, theme_name):
        """应用主题"""
        if theme_name == "dark":
            # 深色主题
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                }
                QToolBar {
                    background-color: #2d2d30;
                    border: none;
                    border-bottom: 1px solid #3e3e42;
                    spacing: 5px;
                    padding: 5px;
                }
                QToolButton {
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: 4px;
                    padding: 5px;
                    color: #d4d4d4;
                }
                QToolButton:hover {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                QToolButton:pressed {
                    background: rgba(255, 255, 255, 0.15);
                }
                QToolButton:disabled {
                    color: #6d6d6d;
                }
                QLineEdit {
                    border: 2px solid #3e3e42;
                    border-radius: 20px;
                    padding: 8px 15px;
                    background: #252526;
                    color: #d4d4d4;
                    font-size: 14px;
                    selection-background-color: #007acc;
                }
                QLineEdit:focus {
                    border: 2px solid #007acc;
                    background: #2a2d2e;
                }
                QLineEdit:hover {
                    border: 2px solid #5d5d5d;
                }
                QTabWidget::pane {
                    border: none;
                    background: #1e1e1e;
                }
                QTabBar::tab {
                    background: #2d2d30;
                    border: 1px solid #3e3e42;
                    border-bottom: none;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    padding: 8px 16px;
                    margin-right: 2px;
                    color: #d4d4d4;
                    font-weight: 500;
                }
                QTabBar::tab:selected {
                    background: #1e1e1e;
                    border-bottom: 2px solid #007acc;
                    color: #ffffff;
                }
                QTabBar::tab:hover {
                    background: #3e3e42;
                }
                /* 使用CSS绘制关闭按钮（"×"符号） */
                QTabBar::close-button {
                    image: none;
                    subcontrol-position: right;
                    subcontrol-origin: padding;
                    width: 16px;
                    height: 16px;
                    margin: 2px;
                }
                QTabBar::close-button::after {
                    content: "×";
                    color: #777;
                    font-size: 12px;
                    font-weight: bold;
                    line-height: 16px;
                }
                QTabBar::close-button:hover::after {
                    content: "×";
                    color: white;
                    background-color: #ff4444;
                    border-radius: 2px;
                    padding: 1px;
                }
                /* 为标签页添加关闭按钮间距 */
                QTabBar::tab {
                    padding-right: 30px;
                }
                QStatusBar {
                    background: #007acc;
                    color: white;
                    border-top: 1px solid #3e3e42;
                }
                QProgressBar {
                    border: 1px solid #3e3e42;
                    border-radius: 3px;
                    text-align: center;
                    background: #252526;
                }
                QProgressBar::chunk {
                    background-color: #007acc;
                    border-radius: 2px;
                }
            """)
        else:
            # 浅色主题（默认）
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f5f5f5;
                }
                QToolBar {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #f8f8f8, stop:1 #e0e0e0);
                    border-bottom: 1px solid #c0c0c0;
                    spacing: 5px;
                    padding: 5px;
                }
                QToolButton {
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: 4px;
                    padding: 5px;
                }
                QToolButton:hover {
                    background: rgba(0, 0, 0, 0.1);
                    border: 1px solid rgba(0, 0, 0, 0.2);
                }
                QToolButton:pressed {
                    background: rgba(0, 0, 0, 0.15);
                }
                QToolButton:disabled {
                    color: #999;
                }
                QLineEdit {
                    border: 2px solid #ddd;
                    border-radius: 20px;
                    padding: 8px 15px;
                    background: white;
                    font-size: 14px;
                    selection-background-color: #2196F3;
                }
                QLineEdit:focus {
                    border: 2px solid #2196F3;
                    background: #f8fdff;
                }
                QLineEdit:hover {
                    border: 2px solid #bbb;
                }
                QTabWidget::pane {
                    border: none;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #f5f5f5, stop:1 #e8e8e8);
                }
                QTabBar::tab {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #f0f0f0, stop:1 #e0e0e0);
                    border: 1px solid #c0c0c0;
                    border-bottom: none;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    padding: 8px 16px;
                    margin-right: 2px;
                    color: #333;
                    font-weight: 500;
                }
                QTabBar::tab:selected {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #ffffff, stop:1 #f0f0f0);
                    border-bottom: 2px solid #2196F3;
                    color: #2196F3;
                }
                QTabBar::tab:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #f8f8f8, stop:1 #e8e8e8);
                }
                /* 使用CSS绘制关闭按钮（"×"符号） */
                QTabBar::close-button {
                    image: none;
                    subcontrol-position: right;
                    subcontrol-origin: padding;
                    width: 16px;
                    height: 16px;
                    margin: 2px;
                }
                QTabBar::close-button::after {
                    content: "×";
                    color: #777;
                    font-size: 12px;
                    font-weight: bold;
                    line-height: 16px;
                }
                QTabBar::close-button:hover::after {
                    content: "×";
                    color: white;
                    background-color: #ff4444;
                    border-radius: 2px;
                    padding: 1px;
                }
                /* 为标签页添加关闭按钮间距 */
                QTabBar::tab {
                    padding-right: 30px;
                }
                QStatusBar {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #f5f5f5, stop:1 #e8e8e8);
                    border-top: 1px solid #c0c0c0;
                    color: #666;
                }
                QProgressBar {
                    border: 1px solid #c0c0c0;
                    border-radius: 3px;
                    text-align: center;
                    background: white;
                }
                QProgressBar::chunk {
                    background-color: #2196F3;
                    border-radius: 2px;
                }
            """)
        
        # 保存主题设置
        self.current_theme = theme_name
    
    def create_system_tray(self):
        """创建系统托盘"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            tray_icon = QSystemTrayIcon(self)
            tray_icon.setIcon(QIcon(self.get_icon_path("browser.png")))
            
            # 创建托盘菜单
            tray_menu = QMenu()
            
            show_action = QAction("显示浏览器", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)
            
            new_tab_action = QAction("新建标签页", self)
            new_tab_action.triggered.connect(self.open_new_tab)
            tray_menu.addAction(new_tab_action)
            
            tray_menu.addSeparator()
            
            quit_action = QAction("退出", self)
            quit_action.triggered.connect(self.close)
            tray_menu.addAction(quit_action)
            
            tray_icon.setContextMenu(tray_menu)
            tray_icon.show()
            
            # 托盘图标点击事件
            tray_icon.activated.connect(self.tray_icon_activated)
    
    def tray_icon_activated(self, reason):
        """托盘图标激活"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.activateWindow()
    
    def show_menu(self):
        """显示菜单"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #2196F3;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background-color: #e0e0e0;
                margin: 5px 0;
            }
        """)
        
        # 新建标签页
        new_tab_action = QAction("新建标签页", self)
        new_tab_action.setShortcut(QKeySequence.AddTab)
        new_tab_action.triggered.connect(self.open_new_tab)
        menu.addAction(new_tab_action)
        
        # 新建窗口
        new_window_action = QAction("新建窗口", self)
        new_window_action.triggered.connect(self.new_window)
        menu.addAction(new_window_action)
        
        menu.addSeparator()
        
        # 书签
        bookmark_action = QAction("书签", self)
        bookmark_action.triggered.connect(self.show_bookmarks)
        menu.addAction(bookmark_action)
        
        # 历史记录
        history_action = QAction("历史记录", self)
        history_action.triggered.connect(self.show_history)
        menu.addAction(history_action)
        
        # 下载
        download_action = QAction("下载", self)
        download_action.triggered.connect(self.show_downloads)
        menu.addAction(download_action)
        
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
        
        # 开发者工具
        dev_tools_action = QAction("开发者工具", self)
        dev_tools_action.setShortcut(QKeySequence("Ctrl+Shift+I"))
        dev_tools_action.triggered.connect(self.open_dev_tools)
        menu.addAction(dev_tools_action)
        
        # 脚本管理
        script_action = QAction("脚本管理", self)
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
    
    def new_window(self):
        """新建浏览器窗口"""
        new_browser = Browser()
        new_browser.show()
    
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
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: #333;
                font-weight: bold;
            }
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                alternate-background-color: #f9f9f9;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px 16px;
                color: #333;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #bbb;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        
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
        
        open_folder_btn = QPushButton("📂 打开脚本文件夹")
        open_folder_btn.clicked.connect(self.open_scripts_folder)
        btn_layout.addWidget(open_folder_btn)
        
        refresh_btn = QPushButton("🔄 刷新列表")
        refresh_btn.clicked.connect(lambda: self.refresh_script_list(script_list))
        btn_layout.addWidget(refresh_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("❌ 关闭")
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
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("关于 Rick浏览器")
        about_dialog.setFixedSize(400, 300)
        about_dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2196F3, stop:1 #1976D2);
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QLabel#title {
                font-size: 24px;
                font-weight: bold;
            }
            QLabel#version {
                font-size: 16px;
                color: #BBDEFB;
            }
            QPushButton {
                background-color: white;
                color: #2196F3;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
            }
        """)
        
        layout = QVBoxLayout(about_dialog)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 标题
        title_label = QLabel("Rick浏览器")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 版本
        version_label = QLabel("版本 6.0.0 - 增强版")
        version_label.setObjectName("version")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        layout.addSpacing(20)
        
        # 描述
        desc_label = QLabel(
            "基于Chromium内核的现代浏览器\n\n"
            "特性：\n"
            "• 增强HTML5视频播放支持\n"
            "• 独立视频播放器\n"
            "• 画中画模式\n"
            "• 书签和历史管理\n"
            "• 用户脚本支持\n"
            "• 深色/浅色主题\n"
            "• 下载管理"
        )
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
        # 按钮
        close_btn = QPushButton("确定")
        close_btn.clicked.connect(about_dialog.close)
        close_btn.setFixedWidth(100)
        layout.addWidget(close_btn, 0, Qt.AlignCenter)
        
        about_dialog.exec_()
    
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
        
        # Ctrl+H - 历史记录
        history_shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
        history_shortcut.activated.connect(self.show_history)
        
        # Ctrl+D - 添加书签
        bookmark_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        bookmark_shortcut.activated.connect(self.toggle_bookmark)
        
        # Ctrl+J - 下载管理
        download_shortcut = QShortcut(QKeySequence("Ctrl+J"), self)
        download_shortcut.activated.connect(self.show_downloads)
        
        # Ctrl+Tab - 下一个标签页
        next_tab_shortcut = QShortcut(QKeySequence("Ctrl+Tab"), self)
        next_tab_shortcut.activated.connect(self.next_tab)
        
        # Ctrl+Shift+Tab - 上一个标签页
        prev_tab_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        prev_tab_shortcut.activated.connect(self.previous_tab)
    
    def next_tab(self):
        """切换到下一个标签页"""
        current_index = self.tabs.currentIndex()
        next_index = (current_index + 1) % self.tabs.count()
        self.tabs.setCurrentIndex(next_index)
    
    def previous_tab(self):
        """切换到上一个标签页"""
        current_index = self.tabs.currentIndex()
        prev_index = (current_index - 1) % self.tabs.count()
        self.tabs.setCurrentIndex(prev_index)
    
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
        
        # 如果不存在，使用默认图标
        default_icons = {
            "browser.png": "🌐",
            "back.png": "⬅️",
            "forward.png": "➡️",
            "refresh.png": "🔄",
            "home.png": "🏠",
            "search.png": "🔍",
            "bookmark.png": "🔖",
            "download.png": "📥",
            "history.png": "📜",
            "add_tab.png": "➕",
            "video.png": "🎬",
            "pip.png": "📺",
            "menu.png": "☰",
            "play.png": "▶️",
            "pause.png": "⏸️",
            "stop.png": "⏹️",
            "close.png": "✕",
            "close_hover.png": "✕"
        }
        
        # 创建图标文件夹
        icon_dir = Path("icons")
        icon_dir.mkdir(exist_ok=True)
        
        # 如果图标不存在，创建文本图标
        if icon_name in default_icons:
            # 使用简单的文本作为图标
            from PyQt5.QtGui import QPixmap, QPainter, QFont, QColor
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            font = QFont("Arial", 20)
            painter.setFont(font)
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, default_icons[icon_name])
            painter.end()
            
            # 保存图标
            pixmap.save(icon_path)
            return icon_path
        
        return ""
    
    def closeEvent(self, event):
        """关闭事件"""
        # 保存书签和历史记录
        self.save_bookmarks()
        self.save_history()
        event.accept()

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("RickBrowser")
    app.setApplicationVersion("6.0.0")
    app.setOrganizationName("RickBrowser")
    
    # 设置字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    browser = Browser()
    browser.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
