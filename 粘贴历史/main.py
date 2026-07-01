"""历史剪贴板 - 应用入口"""
import sys
import os
import traceback
from datetime import datetime


def _setup_startup_logging():
    """配置启动日志，记录到 <项目根>/data/startup.log"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "startup.log")

    # 记录启动时间
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"[{timestamp}] 应用启动\n")
        f.write(f"  Python: {sys.executable}\n")
        f.write(f"  参数: {' '.join(sys.argv[1:]) if len(sys.argv) > 1 else '(无)'}\n")
        f.write(f"  工作目录: {os.getcwd()}\n")

    # 全局异常捕获 -> 写日志
    def _log_exception(exc_type, exc_value, exc_tb):
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 未捕获异常:\n")
            f.write("".join(tb_lines))

    sys.excepthook = _log_exception

    return log_path


def main():
    # --- 设置工作目录为项目根目录 ---
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)

    # --- 启动日志 ---
    try:
        _setup_startup_logging()
    except Exception:
        pass  # 日志初始化失败不影响主流程

    # 确保 src 模块可导入
    sys.path.insert(0, project_dir)

    from PyQt6.QtWidgets import QApplication

    from src.database import init_db
    from src.clipboard_monitor import ClipboardMonitor
    from src.tray_manager import TrayManager
    from src.main_window import MainWindow
    from src.single_instance import is_already_running, bring_existing_to_front

    # --- 单实例检测（必须在 QApplication 之前）---
    if is_already_running():
        bring_existing_to_front()
        sys.exit(0)

    # Windows 任务栏图标设置
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("clipboard-history")

    # 解析命令行参数
    hidden = "--hidden" in sys.argv or "--startup" in sys.argv

    app = QApplication(sys.argv)
    app.setApplicationName("历史剪贴板")
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出，后台继续监听

    # 初始化数据库
    init_db()

    # 创建剪贴板监听器
    monitor = ClipboardMonitor()

    # 创建主窗口（传入监听器，避免自身复制操作被重复记录）
    window = MainWindow(monitor=monitor)
    monitor.new_item_detected.connect(lambda item: window.add_new_item(item))
    monitor.start()

    # 创建系统托盘
    tray = TrayManager(app, window)
    # 设置面板和托盘菜单的开机自启状态保持同步
    window.auto_start_changed.connect(lambda checked: tray.refresh_auto_start_state())

    # 强制创建原生窗口句柄（确保隐藏启动时 FindWindowW 也能找到）
    window.winId()

    # 根据启动模式决定是否显示窗口
    if hidden:
        window.hide()
    else:
        window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
