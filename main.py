# main.py

import os
import sys
import random
import logging
import threading
from PySide6.QtCore import Qt, QPoint, QSize, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QColor, QFont, QAction
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QFrame, QGraphicsDropShadowEffect, 
    QSystemTrayIcon, QMenu, QInputDialog, QListWidget, QLineEdit, QDialog
)
from PySide6.QtSvgWidgets import QSvgWidget

# Project Imports
from logging_config import setup_logging
from config.config_manager import ConfigManager
from config.constants import (
    AVATAR_FILES, AVATARS_DIR, EMOTION_WAITING, EMOTION_HAPPY, EMOTION_SAD,
    EMOTION_EXCITED, EMOTION_THINKING, EMOTION_SLEEPING, MOTIVATIONAL_QUOTES,
    WATER_REMINDERS, XP_REWARDS, XP_BASE, XP_FACTOR, LEVEL_NAMES
)
from database.database import DatabaseManager
from themes.styles import get_stylesheet

# Text to Speech (TTS) Helper
try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    HAS_TTS = False

logger = setup_logging()

def speak_text_async(text: str):
    """Speaks text in a separate thread to prevent GUI freezing."""
    if not HAS_TTS:
        logger.info(f"[Speech Fallback] MiniMe says: {text}")
        return

    def run_tts():
        try:
            engine = pyttsx3.init()
            # Adjust speech rate for a friendlier voice
            engine.setProperty('rate', 150)
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            logger.warning(f"TTS Thread failed: {e}")

    threading.Thread(target=run_tts, daemon=True).start()


