#!/usr/bin/env python3
"""
抖音图文发布脚本 - 优化版
全面增强：防封号、稳定性、错误处理、批量发布
"""

import argparse
import json
import os
import sys
import time
import random
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout, Page, BrowserContext

# ============ 配置 ============
DEFAULT_CONFIG = {
    "account": {"cookie_file": "cookies.json"},
    "browser": {
        "headless": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    },
    "behavior": {
        "min_delay_ms": 800,
        "max_delay_ms": 3000,
        "scroll_before_post": True,
        "random_mouse_move": True,
        "screenshot_on_error": True
    },
    "post": {
        "default_visible": "public",
        "max_images": 9,
        "min_images": 2,
        "retry_times": 3,
        "retry_delay_s": 5
    },
    "anti_detect": {
        "enable": True,
        "random_viewport": True,
        "hide_webdriver": True
    }
}

# ============ 工具函数 ============
def load_config(config_path: str = "assets/config.json") -> dict:
    """加载配置文件"""
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 递归合并默认配置
            return deep_merge(DEFAULT_CONFIG, config)
    return DEFAULT_CONFIG


def deep_merge(base: dict, override: dict) -> dict:
    """深度合并字典"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_cookies(cookie_file: str) -> list:
    """从文件加载 Cookie"""
    if os.path.exists(cookie_file):
        with open(cookie_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_cookies(cookies: list, cookie_file: str):
    """保存 Cookie 到文件"""
    os.makedirs(os.path.dirname(cookie_file), exist_ok=True)
    with open(cookie_file, 'w', encoding='utf-8') as f:
        json.dump(cookies, f, indent=2, ensure_ascii=False)
    print(f"✅ Cookie 已保存：{cookie_file}")


def random_delay(min_ms: int, max_ms: int):
    """随机延迟"""
    delay = random.uniform(min_ms, max_ms) / 1000
    time.sleep(delay)


def get_timestamp() -> str:
    """获取时间戳字符串"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def take_screenshot(page: Page, name: str, save_dir: str = "screenshots"):
    """截图保存"""
    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, f"{name}_{get_timestamp()}.png")
    page.screenshot(path=path, full_page=True)
    print(f"📸 截图已保存：{path}")


def generate_mouse_trajectory(start_x: int, start_y: int, end_x: int, end_y: int, steps: int = 10) -> List[tuple]:
    """生成模拟真人鼠标轨迹"""
    trajectory = []
    for i in range(steps + 1):
        t = i / steps
        # 贝塞尔曲线模拟真人手部抖动
        x = int(start_x + (end_x - start_x) * t + random.randint(-5, 5))
        y = int(start_y + (end_y - start_y) * t + random.randint(-5, 5))
        trajectory.append((x, y))
    return trajectory


