# config/config_manager.py

import os
import json
import logging
from typing import Any, Dict
from threading import Lock

# Set up local logger for configuration lifecycle
logger = logging.getLogger("MiniMe.Config")

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

class ConfigManager:
    """
    Thread-safe Configuration Manager for MiniMe AI.
    Handles reading, writing, and synchronization of runtime parameters.
    """
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(ConfigManager, cls).__new__(cls, *args, **kwargs)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.lock = Lock()
        self.defaults: Dict[str, Any] = {
            "theme": "dark",
            "username": "Hargun",
            "avatar_style": "classic",
            "water_target_ml": 2000,
            "water_interval_mins": 60,
            "pomodoro_duration": 25,
            "short_break_duration": 5,
            "long_break_duration": 15,
            "voice_enabled": True,
            "sound_enabled": True,
            "transparency": 0.9,
            "startup_launch": False,
            "animation_speed": 1.0,
            "always_on_top": True,
            "opacity": 0.95,
            "font_size": 12
        }
        self.config_data = {}
        self.load_config()
        self._initialized = True

    def load_config(self):
        """Loads configuration from file or falls back to defaults."""
        with self.lock:
            if not os.path.exists(CONFIG_FILE):
                logger.warning(f"Config file not found. Creating {CONFIG_FILE} with defaults.")
                self.config_data = self.defaults.copy()
                self._save_config_unsafe()
                return

            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    # Merge with defaults to ensure all keys are present
                    self.config_data = self.defaults.copy()
                    self.config_data.update(data)
                logger.info("Configuration successfully loaded.")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading configuration. Falling back to defaults. Error: {e}")
                self.config_data = self.defaults.copy()

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a configuration value thread-safely."""
        with self.lock:
            # If default is not provided, fall back to default dict
            fallback = default if default is not None else self.defaults.get(key)
            return self.config_data.get(key, fallback)

    def set(self, key: str, value: Any):
        """Sets a configuration value thread-safely and commits it to disk."""
        with self.lock:
            self.config_data[key] = value
            self._save_config_unsafe()
        logger.info(f"Config updated: {key} = {value}")

    def _save_config_unsafe(self):
        """Saves config data to disk without locking (private method)."""
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config_data, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save configuration to disk: {e}")
            raise
