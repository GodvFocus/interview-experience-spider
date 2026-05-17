# 如何获取小红书 Cookie（图文步骤）

小红书的 API 需要登录态 Cookie 才能正常访问。以下是获取步骤：

---

## 步骤一：用 Chrome 登录小红书

1. 打开 Chrome 浏览器，访问 [https://www.xiaohongshu.com](https://www.xiaohongshu.com)
2. 点击右上角登录，扫码或输入手机号登录

---

## 步骤二：打开开发者工具

登录成功后：

1. 按键盘 `F12`（或 `Command + Option + I`）打开开发者工具
2. 点击顶部标签栏中的 **`Application`**（中文版叫"应用程序"）
   - 如果看不到，点击 `>>` 展开更多标签

---

## 步骤三：找到 Cookie

1. 在左侧菜单中，展开 **`Storage`（存储）** → **`Cookies`**
2. 点击 **`https://www.xiaohongshu.com`**
3. 右侧会显示所有 Cookie 列表

---

## 步骤四：复制以下4个字段

找到并复制这4个字段的 **Value（值）**：

| 字段名 | 说明 | 示例长度 |
|--------|------|----------|
| `a1` | 设备标识符 | 约50字符 |
| `web_session` | 登录会话 | 约40字符 |
| `webId` | 用户 ID | 约32字符 |
| `gid` | 设备 ID | 约70字符 |

> 💡 **小技巧**：在 Cookie 列表上方的搜索框输入 `a1` 可以快速定位

---

## 步骤五：填入 config.json

打开项目目录下的 `config.json`，找到 `xiaohongshu.cookies` 部分：

```json
"cookies": {
  "a1": "这里填入 a1 的值",
  "web_session": "这里填入 web_session 的值",
  "webId": "这里填入 webId 的值",
  "gid": "这里填入 gid 的值"
}
```

---

## ⚠️ 注意事项

1. **Cookie 有效期约1天**：过期后需要重新获取
2. **不要泄露 Cookie**：相当于你的登录凭证，不要分享给他人
3. **不要上传到 GitHub**：`config.json` 已加入 `.gitignore`
4. **频率限制**：每次请求间隔0.8秒，避免触发风控

---

## 常见错误

| 错误码 | 含义 | 解决方法 |
|--------|------|----------|
| `300011` | 账号异常/签名错误 | 检查 Node.js 依赖：`cd Spider_XHS_signing && npm install` |
| `461` | Cookie 过期 | 重新获取 Cookie |
| `-1` | 网络异常 | 检查网络，稍后重试 |
