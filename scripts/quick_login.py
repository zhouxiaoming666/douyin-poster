#!/usr/bin/env python3
"""
抖音快速登录 - 生成登录链接，用户手机扫码
"""

import json
import os
import time
import qrcode
from pathlib import Path
from playwright.sync_api import sync_playwright


def main():
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("=" * 50)
    print("🎵 抖音快速登录")
    print("=" * 50)
    print()
    print("📱 请在 60 秒内完成扫码...")
    print()
    
    cookie_file = script_dir.parent / 'assets' / 'cookies.json'
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']
        )
        
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = context.new_page()
        
        try:
            print("🌐 访问抖音创作者平台...")
            page.goto('https://creator.douyin.com/', wait_until='domcontentloaded', timeout=60000)
            time.sleep(3)
            
            # 尝试点击登录
            try:
                login_btn = page.locator('button:has-text("登录"), a:has-text("登录")').first
                if login_btn.is_visible(timeout=5000):
                    print("🔘 点击登录...")
                    login_btn.click()
                    time.sleep(2)
            except:
                pass
            
            # 等待二维码出现
            print("⏳ 等待二维码...")
            time.sleep(3)
            
            # 获取二维码图片
            qr_img = page.locator('img[src*="qrcode"], .qrcode img').first
            if qr_img.is_visible(timeout=10000):
                qr_src = qr_img.get_attribute('src')
                print(f"✅ 二维码已加载")
                
                # 保存二维码图片
                qr_path = script_dir / 'qr_code.png'
                qr_img.screenshot(path=str(qr_path))
                print(f"✅ 二维码已保存：{qr_path}")
                print()
                print(f"📱 二维码文件位置：{qr_path}")
                print("   请查看此文件并扫码登录")
                print()
            else:
                print("⚠️  未检测到二维码，可能已自动显示登录入口")
            
            # 等待登录
            print("⏳ 等待登录确认（60 秒）...")
            max_wait = 60
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                time.sleep(2)
                
                current_url = page.url
                if 'creator.douyin.com' in current_url and 'login' not in current_url.lower():
                    try:
                        # 检查是否有用户信息
                        user_info = page.locator('.user-info, [class*="user-name"]').first
                        if user_info.is_visible(timeout=2000):
                            print("✅ 登录成功！")
                            break
                    except:
                        pass
                
                if '/dashboard' in current_url or '/publish' in current_url:
                    print("✅ 登录成功！")
                    break
            
            # 保存 Cookie
            cookies = context.cookies()
            if cookies:
                cookie_file.parent.mkdir(parents=True, exist_ok=True)
                with open(cookie_file, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, indent=2, ensure_ascii=False)
                print(f"✅ Cookie 已保存：{cookie_file}")
                print()
                print("🎉 登录完成！现在可以发布图文了")
            else:
                print("❌ 未获取到 Cookie，请重试")
                
        except Exception as e:
            print(f"❌ 错误：{e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == '__main__':
    main()
