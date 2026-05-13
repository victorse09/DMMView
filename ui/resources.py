"""
DMMView - Resources
SVG icons and resource definitions for the application.
"""

# SVG icon data as inline strings for independence from external files.
# These are used throughout the application for toolbar and menu icons.

ICONS = {
    'connect': '''<svg viewBox="0 0 24 24" fill="none" stroke="#3fb950" stroke-width="2">
        <path d="M5 12h14M12 5l7 7-7 7"/>
    </svg>''',

    'disconnect': '''<svg viewBox="0 0 24 24" fill="none" stroke="#f85149" stroke-width="2">
        <line x1="18" y1="6" x2="6" y2="18"/>
        <line x1="6" y1="6" x2="18" y2="18"/>
    </svg>''',

    'play': '''<svg viewBox="0 0 24 24" fill="#3fb950">
        <polygon points="5,3 19,12 5,21"/>
    </svg>''',

    'stop': '''<svg viewBox="0 0 24 24" fill="#f85149">
        <rect x="4" y="4" width="16" height="16" rx="2"/>
    </svg>''',

    'download': '''<svg viewBox="0 0 24 24" fill="none" stroke="#58a6ff" stroke-width="2">
        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
        <polyline points="7 10 12 15 17 10"/>
        <line x1="12" y1="15" x2="12" y2="3"/>
    </svg>''',

    'export': '''<svg viewBox="0 0 24 24" fill="none" stroke="#d29922" stroke-width="2">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
        <polyline points="10 9 9 9 8 9"/>
    </svg>''',

    'chart': '''<svg viewBox="0 0 24 24" fill="none" stroke="#bc8cff" stroke-width="2">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
    </svg>''',

    'histogram': '''<svg viewBox="0 0 24 24" fill="none" stroke="#39d2c0" stroke-width="2">
        <rect x="3" y="12" width="4" height="9" rx="1"/>
        <rect x="10" y="5" width="4" height="16" rx="1"/>
        <rect x="17" y="8" width="4" height="13" rx="1"/>
    </svg>''',

    'settings': '''<svg viewBox="0 0 24 24" fill="none" stroke="#8b949e" stroke-width="2">
        <circle cx="12" cy="12" r="3"/>
        <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>
    </svg>''',

    'clear': '''<svg viewBox="0 0 24 24" fill="none" stroke="#f85149" stroke-width="2">
        <polyline points="3 6 5 6 21 6"/>
        <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
    </svg>''',

    'refresh': '''<svg viewBox="0 0 24 24" fill="none" stroke="#58a6ff" stroke-width="2">
        <polyline points="23 4 23 10 17 10"/>
        <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/>
    </svg>''',

    'serial': '''<svg viewBox="0 0 24 24" fill="none" stroke="#d29922" stroke-width="2">
        <rect x="2" y="7" width="20" height="10" rx="2"/>
        <circle cx="7" cy="12" r="1.5" fill="#d29922"/>
        <circle cx="12" cy="12" r="1.5" fill="#d29922"/>
        <circle cx="17" cy="12" r="1.5" fill="#d29922"/>
    </svg>''',

    'meter': '''<svg viewBox="0 0 24 24" fill="none" stroke="#58a6ff" stroke-width="2">
        <rect x="3" y="2" width="18" height="20" rx="3"/>
        <rect x="5" y="4" width="14" height="8" rx="1" fill="#0a0f1a"/>
        <circle cx="8" cy="17" r="1.5"/>
        <circle cx="12" cy="17" r="1.5"/>
        <circle cx="16" cy="17" r="1.5"/>
    </svg>''',

    'info': '''<svg viewBox="0 0 24 24" fill="none" stroke="#58a6ff" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="16" x2="12" y2="12"/>
        <line x1="12" y1="8" x2="12.01" y2="8"/>
    </svg>''',
}


def get_icon_svg(name: str) -> str:
    """Get SVG data for a named icon."""
    return ICONS.get(name, ICONS['info'])


def svg_to_pixmap(svg_data: str, size: int = 24):
    """Convert SVG string to QPixmap."""
    from PyQt6.QtCore import QByteArray
    from PyQt6.QtSvg import QSvgRenderer
    from PyQt6.QtGui import QPixmap, QPainter

    renderer = QSvgRenderer(QByteArray(svg_data.encode('utf-8')))
    pixmap = QPixmap(size, size)
    pixmap.fill()
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


def svg_to_icon(name: str, size: int = 24):
    """Create QIcon from named SVG icon."""
    from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
    from PyQt6.QtCore import QByteArray, Qt

    svg_data = get_icon_svg(name)

    try:
        from PyQt6.QtSvg import QSvgRenderer
        renderer = QSvgRenderer(QByteArray(svg_data.encode('utf-8')))
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)
    except ImportError:
        # Fallback: return empty icon if QtSvg is not available
        return QIcon()
