"""
DMMView - Application Styles
Professional dark theme inspired by Fluke FormView and UNI-T software.
"""

# ──────────────────────────────────────────────────────────────────────
# Color Palette
# ──────────────────────────────────────────────────────────────────────
COLORS = {
    # Base backgrounds
    'bg_darkest':     '#0d1117',
    'bg_dark':        '#161b22',
    'bg_medium':      '#1c2333',
    'bg_card':        '#21283b',
    'bg_elevated':    '#2a3149',
    'bg_hover':       '#30394d',
    'bg_input':       '#151b28',

    # Borders
    'border_dark':    '#2a3149',
    'border_medium':  '#3b4665',
    'border_light':   '#4a5680',

    # Text
    'text_primary':   '#e6edf3',
    'text_secondary': '#8b949e',
    'text_muted':     '#6e7681',
    'text_bright':    '#ffffff',

    # Accent colors
    'accent_blue':    '#58a6ff',
    'accent_blue_hover': '#79c0ff',
    'accent_green':   '#3fb950',
    'accent_green_dim': '#238636',
    'accent_orange':  '#d29922',
    'accent_red':     '#f85149',
    'accent_purple':  '#bc8cff',
    'accent_cyan':    '#39d2c0',

    # LCD Display colors
    'lcd_bg':         '#0a0f1a',
    'lcd_segment_on': '#3fb950',
    'lcd_segment_off':'#1a2332',
    'lcd_value_ac':   '#f0c030',
    'lcd_value_dc':   '#58a6ff',
    'lcd_overload':   '#f85149',

    # Status colors
    'status_connected':    '#3fb950',
    'status_disconnected': '#f85149',
    'status_logging':      '#d29922',
    'status_idle':         '#8b949e',

    # Chart colors
    'chart_bg':       '#0d1117',
    'chart_line':     '#58a6ff',
    'chart_grid':     '#21283b',
    'chart_text':     '#8b949e',
    'chart_fill':     'rgba(88, 166, 255, 0.15)',
    'chart_hist':     '#bc8cff',
}

# ──────────────────────────────────────────────────────────────────────
# Font definitions
# ──────────────────────────────────────────────────────────────────────
FONTS = {
    'family_sans':   'Inter, Segoe UI, Roboto, sans-serif',
    'family_mono':   'JetBrains Mono, Roboto Mono, Consolas, monospace',
    'family_lcd':    'DSEG7 Classic, Roboto Mono, monospace',
    'size_xs':       '10px',
    'size_sm':       '11px',
    'size_base':     '12px',
    'size_md':       '13px',
    'size_lg':       '15px',
    'size_xl':       '18px',
    'size_2xl':      '24px',
    'size_3xl':      '32px',
    'size_display':  '56px',
}


