#!/usr/bin/env python3
"""
Quick script to check database structure for SerpAPI configuration
"""

import sqlite3
import json
import os

def check_database_structure():
    """Check the actual database structure"""
    db_path = "job_applier.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Checking Database Structure for SerpAPI Configuration")
        print("=" * 60)
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        
        print(f"📋 Found {len(tables)} tables:")
        for table in sorted(tables):
            print(f"   • {table}")
        
        # Check for SerpAPI related tables
        serpapi_tables = [t for t in tables if 'serpapi' in t.lower() or 'serp' in t.lower()]
        print(f"\n🔍 SerpAPI-related tables: {serpapi_tables}")
        
        # Check for job_sources table
        if 'job_sources' in tables:
            print(f"\n✅ job_sources table EXISTS")
            cursor.execute("PRAGMA table_info(job_sources);")
            columns = cursor.fetchall()
            print("   Columns:")
            for col in columns:
                print(f"      {col[1]:<20} {col[2]:<15} {'NOT NULL' if col[3] else 'NULL':<8} {col[4] if col[4] else ''}")
        else:
            print(f"\n❌ job_sources table DOES NOT EXIST")
        
        # Check for serpapi_configurations table
        if 'serpapi_configurations' in tables:
            print(f"\n✅ serpapi_configurations table EXISTS")
            cursor.execute("PRAGMA table_info(serpapi_configurations);")
            columns = cursor.fetchall()
            print("   Columns:")
            for col in columns:
                print(f"      {col[1]:<20} {col[2]:<15} {'NOT NULL' if col[3] else 'NULL':<8} {col[4] if col[4] else ''}")
        else:
            print(f"\n❌ serpapi_configurations table DOES NOT EXIST")
        
        # Check user_profiles for integration columns
        if 'user_profiles' in tables:
            print(f"\n📊 user_profiles table structure:")
            cursor.execute("PRAGMA table_info(user_profiles);")
            columns = cursor.fetchall()
            integration_columns = []
            for col in columns:
                col_name = col[1]
                if any(keyword in col_name.lower() for keyword in ['integration', 'config', 'sync', 'source']):
                    integration_columns.append(col_name)
                    print(f"   🔧 {col_name:<25} {col[2]:<15}")
            
            if not integration_columns:
                print("   ⚠️ No integration-related columns found")
        
        # Sample data check
        if 'job_sources' in tables:
            print(f"\n📊 Sample job_sources data:")
            cursor.execute("SELECT id, name, enabled FROM job_sources LIMIT 5;")
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    status = "🟢 Enabled" if row[2] else "🔴 Disabled"
                    print(f"   {row[0]:<15} {row[1]:<25} {status}")
            else:
                print("   No data found")
        
        conn.close()
        
        print(f"\n" + "=" * 60)
        print("💡 Summary:")
        print(f"   • Total tables: {len(tables)}")
        print(f"   • job_sources table: {'✅ EXISTS' if 'job_sources' in tables else '❌ MISSING'}")
        print(f"   • serpapi_configurations: {'✅ EXISTS' if 'serpapi_configurations' in tables else '❌ MISSING'}")
        
        if 'serpapi_configurations' not in tables:
            print(f"\n🔧 ISSUE IDENTIFIED:")
            print(f"   The backend code expects 'serpapi_configurations' table but it doesn't exist!")
            print(f"   This is why SerpAPI configuration is falling back to defaults.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_database_structure()