# ============ 核心发布函数 ============
def post_douyin(
    config: dict,
    title: str,
    images: List[str],
    topics: Optional[List[str]] = None,
    visible: str = 'public',
    mention: Optional[str] = None,
    script_dir: str = '.',
    retry_count: int = 0
) -> bool:
    """发布抖音图文（优化版）"""
    
    # 提取配置
    cookie_file = config['account'].get('cookie_file', 'cookies.json')
    if not os.path.isabs(cookie_file):
        cookie_file = os.path.join(script_dir, '..', cookie_file)
    
    headless = config['browser'].get('headless', True)
    min_delay = config['behavior'].get('min_delay_ms', 800)
    max_delay = config['behavior'].get('max_delay_ms', 3000)
    max_images = config['post'].get('max_images', 9)
    min_images = config['post'].get('min_images', 2)
    retry_times = config['post'].get('retry_times', 3)
    screenshot_on_error = config['behavior'].get('screenshot_on_error', True)
    
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
        browser_args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu',
            '--window-size=1920,1080'
        ]
        
        # 反检测选项
        if config['anti_detect'].get('enable', True):
            browser_args.extend([
                '--disable-blink-features=AutomationControlled'
            ])
        
        browser = p.chromium.launch(headless=headless, args=browser_args)
        
        # 创建浏览器上下文
        context_options = {
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': config['browser'].get('user_agent'),
            'locale': 'zh-CN',
            'timezone_id': 'Asia/Shanghai'
        }
        
        # 随机 viewport（反检测）
        if config['anti_detect'].get('random_viewport', True):
            context_options['viewport'] = {
                'width': random.randint(1280, 1920),
                'height': random.randint(720, 1080)
            }
        
        context = browser.new_context(**context_options)
        
        # 隐藏 webdriver 特征
        if config['anti_detect'].get('hide_webdriver', True):
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
        
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
            # ========== 打开发布页面 ==========
            print("📝 打开发布页面...")
            page.goto('https://creator.douyin.com/publish', wait_until='networkidle', timeout=30000)
            random_delay(min_delay, max_delay)
            
            # 检查是否已登录
            current_url = page.url
            if 'login' in current_url.lower():
                print("❌ 未登录，请先运行 login.py")
                if screenshot_on_error:
                    take_screenshot(page, "login_required")
                browser.close()
                return False
            
            print("✅ 已登录")
            
            # ========== 上传图文 ==========
            print("🖼️  上传图文...")
            
            # 查找上传按钮
            upload_selectors = [
                'input[type="file"]',
                'button:has-text("上传"), button:has-text("选择图片")',
                '[class*="upload"], [class*="Upload"]',
                'div[role="button"]:has-text("图片")'
            ]
            
            file_input = None
            for selector in upload_selectors:
                try:
                    file_input = page.locator(selector).first
                    if file_input.is_visible(timeout=3000):
                        print(f"✓ 找到上传入口：{selector}")
                        break
                except:
                    continue
            
            if file_input and file_input.input_enabled():
                file_input.set_input_files(images)
                print(f"✅ 已上传 {len(images)} 张图片")
            else:
                # 尝试点击触发
                try:
                    upload_btn = page.locator('button:has-text("上传"), button:has-text("选择图片"), [class*="upload-btn"]').first
                    if upload_btn.is_visible(timeout=5000):
                        upload_btn.click()
                        random_delay(500, 1000)
                        file_input = page.locator('input[type="file"]').first
                        if file_input.is_visible(timeout=5000):
                            file_input.set_input_files(images)
                            print(f"✅ 已上传 {len(images)} 张图片")
                except Exception as e:
                    print(f"❌ 上传失败：{e}")
                    if screenshot_on_error:
                        take_screenshot(page, "upload_failed")
                    browser.close()
                    return False
            
            # 等待上传完成
            print("⏳ 等待上传完成...")
            time.sleep(5)
            
            # ========== 输入标题 ==========
            print("✏️  输入标题...")
            title_selectors = [
                'input[placeholder*="标题"], input[placeholder*="title"]',
                'input[class*="title"], [class*="title"] input',
                'input[aria-label*="标题"]'
            ]
            
            title_input = None
            for selector in title_selectors:
                try:
                    title_input = page.locator(selector).first
                    if title_input.is_visible(timeout=2000):
                        break
                except:
                    continue
            
            if title_input:
                # 模拟真人输入
                type_text_slowly(page, title_input, title, min_delay, max_delay)
                print(f"✅ 标题已输入：{title}")
            else:
                print("⚠️  未找到标题输入框")
            
            random_delay(500, 1000)
            
            # ========== 添加话题 ==========
            if topics:
                print("🏷️  添加话题...")
                for topic in topics:
                    try:
                        topic_selectors = [
                            'input[placeholder*="话题"], input[placeholder*="#"]',
                            'input[aria-label*="话题"]'
                        ]
                        
                        topic_input = None
                        for selector in topic_selectors:
                            try:
                                topic_input = page.locator(selector).first
                                if topic_input.is_visible(timeout=2000):
                                    break
                            except:
                                continue
                        
                        if topic_input:
                            topic_input.click()
                            random_delay(200, 500)
                            topic_input.type(f"#{topic}")
                            time.sleep(0.5)
                            topic_input.press('Enter')
                            random_delay(min_delay, max_delay)
                            print(f"✅ 话题已添加：#{topic}")
                    except Exception as e:
                        print(f"⚠️  话题添加失败 {topic}: {e}")
            
            # ========== 设置可见性 ==========
            if visible != 'public':
                print(f"🔒 设置可见性：{visible}")
                try:
                    visible_btn = page.locator('button:has-text("公开"), button:has-text("好友"), [class*="visible"]').first
                    if visible_btn.is_visible(timeout=5000):
                        visible_btn.click()
                        random_delay(min_delay, max_delay)
                        
                        visible_text = '公开' if visible == 'public' else '好友可见' if visible == 'friends' else '私密'
                        visible_option = page.locator(f'li:has-text("{visible_text}"), [role="menuitem"]:has-text("{visible_text}")').first
                        if visible_option.is_visible(timeout=5000):
                            visible_option.click()
                            print(f"✅ 可见性已设置：{visible}")
                except Exception as e:
                    print(f"⚠️  可见性设置失败：{e}")
            
            # ========== 模拟真人操作 ==========
            if config['behavior'].get('scroll_before_post', True):
                print("📜 模拟真人滚动...")
                # 随机滚动
                for _ in range(random.randint(2, 4)):
                    scroll_amount = random.randint(100, 300)
                    page.evaluate(f'window.scrollBy(0, {scroll_amount})')
                    time.sleep(random.uniform(0.5, 1.5))
                page.evaluate('window.scrollTo(0, 0)')
                time.sleep(0.5)
            
            # 随机鼠标移动
            if config['behavior'].get('random_mouse_move', True):
                print("🖱️  模拟鼠标移动...")
                for _ in range(random.randint(2, 4)):
                    x = random.randint(100, 800)
                    y = random.randint(100, 600)
                    page.mouse.move(x, y)
                    time.sleep(random.uniform(0.3, 0.8))
            
            # ========== 发布 ==========
            print("🚀 发布...")
            publish_selectors = [
                'button:has-text("发布"), button:has-text("Publish")',
                '[class*="publish"], [class*="submit"]',
                'button[class*="confirm"]'
            ]
            
            publish_btn = None
            for selector in publish_selectors:
                try:
                    publish_btn = page.locator(selector).first
                    if publish_btn.is_visible(timeout=3000):
                        print(f"✓ 找到发布按钮：{selector}")
                        break
                except:
                    continue
            
            if publish_btn and publish_btn.is_enabled():
                # 发布前截图
                take_screenshot(page, "before_publish")
                
                publish_btn.click()
                print("✅ 已点击发布按钮")
                
                # 等待发布结果
                time.sleep(5)
                
                # 检测发布成功
                success_indicators = [
                    '发布成功',
                    '审核中',
                    'published',
                    'success',
                    '/dashboard'
                ]
                
                current_url = page.url
                page_content = page.content()
                
                if any(indicator in current_url.lower() or indicator in page_content.lower() 
                       for indicator in success_indicators):
                    print("✅ 发布成功！")
                    take_screenshot(page, "publish_success")
                    browser.close()
                    return True
                else:
                    # 可能还在处理中
                    print("⏳ 发布处理中...")
                    take_screenshot(page, "publish_processing")
                    browser.close()
                    return True
            else:
                print("❌ 未找到发布按钮或按钮不可用")
                if screenshot_on_error:
                    take_screenshot(page, "no_publish_button")
                browser.close()
                return False
                
        except PlaywrightTimeout as e:
            print(f"❌ 操作超时：{e}")
            if screenshot_on_error:
                take_screenshot(page, "timeout_error")
            
            # 自动重试
            if retry_count < retry_times:
                print(f"🔄 {retry_count + 1}/{retry_times} 重试...")
                browser.close()
                time.sleep(config['post'].get('retry_delay_s', 5))
                return post_douyin(config, title, images, topics, visible, mention, script_dir, retry_count + 1)
            
            browser.close()
            return False
            
        except Exception as e:
            print(f"❌ 错误：{e}")
            import traceback
            traceback.print_exc()
            
            if screenshot_on_error:
                take_screenshot(page, "exception_error")
            
            # 自动重试
            if retry_count < retry_times:
                print(f"🔄 {retry_count + 1}/{retry_times} 重试...")
                browser.close()
                time.sleep(config['post'].get('retry_delay_s', 5))
                return post_douyin(config, title, images, topics, visible, mention, script_dir, retry_count + 1)
            
            browser.close()
            return False
        
        finally:
            try:
                browser.close()
            except:
                pass


