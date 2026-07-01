# 历史剪贴板 — Claude 项目指引

## 项目简介

一款 Windows 桌面历史剪贴板管理软件。基于 Python + PyQt6 开发，后台常驻系统托盘，自动记录文字和图片复制历史。

## 技术栈

- **语言**：Python 3.14
- **UI**：PyQt6
- **数据库**：sqlite3（内置）
- **打包**：PyInstaller

## 文档体系

| 文档 | 路径 | 说明 |
|------|------|------|
| 产品需求 | [docs/requirements.md](docs/requirements.md) | 功能需求和非功能需求 |
| 技术规格 | [docs/tech-spec.md](docs/tech-spec.md) | 技术栈、数据库、架构 |
| 设计规范 | [docs/design-spec.md](docs/design-spec.md) | UI 色彩、布局、组件 |
| 实施步骤 | [docs/implementation.md](docs/implementation.md) | 分阶段执行计划 |

## 开发日志

存放在 [devlog/](devlog/) 文件夹，以日期命名。
每次开发会话结束后更新当日日志。

## 工作方式

1. **分阶段推进**：严格按照实施步骤文档中的阶段顺序执行
2. **每阶段验证**：通过检查点后再进入下一阶段
3. **运行方式**：`python main.py`
4. **开发完成后更新**：更新 devlog/ 中的当日日志

## 当前状态

- 当前阶段：阶段一（Python 依赖安装 + 基础验证）
- 下一步：安装 Pillow、验证 PyQt6 窗口能启动
