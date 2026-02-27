#!/usr/bin/env python3
"""
抖音视频发布脚本 - 优化版
支持视频上传、封面选择、标题、话题、BGM 等功能
"""

import argparse
import json
import os
import sys
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout, Page, BrowserContext

# ============ 配置 ============
DEFAULT_CONFIG = {
    "account": {"cookie_file": "cookies.json"},
    "browser": {
        "headless": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    },
    "behavior": {
        "min_delay_ms": 1000,
        "max_delay_ms": 3000,
        "scroll_before_post": True,
        "random_mouse_move": True,
        "screenshot_on_error": True
    },
    "video": {
        "max_size_mb": 500,
        "max_duration_s": 300,
        "supported_formats": ["mp4", "mov", "avi", "mkv", "webm"],
        "allow_cover_custom": True,
        "allow_bgm": True
    },
    "post": {
        "default_visible": "public",
        "retry_times": 3,
        "retry_delay_s": 10
    },
    "anti_detect": {
        "enable": True,
        "hide_webdriver": True
    }
}

# ============ 工具函数 ============
def load_config(config_path: str = "assets/config.json") -> dict:
    """加载配置文件"""
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
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


def validate_video(video_path: str, config: dict) -> tuple:
    """验证视频文件"""
    if not os.path.exists(video_path):
        return False, f"视频文件不存在：{video_path}"
    
    # 检查格式
    ext = os.path.splitext(video_path)[1].lower().lstrip('.')
    supported_formats = config['video'].get('supported_formats', ['mp4', 'mov', 'avi'])
    if ext not in supported_formats:
        return False, f"不支持的视频格式：{ext}（支持：{', '.join(supported_formats)}）"
    
    # 检查文件大小
    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    max_size_mb = config['video'].get('max_size_mb', 500)
    if file_size_mb > max_size_mb:
        return False, f"视频文件过大：{file_size_mb:.1f}MB（最大：{max_size_mb}MB）"
    
    return True, "验证通过"


def type_text_slowly(page: Page, element, text: str, min_delay: int, max_delay: int):
    """模拟真人输入"""
    element.click()
    element.press('Control+A')
    element.press('Delete')
    random_delay(200, 500)
    
    for char in text:
        element.type(char)
        if random.random() < 0.1:
            time.sleep(random.uniform(0.3, 0.8))
        else:
            random_delay(min_delay, max_delay)


