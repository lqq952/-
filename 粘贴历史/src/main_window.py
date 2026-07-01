"""主窗口 UI"""
import os
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QScrollArea, QLabel,
    QApplication, QSizePolicy, QFrame, QTextEdit,
    QAbstractScrollArea,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QEvent
from PyQt6.QtGui import QPixmap, QIcon, QFont

from .database import get_items, toggle_pin, toggle_save, get_saved_count, delete_item, get_setting, save_setting, get_item_count, clean_expired, clear_all
from .startup import add_to_startup, remove_from_startup, is_startup_enabled
from .style import (
    BG_MAIN, BG_CARD, ACCENT, ACCENT_HOVER, ACCENT_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT, BORDER, DIVIDER,
    PIN_COLOR, PIN_INACTIVE, DELETE_COLOR, DELETE_HOVER_BG, SUCCESS,
    SAVE_COLOR, SAVE_HOVER_BG, SAVE_BG, SAVE_BORDER,
    CARD_RADIUS, CARD_GAP, LIST_PADDING, TOP_BAR_HEIGHT, TAB_BAR_HEIGHT,
    FILTER_BAR_HEIGHT, FILTER_BTN_ACTIVE, FILTER_BTN_INACTIVE,
    SEARCH_RADIUS, FONT_SIZE_SMALL, GLOBAL_STYLESHEET,
    TAB_ACTIVE, TAB_INACTIVE,
)


