# main.py

import os
import sys
import random
import logging
import threading
from PySide6.QtCore import Qt, QPoint, QSize, QTimer, QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup
from PySide6.QtGui import QIcon, QColor, QFont, QAction, QPixmap
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect,
    QSystemTrayIcon, QMenu, QInputDialog
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

        # Setup auto-hide timers
        self.auto_hide_timer = QTimer(self)
        self.auto_hide_timer.setSingleShot(True)
        self.auto_hide_timer.timeout.connect(self.fade_out)

        # Start Idle Floating Animation
        self.start_bobbing_animation()

        # Initial Summoning
        QTimer.singleShot(1000, lambda: self.summon(f"Hi {self.username}! Ready to crush your goals today? 🚀"))

    def init_ui(self):
        # Configure Frameless, Translucent, Always-on-Top Tool Window
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Clean compact window size
        self.setFixedSize(300, 260)
        self.apply_theme()

        # Opacity effect for clean fade-in/fade-out
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)  # Start hidden

        self.opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_anim.setDuration(600)
        self.opacity_anim.setEasingCurve(QEasingCurve.InOutQuad)

        # 1. SPEECH BUBBLE (Absolute positioning at top)
        self.bubble_frame = QFrame(self)
        self.bubble_frame.setGeometry(10, 10, 280, 85)
        self.bubble_frame.setObjectName("SpeechBubble")
        
        # Premium custom speech bubble style
        self.update_bubble_style()

        bubble_layout = QVBoxLayout(self.bubble_frame)
        bubble_layout.setContentsMargins(12, 10, 12, 10)
        self.bubble_label = QLabel("...", self)
        self.bubble_label.setWordWrap(True)
        self.bubble_label.setFont(QFont("Inter", 11))
        self.bubble_label.setAlignment(Qt.AlignCenter)
        self.bubble_label.setStyleSheet("color: inherit; background: transparent;")
        bubble_layout.addWidget(self.bubble_label)

        # Drop Shadow for speech bubble
        bubble_shadow = QGraphicsDropShadowEffect(self)
        bubble_shadow.setBlurRadius(10)
        bubble_shadow.setColor(QColor(0, 0, 0, 50))
        bubble_shadow.setOffset(0, 3)
        self.bubble_frame.setGraphicsEffect(bubble_shadow)

        # 2. AVATAR CONTAINER (Absolute positioning in middle/bottom)
        self.avatar_container = QWidget(self)
        self.avatar_container.setGeometry(85, 110, 130, 130)
        
        container_layout = QHBoxLayout(self.avatar_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setAlignment(Qt.AlignCenter)

        # Label for standard image formats (Bitmoji PNG/JPG/GIF)
        self.avatar_image_label = QLabel(self.avatar_container)
        self.avatar_image_label.setScaledContents(True)
        self.avatar_image_label.setStyleSheet("background: transparent;")
        self.avatar_image_label.hide()
        container_layout.addWidget(self.avatar_image_label)

        # SVG Widget for default SVGs
        self.avatar_svg_widget = QSvgWidget(self.avatar_container)
        self.avatar_svg_widget.setFixedSize(130, 130)
        self.avatar_svg_widget.setStyleSheet("background: transparent;")
        container_layout.addWidget(self.avatar_svg_widget)

        # Connect click event directly to the container for winks/reacts
        self.avatar_container.mousePressEvent = self.on_avatar_clicked

        # Position window in the bottom-right corner of the primary screen
        self.reposition_to_bottom_right()

    def update_bubble_style(self):
        self.bubble_frame.setStyleSheet(f"""
            QFrame#SpeechBubble {{
                background-color: {self.get_theme_color("bg_card_opaque")};
                border: 2px solid {self.get_theme_color("border_color")};
                border-radius: 16px;
                color: {self.get_theme_color("text_primary")};
            }}
        """)

    def apply_theme(self):
        theme_name = self.db.get_setting("theme", "dark")
        self.setStyleSheet(get_stylesheet(theme_name))
        if hasattr(self, "bubble_frame"):
            self.update_bubble_style()
        
    def get_theme_color(self, key: str) -> str:
        theme_name = self.db.get_setting("theme", "dark")
        from themes.styles import THEMES
        return THEMES.get(theme_name, THEMES["dark"]).get(key, "#ffffff")

    def reposition_to_bottom_right(self):
        try:
            screen_geom = QApplication.primaryScreen().availableGeometry()
            x = screen_geom.width() - 320
            y = screen_geom.height() - 280
            self.move(x, y)
        except Exception as e:
            logger.warning(f"Failed to position window: {e}")

    # Micro-Animations
    def start_bobbing_animation(self):
        """Creates a continuous vertical hovering effect for the avatar."""
        self.bob_group = QSequentialAnimationGroup(self)

        # Up movement
        self.anim_up = QPropertyAnimation(self.avatar_container, b"pos")
        self.anim_up.setDuration(1500)
        self.anim_up.setStartValue(QPoint(85, 110))
        self.anim_up.setEndValue(QPoint(85, 102))
        self.anim_up.setEasingCurve(QEasingCurve.InOutSine)

        # Down movement
        self.anim_down = QPropertyAnimation(self.avatar_container, b"pos")
        self.anim_down.setDuration(1500)
        self.anim_down.setStartValue(QPoint(85, 102))
        self.anim_down.setEndValue(QPoint(85, 110))
        self.anim_down.setEasingCurve(QEasingCurve.InOutSine)

        self.bob_group.addAnimation(self.anim_up)
        self.bob_group.addAnimation(self.anim_down)
        self.bob_group.setLoopCount(-1)  # Infinite
        self.bob_group.start()

    # Fade & Lifecycle System
    def summon(self, text: str, emotion: str = None, duration: int = 7):
        """Fades in the companion, displays the bubble, and registers an auto-hide timer."""
        self.auto_hide_timer.stop()
        
        # Update content & speak
        self.bubble_label.setText(text)
        if emotion:
            self.set_emotion(emotion)
        
        # Speak text if voice is enabled
        voice_on = self.db.get_setting("voice_enabled", "1") == "1"
        if voice_on:
            speak_text_async(text)

        # Shake speech bubble slightly on popup
        self.bubble_frame.move(self.bubble_frame.x(), self.bubble_frame.y() - 3)
        QTimer.singleShot(100, lambda: self.bubble_frame.move(self.bubble_frame.x(), self.bubble_frame.y() + 3))

        # Start fade-in
        self.show()
        self.opacity_anim.stop()
        try:
            self.opacity_anim.finished.disconnect()
        except Exception:
            pass
        self.opacity_anim.setStartValue(self.opacity_effect.opacity())
        self.opacity_anim.setEndValue(1.0)
        self.opacity_anim.start()

        # Set auto-hide timer
        self.auto_hide_timer.start(duration * 1000)

    def fade_out(self):
        """Fades out and hides the window when tasks/speeches are finished."""
        self.opacity_anim.stop()
        try:
            self.opacity_anim.finished.disconnect()
        except Exception:
            pass
        self.opacity_anim.setStartValue(self.opacity_effect.opacity())
        self.opacity_anim.setEndValue(0.0)
        self.opacity_anim.finished.connect(self.hide)
        self.opacity_anim.start()

    # Custom Avatar & Bitmoji loading
    def set_emotion(self, emotion: str):
        """Updates the graphic, preferring custom Bitmojis, falling back to SVG."""
        self.current_emotion = emotion
        
        # 1. Search for custom Bitmoji
        extensions = ["png", "jpg", "jpeg", "webp", "gif"]
        bitmoji_path = None
        
        # Try emotion-specific first, e.g. bitmoji_happy.png
        for ext in extensions:
            p = os.path.join(AVATARS_DIR, f"bitmoji_{emotion}.{ext}")
            if os.path.exists(p):
                bitmoji_path = p
                break
                
        # Fallback to general bitmoji.png
        if not bitmoji_path:
            for ext in extensions:
                p = os.path.join(AVATARS_DIR, f"bitmoji.{ext}")
                if os.path.exists(p):
                    bitmoji_path = p
                    break
        
        # 2. Render selected asset
        if bitmoji_path:
            self.avatar_svg_widget.hide()
            self.avatar_image_label.show()
            
            # Support animated GIFs
            if bitmoji_path.lower().endswith(".gif"):
                from PySide6.QtGui import QMovie
                movie = QMovie(bitmoji_path)
                movie.setScaledSize(QSize(130, 130))
                self.avatar_image_label.setMovie(movie)
                movie.start()
            else:
                pixmap = QPixmap(bitmoji_path)
                scaled = pixmap.scaled(130, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.avatar_image_label.setPixmap(scaled)
        else:
            # Standard SVG fallback
            self.avatar_image_label.hide()
            self.avatar_svg_widget.show()
            filename = AVATAR_FILES.get(emotion, "waiting.svg")
            path = os.path.join(AVATARS_DIR, filename)
            if os.path.exists(path):
                self.avatar_svg_widget.load(path)

    # Click interactions
    def on_avatar_clicked(self, event):
        if event.button() == Qt.LeftButton:
            # Re-summon / speak a new quote
            quote = random.choice(MOTIVATIONAL_QUOTES)
            self.summon(quote, EMOTION_EXCITED, duration=6)
            self.gain_xp(5)

    def trigger_random_reminder(self):
        reminder = random.choice(WATER_REMINDERS).format(username=self.username)
        self.summon(reminder, EMOTION_THINKING, duration=8)

    # Habit Logging Actions
    def log_water_click(self):
        daily_total = self.db.add_water(250)
        self.gain_xp(XP_REWARDS["water"])
        self.summon(f"Hydration logged! +250ml. Today: {daily_total}ml. Keep it up! 💧", EMOTION_HAPPY, duration=6)

    def log_mood_prompt(self):
        # Temporarily stop auto-hide while dialog is showing
        self.auto_hide_timer.stop()
        
        items = ["Happy", "Calm", "Anxious", "Tired", "Stressed", "Productive"]
        item, ok = QInputDialog.getItem(self, "Log Mood", "How are you feeling?", items, 0, False)
        
        if ok and item:
            self.db.log_mood(item)
            if item in ["Happy", "Productive", "Calm"]:
                self.summon(f"Awesome! Feeling {item.lower()}. Let's maintain this flow! ✨", EMOTION_EXCITED, duration=6)
            else:
                self.summon(f"Acknowledge how you feel. Take a deep breath. You got this. 🤍", EMOTION_SAD, duration=6)
        else:
            # Reset timer if cancelled
            self.auto_hide_timer.start(3000)

    # Focus Timer Logic
    def toggle_focus_timer(self):
        if self.is_pomodoro_active:
            self.pomodoro_timer.stop()
            self.is_pomodoro_active = False
            self.update_tray_focus_text()
            self.summon("Focus session cancelled. Rest up! 🧘", EMOTION_WAITING, duration=5)
        else:
            duration_mins = int(self.db.get_setting("pomodoro_duration", 25))
            self.pomodoro_remaining_seconds = duration_mins * 60
            self.pomodoro_timer.start(1000)
            self.is_pomodoro_active = True
            self.update_tray_focus_text()
            self.summon(f"Focus timer started for {duration_mins} minutes! Keep coding. 🧠", EMOTION_THINKING, duration=6)

    def update_pomodoro(self):
        if self.pomodoro_remaining_seconds > 0:
            self.pomodoro_remaining_seconds -= 1
            self.update_tray_focus_text()
            if self.pomodoro_remaining_seconds % 300 == 0:  # Every 5 mins, popup a quote
                self.summon(random.choice(MOTIVATIONAL_QUOTES), EMOTION_THINKING, duration=6)
        else:
            self.pomodoro_timer.stop()
            self.is_pomodoro_active = False
            self.update_tray_focus_text()
            
            # Save focus data & gain XP
            self.db.add_focus_session(25, "study")
            self.gain_xp(XP_REWARDS["pomodoro"])
            self.summon(f"Spectacular! Focus session completed. +{XP_REWARDS['pomodoro']} XP! 🏆", EMOTION_EXCITED, duration=8)

    def update_tray_focus_text(self):
        if self.is_pomodoro_active:
            mins, secs = divmod(self.pomodoro_remaining_seconds, 60)
            self.act_focus.setText(f"⏱️ Cancel Focus ({mins:02d}:{secs:02d})")
        else:
            self.act_focus.setText("⏱️ Start Focus Session")

    def gain_xp(self, amount: int):
        self.xp += amount
        xp_needed = int(XP_BASE * (self.level ** XP_FACTOR))
        
        if self.xp >= xp_needed:
            self.xp -= xp_needed
            self.level += 1
            self.db.set_stat("level", self.level)
            self.summon(f"🎉 LEVEL UP! You reached Level {self.level} - {LEVEL_NAMES.get(self.level, 'Expert')}! 🎉", EMOTION_EXCITED, duration=8)
            
        self.db.set_stat("xp", self.xp)

    # Window Handlers
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
        menu = self.create_actions_menu()
        menu.exec(event.globalPos())

    def toggle_theme(self):
        current = self.db.get_setting("theme", "dark")
        new_theme = "light" if current == "dark" else "dark"
        self.db.set_setting("theme", new_theme)
        self.apply_theme()
        self.summon(f"Switched to {new_theme} theme! 🎨", duration=4)

    def show_progress_dialog(self):
        water_data = self.db.get_weekly_water_data()
        total_water = sum(amount for _, amount in water_data)
        focus_data = self.db.get_weekly_focus_data()
        total_study = sum(mins for _, mins in focus_data.get("study", []))
        total_coding = sum(mins for _, mins in focus_data.get("coding", []))
        
        report = (
            f"Weekly Report:\n"
            f"💧 Water: {total_water} ml\n"
            f"📚 Study: {total_study} mins\n"
            f"💻 Coding: {total_coding} mins\n"
            f"⭐ Level {self.level} ({self.xp} XP)"
        )
        self.summon(report, EMOTION_HAPPY, duration=8)

    # Create Context Menu helper
    def create_actions_menu(self) -> QMenu:
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {self.get_theme_color('bg_sidebar')};
                border: 1px solid {self.get_theme_color('border_color')};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 18px;
                color: {self.get_theme_color('text_primary')};
            }}
            QMenu::item:selected {{
                background-color: {self.get_theme_color('border_color')};
                border-radius: 4px;
            }}
        """)
        
        act_summon = QAction("🙋 Summon Companion", self)
        act_summon.triggered.connect(lambda: self.summon(random.choice(MOTIVATIONAL_QUOTES)))
        menu.addAction(act_summon)
        
        menu.addSeparator()

        act_water = QAction("💧 Log Water (+250ml)", self)
        act_water.triggered.connect(self.log_water_click)
        menu.addAction(act_water)
        
        self.act_focus = QAction(self)
        self.update_workspace_focus_action_text()
        self.act_focus.triggered.connect(self.toggle_focus_timer)
        menu.addAction(self.act_focus)
        
        act_mood = QAction("😊 Log Mood", self)
        act_mood.triggered.connect(self.log_mood_prompt)
        menu.addAction(act_mood)
        
        act_report = QAction("📊 Progress Report", self)
        act_report.triggered.connect(self.show_progress_dialog)
        menu.addAction(act_report)
        
        menu.addSeparator()
        
        act_change_theme = QAction("Switch Theme (Light/Dark)", self)
        act_change_theme.triggered.connect(self.toggle_theme)
        menu.addAction(act_change_theme)
        
        act_exit = QAction("Exit MiniMe", self)
        act_exit.triggered.connect(QApplication.instance().quit)
        menu.addAction(act_exit)
        
        return menu

    def update_workspace_focus_action_text(self):
        if self.is_pomodoro_active:
            mins, secs = divmod(self.pomodoro_remaining_seconds, 60)
            self.act_focus.setText(f"⏱️ Cancel Focus ({mins:02d}:{secs:02d})")
        else:
            self.act_focus.setText("⏱️ Start Focus Session")

    # System Tray Integration
    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        icon_path = os.path.join(AVATARS_DIR, "happy.svg")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            self.tray_icon.setIcon(QApplication.style().standardIcon(QApplication.style().SP_ComputerIcon))
            
        # Re-use actions menu for the system tray
        tray_menu = self.create_actions_menu()
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    if sys.platform == "darwin":
        try:
            from AppKit import NSBundle
            info = NSBundle.mainBundle().infoDictionary()
            info["LSUIElement"] = "1"
        except ImportError:
            pass

    companion = MiniMeCompanion()
    sys.exit(app.exec())
