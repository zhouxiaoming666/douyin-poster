---
name: douyin-poster
description: 抖音图文发布助手。支持图文笔记发布、扫码登录、反检测。使用 Playwright 模拟真人操作。当用户需要发布抖音图文、管理抖音账号时触发此技能。
---

# 抖音图文发布技能 (Douyin Poster)

使用无头浏览器模拟真人操作发布抖音图文，具备反检测能力。

## 快速开始

### 安装

```bash
# 克隆技能
cd /path/to/your/skills
git clone https://github.com/zhouxiaoming666/douyin-poster.git

# 安装依赖
cd douyin-poster
bash scripts/install.sh
```

### 配置

1. **首次登录**（扫码登录）：

```bash
source .venv/bin/activate
python scripts/login.py
```

用手机抖音扫码，登录成功后 Cookie 会自动保存。

2. **发布图文**：

```bash
# 发布图文笔记
python scripts/douyin_post.py \
  --config assets/config.json \
  --title "我的抖音笔记" \
  --images /path/to/img1.jpg /path/to/img2.jpg

# 带话题发布
python scripts/douyin_post.py \
  --config assets/config.json \
  --title "日常分享" \
  --images photo1.jpg photo2.jpg \
  --topics "生活" "日常"
```

## 核心功能

### 1. 真人行为模拟

- **随机延迟**: 操作间插入 1-5 秒随机延迟
- **鼠标轨迹**: 贝塞尔曲线模拟人类鼠标移动
- **随机滚动**: 发布前随机滚动页面
- **输入模拟**: 字符级输入，带随机停顿

### 2. 反检测措施

- **扫码登录**: 避免密码登录风险
- **Cookie 持久化**: 扫码一次，长期有效
- **浏览器指纹保护**: 禁用自动化特征
- **User-Agent 轮换**: 使用真实浏览器 UA

### 3. 发布功能

- **图文笔记**: 支持 2-9 张图片
- **标题文案**: 最多 1000 字
- **话题标签**: 自动添加 #话题#
- **@提及**: 支持@好友
- **可见性**: 公开/好友/仅自己

## 使用示例

### 基础发布

```bash
python scripts/douyin_post.py \
  --config assets/config.json \
  --title "这是第一条抖音" \
  --images image1.jpg image2.jpg
```

### 带话题发布

```bash
python scripts/douyin_post.py \
  --config assets/config.json \
  --title "今天的学习心得" \
  --topics "学习" "成长" \
  --visible public
```

### OpenClaw 集成

```bash
python scripts/openclaw_integration.py \
  --action post \
  --title "来自 OpenClaw 的抖音" \
  --output-json
```

## 脚本说明

| 脚本 | 用途 |
|------|------|
| `douyin_post.py` | 主发布脚本 |
| `login.py` | 扫码登录 |
| `human_behavior.py` | 人类行为模拟工具 |
| `openclaw_integration.py` | OpenClaw 集成接口 |
| `install.sh` | 一键安装脚本 |

## 依赖

- Python 3.8+
- Playwright
- Chromium 浏览器
- 系统依赖：`atk`, `libXcomposite`, `libXdamage`, `libXrandr`, `mesa-libgbm` 等

## 注意事项

1. **首次使用**: 先运行登录脚本，手机抖音扫码
2. **Cookie 保存**: 登录成功后 Cookie 会自动保存
3. **图片要求**: JPG/PNG 格式，建议 1080x1920（9:16）
4. **发布频率**: 建议发布间隔 > 10 分钟
5. **内容审核**: 遵守抖音社区规范

## 故障排除

### 登录失败
- 检查网络连接
- 重新扫码登录
- 检查 Cookie 是否过期

### 发布失败
- 检查图片格式（JPG/PNG）
- 检查图片数量（2-9 张）
- 检查内容是否违规

### 被检测为机器人
- 增加延迟时间（修改 config.json）
- 减少发布频率
- 检查浏览器指纹

## 项目结构

```
douyin-poster/
├── SKILL.md                          # 技能文档
├── clawhub.json                      # Clawhub 配置
├── README.md                         # 使用说明
├── requirements.txt                  # Python 依赖
├── scripts/
│   ├── douyin_post.py               # 主发布脚本
│   ├── login.py                     # 扫码登录
│   ├── human_behavior.py            # 人类行为模拟
│   ├── openclaw_integration.py      # OpenClaw 集成
│   └── install.sh                   # 安装脚本
├── references/
│   └── selectors.md                 # 抖音页面选择器
└── assets/
    └── config.example.json          # 配置模板
```

## 许可证

MIT License

## 支持

- 文档：https://github.com/zhouxiaoming666/douyin-poster
- 问题反馈：https://github.com/zhouxiaoming666/douyin-poster/issues
