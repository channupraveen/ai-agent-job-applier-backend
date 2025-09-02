"""
Database initialization and setup utilities
"""

import sqlite3
import os
from config import Config

def init_database():
    """
    Initialize the database with schema from appropriate SQL file
    """
    config = Config()
    db_url = config.DATABASE_URL
    
    print(f"Initializing database at: {db_url}")
    
    try:
        if db_url.startswith('postgresql'):
            # PostgreSQL setup
            import psycopg
            from urllib.parse import urlparse
            
            result = urlparse(db_url)
            conn = psycopg.connect(
                f"dbname={result.path[1:]} user={result.username} password={result.password} host={result.hostname} port={result.port}"
            )
            cursor = conn.cursor()
            schema_path = os.path.join(os.path.dirname(__file__), '..', 'schema_postgresql.sql')
            
        else:
            # SQLite setup
            import sqlite3
            db_path = db_url.replace('sqlite:///', '')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            schema_path = os.path.join(os.path.dirname(__file__), '..', 'schema.sql')
        
        # Read and execute schema
        with open(schema_path, 'r', encoding='utf-8') as schema_file:
            schema_sql = schema_file.read()
            
        # Execute SQL commands
        if db_url.startswith('postgresql'):
            # PostgreSQL - execute each statement separately
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            for statement in statements:
                if statement:
                    cursor.execute(statement)
        else:
            # SQLite - can use executescript
            cursor.executescript(schema_sql)
            
        conn.commit()
        
        print("Database schema created successfully!")
        print("Initial data inserted!")
        
        # Verify tables were created
        if db_url.startswith('postgresql'):
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
        else:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            
        tables = cursor.fetchall()
        print(f"Created tables: {', '.join([table[0] for table in tables])}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Database initialization failed: {str(e)}")
        return False

def check_database():
    """
    Check if database exists and has required tables
    """
    config = Config()
    db_url = config.DATABASE_URL
    
    try:
        if db_url.startswith('postgresql'):
            # PostgreSQL check
            import psycopg
            from urllib.parse import urlparse
            
            result = urlparse(db_url)
            conn = psycopg.connect(
                f"dbname={result.path[1:]} user={result.username} password={result.password} host={result.hostname} port={result.port}"
            )
            cursor = conn.cursor()
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
            
        else:
            # SQLite check
            import sqlite3
            db_path = db_url.replace('sqlite:///', '')
            if not os.path.exists(db_path):
                print("Database file not found")
                return False
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        
        existing_tables = [table[0] for table in cursor.fetchall()]
        
        required_tables = [
            'job_applications', 'cover_letters', 'application_sessions',
            'user_profiles', 'job_search_criteria', 'application_logs'
        ]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        conn.close()
        
        if missing_tables:
            print(f"Missing tables: {', '.join(missing_tables)}")
            return False
        else:
            print("Database is properly configured!")
            return True
            
    except Exception as e:
        print(f"Database check failed: {str(e)}")
        return False

def reset_database():
    """
    Reset database - drop and recreate all tables
    """
    config = Config()
    db_url = config.DATABASE_URL
    
    try:
        if db_url.startswith('postgresql'):
            # PostgreSQL reset
            import psycopg
            from urllib.parse import urlparse
            
            result = urlparse(db_url)
            conn = psycopg.connect(
                f"dbname={result.path[1:]} user={result.username} password={result.password} host={result.hostname} port={result.port}"
            )
            cursor = conn.cursor()
            
            # Drop all tables
            cursor.execute("""
                DO $$ DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                    END LOOP;
                END $$;
            """)
            conn.commit()
            conn.close()
            
        else:
            # SQLite reset
            db_path = db_url.replace('sqlite:///', '')
            if os.path.exists(db_path):
                os.remove(db_path)
                print(f"Removed existing database: {db_path}")
        
        return init_database()
        
    except Exception as e:
        print(f"Database reset failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting database setup...")
    
    if check_database():
        print("Database already exists and is configured correctly!")
    else:
        print("Setting up database...")
        if init_database():
            print("Database setup complete!")
        else:
            print("Database setup failed!")
