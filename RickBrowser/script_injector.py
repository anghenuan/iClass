"""
脚本注入器 - 支持类似篡改猴的用户脚本
增强HTML5支持
"""

import os
import re
from pathlib import Path
from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import QWebEngineScript

class ScriptInjector:
    """脚本注入器，从scripts文件夹加载用户脚本"""
    
    def __init__(self):
        # 脚本目录
        self.scripts_dir = Path("scripts")
        self.scripts_dir.mkdir(exist_ok=True)
        
        # 脚本缓存
        self.scripts = []
        
        # 加载脚本
        self.load_scripts()
    
    def load_scripts(self):
        """从scripts文件夹加载所有用户脚本"""
        self.scripts.clear()
        
        if not self.scripts_dir.exists():
            return
        
        for script_file in self.scripts_dir.glob("*.user.js"):
            try:
                with open(script_file, 'r', encoding='utf-8') as f:
                    script_content = f.read()
                    
                    # 解析脚本元数据（类似篡改猴格式）
                    metadata = self.parse_metadata(script_content)
                    
                    # 获取脚本名称
                    script_name = metadata.get('name', script_file.name)
                    
                    # 获取匹配规则
                    matches = metadata.get('match', [])
                    excludes = metadata.get('exclude', [])
                    
                    self.scripts.append({
                        'name': script_name,
                        'path': script_file,
                        'content': script_content,
                        'matches': matches,
                        'excludes': excludes,
                        'enabled': True
                    })
                    
                    print(f"加载脚本: {script_name}")
                    
            except Exception as e:
                print(f"加载脚本 {script_file} 时出错: {e}")
        
        # 如果没有脚本，创建示例脚本
        if len(self.scripts) == 0:
            self.create_example_script()
    
    def create_example_script(self):
        """创建示例脚本"""
        example_script = Path(self.scripts_dir) / "example.user.js"
        
        example_content = """// ==UserScript==
// @name         增强HTML5视频支持
// @namespace    http://example.com
// @version      1.0
// @description  增强HTML5视频播放器支持，添加画中画和全屏快捷键
// @author       浏览器开发者
// @match        *://*/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';
    
    console.log('用户脚本已加载: 增强HTML5视频支持');
    
    // 添加视频控制快捷键
    document.addEventListener('keydown', function(e) {
        // F11 - 全屏
        if (e.keyCode === 122) { // F11
            const video = document.querySelector('video');
            if (video) {
                if (video.requestFullscreen) {
                    video.requestFullscreen();
                } else if (video.webkitRequestFullscreen) {
                    video.webkitRequestFullscreen();
                } else if (video.mozRequestFullScreen) {
                    video.mozRequestFullScreen();
                }
            }
        }
        
        // Ctrl+Shift+P - 画中画
        if (e.ctrlKey && e.shiftKey && e.keyCode === 80) { // Ctrl+Shift+P
            const video = document.querySelector('video');
            if (video) {
                if (document.pictureInPictureEnabled && !video.disablePictureInPicture) {
                    if (video !== document.pictureInPictureElement) {
                        video.requestPictureInPicture();
                    } else {
                        document.exitPictureInPicture();
                    }
                }
            }
        }
    });
    
    // 增强视频控制
    function enhanceVideoControls() {
        const videos = document.querySelectorAll('video');
        
        videos.forEach((video, index) => {
            // 确保视频可以画中画
            video.setAttribute('playsinline', '');
            video.setAttribute('webkit-playsinline', '');
            
            // 添加自定义控制
            if (!video.hasAttribute('data-enhanced')) {
                video.setAttribute('data-enhanced', 'true');
                
                // 监听视频播放
                video.addEventListener('play', function() {
                    console.log('视频播放中:', this.src);
                });
            }
        });
    }
    
    // 初始增强
    enhanceVideoControls();
    
    // 监听DOM变化以增强新添加的视频
    const observer = new MutationObserver(function(mutations) {
        enhanceVideoControls();
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
})();
"""
        
        try:
            with open(example_script, 'w', encoding='utf-8') as f:
                f.write(example_content)
            
            self.load_scripts()
            print("已创建示例脚本")
        except Exception as e:
            print(f"创建示例脚本时出错: {e}")
    
    def parse_metadata(self, script_content):
        """解析用户脚本的元数据（类似篡改猴格式）"""
        metadata = {}
        
        # 查找元数据块（在 ==UserScript== 和 ==/UserScript== 之间）
        metadata_pattern = r'// ==UserScript==\s*(.*?)\s*// ==/UserScript=='
        match = re.search(metadata_pattern, script_content, re.DOTALL)
        
        if match:
            metadata_block = match.group(1)
            
            # 解析元数据行
            lines = metadata_block.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('// @'):
                    # 移除注释符号
                    line = line[4:].strip()
                    
                    # 分割键值
                    if ' ' in line:
                        key, value = line.split(' ', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 处理数组类型的元数据（如 @match）
                        if key in ['match', 'include', 'exclude']:
                            if key not in metadata:
                                metadata[key] = []
                            metadata[key].append(value)
                        else:
                            metadata[key] = value
        
        return metadata
    
    def should_inject(self, script, url):
        """检查是否应该为当前URL注入脚本"""
        url_str = url.toString()
        
        # 检查排除规则
        for exclude_pattern in script.get('excludes', []):
            if self.pattern_matches(exclude_pattern, url_str):
                return False
        
        # 检查匹配规则
        matches = script.get('matches', [])
        if not matches:  # 如果没有匹配规则，注入所有页面
            return True
        
        for match_pattern in matches:
            if self.pattern_matches(match_pattern, url_str):
                return True
        
        return False
    
    def pattern_matches(self, pattern, url):
        """检查URL是否匹配模式"""
        try:
            # 将篡改猴模式转换为正则表达式
            regex_pattern = pattern
            
            # 转义正则表达式特殊字符，但保留通配符(*)
            regex_pattern = re.escape(regex_pattern)
            
            # 将转义后的通配符(*)恢复为正则表达式通配符(.*)
            regex_pattern = regex_pattern.replace(r'\*', '.*')
            
            # 匹配整个URL
            regex_pattern = f'^{regex_pattern}$'
            
            return bool(re.match(regex_pattern, url))
        except:
            return False
    
    def inject_to_page(self, page):
        """将脚本注入到页面"""
        current_url = page.url().toString()
        
        for script in self.scripts:
            if script['enabled'] and self.should_inject(script, page.url()):
                try:
                    # 创建脚本对象
                    script_obj = QWebEngineScript()
                    
                    # 设置脚本内容
                    script_obj.setSourceCode(script['content'])
                    
                    # 设置脚本在文档创建后运行
                    script_obj.setInjectionPoint(QWebEngineScript.DocumentCreation)
                    script_obj.setWorldId(QWebEngineScript.MainWorld)
                    script_obj.setRunsOnSubFrames(True)
                    
                    # 将脚本添加到页面
                    page.scripts().insert(script_obj)
                    
                    print(f"注入脚本 '{script['name']}' 到 {current_url}")
                except Exception as e:
                    print(f"注入脚本 '{script['name']}' 时出错: {e}")
    
    def get_script_list(self):
        """获取脚本列表"""
        return [script['name'] for script in self.scripts]
    
    def reload_scripts(self):
        """重新加载脚本"""
        self.load_scripts()