# tests/test_phase1.py

import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logging_config import setup_logging
from config.config_manager import ConfigManager
from config.constants import XP_REWARDS, LEVEL_NAMES

class TestPhase1(unittest.TestCase):
    def setUp(self):
        # Initialize logging
        self.logger = setup_logging()

    def test_logging(self):
        self.assertIsNotNone(self.logger)
        log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "app.log")
        self.assertTrue(os.path.exists(log_file))

    def test_config_manager(self):
        cm = ConfigManager()
        # Verify default value
        self.assertEqual(cm.get("username"), "Hargun")
        
        # Verify writing config updates and persists
        cm.set("water_target_ml", 2500)
        self.assertEqual(cm.get("water_target_ml"), 2500)
        
        # Re-initialize to verify singleton loading from file
        cm2 = ConfigManager()
        self.assertEqual(cm2.get("water_target_ml"), 2500)
        
        # Reset to default for clean state
        cm.set("water_target_ml", 2000)

    def test_constants(self):
        self.assertEqual(XP_REWARDS["water"], 10)
        self.assertEqual(LEVEL_NAMES[1], "Novice Companion")

if __name__ == "__main__":
    unittest.main()
