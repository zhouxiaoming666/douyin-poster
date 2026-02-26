#!/usr/bin/env python3
"""
OpenClaw 集成接口
用于 OpenClaw 技能调用
"""

import argparse
import json
import os
import sys
from pathlib import Path

from douyin_post import load_config, post_douyin


def main():
    """OpenClaw 集成入口"""
    parser = argparse.ArgumentParser(description='OpenClaw 集成接口')
    parser.add_argument('--action', required=True, choices=['post', 'login', 'status'],
                       help='操作类型')
    parser.add_argument('--config', default='assets/config.json', help='配置文件路径')
    parser.add_argument('--title', help='图文标题')
    parser.add_argument('--images', nargs='+', help='图片文件路径')
    parser.add_argument('--topics', nargs='+', help='话题标签')
    parser.add_argument('--visible', choices=['public', 'friends', 'private'],
                       default='public', help='可见性')
    parser.add_argument('--output-json', action='store_true',
                       help='输出 JSON 格式结果')
    
    args = parser.parse_args()
    
    # 切换脚本所在目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    result = {
        'action': args.action,
        'success': False,
        'message': '',
        'data': {}
    }
    
    try:
        config = load_config(args.config)
        
        if args.action == 'login':
            from login import login
            login(config)
            result['success'] = True
            result['message'] = '登录完成'
        
        elif args.action == 'post':
            if not args.title or not args.images:
                result['message'] = '缺少必要参数：title, images'
            else:
                success = post_douyin(
                    config=config,
                    title=args.title,
                    images=args.images,
                    topics=args.topics,
                    visible=args.visible
                )
                result['success'] = success
                result['message'] = '发布成功' if success else '发布失败'
        
        elif args.action == 'status':
            cookie_file = config['account'].get('cookie_file', 'cookies.json')
            if os.path.exists(cookie_file):
                result['success'] = True
                result['message'] = '已登录'
                result['data']['logged_in'] = True
            else:
                result['message'] = '未登录'
                result['data']['logged_in'] = False
        
    except Exception as e:
        result['success'] = False
        result['message'] = str(e)
    
    # 输出结果
    if args.output_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result['success']:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
    
    sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()
