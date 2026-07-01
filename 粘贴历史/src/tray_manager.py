"""系统托盘管理器"""
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QAction
from PyQt6.QtCore import Qt

from .startup import add_to_startup, remove_from_startup, is_startup_enabled


def _create_tray_icon() -> QIcon:
    """生成托盘图标 - 淡蓝色剪贴板图标"""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 淡蓝色圆角矩形背景
    painter.setBrush(QColor("#42A5F5"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(2, 4, 28, 24, 6, 6)

    # 白色线条表示文本
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawRoundedRect(8, 10, 16, 3, 1, 1)
    painter.drawRoundedRect(8, 15, 12, 3, 1, 1)
    painter.drawRoundedRect(8, 20, 14, 3, 1, 1)

    painter.end()
    return QIcon(pixmap)


class TrayManager:
    """系统托盘管理"""

    def __init__(self, app, main_window):
        self._app = app
        self._main_window = main_window
        self._tray = QSystemTrayIcon()
        self._tray.setIcon(_create_tray_icon())
        self._tray.setToolTip("历史剪贴板")

        # 右键菜单
        menu = QMenu()
        show_action = QAction("显示主窗口", menu)
        show_action.triggered.connect(self._show_window)
        menu.addAction(show_action)

        menu.addSeparator()

        # 开机自启开关
        self._auto_start_action = QAction("开机自动启动", menu)
        self._auto_start_action.setCheckable(True)
        self._auto_start_action.setChecked(is_startup_enabled())
        self._auto_start_action.triggered.connect(self._toggle_auto_start)
        menu.addAction(self._auto_start_action)

        menu.addSeparator()

        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(self._quit_app)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)

        # 双击托盘图标显示窗口
        self._tray.activated.connect(self._on_tray_activated)

        self._tray.show()

    def _show_window(self):
        """显示主窗口"""
        self._main_window.show()
        self._main_window.raise_()
        self._main_window.activateWindow()

    def _on_tray_activated(self, reason):
        """托盘图标交互"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()

    def _toggle_auto_start(self, checked: bool):
        """切换开机自启"""
        from .database import save_setting
        if checked:
            success, msg = add_to_startup()
            if not success:
                self._auto_start_action.setChecked(False)
                self._tray.showMessage("历史剪贴板", f"设置开机自启失败\n{msg}", QSystemTrayIcon.MessageIcon.Warning, 3000)
                return
        else:
            remove_from_startup()
        save_setting("auto_start", "1" if checked else "0")

    def refresh_auto_start_state(self):
        """刷新开机自启勾选状态（外部调用）"""
        self._auto_start_action.setChecked(is_startup_enabled())

    def _quit_app(self):
        """退出应用"""
        self._tray.hide()
        self._app.quit()

    def show_notification(self, title: str, message: str):
        """显示系统通知"""
        self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 2000)
