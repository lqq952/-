"""剪贴板监听器 - 信号驱动 + 防抖 + 数据库去重"""
import hashlib
import os
from datetime import datetime
from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication

from .database import add_item, get_items, get_item_by_content, bump_item, IMAGES_DIR


class ClipboardMonitor(QObject):
    """剪贴板变化监听器"""

    new_item_detected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._paused = False          # 暂停标记（应用自身操作时）
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._do_check)
        self._running = False
        self._recent_texts = set()       # 短时内存去重（2秒）
        self._recent_image_hashes = set()  # 短时内存去重（2秒）

    def start(self):
        """开始监听"""
        if not self._running:
            self._running = True
            clipboard = QApplication.clipboard()
            clipboard.dataChanged.connect(self._on_clipboard_change)
            # 初始把当前内容标记为已知（不记录）
            self._paused = True
            QTimer.singleShot(1000, self._resume)

    def pause(self, duration_ms: int = 1000):
        """暂停监听，duration_ms 后自动恢复"""
        self._paused = True
        QTimer.singleShot(duration_ms, self._resume)

    def _resume(self):
        """恢复监听"""
        self._paused = False

    def stop(self):
        """停止监听"""
        self._running = False
        clipboard = QApplication.clipboard()
        try:
            clipboard.dataChanged.disconnect(self._on_clipboard_change)
        except Exception:
            pass

    def _on_clipboard_change(self):
        """剪贴板变化信号 → 防抖 300ms 后处理"""
        if not self._running:
            return
        self._debounce_timer.start(300)

    def _do_check(self):
        """实际检查剪贴板内容 — 图片优先，文件路径次之，纯文本兜底"""
        if self._paused:
            return

        try:
            clipboard = QApplication.clipboard()
            mime = clipboard.mimeData()

            # 1. 直接的图片数据（浏览器右键复制、截图工具、画图板）
            if mime.hasImage():
                image = clipboard.image()
                if not image.isNull():
                    self._maybe_save_image(image)
                    return

            # 2. 文件 URL → 检测是否是图片文件（文件管理器复制）
            if mime.hasUrls():
                from PyQt6.QtGui import QPixmap
                for url in mime.urls():
                    path = url.toLocalFile()
                    if path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff')):
                        pixmap = QPixmap(path)
                        if not pixmap.isNull():
                            self._maybe_save_image(pixmap.toImage())
                            return
                # 非图片文件 → 把路径当文字处理
                text = clipboard.text()
                if text and text.strip():
                    self._maybe_save_text(text)
                return

            # 3. 纯文本
            text = clipboard.text()
            if text and text.strip():
                self._maybe_save_text(text)
        except Exception:
            pass

    def _maybe_save_text(self, text: str):
        """全局内容去重：已存在则置顶，不存在才新增"""
        # 1. 内存级短时去重（防止同一秒内重复信号反复写库）
        if text in self._recent_texts:
            return
        self._recent_texts.add(text)
        QTimer.singleShot(2000, lambda: self._recent_texts.discard(text))

        # 2. 数据库全局查重
        existing = get_item_by_content("text", text)
        if existing:
            # 已存在：更新时间戳（置顶效果）
            bump_item(existing["id"])
            existing["created_at"] = datetime.now().isoformat()
            self.new_item_detected.emit(existing)
            return

        # 3. 真正的新内容
        add_item("text", text, len(text.encode("utf-8")))
        self.new_item_detected.emit({
            "type": "text",
            "content": text,
            "created_at": datetime.now().isoformat(),
        })

    def _maybe_save_image(self, image):
        """保存图片（通过 hash 全局去重）"""
        try:
            img_hash = self._hash_image(image)
            if not img_hash:
                return

            # 1. 内存级短时去重
            if img_hash in self._recent_image_hashes:
                return
            self._recent_image_hashes.add(img_hash)
            QTimer.singleShot(2000, lambda: self._recent_image_hashes.discard(img_hash))

            # 2. 数据库全局查重：遍历所有图片记录比对哈希
            all_items = get_items(limit=1000)
            for item in all_items:
                if item["type"] == "image" and os.path.exists(item["content"]):
                    try:
                        from PyQt6.QtGui import QPixmap
                        existing = QPixmap(item["content"])
                        if not existing.isNull():
                            eh = self._hash_image(existing.toImage())
                            if eh == img_hash:
                                # 已存在：置顶
                                bump_item(item["id"])
                                item["created_at"] = datetime.now().isoformat()
                                self.new_item_detected.emit(item)
                                return
                    except Exception:
                        pass

            # 3. 真正的新图片
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{timestamp}.png"
            filepath = os.path.join(IMAGES_DIR, filename)
            image.save(filepath, "PNG")
            file_size = os.path.getsize(filepath)

            add_item("image", filepath, file_size)
            self.new_item_detected.emit({
                "type": "image",
                "content": filepath,
                "created_at": datetime.now().isoformat(),
            })
        except Exception:
            pass

    @staticmethod
    def _hash_image(image) -> str:
        try:
            bits = image.constBits()
            size = image.sizeInBytes()
            if bits and size > 0:
                return hashlib.md5(bits.asstring(size)).hexdigest()
        except Exception:
            pass
        return ""