def get_stylesheet():
    """Generate the complete application stylesheet."""
    c = COLORS
    f = FONTS

    return f"""
    /* ── Global ─────────────────────────────────────────────────── */
    QMainWindow {{
        background-color: {c['bg_darkest']};
        color: {c['text_primary']};
        font-family: {f['family_sans']};
        font-size: {f['size_base']};
    }}

    QWidget {{
        background-color: transparent;
        color: {c['text_primary']};
        font-family: {f['family_sans']};
    }}

    /* ── Menu Bar ───────────────────────────────────────────────── */
    QMenuBar {{
        background-color: {c['bg_dark']};
        color: {c['text_primary']};
        border-bottom: 1px solid {c['border_dark']};
        padding: 2px;
        font-size: {f['size_md']};
    }}
    QMenuBar::item {{
        padding: 6px 12px;
        border-radius: 4px;
    }}
    QMenuBar::item:selected {{
        background-color: {c['bg_hover']};
    }}
    QMenu {{
        background-color: {c['bg_card']};
        border: 1px solid {c['border_medium']};
        border-radius: 8px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 8px 24px 8px 12px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {c['accent_blue']};
        color: {c['text_bright']};
    }}
    QMenu::separator {{
        height: 1px;
        background: {c['border_dark']};
        margin: 4px 8px;
    }}

    /* ── Tool Bar ───────────────────────────────────────────────── */
    QToolBar {{
        background-color: {c['bg_dark']};
        border-bottom: 1px solid {c['border_dark']};
        padding: 4px 8px;
        spacing: 6px;
    }}
    QToolBar::separator {{
        width: 1px;
        background: {c['border_dark']};
        margin: 4px 6px;
    }}
    QToolButton {{
        background-color: {c['bg_medium']};
        border: 1px solid {c['border_dark']};
        border-radius: 6px;
        padding: 6px 12px;
        color: {c['text_primary']};
        font-size: {f['size_sm']};
        font-weight: 500;
    }}
    QToolButton:hover {{
        background-color: {c['bg_hover']};
        border-color: {c['accent_blue']};
    }}
    QToolButton:pressed {{
        background-color: {c['accent_blue']};
    }}
    QToolButton:checked {{
        background-color: {c['accent_blue']};
        color: {c['text_bright']};
        border-color: {c['accent_blue']};
    }}

    /* ── Tab Widget ─────────────────────────────────────────────── */
    QTabWidget::pane {{
        background-color: {c['bg_darkest']};
        border: 1px solid {c['border_dark']};
        border-radius: 8px;
        border-top-left-radius: 0px;
    }}
    QTabBar::tab {{
        background-color: {c['bg_medium']};
        color: {c['text_secondary']};
        border: 1px solid {c['border_dark']};
        border-bottom: none;
        padding: 8px 20px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        font-size: {f['size_md']};
        font-weight: 500;
    }}
    QTabBar::tab:selected {{
        background-color: {c['bg_darkest']};
        color: {c['accent_blue']};
        border-color: {c['border_medium']};
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {c['bg_hover']};
        color: {c['text_primary']};
    }}

    /* ── Push Buttons ───────────────────────────────────────────── */
    QPushButton {{
        background-color: {c['bg_medium']};
        border: 1px solid {c['border_medium']};
        border-radius: 6px;
        padding: 8px 18px;
        color: {c['text_primary']};
        font-size: {f['size_base']};
        font-weight: 500;
        min-height: 18px;
    }}
    QPushButton:hover {{
        background-color: {c['bg_hover']};
        border-color: {c['accent_blue']};
    }}
    QPushButton:pressed {{
        background-color: {c['accent_blue']};
        color: {c['text_bright']};
    }}
    QPushButton:disabled {{
        background-color: {c['bg_dark']};
        color: {c['text_muted']};
        border-color: {c['border_dark']};
    }}

    /* Primary action buttons */
    QPushButton[cssClass="primary"] {{
        background-color: {c['accent_blue']};
        border-color: {c['accent_blue']};
        color: {c['text_bright']};
    }}
    QPushButton[cssClass="primary"]:hover {{
        background-color: {c['accent_blue_hover']};
    }}

    /* Success buttons */
    QPushButton[cssClass="success"] {{
        background-color: {c['accent_green_dim']};
        border-color: {c['accent_green']};
        color: {c['text_bright']};
    }}
    QPushButton[cssClass="success"]:hover {{
        background-color: {c['accent_green']};
    }}

    /* Danger buttons */
    QPushButton[cssClass="danger"] {{
        background-color: #5a1d1d;
        border-color: {c['accent_red']};
        color: {c['accent_red']};
    }}
    QPushButton[cssClass="danger"]:hover {{
        background-color: {c['accent_red']};
        color: {c['text_bright']};
    }}

    /* ── Combo Boxes ────────────────────────────────────────────── */
    QComboBox {{
        background-color: {c['bg_input']};
        border: 1px solid {c['border_medium']};
        border-radius: 6px;
        padding: 6px 12px;
        color: {c['text_primary']};
        font-size: {f['size_base']};
        min-height: 20px;
    }}
    QComboBox:hover {{
        border-color: {c['accent_blue']};
    }}
    QComboBox::drop-down {{
        border: none;
        padding-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {c['bg_card']};
        border: 1px solid {c['border_medium']};
        border-radius: 6px;
        selection-background-color: {c['accent_blue']};
        color: {c['text_primary']};
        padding: 4px;
    }}

    /* ── Spin Boxes ─────────────────────────────────────────────── */
    QSpinBox, QDoubleSpinBox {{
        background-color: {c['bg_input']};
        border: 1px solid {c['border_medium']};
        border-radius: 6px;
        padding: 6px 8px;
        color: {c['text_primary']};
    }}

    /* ── Labels ─────────────────────────────────────────────────── */
    QLabel {{
        color: {c['text_primary']};
        font-size: {f['size_base']};
    }}
    QLabel[cssClass="heading"] {{
        font-size: {f['size_lg']};
        font-weight: 600;
        color: {c['text_bright']};
    }}
    QLabel[cssClass="subtitle"] {{
        color: {c['text_secondary']};
        font-size: {f['size_sm']};
    }}
    QLabel[cssClass="value-large"] {{
        font-family: {f['family_mono']};
        font-size: {f['size_display']};
        font-weight: 700;
        color: {c['lcd_segment_on']};
    }}

    /* ── Tables ─────────────────────────────────────────────────── */
    QTableWidget, QTableView {{
        background-color: {c['bg_darkest']};
        alternate-background-color: {c['bg_dark']};
        border: 1px solid {c['border_dark']};
        border-radius: 6px;
        gridline-color: {c['border_dark']};
        selection-background-color: {c['accent_blue']};
        selection-color: {c['text_bright']};
        font-size: {f['size_sm']};
    }}
    QTableWidget::item {{
        padding: 4px 8px;
        border: none;
    }}
    QHeaderView::section {{
        background-color: {c['bg_card']};
        color: {c['text_secondary']};
        padding: 6px 8px;
        border: none;
        border-bottom: 2px solid {c['accent_blue']};
        font-weight: 600;
        font-size: {f['size_sm']};
    }}

    /* ── Scroll Bars ────────────────────────────────────────────── */
    QScrollBar:vertical {{
        background: {c['bg_dark']};
        width: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background: {c['border_medium']};
        border-radius: 5px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {c['accent_blue']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: {c['bg_dark']};
        height: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:horizontal {{
        background: {c['border_medium']};
        border-radius: 5px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {c['accent_blue']};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    /* ── Progress Bar ───────────────────────────────────────────── */
    QProgressBar {{
        background-color: {c['bg_dark']};
        border: 1px solid {c['border_dark']};
        border-radius: 6px;
        text-align: center;
        color: {c['text_primary']};
        font-size: {f['size_sm']};
        min-height: 20px;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c['accent_blue']}, stop:1 {c['accent_cyan']});
        border-radius: 5px;
    }}

    /* ── Status Bar ─────────────────────────────────────────────── */
    QStatusBar {{
        background-color: {c['bg_dark']};
        border-top: 1px solid {c['border_dark']};
        color: {c['text_secondary']};
        font-size: {f['size_sm']};
    }}
    QStatusBar::item {{
        border: none;
    }}

    /* ── Group Box ──────────────────────────────────────────────── */
    QGroupBox {{
        background-color: {c['bg_card']};
        border: 1px solid {c['border_dark']};
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 18px;
        font-size: {f['size_md']};
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 2px 8px;
        color: {c['accent_blue']};
    }}

    /* ── Splitter ────────────────────────────────────────────────── */
    QSplitter::handle {{
        background-color: {c['border_dark']};
    }}
    QSplitter::handle:horizontal {{
        width: 2px;
    }}
    QSplitter::handle:vertical {{
        height: 2px;
    }}

    /* ── Check Box ──────────────────────────────────────────────── */
    QCheckBox {{
        spacing: 8px;
        font-size: {f['size_base']};
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 2px solid {c['border_medium']};
        border-radius: 4px;
        background-color: {c['bg_input']};
    }}
    QCheckBox::indicator:checked {{
        background-color: {c['accent_blue']};
        border-color: {c['accent_blue']};
    }}

    /* ── ToolTip ─────────────────────────────────────────────────── */
    QToolTip {{
        background-color: {c['bg_card']};
        border: 1px solid {c['border_medium']};
        border-radius: 6px;
        padding: 6px 10px;
        color: {c['text_primary']};
        font-size: {f['size_sm']};
    }}
    """
