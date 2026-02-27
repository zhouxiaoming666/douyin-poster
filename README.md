# 抖音发布助手 (Douyin Poster)

使用无头浏览器模拟真人操作发布抖音图文/视频，具备反检测能力。

## 特点

- 📱 **扫码登录** - 安全可靠，避免密码泄露
- 🖼️ **图文发布** - 支持 2-9 张图片，自动优化
- 🎬 **视频发布** - 支持视频上传、封面、BGM
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
# 优化版登录（支持无头模式）
python scripts/login_optimized.py --headless

# 调试模式（有头 + 截图）
python scripts/login_optimized.py --debug
```

### 2. 发布图文

```bash
# 基础发布
python scripts/douyin_post_optimized.py \
  --title "我的抖音笔记" \
  --images photo1.jpg photo2.jpg photo3.jpg \
  --topics 生活 日常 摄影

# 无头模式
python scripts/douyin_post_optimized.py \
  --title "测试笔记" \
  --images img1.jpg img2.jpg \
  --headless
```

### 3. 发布视频

```bash
# 基础视频发布
python scripts/douyin_video_post.py \
  --title "我的视频" \
  --video video.mp4 \
  --topics 生活 日常

# 带封面和 BGM
python scripts/douyin_video_post.py \
  --title "精彩瞬间" \
  --video video.mp4 \
  --cover cover.jpg \
  --topics 摄影 旅行 \
  --bgm "周杰伦 晴天"

# 调试模式
python scripts/douyin_video_post.py \
  --title "测试视频" \
  --video test.mp4 \
  --debug
```

## 文档

详细文档：[SKILL.md](SKILL.md)

## 许可证

MIT License
