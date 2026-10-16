# 纯黑主题

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Chrome Manifest V3](https://img.shields.io/badge/Chrome-Manifest_V3-34a853.svg)
![e2e 测试](https://img.shields.io/badge/e2e-11%20passed-brightgreen.svg)

[English](README.md) | 简体中文

一套纯黑方案，同时覆盖**网站页面**和**浏览器界面**：页面用滤镜方案，观感按 GitHub Primer Dark 色板标定；浏览器界面配一个纯黑主题。

> Chrome 平台硬限制：扩展不能改浏览器界面，主题不能带脚本和弹窗——所以一边一个，搭配使用。

## 特性

- **三态模式**：关闭（页面完全不动）／黑暗／护眼（暖色调减少蓝光）
- **亮度、对比度滑杆**（60%–140%，实时生效、永久保存）
- **永久站点过滤**：输入 `github.com` 或粘贴任意 URL，自动归一化为域名统一管理，重启浏览器依然生效
- **快捷键** `Alt+Shift+D` 一键切换当前网站
- **中英双语界面**，默认跟随浏览器语言
- **恢复默认设置**一键重置
- 零网络请求、无统计埋点，设置只存于本地 `chrome.storage.local`

## 安装（解压加载）

1. 打开 `chrome://extensions`，右上角打开「开发者模式」。
2. 「加载已解压的扩展程序」→ 选 `extension` 文件夹。
3. 再次加载 → 选 `browser-theme` 文件夹（浏览器界面立即变黑）。

Windows 版 Chrome 拒绝安装非应用商店来源的 CRX；需要分发请发布到 [Chrome Web Store](https://chrome.google.com/webstore/devconsole)（打包：`python tools/pack.py`）。

## 使用

- 点工具栏月亮图标打开设置；黑暗模式蓝色高亮，护眼模式琥珀高亮。
- 本身已是深色的网站会被反色「洗白」——用站点过滤或 `Alt+Shift+D` 排除。
- 想换回浏览器默认外观：`chrome://settings/appearance` 重置主题，或停用扩展。

## 项目结构

```
black-theme/
├─ extension/          # 扩展本体（网页部分）
│  ├─ manifest.json
│  ├─ dark.css         # 滤镜样式，标定到 #0d1117 / #e6edf3
│  ├─ content.js       # 页面开关标记与滤镜参数
│  ├─ popup.html / popup.js
│  ├─ sw.js            # 快捷键处理
│  ├─ _locales/        # zh_CN / en 语言包
│  └─ icons/           # 光栅化图标
├─ browser-theme/      # 浏览器界面配套主题
├─ icons/icon.svg      # 图标源文件
├─ tools/
│  ├─ make_icons.py    # SVG → PNG（改图标后重跑）
│  └─ pack.py          # CRX 打包（复用 .pem 保持扩展 ID）
└─ test/
   ├─ e2e.py           # 11 条链路端到端回归
   └─ page.html 等     # 测试夹具与效果截图
```

## 开发

```bash
python tools/make_icons.py   # 修改 icons/icon.svg 后重新光栅化
python test/e2e.py           # 端到端回归（需 playwright）
python tools/pack.py         # 打包 black-theme.crx
```

## 已知限制

- 滤镜方案：背景图可能变色；个别网站 `position: fixed/sticky` 悬浮元素会跟随页面滚动。
- Canvas 类应用（Google Docs、Figma）以位图渲染，无法选择性处理——请加入过滤。
- 本身偏深的网站会被「洗白」——这正是站点过滤的用途。

## 隐私

不收集任何数据、零网络请求、无统计埋点。所有设置仅保存在浏览器本地的 `chrome.storage.local`。

## 许可证

[MIT](LICENSE)