# ============ 核心发布函数 ============
def post_video(
    config: dict,
    title: str,
    video_path: str,
    cover_path: Optional[str] = None,
    topics: Optional[List[str]] = None,
    visible: str = 'public',
    bgm_title: Optional[str] = None,
    script_dir: str = '.',
    retry_count: int = 0
) -> bool:
    """发布抖音视频"""
    
    # 提取配置
    cookie_file = config['account'].get('cookie_file', 'cookies.json')
    if not os.path.isabs(cookie_file):
        cookie_file = os.path.join(script_dir, '..', cookie_file)
    
    headless = config['browser'].get('headless', True)
    min_delay = config['behavior'].get('min_delay_ms', 1000)
    max_delay = config['behavior'].get('max_delay_ms', 3000)
    retry_times = config['post'].get('retry_times', 3)
    screenshot_on_error = config['behavior'].get('screenshot_on_error', True)
    
    # 验证视频
    valid, message = validate_video(video_path, config)
    if not valid:
        print(f"❌ {message}")
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
        
        if config['anti_detect'].get('random_viewport', True):
            context_options['viewport'] = {
                'width': random.randint(1280, 1920),
                'height': random.randint(720, 1080)
            }
        
        context = browser.new_context(**context_options)
        
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
            
            # 检查登录
            current_url = page.url
            if 'login' in current_url.lower():
                print("❌ 未登录，请先运行 login.py")
                if screenshot_on_error:
                    take_screenshot(page, "login_required")
                browser.close()
                return False
            
            print("✅ 已登录")
            
            # ========== 切换到视频发布 ==========
            print("🎬 切换到视频发布模式...")
            
            # 查找视频发布入口
            video_tab_selectors = [
                'button:has-text("视频"), tab:has-text("视频")',
                '[role="tab"]:has-text("视频")',
                '[class*="video-tab"], [class*="VideoTab"]'
            ]
            
            video_tab = None
            for selector in video_tab_selectors:
                try:
                    video_tab = page.locator(selector).first
                    if video_tab.is_visible(timeout=3000):
                        print(f"✓ 找到视频标签：{selector}")
                        break
                except:
                    continue
            
            if video_tab:
                video_tab.click()
                random_delay(min_delay, max_delay)
                print("✅ 已切换到视频发布")
            
            # ========== 上传视频 ==========
            print("📹 上传视频...")
            
            upload_selectors = [
                'input[type="file"][accept*="video"]',
                'input[type="file"]',
                'button:has-text("上传视频"), button:has-text("选择视频")',
                '[class*="upload"], [class*="Upload"]'
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
                file_input.set_input_files(video_path)
                print(f"✅ 视频已上传：{os.path.basename(video_path)}")
            else:
                # 尝试点击触发
                try:
                    upload_btn = page.locator('button:has-text("上传视频"), button:has-text("选择视频"), [class*="upload-btn"]').first
                    if upload_btn.is_visible(timeout=5000):
                        upload_btn.click()
                        random_delay(1000, 2000)
                        file_input = page.locator('input[type="file"]').first
                        if file_input.is_visible(timeout=5000):
                            file_input.set_input_files(video_path)
                            print(f"✅ 视频已上传")
                except Exception as e:
                    print(f"❌ 上传失败：{e}")
                    if screenshot_on_error:
                        take_screenshot(page, "upload_failed")
                    browser.close()
                    return False
            
            # 等待视频处理
            print("⏳ 等待视频处理...")
            time.sleep(10)  # 视频处理需要更长时间
            
            # 检测视频是否处理完成
            try:
                # 等待视频预览出现
                video_preview = page.locator('video, [class*="video-preview"], [class*="VideoPreview"]').first
                if video_preview.is_visible(timeout=30000):
                    print("✅ 视频处理完成")
            except:
                print("⚠️  视频可能还在处理中")
            
            # ========== 设置封面 ==========
            if cover_path and config['video'].get('allow_cover_custom', True):
                print("🖼️  设置自定义封面...")
                try:
                    # 查找封面设置按钮
                    cover_btn = page.locator('button:has-text("封面"), [class*="cover"], [class*="Cover"]').first
                    if cover_btn.is_visible(timeout=5000):
                        cover_btn.click()
                        random_delay(500, 1000)
                        
                        # 查找上传封面按钮
                        cover_upload = page.locator('button:has-text("上传封面"), input[type="file"][accept*="image"]').first
                        if cover_upload.is_visible(timeout=5000):
                            if cover_upload.input_enabled():
                                cover_upload.set_input_files(cover_path)
                                print(f"✅ 封面已上传：{os.path.basename(cover_path)}")
                            else:
                                cover_upload.click()
                                random_delay(500, 1000)
                                cover_input = page.locator('input[type="file"]').first
                                if cover_input.is_visible(timeout=3000):
                                    cover_input.set_input_files(cover_path)
                                    print(f"✅ 封面已上传")
                        
                        # 确认封面
                        random_delay(1000, 2000)
                        confirm_cover = page.locator('button:has-text("确定"), button:has-text("确认")').first
                        if confirm_cover.is_visible(timeout=3000):
                            confirm_cover.click()
                            print("✅ 封面已确认")
                except Exception as e:
                    print(f"⚠️  封面设置失败：{e}")
            
            # ========== 输入标题 ==========
            print("✏️  输入标题...")
            title_selectors = [
                'input[placeholder*="标题"], input[placeholder*="title"]',
                'input[class*="title"], [class*="title"] input'
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
                        topic_input = page.locator('input[placeholder*="话题"], input[placeholder*="#"]').first
                        if topic_input.is_visible(timeout=3000):
                            topic_input.click()
                            random_delay(200, 500)
                            topic_input.type(f"#{topic}")
                            time.sleep(0.5)
                            topic_input.press('Enter')
                            random_delay(min_delay, max_delay)
                            print(f"✅ 话题已添加：#{topic}")
                    except Exception as e:
                        print(f"⚠️  话题添加失败 {topic}: {e}")
            
            # ========== 添加 BGM ==========
            if bgm_title and config['video'].get('allow_bgm', True):
                print("🎵 添加背景音乐...")
                try:
                    # 查找添加音乐按钮
                    music_btn = page.locator('button:has-text("添加音乐"), button:has-text("选择音乐"), [class*="music"]').first
                    if music_btn.is_visible(timeout=5000):
                        music_btn.click()
                        random_delay(1000, 2000)
                        
                        # 搜索音乐
                        music_search = page.locator('input[placeholder*="搜索音乐"], input[placeholder*="搜索歌曲"]').first
                        if music_search.is_visible(timeout=3000):
                            music_search.click()
                            random_delay(500, 1000)
                            music_search.type(bgm_title)
                            time.sleep(1)
                            
                            # 选择第一首搜索结果
                            music_result = page.locator('[class*="music-item"], [class*="song-item"]').first
                            if music_result.is_visible(timeout=3000):
                                music_result.click()
                                print(f"✅ BGM 已添加：{bgm_title}")
                            
                            # 关闭音乐面板
                            close_btn = page.locator('button:has-text("关闭"), [class*="close"]').first
                            if close_btn.is_visible(timeout=3000):
                                close_btn.click()
                except Exception as e:
                    print(f"⚠️  BGM 添加失败：{e}")
            
            # ========== 设置可见性 ==========
            if visible != 'public':
                print(f"🔒 设置可见性：{visible}")
                try:
                    visible_btn = page.locator('button:has-text("公开"), button:has-text("好友"), [class*="visible"]').first
                    if visible_btn.is_visible(timeout=5000):
                        visible_btn.click()
                        random_delay(min_delay, max_delay)
                        
                        visible_text = '公开' if visible == 'public' else '好友可见' if visible == 'friends' else '私密'
                        visible_option = page.locator(f'li:has-text("{visible_text}")').first
                        if visible_option.is_visible(timeout=5000):
                            visible_option.click()
                            print(f"✅ 可见性已设置：{visible}")
                except Exception as e:
                    print(f"⚠️  可见性设置失败：{e}")
            
            # ========== 模拟真人操作 ==========
            if config['behavior'].get('scroll_before_post', True):
                print("📜 模拟真人滚动...")
                for _ in range(random.randint(2, 4)):
                    scroll_amount = random.randint(100, 300)
                    page.evaluate(f'window.scrollBy(0, {scroll_amount})')
                    time.sleep(random.uniform(0.5, 1.5))
                page.evaluate('window.scrollTo(0, 0)')
            
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
                '[class*="publish"], [class*="submit"]'
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
                take_screenshot(page, "before_publish")
                
                publish_btn.click()
                print("✅ 已点击发布按钮")
                
                # 等待发布结果
                time.sleep(8)  # 视频发布需要更长时间
                
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
            
            if retry_count < retry_times:
                print(f"🔄 {retry_count + 1}/{retry_times} 重试...")
                browser.close()
                time.sleep(config['post'].get('retry_delay_s', 10))
                return post_video(config, title, video_path, cover_path, topics, visible, bgm_title, script_dir, retry_count + 1)
            
            browser.close()
            return False
            
        except Exception as e:
            print(f"❌ 错误：{e}")
            import traceback
            traceback.print_exc()
            
            if screenshot_on_error:
                take_screenshot(page, "exception_error")
            
            if retry_count < retry_times:
                print(f"🔄 {retry_count + 1}/{retry_times} 重试...")
                browser.close()
                time.sleep(config['post'].get('retry_delay_s', 10))
                return post_video(config, title, video_path, cover_path, topics, visible, bgm_title, script_dir, retry_count + 1)
            
            browser.close()
            return False
        
        finally:
            try:
                browser.close()
            except:
                pass


# ============ 主函数 ============
def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='抖音视频发布工具（优化版）')
    parser.add_argument('--config', default='assets/config.json', help='配置文件路径')
    parser.add_argument('--title', required=True, help='视频标题')
    parser.add_argument('--video', required=True, help='视频文件路径')
    parser.add_argument('--cover', help='封面图片路径（可选）')
    parser.add_argument('--topics', nargs='+', help='话题标签（不含#）')
    parser.add_argument('--visible', choices=['public', 'friends', 'private'], default='public',
                       help='可见性')
    parser.add_argument('--bgm', help='背景音乐标题（可选）')
    parser.add_argument('--headless', action='store_true', help='无头模式')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("=" * 60)
    print("🎵 抖音视频发布工具 - 优化版")
    print(f"📅 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    config = load_config(args.config)
    
    if args.debug:
        config['browser']['headless'] = False
        config['behavior']['screenshot_on_error'] = True
    elif args.headless:
        config['browser']['headless'] = True
    
    success = post_video(
        config=config,
        title=args.title,
        video_path=args.video,
        cover_path=args.cover,
        topics=args.topics,
        visible=args.visible,
        bgm_title=args.bgm,
        script_dir=str(script_dir)
    )
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 视频发布成功！")
    else:
        print("❌ 视频发布失败，请检查日志和截图")
    print("=" * 60)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
