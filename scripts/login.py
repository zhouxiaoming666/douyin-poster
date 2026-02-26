#!/usr/bin/env python3
"""
抖音扫码登录脚本
首次使用需要手机抖音扫码登录
登录成功后 Cookie 会自动保存
"""

import json
import os
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


def load_config(config_path: str = "assets/config.json") -> dict:
    """加载配置文件"""
    default_config = {
        "account": {"cookie_file": "cookies.json"},
        "browser": {"headless": False, "user_agent": "random"}
    }
    
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default_config


def save_cookies(cookies: list, cookie_file: str):
    """保存 Cookie 到文件"""
    with open(cookie_file, 'w', encoding='utf-8') as f:
        json.dump(cookies, f, indent=2)
    print(f"✅ Cookie 已保存：{cookie_file}")


def load_cookies(cookie_file: str) -> list:
    """从文件加载 Cookie"""
    if os.path.exists(cookie_file):
        with open(cookie_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def login(config: dict):
    """执行扫码登录"""
    cookie_file = config['account'].get('cookie_file', 'cookies.json')
    headless = config['browser'].get('headless', False)
    
    # 检查已有 Cookie
    if load_cookies(cookie_file):
        print("⚠️  检测到已有 Cookie，是否重新登录？(y/n): ", end='')
        if input().strip().lower() != 'y':
            print("✅ 使用已有 Cookie")
            return
    
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
        
        page = context.new_page()
        
        try:
            print("📱 打开抖音登录页面...")
            page.goto('https://creator.douyin.com/', wait_until='networkidle', timeout=30000)
            
            # 等待登录按钮
            print("⏳ 等待登录入口...")
            time.sleep(2)
            
            # 尝试点击登录按钮（如果有）
            try:
                login_btn = page.locator('button:has-text("登录"), a:has-text("登录"), .login-btn').first
                if login_btn.is_visible(timeout=5000):
                    login_btn.click()
                    time.sleep(1)
            except:
                pass
            
            # 查找二维码
            print("📱 请用手机抖音扫码登录...")
            
            # 等待二维码出现
            qr_code = page.locator('img[src*="qrcode"], .qrcode img, [class*="qrcode"] img').first
            
            try:
                if qr_code.is_visible(timeout=10000):
                    print("✅ 二维码已显示，请扫码！")
            except:
                print("⚠️  未检测到二维码，页面可能已自动显示登录入口")
            
            # 等待登录成功（检测 Cookie 变化或页面跳转）
            print("⏳ 等待登录确认...")
            
            # 轮询检查登录状态
            max_wait = 120  # 最多等待 120 秒
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                time.sleep(2)
                
                # 检查是否已登录（通过检查特定元素或 URL 变化）
                current_url = page.url
                if 'creator.douyin.com' in current_url and 'login' not in current_url.lower():
                    # 尝试检测用户头像或其他登录后的元素
                    try:
                        user_avatar = page.locator('img[alt*="头像"], .avatar img, [class*="avatar"] img').first
                        if user_avatar.is_visible(timeout=3000):
                            print("✅ 登录成功！")
                            break
                    except:
                        pass
                
                # 检查是否有登录后的特征 URL
                if '/dashboard' in current_url or '/publish' in current_url:
                    print("✅ 登录成功！")
                    break
            
            # 保存 Cookie
            cookies = context.cookies()
            if cookies:
                save_cookies(cookies, cookie_file)
                print("🎉 登录完成！现在可以发布图文了。")
            else:
                print("❌ 未获取到 Cookie，请重试")
                
        except PlaywrightTimeout:
            print("❌ 操作超时，请重试")
        except Exception as e:
            print(f"❌ 错误：{e}")
        finally:
            browser.close()


def main():
    """主函数"""
    # 切换脚本所在目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("=" * 50)
    print("🎵 抖音扫码登录工具")
    print("=" * 50)
    print()
    
    config = load_config()
    login(config)


if __name__ == '__main__':
    main()
