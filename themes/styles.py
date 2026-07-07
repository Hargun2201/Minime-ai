# themes/styles.py

from typing import Dict, Any

# Color Palettes representing high-end modern dark and light modes
THEMES: Dict[str, Dict[str, str]] = {
    "dark": {
        "bg_main": "#0f1115",
        "bg_sidebar": "#161920",
        "bg_card": "rgba(30, 34, 45, 0.7)",
        "bg_card_opaque": "#1e222d",
        "border_color": "rgba(255, 255, 255, 0.08)",
        "border_focus": "#00f2fe",
        
        "text_primary": "#f8f9fa",
        "text_secondary": "#a0a5b5",
        "text_muted": "#686c7b",
        
        "primary": "#4facfe",
        "primary_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4facfe, stop:1 #00f2fe)",
        "accent": "#00f2fe",
        "accent_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b150e6, stop:1 #e287ff)",
        
        "success": "#2ecc71",
        "warning": "#f1c40f",
        "danger": "#e74c3c",
        
        "scroll_track": "#161920",
        "scroll_thumb": "#313543",
        "scroll_thumb_hover": "#4facfe",
    },
    "light": {
        "bg_main": "#f4f6f9",
        "bg_sidebar": "#ffffff",
        "bg_card": "rgba(255, 255, 255, 0.8)",
        "bg_card_opaque": "#ffffff",
        "border_color": "rgba(0, 0, 0, 0.06)",
        "border_focus": "#4facfe",
        
        "text_primary": "#1e293b",
        "text_secondary": "#64748b",
        "text_muted": "#94a3b8",
        
        "primary": "#4facfe",
        "primary_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4facfe, stop:1 #00f2fe)",
        "accent": "#b150e6",
        "accent_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b150e6, stop:1 #e287ff)",
        
        "success": "#10b981",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        
        "scroll_track": "#f1f5f9",
        "scroll_thumb": "#cbd5e1",
        "scroll_thumb_hover": "#94a3b8",
    }
}