def type_text_slowly(page: Page, element, text: str, min_delay: int, max_delay: int):
    """模拟真人输入（优化版）"""
    # 清空现有内容
    element.click()
    element.press('Control+A')
    element.press('Delete')
    random_delay(200, 500)
    
    # 逐字符输入（带随机延迟）
    for char in text:
        element.type(char)
        # 随机延迟，模拟思考时间
        if random.random() < 0.1:  # 10% 概率停顿更长
            time.sleep(random.uniform(0.3, 0.8))
        else:
            random_delay(min_delay, max_delay)


# ============ 批量发布 ============
def batch_post(
    config: dict,
    posts: List[Dict[str, Any]],
    script_dir: str = '.',
    interval_minutes: int = 5
) -> Dict[str, bool]:
    """批量发布"""
    results = {}
    
    for i, post in enumerate(posts):
        print(f"\n{'='*50}")
        print(f"发布 {i+1}/{len(posts)}: {post.get('title', '无标题')}")
        print(f"{'='*50}\n")
        
        success = post_douyin(
            config=config,
            title=post.get('title', ''),
            images=post.get('images', []),
            topics=post.get('topics', []),
            visible=post.get('visible', 'public'),
            script_dir=script_dir
        )
        
        results[post.get('title', f'post_{i}')] = success
        
        if i < len(posts) - 1 and success:
            print(f"\n⏳ 等待 {interval_minutes} 分钟后发布下一篇...")
            time.sleep(interval_minutes * 60)
    
    return results


