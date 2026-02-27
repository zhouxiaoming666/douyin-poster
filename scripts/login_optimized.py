#!/usr/bin/env python3
"""
抖音扫码登录脚本 - 优化版
支持无头模式、自动截图、QQ 发送二维码
"""

import json
import os
import sys
import time
import base64
from pathlib import Path
from datetime import datetime

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


DEFAULT_CONFIG = {
    "account": {"cookie_file": "cookies.json"},
    "browser": {
        "headless": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    },
    "login": {
        "timeout_seconds": 180,
        "check_interval_seconds": 3,
        "auto_save_cookies": True,
        "screenshot_qr": True
    },
    "anti_detect": {
        "enable": True,
        "hide_webdriver": True
    }
}


def load_config(config_path: str = "assets/config.json") -> dict:
    """加载配置文件"""
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 合并默认配置
            for key in DEFAULT_CONFIG:
                if key not in config:
                    config[key] = DEFAULT_CONFIG[key]
                elif isinstance(DEFAULT_CONFIG[key], dict):
                    for sub_key in DEFAULT_CONFIG[key]:
                        if sub_key not in config[key]:
                            config[key][sub_key] = DEFAULT_CONFIG[key][sub_key]
            return config
    return DEFAULT_CONFIG


def save_cookies(cookies: list, cookie_file: str):
    """保存 Cookie 到文件"""
    os.makedirs(os.path.dirname(cookie_file) if os.path.dirname(cookie_file) else '.', exist_ok=True)
    with open(cookie_file, 'w', encoding='utf-8') as f:
        json.dump(cookies, f, indent=2, ensure_ascii=False)
    print(f"✅ Cookie 已保存：{cookie_file}")


