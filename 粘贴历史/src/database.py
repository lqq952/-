"""数据库操作层 - SQLite"""
import sqlite3
import os
import shutil
from datetime import datetime, timedelta

# 数据存储目录: <项目根>/data/
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "data.db")
IMAGES_DIR = os.path.join(DATA_DIR, "images")

# 旧数据目录（用于首次迁移）
_OLD_DATA_DIR = os.path.join(os.getenv("APPDATA", ""), "clipboard-history")

# 默认设置
DEFAULT_SETTINGS = {
    "retention_days": "3",
    "max_items": "500",
    "auto_start": "1",
    "close_action": "tray",  # "tray"=隐藏托盘, "quit"=直接退出
}


def init_db():
    """初始化数据库和存储目录"""
    # 首次迁移：必须在创建新数据库之前执行
    _migrate_from_appdata()

    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clipboard_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            type        TEXT    NOT NULL,
            content     TEXT    NOT NULL,
            pinned      INTEGER DEFAULT 0,
            file_size   INTEGER DEFAULT 0,
            created_at  TEXT    NOT NULL,
            expires_at  TEXT    NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    # 写入默认设置（如不存在）
    for key, value in DEFAULT_SETTINGS.items():
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )

    # 迁移：添加 saved 列（忽略已存在错误）
    try:
        conn.execute("ALTER TABLE clipboard_items ADD COLUMN saved INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


def _migrate_from_appdata():
    """如果旧数据目录存在且新数据目录尚无 data.db，则迁移数据"""
    if not _OLD_DATA_DIR or not os.path.isdir(_OLD_DATA_DIR):
        return

    old_db = os.path.join(_OLD_DATA_DIR, "data.db")
    old_images = os.path.join(_OLD_DATA_DIR, "images")

    # 新目录不存在或 data.db 不存在时才迁移
    if os.path.exists(old_db) and not os.path.exists(DB_PATH):
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(IMAGES_DIR, exist_ok=True)

        # 复制数据库文件
        shutil.copy2(old_db, DB_PATH)
        print(f"[迁移] 数据库已复制: {old_db} -> {DB_PATH}")

        # 复制图片目录
        if os.path.isdir(old_images):
            for fname in os.listdir(old_images):
                src = os.path.join(old_images, fname)
                dst = os.path.join(IMAGES_DIR, fname)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
            print(f"[迁移] 图片已复制: {old_images} -> {IMAGES_DIR}")


def get_connection():
    """获取数据库连接"""
    return sqlite3.connect(DB_PATH)


def get_item_by_content(item_type: str, content: str) -> dict | None:
    """按内容查重，返回匹配的第一条记录或 None"""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM clipboard_items WHERE type = ? AND content = ? ORDER BY created_at DESC LIMIT 1",
        (item_type, content),
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "type": row[1],
        "content": row[2],
        "pinned": bool(row[3]),
        "file_size": row[4],
        "created_at": row[5],
        "expires_at": row[6],
        "saved": bool(row[7]) if len(row) > 7 else False,
    }


def bump_item(item_id: int):
    """更新时间戳到当前时间（置顶效果），保留 pinned/saved 状态"""
    conn = get_connection()
    conn.execute(
        "UPDATE clipboard_items SET created_at = ? WHERE id = ?",
        (datetime.now().isoformat(), item_id),
    )
    conn.commit()
    conn.close()


def add_item(item_type: str, content: str, file_size: int = 0):
    """新增一条剪贴板记录"""
    retention_days = int(get_setting("retention_days", "3"))
    now = datetime.now()
    expires = now + timedelta(days=retention_days)

    conn = get_connection()
    conn.execute(
        """INSERT INTO clipboard_items (type, content, pinned, file_size, created_at, expires_at)
           VALUES (?, ?, 0, ?, ?, ?)""",
        (item_type, content, file_size, now.isoformat(), expires.isoformat()),
    )
    conn.commit()
    conn.close()

    # 检查并执行上限清理
    enforce_max_limit()


def get_items(search: str = "", limit: int = 500):
    """获取历史列表，置顶优先+时间降序，支持搜索过滤"""
    conn = get_connection()
    if search:
        query = """
            SELECT * FROM clipboard_items
            WHERE type = 'text' AND content LIKE ?
            ORDER BY saved DESC, pinned DESC, created_at DESC
            LIMIT ?
        """
        rows = conn.execute(query, (f"%{search}%", limit)).fetchall()
    else:
        query = """
            SELECT * FROM clipboard_items
            ORDER BY saved DESC, pinned DESC, created_at DESC
            LIMIT ?
        """
        rows = conn.execute(query, (limit,)).fetchall()
    conn.close()

    items = []
    for row in rows:
        items.append({
            "id": row[0],
            "type": row[1],
            "content": row[2],
            "pinned": bool(row[3]),
            "file_size": row[4],
            "created_at": row[5],
            "expires_at": row[6],
            "saved": bool(row[7]) if len(row) > 7 else False,
        })
    return items


