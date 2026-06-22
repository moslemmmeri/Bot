# ui_helpers.py
# توابع کمکی برای بهبود UX/UI
# شامل: فرمت‌بندی پیشرفته پیام‌ها، ساخت جداول متنی، ایموجی‌ها و ...

import re
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
from textwrap import fill


# ============================================================
# ایموجی‌های پرکاربرد (تکمیل شده)
# ============================================================

class Emojis:
    """ایموجی‌های پرکاربرد برای استفاده در پیام‌ها"""
    
    # وضعیت‌ها
    CHECK = "✅"
    CROSS = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    QUESTION = "❓"
    STAR = "⭐"
    HEART = "❤️"
    FIRE = "🔥"
    
    # جهات
    ARROW_UP = "⬆️"
    ARROW_DOWN = "⬇️"
    ARROW_LEFT = "⬅️"
    ARROW_RIGHT = "➡️"
    BACK = "🔙"
    NEXT = "➡️"
    
    # اشیاء
    GEAR = "⚙️"
    LOCK = "🔐"
    KEY = "🔑"
    BELL = "🔔"
    MEGAPHONE = "📢"
    ENVELOPE = "📧"
    PHONE = "📞"
    
    # فایل‌ها
    FILE = "📄"
    FOLDER = "📁"
    PHOTO = "🖼️"
    DOCUMENT = "📎"
    PDF = "📕"
    EXCEL = "📊"
    CSV = "📋"
    
    # کاربران
    USER = "👤"
    USER_GROUP = "👥"
    ADMIN = "🛡️"
    OWNER = "👑"
    
    # خدمات
    SERVICE = "🔘"
    SUBMENU = "📂"
    MENU = "📋"
    SETTINGS = "⚙️"
    
    # وضعیت سفارش
    PENDING = "⏳"
    PAID = "✅"
    COMPLETED = "🎉"
    CANCELLED = "❌"
    
    # زمان
    CLOCK = "⏰"
    CALENDAR = "📅"
    DATE = "📅"
    TIME = "⏱️"
    
    # مالی
    MONEY = "💰"
    CREDIT_CARD = "💳"
    WALLET = "👛"
    PRICE_TAG = "🏷️"
    
    # سرگرمی
    PARTY = "🎉"
    GIFT = "🎁"
    TROPHY = "🏆"
    MEDAL = "🥇"
    CROWN = "👑"
    
    # موارد متفرقه
    MAGNIFY = "🔍"
    PENCIL = "✏️"
    TRASH = "🗑️"
    SAVE = "💾"
    PRINT = "🖨️"
    COMPUTER = "💻"
    MOBILE = "📱"
    GLOBE = "🌐"
    FLAG = "🚩"
    THUMBS_UP = "👍"
    THUMBS_DOWN = "👎"
    CLAP = "👏"
    WAVE = "👋"
    SMILE = "😊"
    SAD = "😢"
    ANGRY = "😤"
    
    # اضافه شده برای آمار و تحلیل
    STATS = "📊"
    CHART = "📈"
    DASHBOARD = "📋"
    ANALYTICS = "📉"
    
    # اضافه شده برای مدیریت کاربران
    BLOCK = "🚫"
    UNBLOCK = "✅"
    SEARCH = "🔍"
    FILTER = "🎯"
    
    # اضافه شده برای پیام‌های عمومی
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING_SIGN = "⚠️"
    INFO_SIGN = "ℹ️"


# ============================================================
# فرمت‌بندی متن (همانند قبل)
# ============================================================

