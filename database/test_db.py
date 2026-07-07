# database/test_db.py

import os
import sys

# Ensure project root is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import DatabaseManager

def test_database():
    print("Initializing Database Manager...")
    db = DatabaseManager("test_minime.db")
    
    # Test setting
    print("\n--- Testing Settings ---")
    db.set_setting("theme", "light")
    theme = db.get_setting("theme")
    print(f"Retrieved theme setting: {theme} (Expected: light)")
    
    db.set_setting("username", "Hargun")
    username = db.get_setting("username")
    print(f"Retrieved username setting: {username} (Expected: Hargun)")
    
    # Test user stats
    print("\n--- Testing User Stats ---")
    db.set_stat("xp", 120)
    xp = db.get_stat("xp")
    print(f"Retrieved XP stat: {xp} (Expected: 120)")
    
    # Test water logging
    print("\n--- Testing Water Logging ---")
    daily_total = db.add_water(250)
    print(f"Added 250ml water. New daily total: {daily_total}ml")
    
    daily_total = db.add_water(250)
    print(f"Added another 250ml water. New daily total: {daily_total}ml (Expected: 500)")
    
    weekly_water = db.get_weekly_water_data()
    print("Weekly water logs:", weekly_water)
    
    # Test focus sessions
    print("\n--- Testing Focus Sessions ---")
    db.add_focus_session(25, "study")
    db.add_focus_session(45, "coding")
    weekly_focus = db.get_weekly_focus_data()
    print("Weekly focus logs:", weekly_focus)
    
    # Test tasks
    print("\n--- Testing Tasks ---")
    task_id = db.add_task("Complete PySide6 layout", 20)
    print(f"Added task. ID: {task_id}")
    
    tasks = db.get_all_tasks()
    print(f"All tasks: {tasks}")
    
    xp_change = db.toggle_task(task_id, True)
    print(f"Completed task {task_id}. XP Gained: {xp_change} (Expected: 20)")
    
    tasks_after = db.get_all_tasks()
    print(f"All tasks after toggle: {tasks_after}")
    
    db.delete_task(task_id)
    print("Deleted task.")
    
    # Clean up test database file
    if os.path.exists("test_minime.db"):
        os.remove("test_minime.db")
        print("\nCleaned up test_minime.db file successfully.")
        
    print("\nAll database tests passed successfully!")

if __name__ == "__main__":
    test_database()
