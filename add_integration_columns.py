"""
Simple script to add missing database columns
Run this after setting up your database connection
"""

import sqlite3
import os

# Path to your SQLite database
DATABASE_PATH = "job_applier.db"

def add_integration_columns():
    """Add integration columns to user_profiles table"""
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Database file not found: {DATABASE_PATH}")
        return False
        
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        print("🔄 Adding integration columns...")
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(user_profiles)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        if 'job_sources_config' not in existing_columns:
            print("➕ Adding job_sources_config column...")
            cursor.execute("ALTER TABLE user_profiles ADD COLUMN job_sources_config TEXT")
            print("✅ Added job_sources_config")
        else:
            print("ℹ️ job_sources_config already exists")
            
        if 'sync_preferences' not in existing_columns:
            print("➕ Adding sync_preferences column...")
            cursor.execute("ALTER TABLE user_profiles ADD COLUMN sync_preferences TEXT")
            print("✅ Added sync_preferences")
        else:
            print("ℹ️ sync_preferences already exists")
        
        conn.commit()
        conn.close()
        
        print("✅ Database migration completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = add_integration_columns()
    if success:
        print("🎉 Ready to test the integrations component!")
    else:
        print("💡 Make sure your database file exists and is accessible.")