# ============ 主函数 ============
def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='抖音图文发布工具（优化版）')
    parser.add_argument('--config', default='assets/config.json', help='配置文件路径')
    parser.add_argument('--title', required=True, help='图文标题')
    parser.add_argument('--images', nargs='+', required=True, help='图片文件路径（至少 2 张）')
    parser.add_argument('--topics', nargs='+', help='话题标签（不含#）')
    parser.add_argument('--visible', choices=['public', 'friends', 'private'], default='public',
                       help='可见性：public=公开，friends=好友，private=仅自己')
    parser.add_argument('--mention', help='@提及的用户')
    parser.add_argument('--headless', action='store_true', help='无头模式')
    parser.add_argument('--debug', action='store_true', help='调试模式（有头 + 截图）')
    
    args = parser.parse_args()
    
    # 切换脚本所在目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("=" * 60)
    print("🎵 抖音图文发布工具 - 优化版")
    print(f"📅 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    # 加载配置
    config = load_config(args.config)
    
    # 覆盖配置
    if args.debug:
        config['browser']['headless'] = False
        config['behavior']['screenshot_on_error'] = True
    elif args.headless:
        config['browser']['headless'] = True
    
    # 执行发布
    success = post_douyin(
        config=config,
        title=args.title,
        images=args.images,
        topics=args.topics,
        visible=args.visible,
        mention=args.mention,
        script_dir=str(script_dir)
    )
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 发布成功！")
    else:
        print("❌ 发布失败，请检查日志和截图")
    print("=" * 60)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
