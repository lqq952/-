# 技术规格文档 — 历史剪贴板

> 版本：v1.1 | 日期：2026-06-30 | 更新：切换为 Python 技术栈

---

## 1. 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 语言 | Python | 3.14.6 |
| UI 框架 | PyQt6 | 6.11.0 |
| 数据库 | sqlite3 | 内置 |
| 剪贴板 | PyQt6 QClipboard | 内置 |
| 系统托盘 | PyQt6 QSystemTrayIcon | 内置 |
| 图片处理 | PIL (Pillow) | 最新 |
| 打包 | PyInstaller | 最新 |

> **为什么放弃 Electron？** Electron 在 Windows 上存在已知 Bug（[#49034](https://github.com/electron/electron/issues/49034)），`require('electron')` 无法正确加载 API 模块，且暂无可靠解决方案。Python + PyQt6 方案更稳定，功能完全一致。

## 2. 项目结构

```
历史粘贴·/
├── main.py                   # 应用入口
├── src/
│   ├── database.py           # SQLite 数据库操作
│   ├── clipboard_monitor.py  # 剪贴板轮询 + 去重
│   ├── tray_manager.py       # 系统托盘管理
│   ├── main_window.py        # 主窗口 UI
│   └── style.py              # 样式常量（淡蓝色主题）
├── assets/
│   └── icon.png              # 应用图标
├── docs/                     # 文档
├── devlog/                   # 开发日志
└── requirements.txt          # Python 依赖
```

## 3. 数据库设计

数据库位置：`%APPDATA%/clipboard-history/data.db`

```sql
CREATE TABLE IF NOT EXISTS clipboard_items (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  type        TEXT    NOT NULL,   -- 'text' | 'image'
  content     TEXT    NOT NULL,   -- 文字内容 或 图片文件路径
  pinned      INTEGER DEFAULT 0,  -- 0=否, 1=置顶
  file_size   INTEGER DEFAULT 0,  -- 字节数
  created_at  TEXT    NOT NULL,   -- ISO 8601
  expires_at  TEXT    NOT NULL    -- ISO 8601
);

CREATE TABLE IF NOT EXISTS settings (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
```

图片存储：`%APPDATA%/clipboard-history/images/`

## 4. 剪贴板监听

- 使用 `QTimer` 每 500ms 触发
- 读取 `QApplication.clipboard()`
- 文字：`clipboard.text()` 
- 图片：`clipboard.pixmap()` → 保存为 PNG
- 去重：对内容计算 hash（hashlib.md5）

## 5. 打包

使用 PyInstaller 打包为单个 .exe：
```bash
pyinstaller --onefile --windowed --icon=assets/icon.png --name="历史剪贴板" main.py
```
