#!/usr/bin/env python3
"""生成抖音登录二维码并保存为图片"""
import json, os, time, base64
from pathlib import Path
from playwright.sync_api import sync_playwright

os.chdir(Path(__file__).parent)

print("="*50)
print("🎵 生成抖音登录二维码")
print("="*50)
print()

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
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
        print("🔍 提取二维码...")
        qr_data_url = None
        
        # 查找二维码图片
        img_elements = page.locator('img').all()
        for img in img_elements:
            try:
                src = img.get_attribute('src')
                if src and src.startswith('data:image') and ('qrcode' in src.lower() or 'qr' in src.lower()):
                    qr_data_url = src
                    print(f"✅ 找到二维码 (base64)")
                    break
            except:
                pass
        
        if not qr_data_url:
            # 尝试查找任何 data:image 的图片
            for img in img_elements:
                try:
                    src = img.get_attribute('src')
                    if src and src.startswith('data:image/png'):
                        qr_data_url = src
                        print(f"✅ 找到候选二维码图片")
                        break
                except:
                    pass
        
        if qr_data_url:
            # 保存 base64 图片
            qr_path = Path('douyin_login_qr.png')
            
            # 提取 base64 数据
            if ',' in qr_data_url:
                base64_data = qr_data_url.split(',')[1]
            else:
                base64_data = qr_data_url
            
            # 解码并保存
            img_data = base64.b64decode(base64_data)
            with open(qr_path, 'wb') as f:
                f.write(img_data)
            
            print(f"✅ 二维码已保存：{qr_path.absolute()}")
            print(f"📊 图片大小：{len(img_data)} 字节")
            print()
            print(f"📎 文件路径：{qr_path.absolute()}")
            
            # 返回文件路径供 QQ 发送
            print(str(qr_path.absolute()))
        else:
            print("❌ 未找到二维码")
        
        # 等待扫码
        print()
        print("⏳ 等待扫码（90 秒）...")
        for i in range(45):
            time.sleep(2)
            
            if 'creator.douyin.com' in page.url and 'login' not in page.url.lower():
                print("✅ 检测到登录！")
                break
        
        # 保存 Cookie
        cookies = context.cookies()
        if cookies:
            cookie_file = Path('assets/cookies.json')
            cookie_file.parent.mkdir(parents=True, exist_ok=True)
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            print(f"✅ Cookie 已保存：{cookie_file}")
        
        print()
        print("🎉 完成！")
        
    except Exception as e:
        print(f"❌ 错误：{e}")
    finally:
        browser.close()
