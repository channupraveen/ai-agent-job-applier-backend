#!/usr/bin/env python3
"""
Database Migration: Add SerpAPI Configuration Table
This script adds the missing serpapi_configurations table to your database
"""

import sqlite3
import os
from datetime import datetime

def create_serpapi_configuration_table():
    """Create the missing serpapi_configurations table"""
    
    db_path = "job_applier.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🚀 Creating SerpAPI Configuration Table")
        print("=" * 50)
        
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='serpapi_configurations';
        """)
        
        if cursor.fetchone():
            print("ℹ️ serpapi_configurations table already exists")
            conn.close()
            return True
        
        # Create the serpapi_configurations table
        print("📝 Creating serpapi_configurations table...")
        
        create_table_sql = """
        CREATE TABLE serpapi_configurations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            api_key VARCHAR(255) NOT NULL,
            engine VARCHAR(50) DEFAULT 'google_jobs',
            location VARCHAR(255) DEFAULT 'India',
            google_domain VARCHAR(100) DEFAULT 'google.com',
            hl VARCHAR(10) DEFAULT 'en',
            gl VARCHAR(10) DEFAULT 'in',
            max_jobs_per_sync INTEGER DEFAULT 50,
            search_radius INTEGER DEFAULT 50,
            ltype INTEGER DEFAULT 0,
            date_posted VARCHAR(20) DEFAULT 'any',
            job_type VARCHAR(20) DEFAULT 'any',
            no_cache BOOLEAN DEFAULT FALSE,
            output VARCHAR(20) DEFAULT 'json',
            is_active BOOLEAN DEFAULT TRUE,
            last_test_at DATETIME,
            last_test_status VARCHAR(20),
            last_test_jobs_found INTEGER DEFAULT 0,
            last_test_message TEXT,
            total_api_calls INTEGER DEFAULT 0,
            last_sync_at DATETIME,
            jobs_fetched_total INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_profiles (id) ON DELETE CASCADE
        );
        """
        
        cursor.execute(create_table_sql)
        
        # Create index for performance
        print("📊 Creating indexes...")
        cursor.execute("""
            CREATE INDEX idx_serpapi_configurations_user_id 
            ON serpapi_configurations (user_id);
        """)
        
        cursor.execute("""
            CREATE INDEX idx_serpapi_configurations_active 
            ON serpapi_configurations (is_active);
        """)
        
        # Insert default configuration for existing users
        print("➕ Adding default SerpAPI configuration for existing users...")
        
        cursor.execute("SELECT id FROM user_profiles LIMIT 1;")
        user_result = cursor.fetchone()
        
        if user_result:
            user_id = user_result[0]
            
            default_config_sql = """
            INSERT INTO serpapi_configurations (
                user_id, api_key, engine, location, google_domain, hl, gl,
                max_jobs_per_sync, search_radius, ltype, date_posted, job_type,
                no_cache, output, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            
            default_values = (
                user_id,
                'a448fc3f98bea2711a110c46c86d75cc09e786b729a8212f666c89d35800429f',  # API key
                'google_jobs',      # engine
                'India',           # location
                'google.com',      # google_domain
                'en',              # hl (interface language)
                'in',              # gl (country code)
                50,                # max_jobs_per_sync
                50,                # search_radius
                0,                 # ltype (0=all jobs, 1=remote only)
                'any',             # date_posted
                'any',             # job_type
                False,             # no_cache
                'json',            # output
                True,              # is_active
                datetime.now(),    # created_at
                datetime.now()     # updated_at
            )
            
            cursor.execute(default_config_sql, default_values)
            print(f"✅ Added default configuration for user ID: {user_id}")
        else:
            print("ℹ️ No users found - default configuration will be created when user configures SerpAPI")
        
        # Also ensure job_sources table has googlejobs entry
        print("🔍 Checking job_sources table for Google Jobs entry...")
        
        cursor.execute("SELECT id FROM job_sources WHERE id = 'googlejobs';")
        google_jobs_result = cursor.fetchone()
        
        if not google_jobs_result:
            print("➕ Adding Google Jobs API source to job_sources...")
            
            # Check if job_sources table exists first
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='job_sources';
            """)
            
            if cursor.fetchone():
                cursor.execute("""
                    INSERT INTO job_sources (
                        id, name, enabled, api_key, base_url, rate_limit, 
                        total_jobs, status, icon
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    'googlejobs',
                    'Google Jobs API',
                    True,
                    'a448fc3f98bea2711a110c46c86d75cc09e786b729a8212f666c89d35800429f',
                    'https://serpapi.com/search.json',
                    100,
                    0,
                    'active',
                    'pi pi-google'
                ))
                print("✅ Added Google Jobs API to job_sources")
            else:
                print("⚠️ job_sources table not found - this might need to be created separately")
        else:
            print("✅ Google Jobs API already exists in job_sources")
        
        conn.commit()
        conn.close()
        
        print("\n" + "=" * 50)
        print("🎉 Migration completed successfully!")
        print("\n📋 What was added:")
        print("   • serpapi_configurations table with all required columns")
        print("   • Indexes for performance optimization")
        print("   • Default configuration for existing users")
        print("   • Google Jobs API entry in job_sources (if missing)")
        
        print("\n🔧 Next Steps:")
        print("   1. Restart your FastAPI backend server")
        print("   2. Test the SerpAPI configuration in frontend")
        print("   3. Verify configuration is saved and loaded properly")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def verify_migration():
    """Verify the migration was successful"""
    
    db_path = "job_applier.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n🔍 Verifying Migration...")
        
        # Check table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='serpapi_configurations';
        """)
        
        if cursor.fetchone():
            print("✅ serpapi_configurations table exists")
            
            # Check table structure
            cursor.execute("PRAGMA table_info(serpapi_configurations);")
            columns = cursor.fetchall()
            print(f"   📊 Table has {len(columns)} columns")
            
            # Check for data
            cursor.execute("SELECT COUNT(*) FROM serpapi_configurations;")
            count = cursor.fetchone()[0]
            print(f"   📊 Table has {count} configuration(s)")
            
            if count > 0:
                cursor.execute("""
                    SELECT user_id, engine, location, max_jobs_per_sync 
                    FROM serpapi_configurations 
                    LIMIT 1;
                """)
                config = cursor.fetchone()
                print(f"   📋 Sample config: User {config[0]}, Engine: {config[1]}, Location: {config[2]}, Max Jobs: {config[3]}")
        else:
            print("❌ serpapi_configurations table not found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Verification error: {e}")

if __name__ == "__main__":
    print("🔧 SerpAPI Configuration Database Migration")
    print("=" * 60)
    
    success = create_serpapi_configuration_table()
    
    if success:
        verify_migration()
        print("\n🎯 READY TO TEST!")
        print("Your SerpAPI configuration should now work properly.")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
