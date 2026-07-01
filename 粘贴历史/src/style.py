"""UI 样式常量 - 淡蓝色主题"""

# === 色彩 ===
BG_MAIN = "#F0F7FF"
BG_CARD = "#FFFFFF"
BG_SEARCH = "#FFFFFF"
BG_SETTINGS = "#FFFFFF"

ACCENT = "#42A5F5"
ACCENT_HOVER = "#1E88E5"
ACCENT_LIGHT = "#E3F2FD"

TEXT_PRIMARY = "#212121"
TEXT_SECONDARY = "#616161"
TEXT_HINT = "#9E9E9E"

BORDER = "#E0E0E0"
DIVIDER = "#EEEEEE"

PIN_COLOR = "#FFA726"
PIN_INACTIVE = "#BDBDBD"
DELETE_COLOR = "#EF5350"
DELETE_HOVER_BG = "#FFEBEE"
SUCCESS = "#66BB6A"

# === 保存/永久保留颜色 ===
SAVE_COLOR    = "#7E57C2"   # 紫色主色
SAVE_HOVER_BG = "#EDE7F6"   # 浅紫悬停
SAVE_BG       = "#F3E5F5"   # 已保存卡片背景
SAVE_BORDER   = "#CE93D8"   # 已保存卡片边框

# === 尺寸 ===
WINDOW_WIDTH = 480
WINDOW_HEIGHT = 600
WINDOW_MIN_WIDTH = 400
WINDOW_MIN_HEIGHT = 500

TOP_BAR_HEIGHT = 48
TAB_BAR_HEIGHT = 40
CARD_PADDING = 14
CARD_RADIUS = 10
CARD_GAP = 8
LIST_PADDING = 12

SEARCH_RADIUS = 8

# === 字体 ===
FONT_FAMILY = '"Microsoft YaHei", "微软雅黑", sans-serif'
FONT_SIZE_TITLE = 14
FONT_SIZE_BODY = 13
FONT_SIZE_SMALL = 12

# === 全局样式表 ===
GLOBAL_STYLESHEET = f"""
QWidget {{
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_BODY}px;
    color: {TEXT_PRIMARY};
}}

QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {TEXT_HINT};
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: none;
}}
"""

# === 标签页栏样式 ===
TAB_INACTIVE = f"""
    QPushButton {{
        background: transparent;
        color: {TEXT_SECONDARY};
        border: none;
        border-radius: 0;
        padding: 8px 20px;
        font-size: 13px;
        font-weight: normal;
        border-bottom: 2px solid transparent;
    }}
    QPushButton:hover {{
        color: {ACCENT};
        background: {ACCENT_LIGHT};
    }}
"""

TAB_ACTIVE = f"""
    QPushButton {{
        background: transparent;
        color: {ACCENT};
        border: none;
        border-radius: 0;
        padding: 8px 20px;
        font-size: 13px;
        font-weight: 600;
        border-bottom: 2px solid {ACCENT};
    }}
"""

# === 筛选按钮栏样式 ===
FILTER_BAR_HEIGHT = 36

FILTER_BTN_INACTIVE = f"""
    QPushButton {{
        background: transparent;
        color: {TEXT_SECONDARY};
        border: none;
        border-radius: 14px;
        padding: 4px 14px;
        font-size: 12px;
    }}
    QPushButton:hover {{
        color: {ACCENT};
        background: {ACCENT_LIGHT};
    }}
"""

FILTER_BTN_ACTIVE = f"""
    QPushButton {{
        background: {ACCENT};
        color: white;
        border: none;
        border-radius: 14px;
        padding: 4px 14px;
        font-size: 12px;
        font-weight: 500;
    }}
"""
