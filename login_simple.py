#!/usr/bin/env python3
"""抖音登录 - 简化版"""
import json, os, time
from pathlib import Path
from playwright.sync_api import sync_playwright

os.chdir(Path(__file__).parent)
cookie_file = 'assets/cookies.json'

print("="*50)
print("🎵 抖音登录 - 请扫码")
print("="*50)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--no-sandbox', '--disable-gpu'])
    context = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = context.new_page()
    
    print("🌐 打开抖音...")
    page.goto('https://creator.douyin.com/', timeout=60000)
    time.sleep(5)
    
    print("📱 请在弹出的窗口中扫码登录")
    print("⏳ 等待 60 秒...")
    
    for i in range(30):
        time.sleep(2)
        if 'login' not in page.url.lower() and 'creator.douyin.com' in page.url:
            print("✅ 登录成功！")
            cookies = context.cookies()
            if cookies:
                os.makedirs('assets', exist_ok=True)
                with open(cookie_file, 'w') as f:
                    json.dump(cookies, f, indent=2)
                print(f"✅ Cookie 已保存：{cookie_file}")
            break
    
    time.sleep(3)
    browser.close()
    print("🎉 完成！")
