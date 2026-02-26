# 抖音图文发布助手 (Douyin Poster)

使用无头浏览器模拟真人操作发布抖音图文，具备反检测能力。

## 特点

- 📱 **扫码登录** - 安全可靠，避免密码泄露
- 🖼️ **图文发布** - 支持 2-9 张图片，自动优化
- 🤖 **真人模拟** - 鼠标轨迹、随机延迟、输入模拟
- 🛡️ **反检测** - 浏览器指纹保护、Cookie 持久化
- ⚡ **简单易用** - 一行命令发布

## 安装

```bash
git clone https://github.com/zhouxiaoming666/douyin-poster.git
cd douyin-poster
bash scripts/install.sh
```

## 使用

### 1. 扫码登录

```bash
python scripts/login.py
```

### 2. 发布图文

```bash
python scripts/douyin_post.py \
  --config assets/config.json \
  --title "我的抖音笔记" \
  --images photo1.jpg photo2.jpg \
  --topics "生活" "日常"
```

## 文档

详细文档：[SKILL.md](SKILL.md)

## 许可证

MIT License
