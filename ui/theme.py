"""
Visual theme constants for BindClicker UI.

Dark modern aesthetic with vibrant accent colours.
"""

# ---------------------------------------------------------------------------
# Colour Palette
# ---------------------------------------------------------------------------

# Backgrounds
BG_DARK = "#0f0f1a"
BG_PANEL = "#161625"
BG_CARD = "#1e1e32"
BG_HOVER = "#2a2a44"
BG_INPUT = "#12121f"

# Accents
ACCENT_PRIMARY = "#6c63ff"       # Purple
ACCENT_SECONDARY = "#3b82f6"     # Blue
ACCENT_GRADIENT_START = "#6c63ff"
ACCENT_GRADIENT_END = "#3b82f6"

# Status colours
STATUS_RECORDING = "#ef4444"     # Red
STATUS_EXECUTING = "#22c55e"     # Green
STATUS_IDLE = "#6b7280"          # Grey
STATUS_ERROR = "#f59e0b"         # Amber

# Text
TEXT_PRIMARY = "#f1f5f9"
TEXT_SECONDARY = "#94a3b8"
TEXT_MUTED = "#64748b"
TEXT_ACCENT = "#818cf8"

# Borders
BORDER_DEFAULT = "#2d2d4a"
BORDER_FOCUS = "#6c63ff"

# Buttons
BTN_RECORD = "#ef4444"
BTN_RECORD_HOVER = "#dc2626"
BTN_EXECUTE = "#22c55e"
BTN_EXECUTE_HOVER = "#16a34a"
BTN_STOP = "#f59e0b"
BTN_STOP_HOVER = "#d97706"
BTN_DEFAULT = "#6c63ff"
BTN_DEFAULT_HOVER = "#5b54e6"
BTN_DANGER = "#ef4444"
BTN_DANGER_HOVER = "#dc2626"

# Table
TABLE_ROW_EVEN = "#1a1a2e"
TABLE_ROW_ODD = "#161625"
TABLE_HEADER = "#2a2a44"
TABLE_SELECTED = "#3b3b6b"

# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------
FONT_FAMILY = "Segoe UI"
FONT_SIZE_XS = 10
FONT_SIZE_SM = 11
FONT_SIZE_MD = 13
FONT_SIZE_LG = 16
FONT_SIZE_XL = 20
FONT_SIZE_XXL = 26

# ---------------------------------------------------------------------------
# Dimensions
# ---------------------------------------------------------------------------
SIDEBAR_WIDTH = 260
CORNER_RADIUS = 8
CORNER_RADIUS_SM = 6
PADDING = 12
PADDING_SM = 6
PADDING_LG = 20

# ---------------------------------------------------------------------------
# Status Labels
# ---------------------------------------------------------------------------
STATUS_LABELS = {
    "idle": "● Idle",
    "recording": "● Recording",
    "executing": "● Executing",
    "error": "● Error",
}

STATUS_COLORS = {
    "idle": STATUS_IDLE,
    "recording": STATUS_RECORDING,
    "executing": STATUS_EXECUTING,
    "error": STATUS_ERROR,
}