def toggle_pin(item_id: int) -> bool:
    """切换置顶状态，返回新状态"""
    conn = get_connection()
    row = conn.execute("SELECT pinned FROM clipboard_items WHERE id = ?", (item_id,)).fetchone()
    if row:
        new_state = 0 if row[0] else 1
        conn.execute("UPDATE clipboard_items SET pinned = ? WHERE id = ?", (new_state, item_id))
        conn.commit()
        conn.close()
        return bool(new_state)
    conn.close()
    return False


def toggle_save(item_id: int):
    """切换永久保存状态。返回 True=已保存, False=已取消, None=已达上限"""
    conn = get_connection()
    row = conn.execute("SELECT saved FROM clipboard_items WHERE id = ?", (item_id,)).fetchone()
    if not row:
        conn.close()
        return False

    if row[0] == 1:
        conn.execute("UPDATE clipboard_items SET saved = 0 WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
        return False
    else:
        count = conn.execute("SELECT COUNT(*) FROM clipboard_items WHERE saved = 1").fetchone()[0]
        if count >= 10:
            conn.close()
            return None  # 已达上限
        conn.execute("UPDATE clipboard_items SET saved = 1 WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
        return True


def get_saved_count() -> int:
    """返回当前已永久保存的数量"""
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM clipboard_items WHERE saved = 1").fetchone()[0]
    conn.close()
    return count


def delete_item(item_id: int):
    """删除单条记录（图片同时删除文件）"""
    conn = get_connection()
    row = conn.execute("SELECT type, content FROM clipboard_items WHERE id = ?", (item_id,)).fetchone()
    if row and row[0] == "image":
        img_path = row[1]
        if os.path.exists(img_path):
            os.remove(img_path)
    conn.execute("DELETE FROM clipboard_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


def clean_expired():
    """清理过期记录（跳过置顶项）"""
    conn = get_connection()
    now = datetime.now().isoformat()
    # 先删除过期图片文件（跳过置顶和已保存）
    rows = conn.execute(
        "SELECT id, content FROM clipboard_items WHERE pinned = 0 AND saved = 0 AND expires_at < ? AND type = 'image'",
        (now,),
    ).fetchall()
    for row in rows:
        img_path = row[1]
        if os.path.exists(img_path):
            os.remove(img_path)
    # 删除过期记录（跳过置顶和已保存）
    conn.execute(
        "DELETE FROM clipboard_items WHERE pinned = 0 AND saved = 0 AND expires_at < ?",
        (now,),
    )
    conn.commit()
    conn.close()


def enforce_max_limit():
    """强制上限：超出max_items则删除最旧的非置顶记录"""
    max_items = int(get_setting("max_items", "500"))
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM clipboard_items WHERE saved = 0").fetchone()[0]
    if count > max_items:
        excess = count - max_items
        # 删除最旧的excess条非置顶非保存记录（先删图片文件）
        rows = conn.execute(
            """SELECT id, content FROM clipboard_items
               WHERE pinned = 0 AND saved = 0
               ORDER BY created_at ASC LIMIT ?""",
            (excess,),
        ).fetchall()
        for row in rows:
            if os.path.exists(row[1]):
                try:
                    os.remove(row[1])
                except OSError:
                    pass
        conn.execute(
            """DELETE FROM clipboard_items WHERE id IN (
               SELECT id FROM clipboard_items
               WHERE pinned = 0 AND saved = 0
               ORDER BY created_at ASC LIMIT ?
            )""",
            (excess,),
        )
    conn.commit()
    conn.close()


def get_setting(key: str, default: str = "") -> str:
    """读取设置"""
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row[0] if row else default


def save_setting(key: str, value: str):
    """保存设置"""
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, value),
    )
    conn.commit()
    conn.close()


def clear_all():
    """一键清除所有记录（包括图片文件）"""
    conn = get_connection()
    # 先删除所有非保存图片文件
    rows = conn.execute("SELECT content FROM clipboard_items WHERE type = 'image' AND saved = 0").fetchall()
    for row in rows:
        if os.path.exists(row[0]):
            try:
                os.remove(row[0])
            except OSError:
                pass
    conn.execute("DELETE FROM clipboard_items WHERE saved = 0")
    conn.commit()
    conn.close()


def get_item_count() -> int:
    """获取当前记录总数"""
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM clipboard_items").fetchone()[0]
    conn.close()
    return count