class TextFormatter:
    """فرمت‌بندی پیشرفته متن برای پیام‌ها"""
    
    @staticmethod
    def bold(text: str) -> str:
        return f"*{text}*"
    
    @staticmethod
    def italic(text: str) -> str:
        return f"_{text}_"
    
    @staticmethod
    def underline(text: str) -> str:
        return f"__{text}__"
    
    @staticmethod
    def strikethrough(text: str) -> str:
        return f"~{text}~"
    
    @staticmethod
    def code(text: str) -> str:
        return f"`{text}`"
    
    @staticmethod
    def code_block(text: str, language: str = "") -> str:
        if language:
            return f"```{language}\n{text}\n```"
        return f"```\n{text}\n```"
    
    @staticmethod
    def link(text: str, url: str) -> str:
        return f"[{text}]({url})"
    
    @staticmethod
    def quote(text: str) -> str:
        return f"> {text}"
    
    @staticmethod
    def spoiler(text: str) -> str:
        return f"||{text}||"
    
    @staticmethod
    def header(text: str, level: int = 1) -> str:
        if level == 1:
            return f"# {text}"
        elif level == 2:
            return f"## {text}"
        elif level == 3:
            return f"### {text}"
        return text
    
    @staticmethod
    def list_item(text: str, indent: int = 0) -> str:
        spaces = "  " * indent
        return f"{spaces}• {text}"
    
    @staticmethod
    def numbered_item(text: str, number: int, indent: int = 0) -> str:
        spaces = "  " * indent
        return f"{spaces}{number}. {text}"
    
    @staticmethod
    def horizontal_line() -> str:
        return "─" * 30
    
    @staticmethod
    def double_line() -> str:
        return "═" * 30
    
    @staticmethod
    def space(lines: int = 1) -> str:
        return "\n" * lines
    
    @staticmethod
    def format_number(num: Union[int, float]) -> str:
        if num is None:
            return "۰"
        try:
            return f"{int(num):,}"
        except:
            return str(num)
    
    @staticmethod
    def format_percentage(num: float, decimals: int = 1) -> str:
        if num is None:
            return "۰%"
        try:
            return f"{num:.{decimals}f}%"
        except:
            return f"{num}%"
    
    @staticmethod
    def format_currency(amount: int, currency: str = "ریال") -> str:
        return f"{TextFormatter.format_number(amount)} {currency}"
    
    @staticmethod
    def format_datetime(dt: Union[str, datetime]) -> str:
        if not dt:
            return "نامشخص"
        try:
            if isinstance(dt, str):
                if len(dt) > 16:
                    return dt[:16]
                return dt
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return str(dt)
    
    @staticmethod
    def format_date(dt: Union[str, datetime]) -> str:
        if not dt:
            return "نامشخص"
        try:
            if isinstance(dt, str):
                return dt[:10]
            return dt.strftime("%Y-%m-%d")
        except:
            return str(dt)
    
    @staticmethod
    def format_time(dt: Union[str, datetime]) -> str:
        if not dt:
            return "نامشخص"
        try:
            if isinstance(dt, str) and len(dt) >= 16:
                return dt[11:16]
            return dt.strftime("%H:%M")
        except:
            return str(dt)
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        if seconds < 60:
            return f"{seconds} ثانیه"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} دقیقه"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours} ساعت {minutes} دقیقه"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days} روز {hours} ساعت"


# ============================================================
# ساخت جداول متنی (همانند قبل)
# ============================================================