def load_cookies(cookie_file: str) -> list:
    """从文件加载 Cookie"""
    if os.path.exists(cookie_file):
        with open(cookie_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def image_to_base64(image_path: str) -> str:
    """图片转 Base64"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def get_timestamp() -> str:
    """获取时间戳字符串"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def login(config: dict, script_dir: str = '.'):
    """执行扫码登录（优化版）"""
    cookie_file = config['account'].get('cookie_file', 'cookies.json')
    if not os.path.isabs(cookie_file):
        cookie_file = os.path.join(script_dir, '..', cookie_file)
    
    headless = config['browser'].get('headless', True)
    timeout_seconds = config['login'].get('timeout_seconds', 180)
    check_interval = config['login'].get('check_interval_seconds', 3)
    screenshot_qr = config['login'].get('screenshot_qr', True)
    
    # 检查已有 Cookie
    existing_cookies = load_cookies(cookie_file)
    if existing_cookies:
        print("⚠️  检测到已有 Cookie")
        print(f"   文件：{cookie_file}")
        print(f"   数量：{len(existing_cookies)}")
        print("\n是否重新登录？(y/n): ", end='', flush=True)
        try:
            response = input().strip().lower()
            if response != 'y':
                print("✅ 使用已有 Cookie")
                return True
        except:
            print("\n✅ 使用已有 Cookie")
            return True
    
    print("🌐 启动浏览器...")
    
    with sync_playwright() as p:
        # 启动浏览器
        browser_args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu',
            '--window-size=1920,1080'
        ]
        
        # 反检测
        if config['anti_detect'].get('enable', True):
            browser_args.append('--disable-blink-features=AutomationControlled')
        
        browser = p.chromium.launch(headless=headless, args=browser_args)
        
        # 创建上下文
        context_options = {
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': config['browser'].get('user_agent'),
            'locale': 'zh-CN',
            'timezone_id': 'Asia/Shanghai'
        }
        
        context = browser.new_context(**context_options)
        
        # 隐藏 webdriver
        if config['anti_detect'].get('hide_webdriver', True):
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
        
        page = context.new_page()
        
        try:
            print("📱 打开抖音创作者平台...")
            page.goto('https://creator.douyin.com/', wait_until='networkidle', timeout=30000)
            
            # 等待登录入口
            print("⏳ 等待登录入口...")
            time.sleep(3)
            
            # 尝试点击登录按钮
            try:
                login_btn = page.locator('button:has-text("登录"), a:has-text("登录"), .login-btn, [class*="login-btn"]').first
                if login_btn.is_visible(timeout=5000):
                    print("✓ 点击登录按钮")
                    login_btn.click()
                    time.sleep(2)
            except Exception as e:
                print(f"⚠️  未找到登录按钮或已在登录页")
            
            # 查找二维码
            print("📱 准备二维码...")
            qr_dir = os.path.join(script_dir, '..', 'qrcode')
            os.makedirs(qr_dir, exist_ok=True)
            qr_path = os.path.join(qr_dir, f"login_qr_{get_timestamp()}.png")
            
            # 等待二维码出现
            qr_selectors = [
                'img[src*="qrcode"], .qrcode img, [class*="qrcode"] img',
                'canvas',
                'img[src*="login"]'
            ]
            
            qr_element = None
            for selector in qr_selectors:
                try:
                    qr_element = page.locator(selector).first
                    if qr_element.is_visible(timeout=5000):
                        print(f"✓ 找到二维码：{selector}")
                        break
                except:
                    continue
            
            # 截图
            if screenshot_qr:
                print("📸 截取二维码...")
                page.screenshot(path=qr_path, full_page=True)
                print(f"✅ 二维码已保存：{qr_path}")
                
                # 尝试截取二维码元素
                if qr_element:
                    try:
                        qr_element_path = os.path.join(qr_dir, f"login_qr_code_{get_timestamp()}.png")
                        qr_element.screenshot(path=qr_element_path)
                        print(f"✅ 二维码特写：{qr_element_path}")
                    except:
                        pass
            
            print(f"\n{'='*60}")
            print("📱 请用手机抖音扫码登录")
            print(f"⏰ 有效期：{timeout_seconds}秒")
            print(f"📁 二维码：{qr_path}")
            print(f"{'='*60}\n")
            
            # 等待登录
            print("⏳ 等待登录确认...")
            start_time = time.time()
            logged_in = False
            
            while time.time() - start_time < timeout_seconds:
                time.sleep(check_interval)
                
                # 检查登录状态
                current_url = page.url
                
                # 登录成功标志
                success_indicators = [
                    lambda: page.locator('img[alt*="头像"], .avatar img, [class*="avatar"] img').first.is_visible(timeout=2000),
                    lambda: '/dashboard' in current_url or '/publish' in current_url,
                    lambda: 'creator.douyin.com' in current_url and 'login' not in current_url.lower()
                ]
                
                try:
                    for indicator in success_indicators:
                        if indicator():
                            print("✅ 登录成功！")
                            logged_in = True
                            break
                    if logged_in:
                        break
                except:
                    continue
            
            if not logged_in:
                print(f"❌ 等待超时（{timeout_seconds}秒）")
                browser.close()
                return False
            
            # 保存 Cookie
            cookies = context.cookies()
            if cookies and config['login'].get('auto_save_cookies', True):
                save_cookies(cookies, cookie_file)
                print("🎉 登录完成！现在可以发布图文了。")
                return True
            else:
                print("❌ 未获取到 Cookie，请重试")
                browser.close()
                return False
                
        except PlaywrightTimeout as e:
            print(f"❌ 操作超时：{e}")
            browser.close()
            return False
            
        except Exception as e:
            print(f"❌ 错误：{e}")
            import traceback
            traceback.print_exc()
            browser.close()
            return False
        
        finally:
            try:
                browser.close()
            except:
                pass


def main():
    """主函数"""
    # 切换脚本所在目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("=" * 60)
    print("🎵 抖音扫码登录工具 - 优化版")
    print(f"📅 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    config = load_config()
    
    # 支持命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='抖音扫码登录')
    parser.add_argument('--headless', action='store_true', help='无头模式')
    parser.add_argument('--debug', action='store_true', help='调试模式（有头）')
    parser.add_argument('--timeout', type=int, default=180, help='超时时间（秒）')
    args = parser.parse_args()
    
    # 覆盖配置
    if args.debug:
        config['browser']['headless'] = False
    elif args.headless:
        config['browser']['headless'] = True
    
    if args.timeout:
        config['login']['timeout_seconds'] = args.timeout
    
    success = login(config, script_dir=str(script_dir))
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 登录成功！")
    else:
        print("❌ 登录失败")
    print("=" * 60)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
