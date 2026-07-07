# config/constants.py

import os

# Base directory references
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
AVATARS_DIR = os.path.join(ASSETS_DIR, "avatars")
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")

# Ensure assets subdirectories exist
os.makedirs(AVATARS_DIR, exist_ok=True)
os.makedirs(ICONS_DIR, exist_ok=True)
os.makedirs(SOUNDS_DIR, exist_ok=True)

# Gamification Configuration
XP_BASE = 100          # XP required to complete Level 1
XP_FACTOR = 1.2        # XP scaling factor per level (Level N requires XP_BASE * (N ^ XP_FACTOR))
XP_REWARDS = {
    "water": 10,       # XP gained from tracking water
    "task": 25,        # XP gained from completing a standard task
    "pomodoro": 50,    # XP gained from completing a 25-min pomodoro
    "deep_work": 15,   # XP gained per 10 minutes of deep work focus
    "streak_daily": 40,# XP bonus for maintaining daily activity streak
}

# Levels configuration
LEVEL_NAMES = {
    1: "Novice Companion",
    2: "Habit Builder",
    3: "Focus Disciple",
    4: "Productivity Knight",
    5: "Deep Work Master",
    10: "Zen Grandmaster"
}

# Emotion Mapping States
EMOTION_HAPPY = "happy"
EMOTION_SAD = "sad"
EMOTION_EXCITED = "excited"
EMOTION_THINKING = "thinking"
EMOTION_SLEEPING = "sleeping"
EMOTION_WAITING = "waiting"   # Default idle state
EMOTION_CODING = "thinking"   # Maps to thinking or coding avatar visual
EMOTION_STUDYING = "thinking"
EMOTION_PROUD = "excited"
EMOTION_HYDRATED = "happy"

# Avatar Assets
AVATAR_FILES = {
    EMOTION_HAPPY: "happy.svg",
    EMOTION_SAD: "sad.svg",
    EMOTION_EXCITED: "excited.svg",
    EMOTION_THINKING: "thinking.svg",
    EMOTION_SLEEPING: "sleeping.svg",
    EMOTION_WAITING: "waiting.svg"
}

# Default Timing Constraints (Fallback defaults if config is modified)
MIN_WATER_INTERVAL_MINUTES = 10
MAX_WATER_INTERVAL_MINUTES = 360
DEFAULT_WATER_AMOUNT_ML = 250

# Dialogue Heuristics
MOTIVATIONAL_QUOTES = [
    "Focus on being productive instead of busy. 🚀",
    "One step at a time. You've got this! ✨",
    "The secret of getting ahead is getting started. 💪",
    "Believe you can and you're halfway there. 🌟",
    "Deep work is the superpower of the 21st century. 🧠",
    "Quality is not an act, it is a habit. 💎",
    "Make each day your masterpiece. 🎨"
]

WATER_REMINDERS = [
    "Hey {username}! Time for a quick break and a glass of water. 💧 Your brain runs best hydrated!",
    "Hey there 😊 Let's stay hydrated! Grab a glass of water and keep up the great work.",
    "Did you know drinking water improves focus by 14%? Let's take a sip together! 🥛",
    "Time to stretch and hydrate, {username}! Click to confirm your glass of water. 💧"
]

BREAK_REMINDERS = [
    "Time for a break! Stand up, stretch, and relax your eyes for a few minutes. 👀",
    "Great session, {username}! Walk around, grab a tea, or take some deep breaths. 🧘",
    "Focus timer complete! Step away from the screen for a moment to recharge. 🔋"
]
