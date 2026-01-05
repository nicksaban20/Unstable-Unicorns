"""Terminal color utilities for Unstable Unicorns CLI."""

import sys
from enum import Enum
from typing import Optional


class Color(Enum):
    """ANSI color codes."""
    # Reset
    RESET = "\033[0m"

    # Regular colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # Styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"


# Check if terminal supports colors
def supports_color() -> bool:
    """Check if the terminal supports ANSI colors."""
    if not hasattr(sys.stdout, "isatty"):
        return False
    if not sys.stdout.isatty():
        return False
    return True


# Global flag for color support
COLOR_ENABLED = supports_color()


def set_color_enabled(enabled: bool) -> None:
    """Enable or disable colors globally."""
    global COLOR_ENABLED
    COLOR_ENABLED = enabled


def colorize(text: str, *colors: Color) -> str:
    """Apply colors to text.

    Args:
        text: Text to colorize
        colors: Color codes to apply

    Returns:
        Colorized text (or plain text if colors disabled)
    """
    if not COLOR_ENABLED or not colors:
        return text

    color_codes = "".join(c.value for c in colors)
    return f"{color_codes}{text}{Color.RESET.value}"


# Convenience functions for common color combinations
def bold(text: str) -> str:
    """Make text bold."""
    return colorize(text, Color.BOLD)


def dim(text: str) -> str:
    """Make text dim."""
    return colorize(text, Color.DIM)


def success(text: str) -> str:
    """Green text for success messages."""
    return colorize(text, Color.BRIGHT_GREEN)


def error(text: str) -> str:
    """Red text for error messages."""
    return colorize(text, Color.BRIGHT_RED)


def warning(text: str) -> str:
    """Yellow text for warnings."""
    return colorize(text, Color.BRIGHT_YELLOW)


def info(text: str) -> str:
    """Cyan text for info."""
    return colorize(text, Color.BRIGHT_CYAN)


def highlight(text: str) -> str:
    """Magenta text for highlights."""
    return colorize(text, Color.BRIGHT_MAGENTA)


# Card type colors
def card_color(card_type: str) -> str:
    """Get color code for a card type."""
    colors = {
        "BABY_UNICORN": Color.BRIGHT_WHITE,
        "BASIC_UNICORN": Color.WHITE,
        "MAGICAL_UNICORN": Color.BRIGHT_MAGENTA,
        "UPGRADE": Color.BRIGHT_GREEN,
        "DOWNGRADE": Color.BRIGHT_RED,
        "MAGIC": Color.BRIGHT_BLUE,
        "INSTANT": Color.BRIGHT_YELLOW,
    }
    return colors.get(card_type, Color.WHITE).value


def colorize_card(name: str, card_type: str) -> str:
    """Colorize a card name based on its type."""
    if not COLOR_ENABLED:
        return name
    return f"{card_color(card_type)}{name}{Color.RESET.value}"


# Unicode symbols for better display
SYMBOLS = {
    "unicorn": "🦄",
    "star": "⭐",
    "heart": "❤️",
    "skull": "💀",
    "check": "✓",
    "cross": "✗",
    "arrow_right": "→",
    "arrow_left": "←",
    "bullet": "•",
    "diamond": "◆",
    "square": "■",
    "circle": "●",
}


def symbol(name: str, fallback: str = "*") -> str:
    """Get a Unicode symbol with fallback for unsupported terminals."""
    try:
        # Try to encode the symbol
        sym = SYMBOLS.get(name, fallback)
        sym.encode(sys.stdout.encoding or "utf-8")
        return sym
    except (UnicodeEncodeError, LookupError):
        return fallback


# Box drawing for nice borders
class Box:
    """Box drawing characters."""
    # Light box
    TOP_LEFT = "┌"
    TOP_RIGHT = "┐"
    BOTTOM_LEFT = "└"
    BOTTOM_RIGHT = "┘"
    HORIZONTAL = "─"
    VERTICAL = "│"
    T_DOWN = "┬"
    T_UP = "┴"
    T_RIGHT = "├"
    T_LEFT = "┤"
    CROSS = "┼"

    @classmethod
    def line(cls, width: int) -> str:
        """Create a horizontal line."""
        return cls.HORIZONTAL * width

    @classmethod
    def box_top(cls, width: int) -> str:
        """Create top of a box."""
        return cls.TOP_LEFT + cls.line(width - 2) + cls.TOP_RIGHT

    @classmethod
    def box_bottom(cls, width: int) -> str:
        """Create bottom of a box."""
        return cls.BOTTOM_LEFT + cls.line(width - 2) + cls.BOTTOM_RIGHT

    @classmethod
    def box_row(cls, content: str, width: int) -> str:
        """Create a row of a box with content."""
        padding = width - len(content) - 2
        return cls.VERTICAL + content + " " * padding + cls.VERTICAL


def print_header(text: str, width: int = 60) -> None:
    """Print a styled header."""
    print()
    print(colorize(Box.box_top(width), Color.BRIGHT_CYAN))
    centered = text.center(width - 2)
    print(colorize(Box.VERTICAL, Color.BRIGHT_CYAN) +
          colorize(centered, Color.BOLD, Color.BRIGHT_WHITE) +
          colorize(Box.VERTICAL, Color.BRIGHT_CYAN))
    print(colorize(Box.box_bottom(width), Color.BRIGHT_CYAN))


def print_subheader(text: str, width: int = 60) -> None:
    """Print a styled subheader."""
    line = Box.line(width)
    print(colorize(line, Color.DIM))
    print(colorize(f" {text}", Color.BOLD))
    print(colorize(line, Color.DIM))


def progress_bar(current: int, total: int, width: int = 30, label: str = "") -> str:
    """Create a progress bar string."""
    filled = int(width * current / total)
    empty = width - filled

    bar = colorize("█" * filled, Color.BRIGHT_GREEN) + colorize("░" * empty, Color.DIM)

    percentage = f"{100 * current / total:.0f}%"

    if label:
        return f"{label}: [{bar}] {current}/{total} ({percentage})"
    return f"[{bar}] {current}/{total} ({percentage})"
