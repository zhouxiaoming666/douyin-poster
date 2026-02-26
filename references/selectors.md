# 抖音页面选择器参考

本文档记录抖音创作者平台的页面元素选择器，用于自动化脚本。

## 登录页面

### 登录入口
```css
/* 登录按钮 */
button:has-text("登录")
a:has-text("登录")
.login-btn

/* 二维码容器 */
img[src*="qrcode"]
.qrcode img
[class*="qrcode"] img
```

### 用户头像（登录成功标志）
```css
img[alt*="头像"]
.avatar img
[class*="avatar"] img
```

## 发布页面

### 发布入口
```css
/* 图文发布按钮 */
button:has-text("图文")
[class*="image"]
[class*="photo"]

/* 发布按钮 */
button:has-text("发布")
button:has-text("Publish")
```

### 表单元素
```css
/* 标题输入框 */
input[placeholder*="标题"]
input[placeholder*="title"]
[class*="title"] input

/* 话题输入框 */
input[placeholder*="话题"]
input[placeholder*="#"]

/* 文件上传 */
input[type="file"]

/* 可见性选择 */
[class*="visible"]
button:has-text("公开")
button:has-text("好友")
```

## 注意事项

1. **选择器可能变化**：抖音会更新 UI，选择器可能失效
2. **优先使用文本选择器**：`button:has-text("发布")` 比 CSS 类更稳定
3. **多选择器 Fallback**：准备多个选择器备选
4. **等待元素**：使用 `waitForSelector` 确保元素加载

## 调试技巧

```python
# 在浏览器中测试选择器
page.locator('your-selector').is_visible()

# 获取所有匹配元素
elements = page.locator('your-selector').all()
print(f"找到 {len(elements)} 个元素")

# 截图调试
page.screenshot(path='debug.png')
```

## 更新日志

- 2026-02-26: 初始版本，基于抖音创作者平台 v2026.02
