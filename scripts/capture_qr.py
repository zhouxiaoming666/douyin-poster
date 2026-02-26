#!/usr/bin/env python3
"""
抖音登录二维码捕获脚本
启动浏览器，打开登录页面，截图二维码
"""

import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("=" * 50)
    print("🎵 抖音登录二维码捕获")
    print("=" * 50)
    print()
    
    with sync_playwright() as p:
        # 启动浏览器（不 headless）
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--start-maximized'
            ]
        )
        
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = context.new_page()
        
        try:
            print("📱 打开抖音登录页面...")
            page.goto('https://creator.douyin.com/', wait_until='networkidle', timeout=30000)
            
            time.sleep(3)
            
            # 截图
            print("📸 截图保存...")
            screenshot_path = script_dir / 'login_qr.png'
            page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"✅ 截图已保存：{screenshot_path}")
            
            # 尝试点击登录按钮
            try:
                login_btn = page.locator('button:has-text("登录"), a:has-text("登录")').first
                if login_btn.is_visible(timeout=5000):
                    print("🔘 点击登录按钮...")
                    login_btn.click()
                    time.sleep(2)
                    
                    # 再次截图
                    page.screenshot(path=str(screenshot_path), full_page=True)
                    print(f"✅ 更新截图：{screenshot_path}")
            except Exception as e:
                print(f"⚠️  未找到登录按钮：{e}")
            
            print()
            print("=" * 50)
            print("📱 请查看截图文件：login_qr.png")
            print("⏳ 等待 60 秒供您扫码...")
            print("=" * 50)
            
            # 等待扫码
            max_wait = 60
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                time.sleep(2)
                
                # 检查登录状态
                current_url = page.url
                if 'login' not in current_url.lower() and 'creator.douyin.com' in current_url:
                    print("✅ 检测到登录成功！")
                    
                    # 保存 Cookie
                    cookies = context.cookies()
                    if cookies:
                        cookie_file = script_dir.parent / 'assets' / 'cookies.json'
                        with open(cookie_file, 'w', encoding='utf-8') as f:
                            json.dump(cookies, f, indent=2, ensure_ascii=False)
                        print(f"✅ Cookie 已保存：{cookie_file}")
                    break
            
            print()
            print("🎉 完成！")
            
        except Exception as e:
            print(f"❌ 错误：{e}")
            import traceback
            traceback.print_exc()
        finally:
            time.sleep(3)
            browser.close()


if __name__ == '__main__':
    main()