class MiniMeCompanion(QWidget):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.db = DatabaseManager()
        
        # Load user states from DB
        self.level = int(self.db.get_stat("level", 1))
        self.xp = int(self.db.get_stat("xp", 0))
        self.username = self.db.get_setting("username", "Hargun")
        
        # UI State Variables
        self.current_emotion = EMOTION_WAITING
        self.is_panel_visible = True
        self.drag_position = QPoint()
        
        # Pomodoro Timer Variables
        self.pomodoro_timer = QTimer(self)
        self.pomodoro_timer.timeout.connect(self.update_pomodoro)
        self.pomodoro_remaining_seconds = 0
        self.is_pomodoro_active = False

        self.init_ui()
        self.setup_tray_icon()
        self.set_emotion(EMOTION_HAPPY)
        
        # Schedule water reminder check (every 5 minutes)
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self.trigger_random_reminder)
        interval_mins = int(self.db.get_setting("water_interval_mins", 60))
        self.reminder_timer.start(interval_mins * 60 * 1000)

        # Initial Greeting
        QTimer.singleShot(1000, lambda: self.say(f"Hi {self.username}! Ready to crush your goals today? 🚀"))

    def init_ui(self):
        # Configure Frameless, Translucent, Always-on-Top Window
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(300, 480)
        
        # Position window in the bottom-right corner of the primary screen
        try:
            screen_geom = QApplication.primaryScreen().availableGeometry()
            x = screen_geom.width() - 320
            y = screen_geom.height() - 500
            self.move(x, y)
        except Exception as e:
            logger.warning(f"Failed to position window: {e}")

        
        # Set Global Theme Stylesheet
        self.apply_theme()

        # Layout Container with Custom Shadow Effect
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        self.container = QFrame(self)
        self.container.setObjectName("MainContainer")
        self.container.setStyleSheet(f"""
            QFrame#MainContainer {{
                background-color: {self.get_theme_color("bg_main")};
                border: 2px solid {self.get_theme_color("border_color")};
                border-radius: 20px;
            }}
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(12)

        # 1. SPEECH BUBBLE (Glassmorphic style)
        self.bubble_frame = QFrame(self)
        self.bubble_frame.setObjectName("GlassCard")
        self.bubble_frame.setFrameShape(QFrame.StyledPanel)
        
        bubble_layout = QVBoxLayout(self.bubble_frame)
        bubble_layout.setContentsMargins(12, 10, 12, 10)
        
        self.bubble_label = QLabel("...", self)
        self.bubble_label.setWordWrap(True)
        self.bubble_label.setFont(QFont("Inter", 11))
        self.bubble_label.setAlignment(Qt.AlignCenter)
        self.bubble_label.setStyleSheet(f"color: {self.get_theme_color('text_primary')};")
        bubble_layout.addWidget(self.bubble_label)
        
        container_layout.addWidget(self.bubble_frame)

        # 2. AVATAR SVG DISPLAY
        self.avatar_container = QWidget(self)
        avatar_layout = QHBoxLayout(self.avatar_container)
        avatar_layout.setAlignment(Qt.AlignCenter)
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        
        self.avatar_widget = QSvgWidget(self)
        self.avatar_widget.setFixedSize(130, 130)
        avatar_layout.addWidget(self.avatar_widget)
        
        container_layout.addWidget(self.avatar_container)

        # 3. INTERACTIVE MINI PANEL (XP, level, quick buttons)
        self.panel_frame = QFrame(self)
        self.panel_frame.setObjectName("CardWidget")
        
        panel_layout = QVBoxLayout(self.panel_frame)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(10)
        
        # Level & Progress info
        self.level_label = QLabel(f"Lvl {self.level} - {LEVEL_NAMES.get(self.level, 'Helper')}", self)
        self.level_label.setFont(QFont("Outfit", 12, QFont.Bold))
        self.level_label.setStyleSheet(f"color: {self.get_theme_color('text_primary')};")
        panel_layout.addWidget(self.level_label)
        
        # XP Progress Bar
        self.xp_bar = QProgressBar(self)
        self.xp_bar.setTextVisible(False)
        self.update_xp_bar()
        panel_layout.addWidget(self.xp_bar)

        # Quick Actions Grid
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(6)
        
        self.btn_water = QPushButton("💧 +250ml", self)
        self.btn_water.clicked.connect(self.log_water_click)
        
        self.btn_focus = QPushButton("⏱️ Focus", self)
        self.btn_focus.clicked.connect(self.toggle_focus_timer)
        
        self.btn_mood = QPushButton("😊 Mood", self)
        self.btn_mood.clicked.connect(self.log_mood_prompt)
        
        actions_layout.addWidget(self.btn_water)
        actions_layout.addWidget(self.btn_focus)
        actions_layout.addWidget(self.btn_mood)
        
        panel_layout.addLayout(actions_layout)
        container_layout.addWidget(self.panel_frame)

        # Drop Shadow for overall premium look
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 5)
        self.container.setGraphicsEffect(shadow)

        main_layout.addWidget(self.container)

        # Bubble fade animation
        self.bubble_anim = QPropertyAnimation(self.bubble_frame, b"maximumSize")
        self.bubble_anim.setDuration(300)
        self.bubble_anim.setEasingCurve(QEasingCurve.OutQuad)
        
        # Connect Click Event on Avatar
        self.avatar_widget.mousePressEvent = self.on_avatar_clicked

    # Theme Management
    def apply_theme(self):
        theme_name = self.db.get_setting("theme", "dark")
        self.setStyleSheet(get_stylesheet(theme_name))
        
    def get_theme_color(self, key: str) -> str:
        theme_name = self.db.get_setting("theme", "dark")
        from themes.styles import THEMES
        return THEMES.get(theme_name, THEMES["dark"]).get(key, "#ffffff")

    def update_xp_bar(self):
        xp_needed = int(XP_BASE * (self.level ** XP_FACTOR))
        self.xp_bar.setMaximum(xp_needed)
        self.xp_bar.setValue(self.xp)
        self.level_label.setText(f"Lvl {self.level} - {LEVEL_NAMES.get(self.level, 'Helper')}")

    # Core Communication (Bubble + Speech)
    def say(self, text: str, emotion: str = None):
        """Displays text in the bubble and speaks it if audio is enabled."""
        self.bubble_label.setText(text)
        if emotion:
            self.set_emotion(emotion)
        
        # Shake / bounce bubble effect using micro-animation
        self.bubble_frame.move(self.bubble_frame.x(), self.bubble_frame.y() - 5)
        QTimer.singleShot(100, lambda: self.bubble_frame.move(self.bubble_frame.x(), self.bubble_frame.y() + 5))
        
        # TTS Speak if audio configuration permits
        voice_on = self.db.get_setting("voice_enabled", "1") == "1"
        if voice_on:
            speak_text_async(text)

    def set_emotion(self, emotion: str):
        """Updates the Avatar SVG graphic based on the emotion key."""
        self.current_emotion = emotion
        filename = AVATAR_FILES.get(emotion, "waiting.svg")
        path = os.path.join(AVATARS_DIR, filename)
        if os.path.exists(path):
            self.avatar_widget.load(path)
            logger.debug(f"Emotion updated to {emotion} using file {path}")
        else:
            logger.warning(f"Avatar file not found: {path}")

    # Interactive Click Reactions
    def on_avatar_clicked(self, event):
        if event.button() == Qt.LeftButton:
            # Cycle through positive animations and state motivational quotes
            self.set_emotion(EMOTION_EXCITED)
            quote = random.choice(MOTIVATIONAL_QUOTES)
            self.say(quote)
            self.gain_xp(5)  # Fun minor click reward!
            
            # Revert to waiting state after 4 seconds
            QTimer.singleShot(4000, lambda: self.set_emotion(EMOTION_WAITING))

    def trigger_random_reminder(self):
        """Periodically triggers reminders like drinking water."""
        reminder = random.choice(WATER_REMINDERS).format(username=self.username)
        self.say(reminder, EMOTION_THINKING)

    # Habit Logging Functions
    def log_water_click(self):
        daily_total = self.db.add_water(250)
        self.gain_xp(XP_REWARDS["water"])
        self.say(f"Awesome! Hydrated +250ml. Today's total: {daily_total}ml. Keep it up! 💧", EMOTION_HAPPY)

    def log_mood_prompt(self):
        items = ["Happy", "Calm", "Anxious", "Tired", "Stressed", "Productive"]
        item, ok = QInputDialog.getItem(self, "Log Mood", "How are you feeling right now?", items, 0, False)
        if ok and item:
            self.db.log_mood(item)
            if item in ["Happy", "Productive", "Calm"]:
                self.say(f"So glad to hear you're feeling {item.lower()}! Let's sustain this flow. ✨", EMOTION_EXCITED)
            else:
                self.say(f"Acknowledge how you feel. Take a deep breath. You are doing great. 🤍", EMOTION_SAD)

    # Pomodoro Timer Implementation
    def toggle_focus_timer(self):
        if self.is_pomodoro_active:
            # Stop Pomodoro
            self.pomodoro_timer.stop()
            self.is_pomodoro_active = False
            self.btn_focus.setText("⏱️ Focus")
            self.say("Focus session cancelled. Rest up! 🧘", EMOTION_WAITING)
        else:
            # Start Pomodoro (25 minutes by default)
            duration_mins = int(self.db.get_setting("pomodoro_duration", 25))
            self.pomodoro_remaining_seconds = duration_mins * 60
            self.pomodoro_timer.start(1000) # Every 1 second
            self.is_pomodoro_active = True
            self.set_emotion(EMOTION_THINKING)
            self.say(f"Let's focus for {duration_mins} minutes, {self.username}! No distractions. 🧠", EMOTION_THINKING)
            self.update_focus_button_text()

    def update_pomodoro(self):
        if self.pomodoro_remaining_seconds > 0:
            self.pomodoro_remaining_seconds -= 1
            self.update_focus_button_text()
            if self.pomodoro_remaining_seconds % 300 == 0:  # Remind motivational quotes every 5 mins
                self.say(random.choice(MOTIVATIONAL_QUOTES), EMOTION_THINKING)
        else:
            self.pomodoro_timer.stop()
            self.is_pomodoro_active = False
            self.btn_focus.setText("⏱️ Focus")
            
            # Log successful focus session & reward XP
            self.db.add_focus_session(25, "study")
            self.gain_xp(XP_REWARDS["pomodoro"])
            self.say(f"Spectacular job! Focus session completed. +{XP_REWARDS['pomodoro']} XP gained! 🏆", EMOTION_EXCITED)

    def update_focus_button_text(self):
        mins, secs = divmod(self.pomodoro_remaining_seconds, 60)
        self.btn_focus.setText(f"⏱️ {mins:02d}:{secs:02d}")

    # Gamification Progress Engine
    def gain_xp(self, amount: int):
        self.xp += amount
        xp_needed = int(XP_BASE * (self.level ** XP_FACTOR))
        
        if self.xp >= xp_needed:
            self.xp -= xp_needed
            self.level += 1
            self.db.set_stat("level", self.level)
            self.say(f"🎉 LEVEL UP! You reached Level {self.level} - {LEVEL_NAMES.get(self.level, 'Expert')}! 🎉", EMOTION_EXCITED)
            
        self.db.set_stat("xp", self.xp)
        self.update_xp_bar()

    # Dragging & Context Menu Window Handlers
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if hasattr(event, 'globalPosition'):
                gp = event.globalPosition().toPoint()
            else:
                gp = event.globalPos()
            self.drag_position = gp - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if hasattr(event, 'globalPosition'):
                gp = event.globalPosition().toPoint()
            else:
                gp = event.globalPos()
            self.move(gp - self.drag_position)
            event.accept()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {self.get_theme_color('bg_sidebar')};
                border: 1px solid {self.get_theme_color('border_color')};
                border-radius: 8px;
                padding: 5px;
            }}
            QMenu::item {{
                padding: 6px 20px;
                color: {self.get_theme_color('text_primary')};
            }}
            QMenu::item:selected {{
                background-color: {self.get_theme_color('border_color')};
                border-radius: 4px;
            }}
        """)
        
        act_toggle_panel = QAction("Toggle Info Panel", self)
        act_toggle_panel.triggered.connect(self.toggle_panel)
        menu.addAction(act_toggle_panel)
        
        act_change_theme = QAction("Switch Theme (Light/Dark)", self)
        act_change_theme.triggered.connect(self.toggle_theme)
        menu.addAction(act_change_theme)
        
        act_reset_stats = QAction("View Progress Report", self)
        act_reset_stats.triggered.connect(self.show_progress_dialog)
        menu.addAction(act_reset_stats)
        
        menu.addSeparator()
        
        act_exit = QAction("Exit MiniMe", self)
        act_exit.triggered.connect(QApplication.instance().quit)
        menu.addAction(act_exit)
        
        menu.exec(event.globalPos())

    def toggle_panel(self):
        self.is_panel_visible = not self.is_panel_visible
        self.panel_frame.setVisible(self.is_panel_visible)
        new_height = 480 if self.is_panel_visible else 260
        self.setFixedSize(300, new_height)

    def toggle_theme(self):
        current_theme = self.db.get_setting("theme", "dark")
        new_theme = "light" if current_theme == "dark" else "dark"
        self.db.set_setting("theme", new_theme)
        self.apply_theme()
        # Repaint custom container style
        self.container.setStyleSheet(f"""
            QFrame#MainContainer {{
                background-color: {self.get_theme_color("bg_main")};
                border: 2px solid {self.get_theme_color("border_color")};
                border-radius: 20px;
            }}
        """)
        self.say(f"Switched to {new_theme} mode! 🎨")

    def show_progress_dialog(self):
        water_data = self.db.get_weekly_water_data()
        total_water = sum(amount for _, amount in water_data)
        focus_data = self.db.get_weekly_focus_data()
        total_study = sum(mins for _, mins in focus_data.get("study", []))
        total_coding = sum(mins for _, mins in focus_data.get("coding", []))
        
        report = (
            f"--- Weekly Activity Summary ---\n\n"
            f"💧 Water Consumption: {total_water} ml\n"
            f"📚 Study Focus: {total_study} minutes\n"
            f"💻 Coding Focus: {total_coding} minutes\n\n"
            f"XP Level: Level {self.level} ({self.xp} XP)"
        )
        self.say(report, EMOTION_EXCITED)

    # System Tray Integration
    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        # Load a default tray icon (using happy.svg rendered to tray if possible, or fallback circle)
        icon_path = os.path.join(AVATARS_DIR, "happy.svg")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            self.tray_icon.setIcon(QApplication.style().standardIcon(QApplication.style().SP_ComputerIcon))
            
        tray_menu = QMenu()
        tray_menu.setStyleSheet("padding: 5px;")
        
        act_show = QAction("Show MiniMe", self)
        act_show.triggered.connect(self.show)
        
        act_hide = QAction("Hide MiniMe", self)
        act_hide.triggered.connect(self.hide)
        
        act_exit = QAction("Quit", self)
        act_exit.triggered.connect(QApplication.instance().quit)
        
        tray_menu.addAction(act_show)
        tray_menu.addAction(act_hide)
        tray_menu.addSeparator()
        tray_menu.addAction(act_exit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Enable high DPI scaling
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # Hide application from macOS Dock to keep it as a pure widget desktop companion
    # (Optional, but highly matches modern widget behavior)
    if sys.platform == "darwin":
        try:
            from AppKit import NSBundle, NSApplicationActivationPolicyProhibited
            info = NSBundle.mainBundle().infoDictionary()
            info["LSUIElement"] = "1"
        except ImportError:
            pass

    companion = MiniMeCompanion()
    companion.show()
    sys.exit(app.exec())
