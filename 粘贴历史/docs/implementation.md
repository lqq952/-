# 实施步骤 — 历史剪贴板

> 版本：v1.0 | 日期：2026-06-30

---

## 执行原则

- 🔒 **分阶段推进**：一个阶段完成并验证后再进入下一阶段
- ✅ **每阶段有检查点**：通过检查点才算阶段完成
- 📝 **每阶段写日志**：记录完成情况和遇到的问题
- 🐛 **有问题先修**：不在有 bug 的代码上继续叠加

---

## 阶段一：项目初始化

**目标**：搭建 Electron 项目骨架，确认能启动空白窗口。

**步骤**：
1. `npm init` 初始化项目
2. 安装依赖：`electron`、`electron-builder`（devDependencies）、`better-sqlite3`
3. 创建最小 `src/main.js`（创建窗口）
4. 创建最小 `src/renderer/index.html`（空白页面）
5. 配置 `package.json` 的 `main` 和 `scripts`
6. 运行 `npm start` 验证

**检查点**：执行 `npm start` → 出现空白 Electron 窗口

**产出文件**：
- `package.json`
- `src/main.js`（最小版）
- `src/renderer/index.html`（最小版）

---

## 阶段二：数据库层

**目标**：实现数据存储和基本 CRUD 操作。

**步骤**：
1. 创建 `src/database.js`
   - 初始化数据库（建表）
   - `addItem(type, content, size)` — 新增记录
   - `getItems(search, limit)` — 查询列表（支持搜索、自动排序置顶优先+时间降序）
   - `togglePin(id)` — 切换置顶
   - `deleteItem(id)` — 删除单条
   - `cleanExpired()` — 清理过期
   - `enforceMax()` — 强制上限
   - `getSettings()` / `saveSetting(key, value)` — 设置读写
2. 创建 `src/settings.js`（封装设置读写）
3. 写简单测试（直接 node 运行 database.js 验证）

**检查点**：`node src/database.js` → 能写入、查询、删除记录，无报错

**产出文件**：
- `src/database.js`
- `src/settings.js`

---

## 阶段三：核心后台功能

**目标**：剪贴板监听正常工作，系统托盘可交互。

**步骤**：
1. 创建 `src/clipboard-monitor.js`
   - `start(callback)` — 开始轮询
   - `stop()` — 停止
   - 内部去重逻辑
2. 创建 `src/tray.js`
   - 创建托盘图标
   - 右键菜单
   - 点击行为
3. 创建 `src/preload.js`
   - 暴露 IPC API 给渲染进程
4. 更新 `src/main.js`
   - 引入剪贴板监听和托盘
   - 注册全局快捷键 Ctrl+Shift+V
   - 设置 IPC handlers

**检查点**：
- 启动后系统托盘出现图标
- 复制文字 → 数据库有记录
- 复制图片 → 数据库有记录 + images 文件夹有图
- Ctrl+Shift+V 能切换窗口显示

**产出文件**：
- `src/clipboard-monitor.js`
- `src/tray.js`
- `src/preload.js`
- `src/main.js`（完整版）

---

## 阶段四：UI 界面

**目标**：完整的用户界面，所有交互可用。

**步骤**：
1. 创建 `src/renderer/index.html` — 页面结构
2. 创建 `src/renderer/style.css` — 淡蓝色主题样式
3. 创建 `src/renderer/app.js` — 所有前端逻辑
   - 加载历史列表
   - 搜索筛选
   - 点击复制
   - 置顶/取消置顶
   - 删除
   - 设置面板
   - Toast 提示
4. 窗口与渲染进程通信

**检查点**：
- 打开窗口看到完整卡片列表
- 搜索框可筛选内容
- 点击卡片能复制
- 置顶/删除按钮生效
- 设置面板可修改保留天数

**产出文件**：
- `src/renderer/index.html`
- `src/renderer/style.css`
- `src/renderer/app.js`

---

## 阶段五：打包与最终测试

**目标**：生成可安装的 Windows .exe。

**步骤**：
1. 创建 `electron-builder.yml` 打包配置
2. 准备 `assets/icon.png`
3. 运行 `npm run build`
4. 在 Windows 上安装测试
5. 修复打包相关问题

**检查点**：
- 双击 .exe 能安装
- 安装后软件正常运行
- 所有功能正常工作

**产出**：
- `dist/历史剪贴板 Setup x.x.x.exe`
