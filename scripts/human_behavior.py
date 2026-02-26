#!/usr/bin/env python3
"""
人类行为模拟工具
提供鼠标轨迹、随机延迟、输入模拟等功能
"""

import random
import time
from typing import Tuple


def random_delay(min_ms: int = 1000, max_ms: int = 5000) -> float:
    """
    生成随机延迟（秒）
    
    Args:
        min_ms: 最小延迟（毫秒）
        max_ms: 最大延迟（毫秒）
    
    Returns:
        延迟时间（秒）
    """
    delay = random.uniform(min_ms, max_ms) / 1000
    time.sleep(delay)
    return delay


def bezier_curve(start: Tuple[int, int], end: Tuple[int, int], steps: int = 100) -> list:
    """
    生成贝塞尔曲线路径（模拟人类鼠标移动）
    
    Args:
        start: 起始坐标 (x, y)
        end: 目标坐标 (x, y)
        steps: 路径点数
    
    Returns:
        路径点列表 [(x1, y1), (x2, y2), ...]
    """
    # 随机控制点（让路径有弧度）
    control_x = start[0] + (end[0] - start[0]) * 0.5 + random.uniform(-100, 100)
    control_y = start[1] + (end[1] - start[1]) * 0.5 + random.uniform(-100, 100)
    
    path = []
    for i in range(steps):
        t = i / steps
        # 二次贝塞尔曲线公式
        x = (1 - t) ** 2 * start[0] + 2 * (1 - t) * t * control_x + t ** 2 * end[0]
        y = (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * control_y + t ** 2 * end[1]
        path.append((int(x), int(y)))
    
    return path


def human_typing_delay() -> float:
    """
    模拟真人打字延迟（秒）
    
    Returns:
        延迟时间（秒）
    """
    # 正常人打字速度：每分钟 40-80 个字符
    # 每个字符间隔：0.75-1.5 秒
    base_delay = random.uniform(0.05, 0.2)
    
    # 偶尔停顿（思考）
    if random.random() < 0.1:
        base_delay += random.uniform(0.5, 2.0)
    
    return base_delay


def random_scroll(page, min_times: int = 2, max_times: int = 5):
    """
    模拟真人滚动页面
    
    Args:
        page: Playwright page 对象
        min_times: 最少滚动次数
        max_times: 最多滚动次数
    """
    times = random.randint(min_times, max_times)
    
    for _ in range(times):
        # 随机滚动距离
        scroll_distance = random.randint(100, 500)
        direction = random.choice([1, -1])
        
        page.evaluate(f'window.scrollBy(0, {scroll_distance * direction})')
        time.sleep(random.uniform(0.5, 1.5))


def add_random_mouse_movement(page):
    """
    添加随机鼠标移动（模拟真人）
    
    Args:
        page: Playwright page 对象
    """
    # 获取视口大小
    viewport = page.viewport_size or {'width': 1280, 'height': 800}
    
    # 随机目标位置
    target_x = random.randint(100, viewport['width'] - 100)
    target_y = random.randint(100, viewport['height'] - 100)
    
    # 生成路径并移动
    path = bezier_curve((viewport['width'] // 2, viewport['height'] // 2), (target_x, target_y))
    
    for x, y in path[::10]:  # 每 10 个点移动一次
        page.mouse.move(x, y)
        time.sleep(0.01)


if __name__ == '__main__':
    # 测试
    print("测试贝塞尔曲线:")
    path = bezier_curve((0, 0), (100, 100))
    print(f"生成 {len(path)} 个路径点")
    print(f"前 5 个点：{path[:5]}")
    
    print("\n测试随机延迟:")
    for i in range(5):
        delay = random_delay(100, 300)
        print(f"延迟：{delay:.3f}秒")
