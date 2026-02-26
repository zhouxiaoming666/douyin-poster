#!/usr/bin/env python3
"""抖音扫码登录 - 生成二维码图片"""
import json, os, time, base64
from pathlib import Path
from playwright.sync_api import sync_playwright

os.chdir(Path(__file__).parent)

print("="*50)
print("🎵 抖音扫码登录")
print("="*50)
print()

# 删除旧 Cookie
cookie_file = Path('assets/cookies.json')
if cookie_file.exists():
    cookie_file.unlink()
    print("🗑️  已删除旧 Cookie")

with sync_playwright() as p:
    # 启动浏览器（不 headless，方便调试）
    browser = p.chromium.launch(
        headless=False,
        args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage', '--start-maximized']
    )
    
    context = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = context.new_page()
    
    try:
        print("🌐 打开抖音创作者平台...")
        page.goto('https://creator.douyin.com/', wait_until='domcontentloaded', timeout=60000)
        time.sleep(5)
        
        # 尝试点击登录按钮
        print("🔘 查找登录入口...")
        try:
            login_btn = page.locator('button:has-text("登录"), a:has-text("登录"), [class*="login"]').first
            if login_btn.is_visible(timeout=5000):
                login_btn.click()
                print("✅ 已点击登录按钮")
                time.sleep(3)
        except Exception as e:
            print(f"⚠️  登录按钮未找到：{e}")
        
        # 等待二维码
        print("📱 等待二维码出现...")
        time.sleep(3)
        
        # 截图保存
        qr_path = Path('qr_login.png')
        page.screenshot(path=str(qr_path), full_page=True)
        print(f"✅ 截图已保存：{qr_path.absolute()}")
        print()
        print(f"📎 文件路径：{qr_path.absolute()}")
        print("   请查看此图片中的二维码并扫码")
        print()
        
        # 等待登录
        print("⏳ 等待扫码登录（90 秒）...")
        for i in range(45):
            time.sleep(2)
            
            # 检查 URL 变化
            if 'creator.douyin.com' in page.url and 'login' not in page.url.lower():
                print("✅ 检测到登录成功！")
                break
            
            # 检查用户元素
            try:
                user_elem = page.locator('[class*="user"], [class*="avatar"]').first
                if user_elem.is_visible(timeout=1000):
                    print("✅ 检测到用户信息！")
                    break
            except:
                pass
        
        # 保存 Cookie
        cookies = context.cookies()
        if cookies:
            cookie_file.parent.mkdir(parents=True, exist_ok=True)
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            print(f"✅ Cookie 已保存：{cookie_file}")
            print(f"📊 共 {len(cookies)} 个 Cookie")
        else:
            print("❌ 未获取到 Cookie")
        
        print()
        print("🎉 完成！")
        
    except Exception as e:
        print(f"❌ 错误：{e}")
        import traceback
        traceback.print_exc()
    finally:
        time.sleep(5)
        browser.close()