class ClipCard(QFrame):
    """单条历史记录卡片"""

    pin_toggled = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)
    copy_clicked = pyqtSignal(int)
    save_toggled = pyqtSignal(int)
    preview_clicked = pyqtSignal(int)  # 图片卡片点击 → 预览弹窗

    def __init__(self, item: dict, parent=None):
        super().__init__(parent)
        self._item = item
        self._pinned = item["pinned"]
        self._saved = item.get("saved", False)
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("clipCard")
        self.setStyleSheet(self._card_style())
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(56)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 10, 10)
        layout.setSpacing(10)

        # 左侧内容区
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)

        if self._item["type"] == "text":
            text = self._item["content"]
            # 多行展示：保留换行，限制 800 字防止过长
            if len(text) > 800:
                text = text[:800] + "…"
            self._text_edit = QTextEdit()
            self._text_edit.setPlainText(text)
            self._text_edit.setReadOnly(True)
            self._text_edit.setFrameShape(QFrame.Shape.NoFrame)
            self._text_edit.setStyleSheet(
                f"color: {TEXT_PRIMARY}; font-size: 13px; background: transparent; "
                f"selection-background-color: {ACCENT_LIGHT}; selection-color: {TEXT_PRIMARY};"
            )
            self._text_edit.setMaximumHeight(220)
            self._text_edit.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
            self._text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self._text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self._text_edit.document().setDocumentMargin(0)
            self._text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            content_layout.addWidget(self._text_edit)
        else:
            # 图片：缩略图 + 标签
            img_row = QHBoxLayout()
            img_row.setSpacing(6)
            thumb = QLabel()
            pixmap = QPixmap(self._item["content"])
            if not pixmap.isNull():
                pixmap = pixmap.scaledToHeight(40, Qt.TransformationMode.SmoothTransformation)
                thumb.setPixmap(pixmap)
                thumb.setFixedSize(pixmap.width(), 40)
            img_row.addWidget(thumb)
            img_label = QLabel("[图片]")
            img_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
            img_row.addWidget(img_label)
            img_row.addStretch()
            content_layout.addLayout(img_row)

        # 时间戳 + 置顶标记
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(8)
        time_str = self._format_time(self._item["created_at"])
        time_label = QLabel(time_str)
        time_label.setStyleSheet(f"color: {TEXT_HINT}; font-size: {FONT_SIZE_SMALL}px;")
        footer_layout.addWidget(time_label)

        if self._pinned:
            pinned_badge = QLabel("📌 已置顶")
            pinned_badge.setStyleSheet(f"""
                color: {PIN_COLOR};
                font-size: 11px;
                font-weight: 500;
                background: #FFF3E0;
                border-radius: 4px;
                padding: 1px 6px;
            """)
            footer_layout.addWidget(pinned_badge)

        footer_layout.addStretch()
        content_layout.addLayout(footer_layout)

        layout.addLayout(content_layout, 1)

        # 右侧按钮区
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(4)

        # 永久保存按钮
        save_btn = QPushButton("⭐")
        save_btn.setFixedSize(28, 28)
        save_btn.setToolTip("永久保存" if not self._saved else "取消保存")
        save_btn.setStyleSheet(self._save_btn_style())
        save_btn.clicked.connect(lambda: self.save_toggled.emit(self._item["id"]))
        btn_layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # 置顶按钮
        pin_btn = QPushButton("📌")
        pin_btn.setFixedSize(28, 28)
        pin_btn.setToolTip("置顶" if not self._pinned else "取消置顶")
        pin_btn.setStyleSheet(self._pin_btn_style())
        pin_btn.clicked.connect(lambda: self.pin_toggled.emit(self._item["id"]))
        btn_layout.addWidget(pin_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # 删除按钮
        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(28, 28)
        del_btn.setToolTip("删除")
        del_btn.setStyleSheet(self._del_btn_style())
        del_btn.clicked.connect(lambda: self.delete_clicked.emit(self._item["id"]))
        btn_layout.addWidget(del_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(btn_layout)

    def mousePressEvent(self, event):
        """点击卡片：图片→预览弹窗，文字空白处→复制全文（文字编辑区可选取）"""
        if self._item["type"] == "image":
            self.preview_clicked.emit(self._item["id"])
        else:
            # 点文字编辑区 → 不触发复制，让用户自由选取文字
            if hasattr(self, '_text_edit'):
                pos = self._text_edit.mapFrom(self, event.position().toPoint())
                if self._text_edit.rect().contains(pos):
                    return
            self.copy_clicked.emit(self._item["id"])

    def _card_style(self):
        if self._saved:
            return f"""
                #clipCard {{
                    background: {SAVE_BG};
                    border-radius: {CARD_RADIUS}px;
                    border: 1.5px solid {SAVE_BORDER};
                }}
                #clipCard:hover {{
                    border: 1.5px solid {SAVE_COLOR};
                }}
            """
        if self._pinned:
            return f"""
                #clipCard {{
                    background: #FFF8E1;
                    border-radius: {CARD_RADIUS}px;
                    border: 1.5px solid {PIN_COLOR};
                }}
                #clipCard:hover {{
                    border: 1.5px solid #F57C00;
                }}
            """
        else:
            return f"""
                #clipCard {{
                    background: {BG_CARD};
                    border-radius: {CARD_RADIUS}px;
                    border: 1px solid {DIVIDER};
                }}
                #clipCard:hover {{
                    border: 1px solid {ACCENT};
                }}
            """

    def _pin_btn_style(self):
        if self._pinned:
            return f"""
                QPushButton {{
                    background: #FFF3E0;
                    border: 1px solid {PIN_COLOR};
                    border-radius: 6px;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background: #FFE0B2;
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    font-size: 14px;
                    color: {PIN_INACTIVE};
                }}
                QPushButton:hover {{
                    color: {PIN_COLOR};
                    background: {ACCENT_LIGHT};
                    border-radius: 6px;
                }}
            """

    def _save_btn_style(self):
        if self._saved:
            return f"""
                QPushButton {{
                    background: {SAVE_HOVER_BG};
                    border: 1px solid {SAVE_COLOR};
                    border-radius: 6px;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background: #D1C4E9;
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    font-size: 14px;
                    color: {TEXT_HINT};
                }}
                QPushButton:hover {{
                    color: {SAVE_COLOR};
                    background: {SAVE_HOVER_BG};
                    border-radius: 6px;
                }}
            """

    def _del_btn_style(self):
        return f"""
            QPushButton {{
                background: transparent;
                border: none;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {DELETE_HOVER_BG};
                border-radius: 4px;
            }}
        """

    @staticmethod
    def _format_time(iso_str: str) -> str:
        try:
            dt = datetime.fromisoformat(iso_str)
            now = datetime.now()
            diff = now - dt
            if diff.seconds < 60:
                return "刚刚"
            elif diff.seconds < 3600:
                return f"{diff.seconds // 60}分钟前"
            elif diff.days == 0:
                return f"{diff.seconds // 3600}小时前"
            elif diff.days == 1:
                return "昨天 " + dt.strftime("%H:%M")
            else:
                return dt.strftime("%m-%d %H:%M")
        except Exception:
            return iso_str


class ImagePreviewDialog(QWidget):
    """全屏图片预览弹窗 — 半透明遮罩 + 居中大图 + 复制/关闭按钮"""

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self._image_path = image_path
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._setup_ui()

    def _setup_ui(self):
        import os as _os
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.availableGeometry())
        else:
            self.resize(800, 600)

        # 半透明遮罩背景
        self.setStyleSheet("ImagePreviewDialog { background: rgba(0, 0, 0, 180); }")

        # 居中布局
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 白色卡片
        self._card = QFrame()
        self._card.setObjectName("previewCard")
        self._card.setCursor(Qt.CursorShape.ArrowCursor)
        self._card.setStyleSheet(f"""
            #previewCard {{
                background: {BG_CARD};
                border-radius: 16px;
                border: 1px solid {BORDER};
            }}
        """)
        self._card.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

        card_layout = QVBoxLayout(self._card)
        card_layout.setContentsMargins(16, 16, 16, 12)
        card_layout.setSpacing(10)

        # 图片
        pixmap = QPixmap(self._image_path)
        if pixmap.isNull():
            error_label = QLabel("图片文件不存在或已损坏")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 14px; padding: 40px;")
            card_layout.addWidget(error_label)
        else:
            max_w = int(self.width() * 0.8)
            max_h = int(self.height() * 0.8)
            scaled = pixmap.scaled(max_w, max_h,
                                   Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
            img_label = QLabel()
            img_label.setPixmap(scaled)
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_label.setStyleSheet("background: transparent; border: none;")
            img_label.setMaximumSize(max_w, max_h)
            card_layout.addWidget(img_label)

        # 按钮栏
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addStretch()

        copy_btn = QPushButton("复制")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background: {ACCENT_HOVER}; }}
        """)
        copy_btn.clicked.connect(self._on_copy)
        btn_layout.addWidget(copy_btn)

        close_btn = QPushButton("关闭")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BG_CARD};
                color: {TEXT_SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 8px 24px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {DIVIDER};
                color: {TEXT_PRIMARY};
            }}
        """)
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        card_layout.addLayout(btn_layout)
        outer.addWidget(self._card)

    def _on_copy(self):
        """复制原图到剪贴板并关闭"""
        pixmap = QPixmap(self._image_path)
        if pixmap.isNull():
            return
        QApplication.clipboard().setPixmap(pixmap)
        self.close()
        # Toast 通知（通过父窗口）
        p = self.parent()
        if p and hasattr(p, '_show_toast'):
            p._show_toast("✅ 已复制到剪贴板")

    def mousePressEvent(self, event):
        """点击遮罩空白处关闭"""
        child = self.childAt(event.position().toPoint())
        if child is not None and (child is self._card or self._card.isAncestorOf(child)):
            return
        self.close()

    def keyPressEvent(self, event):
        """Esc 关闭"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


class MainWindow(QMainWindow):
    """主窗口"""

    auto_start_changed = pyqtSignal(bool)  # 开机自启状态变化 → 通知托盘同步

    def __init__(self, monitor=None):
        super().__init__()
        self._monitor = monitor  # 剪贴板监听器引用
        self._current_tab = "all"  # 当前标签页: "all" | "saved"
        self._current_filter = "all"  # 当前类型筛选: "all" | "text" | "image"
        self.setWindowTitle("历史剪贴板")
        self.resize(480, 600)
        self.setMinimumSize(400, 500)

        # 全局样式
        self.setStyleSheet(GLOBAL_STYLESHEET)

        # 中央 Widget
        central = QWidget()
        central.setStyleSheet(f"background: {BG_MAIN};")
        self.setCentralWidget(central)

        self._main_layout = QVBoxLayout(central)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # 顶栏
        self._setup_top_bar()
        # 标签页栏
        self._setup_tab_bar()
        # 类型筛选栏
        self._setup_filter_bar()
        # 滚动列表
        self._setup_list_area()
        # Toast
        self._setup_toast()
        # 设置面板（初始隐藏）
        self._settings_panel = None

        # 初始加载
        self._refresh_list()

        # 定时清理过期
        self._cleanup_timer = QTimer(self)
        self._cleanup_timer.timeout.connect(self._auto_cleanup)
        self._cleanup_timer.start(3600000)  # 每小时

        # 启动时清理
        clean_expired()

    def _setup_top_bar(self):
        """顶栏：搜索框 + 设置按钮"""
        top_bar = QWidget()
        top_bar.setFixedHeight(TOP_BAR_HEIGHT)
        top_bar.setStyleSheet(f"background: {BG_MAIN}; border-bottom: 1px solid {BORDER};")

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(12, 8, 8, 8)
        layout.setSpacing(8)

        # 搜索框
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("搜索剪贴板历史...")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: {SEARCH_RADIUS}px;
                padding: 6px 12px;
                font-size: 14px;
                color: {TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border: 1px solid {ACCENT};
            }}
        """)
        self._search_input.textChanged.connect(self._on_search)
        layout.addWidget(self._search_input)

        # 设置按钮
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(32, 32)
        settings_btn.setToolTip("设置")
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                font-size: 18px;
                color: {TEXT_SECONDARY};
            }}
            QPushButton:hover {{
                color: {ACCENT};
                background: {ACCENT_LIGHT};
                border-radius: 6px;
            }}
        """)
        settings_btn.clicked.connect(self._toggle_settings)
        layout.addWidget(settings_btn)

        self._main_layout.addWidget(top_bar)

    def _setup_tab_bar(self):
        """标签页栏：全部记录 | ⭐ 收藏"""
        tab_bar = QWidget()
        tab_bar.setFixedHeight(TAB_BAR_HEIGHT)
        tab_bar.setStyleSheet(f"background: {BG_MAIN}; border-bottom: 1px solid {BORDER};")

        layout = QHBoxLayout(tab_bar)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(0)

        # 全部记录 标签
        self._tab_all = QPushButton("全部记录")
        self._tab_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self._tab_all.clicked.connect(lambda: self._switch_tab("all"))
        layout.addWidget(self._tab_all)

        # 收藏 标签
        self._tab_saved = QPushButton("⭐ 收藏")
        self._tab_saved.setCursor(Qt.CursorShape.PointingHandCursor)
        self._tab_saved.clicked.connect(lambda: self._switch_tab("saved"))
        layout.addWidget(self._tab_saved)

        layout.addStretch()
        self._main_layout.addWidget(tab_bar)

        # 初始状态
        self._update_tab_styles()

    def _switch_tab(self, tab: str):
        """切换标签页"""
        if self._current_tab == tab:
            return
        self._current_tab = tab
        self._update_tab_styles()
        # 切换到收藏时清空搜索并隐藏；切回时恢复
        if tab == "saved":
            self._search_input.clear()
            self._search_input.setVisible(False)
        else:
            self._search_input.setVisible(True)
        self._refresh_list()

    def _update_tab_styles(self):
        """更新标签页按钮样式 + 收藏徽标数字"""
        is_all = self._current_tab == "all"
        self._tab_all.setStyleSheet(TAB_ACTIVE if is_all else TAB_INACTIVE)
        self._tab_saved.setStyleSheet(TAB_ACTIVE if not is_all else TAB_INACTIVE)
        # 更新收藏徽标
        if not is_all:
            self._tab_saved.setText(f"⭐ 收藏 ({get_saved_count()})")
        else:
            self._tab_saved.setText("⭐ 收藏")

    def _setup_filter_bar(self):
        """类型筛选栏：全部 | 文字 | 图片"""
        bar = QWidget()
        bar.setFixedHeight(FILTER_BAR_HEIGHT)
        bar.setStyleSheet(f"background: {BG_MAIN}; border-bottom: 1px solid {BORDER};")

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 2, 12, 2)
        layout.setSpacing(6)

        self._filter_btns = {}
        for key, label in [("all", "全部"), ("text", "文字"), ("image", "图片")]:
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._switch_filter(k))
            self._filter_btns[key] = btn
            layout.addWidget(btn)

        layout.addStretch()
        self._main_layout.addWidget(bar)
        self._update_filter_styles()

    def _switch_filter(self, filter_type: str):
        """切换类型筛选"""
        if self._current_filter == filter_type:
            return
        self._current_filter = filter_type
        self._update_filter_styles()
        self._refresh_list()

    def _update_filter_styles(self):
        """更新筛选按钮样式"""
        for key, btn in self._filter_btns.items():
            btn.setStyleSheet(FILTER_BTN_ACTIVE if key == self._current_filter else FILTER_BTN_INACTIVE)

    def _setup_list_area(self):
        """滚动卡片列表区域"""
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setStyleSheet(f"background: {BG_MAIN}; border: none;")

        self._list_container = QWidget()
        self._list_container.setStyleSheet(f"background: {BG_MAIN};")
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(LIST_PADDING, LIST_PADDING, LIST_PADDING, LIST_PADDING)
        self._list_layout.setSpacing(CARD_GAP)
        self._list_layout.addStretch()

        self._scroll_area.setWidget(self._list_container)
        self._main_layout.addWidget(self._scroll_area, 1)

    def _setup_toast(self):
        """底部 Toast 提示"""
        self._toast = QLabel(self)
        self._toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._toast.setStyleSheet(f"""
            QLabel {{
                background: {TEXT_PRIMARY};
                color: white;
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 13px;
            }}
        """)
        self._toast.setVisible(False)
        self._toast.raise_()

    def _create_saved_section_header(self, count: int) -> QWidget:
        """创建「已保存」分区标题"""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 6, 0, 2)
        layout.setSpacing(6)

        icon = QLabel("⭐")
        icon.setStyleSheet("font-size: 13px;")
        layout.addWidget(icon)

        label = QLabel(f"已保存 ({count}/10)")
        label.setStyleSheet(f"color: {SAVE_COLOR}; font-size: 12px; font-weight: 500;")
        layout.addWidget(label)

        if count >= 10:
            full = QLabel("已满")
            full.setStyleSheet(f"""
                color: {DELETE_COLOR}; font-size: 10px;
                background: {DELETE_HOVER_BG}; border-radius: 3px;
                padding: 1px 5px;
            """)
            layout.addWidget(full)

        layout.addStretch()
        return header

    def _create_divider(self) -> QFrame:
        """创建水平分隔线"""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color: {DIVIDER}; margin: 4px 0;")
        return line

    def _refresh_list(self):
        """刷新卡片列表 — 按当前标签页过滤"""
        # 清除现有卡片（保留最后的 stretch）
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 加载数据
        search = self._search_input.text().strip() if hasattr(self, '_search_input') else ""
        items = get_items(search)

        # 按标签页过滤：收藏和全部互斥
        if self._current_tab == "saved":
            items = [i for i in items if i.get("saved")]
        else:
            items = [i for i in items if not i.get("saved")]

        # 按类型筛选
        if self._current_filter == "text":
            items = [i for i in items if i["type"] == "text"]
        elif self._current_filter == "image":
            items = [i for i in items if i["type"] == "image"]

        if not items:
            empty_map = {
                ("saved", "all"): "⭐\n还没有永久保存的记录\n点击卡片上的 ⭐ 按钮保存",
                ("saved", "text"): "⭐\n还没有永久保存的文字记录",
                ("saved", "image"): "⭐\n还没有永久保存的图片记录",
                ("all", "text"): "📋\n还没有文字记录\n试试复制一些文字吧",
                ("all", "image"): "📋\n还没有图片记录\n试试复制一张图片吧",
                ("all", "all"): "📋\n还没有复制记录\n试试复制一些文字或图片吧",
            }
            empty_text = empty_map.get(
                (self._current_tab, self._current_filter),
                "📋\n暂无记录",
            )
            empty = QLabel(empty_text)
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color: {TEXT_HINT}; font-size: 14px; padding: 40px 0;")
            self._list_layout.insertWidget(0, empty)
            return

        def _wire_card(card):
            card.save_toggled.connect(self._on_save)
            card.pin_toggled.connect(self._on_pin)
            card.delete_clicked.connect(self._on_delete)
            card.copy_clicked.connect(self._on_copy)
            card.preview_clicked.connect(self._on_preview)

        insert_pos = 0
        for item in items:
            card = ClipCard(item)
            _wire_card(card)
            self._list_layout.insertWidget(insert_pos, card)
            insert_pos += 1

    def _on_search(self, text):
        """搜索文字变化"""
        self._refresh_list()

    def _on_pin(self, item_id: int):
        """置顶切换"""
        toggle_pin(item_id)
        self._refresh_list()

    def _on_save(self, item_id: int):
        """永久保存切换"""
        result = toggle_save(item_id)
        if result is None:
            self._show_toast("❌ 最多永久保存 10 条记录")
            return
        self._update_tab_styles()
        self._refresh_list()
        if result:
            self._show_toast("⭐ 已永久保存")
        else:
            self._show_toast("✅ 已取消保存")

    def _on_delete(self, item_id: int):
        """删除记录"""
        delete_item(item_id)
        self._refresh_list()

    def _on_copy(self, item_id: int):
        """复制到剪贴板"""
        items = get_items()
        target = next((i for i in items if i["id"] == item_id), None)
        if not target:
            return

        clipboard = QApplication.clipboard()
        if target["type"] == "text":
            clipboard.setText(target["content"])
        else:
            pixmap = QPixmap(target["content"])
            if not pixmap.isNull():
                clipboard.setPixmap(pixmap)

        # 告诉监听器：这是我放的，暂停一下别重复记录
        if self._monitor:
            self._monitor.pause()

        self._show_toast("✅ 已复制到剪贴板")

    def _on_preview(self, item_id: int):
        """弹出图片大图预览窗口"""
        items = get_items()
        target = next((i for i in items if i["id"] == item_id), None)
        if not target or target["type"] != "image":
            return

        # 暂停监听器，防止预览窗口中复制操作被重新记录
        if self._monitor:
            self._monitor.pause(2000)

        dialog = ImagePreviewDialog(target["content"], parent=self)
        dialog.show()

    def _show_toast(self, message: str):
        """显示 Toast"""
        self._toast.setText(message)
        self._toast.adjustSize()
        x = (self.width() - self._toast.width()) // 2
        y = self.height() - 60
        self._toast.move(x, y)
        self._toast.setVisible(True)
        self._toast.raise_()
        QTimer.singleShot(2000, lambda: self._toast.setVisible(False))

    def resizeEvent(self, event):
        """窗口大小变化时重新定位 Toast"""
        super().resizeEvent(event)
        if hasattr(self, '_toast') and self._toast.isVisible():
            x = (self.width() - self._toast.width()) // 2
            y = self.height() - 60
            self._toast.move(x, y)

    # === 设置面板 ===

    def _toggle_settings(self):
        """切换设置面板"""
        if self._settings_panel and self._settings_panel.isVisible():
            self._settings_panel.hide()
        else:
            self._show_settings()

    def _show_settings(self):
        """显示设置面板（浮层）"""
        if not self._settings_panel:
            self._settings_panel = self._create_settings_panel()
        self._settings_panel.setVisible(True)
        self._settings_panel.raise_()

    def _create_settings_panel(self) -> QFrame:
        """创建设置浮层面板"""
        panel = QFrame(self)
        panel.setFixedSize(300, 430)
        panel.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # 标题
        title = QLabel("⚙ 设置")
        title.setStyleSheet(f"font-size: 16px; font-weight: 500; color: {TEXT_PRIMARY};")
        layout.addWidget(title)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {DIVIDER};")
        layout.addWidget(sep)

        # 保留天数
        layout.addWidget(QLabel("保留天数:"))
        days_layout = QHBoxLayout()
        days_layout.setSpacing(8)
        self._day_btns = {}
        current_days = get_setting("retention_days", "3")
        for days, label in [("1", "1天"), ("3", "3天"), ("5", "5天")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(days == current_days)
            btn.setStyleSheet(self._day_btn_style(days == current_days))
            btn.clicked.connect(lambda checked, d=days: self._on_days_changed(d))
            self._day_btns[days] = btn
            days_layout.addWidget(btn)
        layout.addLayout(days_layout)

        # 记录总数
        count = get_item_count()
        count_label = QLabel(f"当前记录：{count} 条")
        count_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(count_label)

        # 开机自启开关
        from PyQt6.QtWidgets import QCheckBox
        self._auto_start_cb = QCheckBox("开机自动启动（隐藏到托盘）")
        self._auto_start_cb.setChecked(is_startup_enabled())
        self._auto_start_cb.setStyleSheet(f"""
            QCheckBox {{
                color: {TEXT_PRIMARY};
                font-size: 13px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
            }}
        """)
        self._auto_start_cb.toggled.connect(self._on_auto_start_toggled)
        layout.addWidget(self._auto_start_cb)

        # 关闭窗口行为
        self._close_quit_cb = QCheckBox("关闭窗口时直接退出程序")
        self._close_quit_cb.setChecked(get_setting("close_action") == "quit")
        self._close_quit_cb.setStyleSheet(f"""
            QCheckBox {{
                color: {TEXT_PRIMARY};
                font-size: 13px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
            }}
        """)
        self._close_quit_cb.toggled.connect(self._on_close_action_toggled)
        layout.addWidget(self._close_quit_cb)

        # 手动清理按钮
        clean_btn = QPushButton("立即清理过期记录")
        clean_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {ACCENT_HOVER};
            }}
        """)
        clean_btn.clicked.connect(self._manual_cleanup)
        layout.addWidget(clean_btn)

        # 一键清除所有按钮
        clear_all_btn = QPushButton("🗑 清除全部记录")
        clear_all_btn.setStyleSheet(f"""
            QPushButton {{
                background: white;
                color: {DELETE_COLOR};
                border: 1px solid {DELETE_COLOR};
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {DELETE_HOVER_BG};
            }}
        """)
        clear_all_btn.clicked.connect(self._clear_all)
        layout.addWidget(clear_all_btn)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_HINT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 6px;
            }}
            QPushButton:hover {{
                background: {DIVIDER};
            }}
        """)
        close_btn.clicked.connect(panel.hide)
        layout.addWidget(close_btn)

        layout.addStretch()

        # 定位：右上角
        panel.move(self.width() - 310, 50)
        return panel

    def _day_btn_style(self, checked: bool) -> str:
        if checked:
            return f"""
                QPushButton {{
                    background: {ACCENT};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-size: 13px;
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background: {ACCENT_LIGHT};
                    color: {TEXT_SECONDARY};
                    border: 1px solid {BORDER};
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    border: 1px solid {ACCENT};
                }}
            """

    def _on_days_changed(self, days: str):
        """保留天数切换"""
        save_setting("retention_days", days)
        for d, btn in self._day_btns.items():
            btn.setStyleSheet(self._day_btn_style(d == days))
            btn.setChecked(d == days)

    def _on_auto_start_toggled(self, checked: bool):
        """开机自启开关切换"""
        if checked:
            success, msg = add_to_startup()
            if not success:
                self._auto_start_cb.blockSignals(True)
                self._auto_start_cb.setChecked(False)
                self._auto_start_cb.blockSignals(False)
                self._show_toast(f"❌ 设置开机自启失败\n{msg}")
                return
        else:
            remove_from_startup()
        save_setting("auto_start", "1" if checked else "0")
        # 通知托盘菜单同步状态
        self.auto_start_changed.emit(checked)

    def _on_close_action_toggled(self, checked: bool):
        """关闭窗口行为切换"""
        save_setting("close_action", "quit" if checked else "tray")

    def _manual_cleanup(self):
        """手动清理过期"""
        if self._monitor:
            self._monitor.pause()
        clean_expired()
        self._refresh_list()
        self._show_toast("✅ 已清理过期记录")

    def _clear_all(self):
        """一键清除全部记录"""
        if self._monitor:
            self._monitor.pause(2000)  # 暂停2秒，确保清除后不被重新记录
        clear_all()
        self._refresh_list()
        self._show_toast("✅ 已清除全部记录")

    def _auto_cleanup(self):
        """自动清理"""
        clean_expired()
        self._refresh_list()

    def add_new_item(self, item: dict):
        """外部调用：收到新剪贴板内容时刷新列表"""
        self._refresh_list()

    def closeEvent(self, event):
        """关闭窗口：按设置决定隐藏托盘还是直接退出"""
        if get_setting("close_action") == "quit":
            event.accept()
            QApplication.quit()
        else:
            event.ignore()
            self.hide()
