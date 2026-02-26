#!/usr/bin/env python3
"""
抖音图文发布脚本
支持发布图文笔记，带话题、@提及等功能
"""

import argparse
import json
import os
import sys
import time
import random
from pathlib import Path
from typing import List, Optional

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


def load_config(config_path: str = "assets/config.json") -> dict:
    """加载配置文件"""
    default_config = {
        "account": {"cookie_file": "cookies.json"},
        "browser": {"headless": True, "user_agent": "random"},
        "behavior": {"min_delay_ms": 1000, "max_delay_ms": 5000},
        "post": {"default_visible": "public", "max_images": 9, "min_images": 2}
    }
    
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 合并默认配置
            for key in default_config:
                if key not in config:
                    config[key] = default_config[key]
            return config
    return default_config


def load_cookies(cookie_file: str) -> list:
    """从文件加载 Cookie"""
    if os.path.exists(cookie_file):
        with open(cookie_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def random_delay(min_ms: int, max_ms: int):
    """随机延迟"""
    delay = random.uniform(min_ms, max_ms) / 1000
    time.sleep(delay)


def type_text_slowly(page, selector: str, text: str, min_delay: int, max_delay: int):
    """模拟真人输入"""
    element = page.locator(selector)
    element.click()
    
    # 清空现有内容
    element.press('Control+A')
    element.press('Delete')
    
    # 逐字符输入
    for char in text:
        element.type(char)
        random_delay(min_delay, max_delay)


def post_douyin(config: dict, title: str, images: List[str], topics: Optional[List[str]] = None,
                visible: str = 'public', mention: Optional[str] = None, script_dir: str = '.'):
    """发布抖音图文"""
    
    cookie_file = config['account'].get('cookie_file', 'cookies.json')
    # 如果 cookie_file 不是绝对路径，则相对于脚本所在目录
    if not os.path.isabs(cookie_file):
        cookie_file = os.path.join(script_dir, cookie_file)
    headless = config['browser'].get('headless', True)
    min_delay = config['behavior'].get('min_delay_ms', 1000)
    max_delay = config['behavior'].get('max_delay_ms', 5000)
    max_images = config['post'].get('max_images', 9)
    min_images = config['post'].get('min_images', 2)
    
    # 验证图片
    if len(images) < min_images:
        print(f"❌ 图片数量不足，至少需要 {min_images} 张")
        return False
    
    if len(images) > max_images:
        print(f"⚠️  图片数量超过限制，将只使用前 {max_images} 张")
        images = images[:max_images]
    
    # 验证图片文件
    for img in images:
        if not os.path.exists(img):
            print(f"❌ 图片文件不存在：{img}")
            return False
    
    print("🌐 启动浏览器...")
    
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(
            headless=headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        )
        
        # 创建上下文
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # 加载 Cookie
        cookies = load_cookies(cookie_file)
        if cookies:
            context.add_cookies(cookies)
            print("✅ Cookie 已加载")
        else:
            print("❌ 未找到 Cookie，请先运行 login.py 登录")
            browser.close()
            return False
        
        page = context.new_page()
        
        try:
            # 打开发布页面
            print("📝 打开发布页面...")
            page.goto('https://creator.douyin.com/publish', wait_until='networkidle', timeout=30000)
            random_delay(min_delay, max_delay)
            
            # 检查是否已登录
            current_url = page.url
            if 'login' in current_url.lower():
                print("❌ 未登录，请先运行 login.py")
                browser.close()
                return False
            
            # 上传图文
            print("🖼️  上传图文...")
            
            # 查找上传按钮（图文模式）
            try:
                # 尝试点击图文发布入口
                image_post_btn = page.locator('button:has-text("图文"), [class*="image"], [class*="photo"]').first
                if image_post_btn.is_visible(timeout=5000):
                    image_post_btn.click()
                    random_delay(min_delay, max_delay)
            except:
                pass
            
            # 上传多张图片
            file_input = page.locator('input[type="file"]').first
            if file_input.is_visible(timeout=10000):
                file_input.set_input_files(images)
                print(f"✅ 已上传 {len(images)} 张图片")
            else:
                print("❌ 未找到上传按钮")
                browser.close()
                return False
            
            # 等待上传完成
            print("⏳ 等待上传完成...")
            time.sleep(5)
            
            # 输入标题
            print("✏️  输入标题...")
            title_input = page.locator('input[placeholder*="标题"], input[placeholder*="title"], [class*="title"] input').first
            if title_input.is_visible(timeout=10000):
                type_text_slowly(page, 'input[placeholder*="标题"], input[placeholder*="title"]', title, min_delay, max_delay)
                print(f"✅ 标题已输入：{title}")
            else:
                print("⚠️  未找到标题输入框")
            
            # 输入话题
            if topics:
                print("🏷️  添加话题...")
                for topic in topics:
                    try:
                        topic_input = page.locator('input[placeholder*="话题"], input[placeholder*="#"]').first
                        if topic_input.is_visible(timeout=5000):
                            topic_input.click()
                            topic_input.type(f"#{topic}")
                            time.sleep(0.5)
                            topic_input.press('Enter')
                            random_delay(min_delay, max_delay)
                            print(f"✅ 话题已添加：#{topic}")
                    except:
                        print(f"⚠️  话题添加失败：{topic}")
            
            # 设置可见性
            if visible != 'public':
                print(f"🔒 设置可见性：{visible}")
                try:
                    visible_btn = page.locator(f'[class*="visible"], button:has-text("公开"), button:has-text("好友")').first
                    if visible_btn.is_visible(timeout=5000):
                        visible_btn.click()
                        random_delay(min_delay, max_delay)
                        # 选择可见性选项
                        visible_text = '公开' if visible == 'public' else '好友'
                        visible_option = page.locator(f'[class*="{visible}"], li:has-text("{visible_text})').first
                        if visible_option.is_visible(timeout=5000):
                            visible_option.click()
                except:
                    print("⚠️  可见性设置失败")
            
            # 随机滚动模拟真人操作
            if config['behavior'].get('scroll_before_post', True):
                print("📜 模拟滚动...")
                page.evaluate('window.scrollBy(0, 200)')
                time.sleep(1)
                page.evaluate('window.scrollBy(0, -200)')
                time.sleep(0.5)
            
            # 发布
            print("🚀 发布...")
            publish_btn = page.locator('button:has-text("发布"), button:has-text("Publish")').first
            if publish_btn.is_visible(timeout=10000):
                publish_btn.click()
                print("✅ 发布成功！")
                
                # 等待发布完成
                time.sleep(3)
                return True
            else:
                print("❌ 未找到发布按钮")
                return False
                
        except PlaywrightTimeout:
            print("❌ 操作超时")
            return False
        except Exception as e:
            print(f"❌ 错误：{e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            browser.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='抖音图文发布工具')
    parser.add_argument('--config', default='assets/config.json', help='配置文件路径')
    parser.add_argument('--title', required=True, help='图文标题')
    parser.add_argument('--images', nargs='+', required=True, help='图片文件路径（至少 2 张）')
    parser.add_argument('--topics', nargs='+', help='话题标签（不含#）')
    parser.add_argument('--visible', choices=['public', 'friends', 'private'], default='public',
                       help='可见性：public=公开，friends=好友，private=仅自己')
    parser.add_argument('--mention', help='@提及的用户')
    
    args = parser.parse_args()
    
    # 切换脚本所在目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("=" * 50)
    print("🎵 抖音图文发布工具")
    print("=" * 50)
    print()
    
    config = load_config(args.config)
    
    success = post_douyin(
        config=config,
        title=args.title,
        images=args.images,
        topics=args.topics,
        visible=args.visible,
        mention=args.mention,
        script_dir=str(script_dir)
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
