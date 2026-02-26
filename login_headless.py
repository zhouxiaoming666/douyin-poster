#!/usr/bin/env python3
"""抖音登录 - 无头模式，提取二维码 URL"""
import json, os, time, re
from pathlib import Path
from playwright.sync_api import sync_playwright

os.chdir(Path(__file__).parent)

print("="*50)
print("🎵 抖音扫码登录")
print("="*50)
print()

cookie_file = Path('assets/cookies.json')
if cookie_file.exists():
    cookie_file.unlink()
    print("🗑️  已删除旧 Cookie")

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,  # 无头模式
        args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']
    )
    
    context = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = context.new_page()
    
    try:
        print("🌐 打开抖音创作者平台...")
        page.goto('https://creator.douyin.com/', wait_until='domcontentloaded', timeout=60000)
        time.sleep(5)
        
        # 点击登录
        print("🔘 查找登录入口...")
        try:
            login_btn = page.locator('button:has-text("登录"), a:has-text("登录")').first
            if login_btn.is_visible(timeout=5000):
                login_btn.click()
                print("✅ 已点击登录")
                time.sleep(3)
        except:
            pass
        
        # 等待二维码
        print("📱 等待二维码...")
        time.sleep(5)
        
        # 获取二维码图片的 src
        print("🔍 提取二维码 URL...")
        qr_urls = []
        
        # 方法 1: 查找二维码图片
        img_elements = page.locator('img').all()
        for img in img_elements:
            try:
                src = img.get_attribute('src')
                if src and ('qrcode' in src.lower() or 'qr' in src.lower()):
                    qr_urls.append(src)
                    print(f"✅ 找到二维码 URL: {src[:100]}...")
            except:
                pass
        
        # 方法 2: 查找二维码 canvas
        if not qr_urls:
            canvas = page.locator('canvas').first
            if canvas.is_visible(timeout=5000):
                print("✅ 找到二维码 canvas")
                # canvas 需要截图，但我们用另一个方法
        
        # 方法 3: 从网络请求中获取
        if not qr_urls:
            print("⏳ 监听网络请求...")
            # 检查页面源码
            content = page.content()
            qr_matches = re.findall(r'(https?://[^\s"\']+qrcode[^\s"\']+)', content, re.IGNORECASE)
            if qr_matches:
                qr_urls = qr_matches[:5]
                print(f"✅ 从源码找到 {len(qr_urls)} 个二维码链接")
        
        if qr_urls:
            print()
            print("="*50)
            print("📱 二维码 URL 已提取:")
            for i, url in enumerate(qr_urls[:3], 1):
                print(f"{i}. {url}")
            print()
            print("⚠️  由于服务器限制，无法直接显示图片")
            print("   请在浏览器中打开上述 URL 查看二维码")
            print("="*50)
        else:
            print("⚠️  未找到二维码 URL")
            print("   可能需要手动查看浏览器窗口")
        
        # 等待登录
        print()
        print("⏳ 等待扫码登录（90 秒）...")
        logged_in = False
        
        for i in range(45):
            time.sleep(2)
            
            if 'creator.douyin.com' in page.url and 'login' not in page.url.lower():
                print("✅ 检测到登录！")
                logged_in = True
                break
        
        if not logged_in:
            # 检查 Cookie 变化
            cookies = context.cookies()
            auth_cookies = [c for c in cookies if 'session' in c['name'].lower() or 'passport' in c['name'].lower() or 'token' in c['name'].lower()]
            if len(auth_cookies) > 2:
                print("✅ 检测到认证 Cookie！")
                logged_in = True
        
        # 保存 Cookie
        cookies = context.cookies()
        if cookies:
            cookie_file.parent.mkdir(parents=True, exist_ok=True)
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            print(f"✅ Cookie 已保存：{cookie_file}")
            print(f"📊 共 {len(cookies)} 个 Cookie")
        
        print()
        print("🎉 完成！")
        
    except Exception as e:
        print(f"❌ 错误：{e}")
    finally:
        browser.close()