def get_stylesheet(theme_name: str = "dark", transparency: float = 0.9) -> str:
    """
    Generates a premium global Qt Style Sheet (QSS) for the application.
    Supports modern card structures, glassmorphism approximations, and sleek inputs.
    """
    t = THEMES.get(theme_name, THEMES["dark"])
    
    # Calculate RGBA values for transparent panels
    card_bg = t["bg_card"]
    
    stylesheet = f"""
    /* Global Base */
    QWidget {{
        font-family: 'Outfit', 'Inter', 'Segoe UI', -apple-system, sans-serif;
        color: {t["text_primary"]};
        background: transparent;
    }}
    
    QMainWindow {{
        background-color: {t["bg_main"]};
    }}
    
    /* Core Layout Panels */
    QFrame#MainContainer {{
        background-color: {t["bg_main"]};
    }}
    
    QFrame#SidebarPanel {{
        background-color: {t["bg_sidebar"]};
        border-right: 1px solid {t["border_color"]};
    }}
    
    /* Rounded Cards */
    QFrame.Card, QFrame#CardWidget {{
        background-color: {t["bg_card_opaque"]};
        border: 1px solid {t["border_color"]};
        border-radius: 16px;
    }}
    
    QFrame.GlassCard {{
        background-color: {card_bg};
        border: 1px solid {t["border_color"]};
        border-radius: 16px;
    }}
    
    /* Typography Helpers */
    QLabel#HeadingLarge {{
        font-size: 26px;
        font-weight: 800;
        color: {t["text_primary"]};
    }}
    
    QLabel#HeadingMedium {{
        font-size: 18px;
        font-weight: 700;
        color: {t["text_primary"]};
    }}
    
    QLabel#HeadingSmall {{
        font-size: 14px;
        font-weight: 600;
        color: {t["text_primary"]};
    }}
    
    QLabel#TextSecondary {{
        color: {t["text_secondary"]};
        font-size: 13px;
    }}
    
    QLabel#TextMuted {{
        color: {t["text_muted"]};
        font-size: 11px;
    }}
    
    /* Buttons */
    QPushButton {{
        background-color: {t["bg_card_opaque"]};
        border: 1px solid {t["border_color"]};
        color: {t["text_primary"]};
        padding: 8px 16px;
        border-radius: 10px;
        font-size: 13px;
        font-weight: 600;
    }}
    
    QPushButton:hover {{
        background-color: {t["border_color"]};
        border-color: {t["text_muted"]};
    }}
    
    QPushButton:pressed {{
        background-color: rgba(255,255,255, 0.02);
    }}
    
    QPushButton#PrimaryButton {{
        background: {t["primary_gradient"]};
        color: #ffffff;
        border: none;
    }}
    
    QPushButton#PrimaryButton:hover {{
        opacity: 0.9;
    }}
    
    QPushButton#PrimaryButton:pressed {{
        opacity: 0.8;
    }}
    
    QPushButton#SidebarButton {{
        background-color: transparent;
        border: none;
        text-align: left;
        padding: 10px 16px;
        border-radius: 8px;
        color: {t["text_secondary"]};
        font-size: 14px;
    }}
    
    QPushButton#SidebarButton:hover {{
        background-color: {t["border_color"]};
        color: {t["text_primary"]};
    }}
    
    QPushButton#SidebarButton[active="true"] {{
        background-color: {t["border_color"]};
        color: {t["primary"]};
        font-weight: 700;
    }}
    
    QPushButton#DangerButton {{
        background-color: {t["danger"]};
        color: #ffffff;
        border: none;
    }}
    
    QPushButton#DangerButton:hover {{
        opacity: 0.9;
    }}
    
    /* Inputs: Lines and Texts */
    QLineEdit, QTextEdit {{
        background-color: rgba(0, 0, 0, 0.15) if theme_name == "dark" else rgba(255, 255, 255, 0.8);
        border: 1px solid {t["border_color"]};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 13px;
        color: {t["text_primary"]};
    }}
    
    QLineEdit:focus, QTextEdit:focus {{
        border: 1.5px solid {t["border_focus"]};
    }}
    
    /* Progress Bar */
    QProgressBar {{
        background-color: {t["border_color"]};
        border: none;
        height: 8px;
        border-radius: 4px;
        text-align: center;
    }}
    
    QProgressBar::chunk {{
        background: {t["primary_gradient"]};
        border-radius: 4px;
    }}
    
    /* Scrollbars */
    QScrollBar:vertical {{
        border: none;
        background: {t["scroll_track"]};
        width: 8px;
        margin: 0px;
        border-radius: 4px;
    }}
    
    QScrollBar::handle:vertical {{
        background: {t["scroll_thumb"]};
        min-height: 20px;
        border-radius: 4px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background: {t["scroll_thumb_hover"]};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none;
        background: none;
        height: 0px;
    }}
    
    QScrollBar:horizontal {{
        border: none;
        background: {t["scroll_track"]};
        height: 8px;
        margin: 0px;
        border-radius: 4px;
    }}
    
    QScrollBar::handle:horizontal {{
        background: {t["scroll_thumb"]};
        min-width: 20px;
        border-radius: 4px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background: {t["scroll_thumb_hover"]};
    }}
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        border: none;
        background: none;
        width: 0px;
    }}
    
    /* Tabs & Dialogs */
    QTabWidget::pane {{
        border: 1px solid {t["border_color"]};
        border-radius: 12px;
        background-color: {t["bg_card_opaque"]};
        padding: 10px;
    }}
    
    QTabBar::tab {{
        background-color: transparent;
        color: {t["text_secondary"]};
        padding: 8px 16px;
        margin-right: 4px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-weight: 600;
    }}
    
    QTabBar::tab:selected {{
        background-color: {t["bg_card_opaque"]};
        color: {t["primary"]};
        border: 1px solid {t["border_color"]};
        border-bottom-color: transparent;
    }}
    
    QTabBar::tab:hover:!selected {{
        background-color: {t["border_color"]};
        color: {t["text_primary"]};
    }}
    
    /* Lists and Tables */
    QListWidget, QTableWidget {{
        background-color: transparent;
        border: none;
    }}
    
    QListWidget::item {{
        background-color: {t["bg_card_opaque"]};
        border: 1px solid {t["border_color"]};
        border-radius: 8px;
        padding: 8px 12px;
        margin-bottom: 6px;
    }}
    
    QListWidget::item:hover {{
        background-color: {t["border_color"]};
    }}
    
    QListWidget::item:selected {{
        border-color: {t["primary"]};
        color: {t["text_primary"]};
    }}
    
    /* Dialogs */
    QDialog {{
        background-color: {t["bg_main"]};
    }}
    """
    return stylesheet