class TextTable:
    """ساخت جدول متنی برای نمایش در پیام‌ها"""
    
    def __init__(self, headers: List[str], align: List[str] = None):
        self.headers = headers
        self.columns = len(headers)
        self.align = align or ['l'] * self.columns
        self.rows: List[List[str]] = []
        self.widths = [len(h) for h in headers]
    
    def add_row(self, row: List[str]) -> 'TextTable':
        if len(row) > self.columns:
            row = row[:self.columns]
        elif len(row) < self.columns:
            row.extend([''] * (self.columns - len(row)))
        
        self.rows.append(row)
        for i, cell in enumerate(row):
            self.widths[i] = max(self.widths[i], len(str(cell)))
        return self
    
    def add_rows(self, rows: List[List[str]]) -> 'TextTable':
        for row in rows:
            self.add_row(row)
        return self
    
    def _format_cell(self, text: str, width: int, align: str) -> str:
        if align == 'c':
            return text.center(width)
        elif align == 'r':
            return text.rjust(width)
        else:  # 'l'
            return text.ljust(width)
    
    def _create_separator(self) -> str:
        parts = []
        for width in self.widths:
            parts.append("─" * (width + 2))
        return "┼".join(parts)
    
    def render(self, style: str = "simple") -> str:
        if style == "markdown":
            return self._render_markdown()
        elif style == "box":
            return self._render_box()
        return self._render_simple()
    
    def _render_simple(self) -> str:
        lines = []
        header_parts = []
        for i, header in enumerate(self.headers):
            header_parts.append(self._format_cell(header, self.widths[i], self.align[i]))
        lines.append(" | ".join(header_parts))
        lines.append("-" * (sum(self.widths) + 3 * (self.columns - 1)))
        for row in self.rows:
            parts = []
            for i, cell in enumerate(row):
                parts.append(self._format_cell(str(cell), self.widths[i], self.align[i]))
            lines.append(" | ".join(parts))
        return "\n".join(lines)
    
    def _render_markdown(self) -> str:
        lines = []
        header_parts = []
        for i, header in enumerate(self.headers):
            header_parts.append(self._format_cell(header, self.widths[i], 'c'))
        lines.append("| " + " | ".join(header_parts) + " |")
        sep_parts = []
        for width in self.widths:
            sep_parts.append(":" + "-" * (width) + ":")
        lines.append("|" + "|".join(sep_parts) + "|")
        for row in self.rows:
            parts = []
            for i, cell in enumerate(row):
                align = self.align[i]
                if align == 'c':
                    cell_str = cell.center(self.widths[i])
                elif align == 'r':
                    cell_str = cell.rjust(self.widths[i])
                else:
                    cell_str = cell.ljust(self.widths[i])
                parts.append(cell_str)
            lines.append("| " + " | ".join(parts) + " |")
        return "\n".join(lines)
    
    def _render_box(self) -> str:
        lines = []
        top = "┌" + "─" * (sum(self.widths) + 3 * (self.columns - 1) + 2) + "┐"
        lines.append(top)
        header_parts = []
        for i, header in enumerate(self.headers):
            header_parts.append(self._format_cell(header, self.widths[i], 'c'))
        lines.append("│ " + " │ ".join(header_parts) + " │")
        lines.append("├" + "─" * (sum(self.widths) + 3 * (self.columns - 1) + 2) + "┤")
        for row in self.rows:
            parts = []
            for i, cell in enumerate(row):
                parts.append(self._format_cell(str(cell), self.widths[i], self.align[i]))
            lines.append("│ " + " │ ".join(parts) + " │")
        bottom = "└" + "─" * (sum(self.widths) + 3 * (self.columns - 1) + 2) + "┘"
        lines.append(bottom)
        return "\n".join(lines)


# ============================================================
# ساخت کارت‌های اطلاعاتی (همانند قبل)
# ============================================================

class InfoCard:
    """ساخت کارت اطلاعاتی با فرمت زیبا"""
    
    @staticmethod
    def create(title: str, items: Dict[str, Any], emoji: str = "📋") -> str:
        lines = [
            f"{emoji} **{title}**",
            TextFormatter.horizontal_line()
        ]
        for key, value in items.items():
            if value is not None and value != "":
                lines.append(f"**{key}:** {value}")
        lines.append(TextFormatter.horizontal_line())
        return "\n".join(lines)


# ============================================================
# ساخت پیام‌های وضعیت (همانند قبل)
# ============================================================

class StatusMessage:
    """ساخت پیام‌های وضعیت با فرمت زیبا"""
    
    @staticmethod
    def success(message: str, details: Dict[str, Any] = None) -> str:
        msg = f"{Emojis.CHECK} **موفقیت**\n\n{message}"
        if details:
            for key, value in details.items():
                msg += f"\n**{key}:** {value}"
        return msg
    
    @staticmethod
    def error(message: str, details: Dict[str, Any] = None) -> str:
        msg = f"{Emojis.CROSS} **خطا**\n\n{message}"
        if details:
            for key, value in details.items():
                msg += f"\n**{key}:** {value}"
        return msg
    
    @staticmethod
    def warning(message: str, details: Dict[str, Any] = None) -> str:
        msg = f"{Emojis.WARNING_SIGN} **هشدار**\n\n{message}"
        if details:
            for key, value in details.items():
                msg += f"\n**{key}:** {value}"
        return msg
    
    @staticmethod
    def info(message: str, details: Dict[str, Any] = None) -> str:
        msg = f"{Emojis.INFO_SIGN} **اطلاعیه**\n\n{message}"
        if details:
            for key, value in details.items():
                msg += f"\n**{key}:** {value}"
        return msg


# ============================================================
# ساخت کیبورد (همانند قبل)
# ============================================================

def build_menu_keyboard(items: List[Tuple[str, str]], cols: int = 2) -> List[List[Dict]]:
    keyboard = []
    row = []
    for i, (text, callback) in enumerate(items):
        row.append({"text": text, "callback_data": callback})
        if (i + 1) % cols == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return keyboard


# ============================================================
# صادر کردن
# ============================================================

__all__ = [
    'Emojis',
    'TextFormatter',
    'TextTable',
    'InfoCard',
    'StatusMessage',
    'build_menu_keyboard',
]