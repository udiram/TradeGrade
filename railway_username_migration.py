#!/usr/bin/env python3
"""
Railway-specific migration script for adding username field and injury status columns
This handles the MySQL database on Railway
"""

import os
import sys
import pymysql
from urllib.parse import urlparse

def get_database_url():
    """Get database URL from Railway environment variables"""
    # Try different Railway environment variable names
    for var in ['DATABASE_URL', 'MYSQL_URL', 'SQLALCHEMY_DATABASE_URI']:
        url = os.getenv(var)
        if url:
            print(f"Found database URL in {var}")
            return url
    print("No database URL found in environment variables")
    return None

def parse_database_url(url):
    """Parse database URL into connection parameters"""
    parsed = urlparse(url)
    return {
        'host': parsed.hostname,
        'port': parsed.port or 3306,
        'user': parsed.username,
        'password': parsed.password,
        'database': parsed.path[1:] if parsed.path else 'railway'
    }

def add_username_column():
    """Add username column to existing users table and injury status columns to player table"""
    db_url = get_database_url()
    if not db_url:
        print("❌ No database URL found in environment variables")
        return False
    
    try:
        # Parse connection parameters
        conn_params = parse_database_url(db_url)
        print(f"Connecting to database: {conn_params['host']}:{conn_params['port']}")
        
        # Connect to database
        connection = pymysql.connect(**conn_params)
        cursor = connection.cursor()
        
        print("✅ Connected to Railway MySQL database")
        
        # Check if username column already exists
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'user' AND COLUMN_NAME = 'username'
        """, (conn_params['database'],))
        
        username_exists = cursor.fetchone()
        if username_exists:
            print("✅ Username column already exists")
        else:
            print("🔄 Adding username column...")
            
            # Add username column as nullable first
            cursor.execute("ALTER TABLE user ADD COLUMN username VARCHAR(50) NULL")
            print("✅ Username column added")
            
            # Generate usernames for existing users
            print("🔄 Generating usernames for existing users...")
            cursor.execute("SELECT id, email FROM user WHERE username IS NULL")
            users = cursor.fetchall()
            
            print(f"Found {len(users)} users without usernames")
            
            for user_id, email in users:
                # Generate username from email
                username_base = email.split('@')[0].lower()
                # Remove any non-alphanumeric characters except underscore
                username_base = ''.join(c for c in username_base if c.isalnum() or c == '_')
                # Ensure it starts with a letter or underscore
                if username_base and not username_base[0].isalpha() and username_base[0] != '_':
                    username_base = 'user_' + username_base
                
                username = username_base
                
                # Ensure username is unique
                counter = 1
                while True:
                    cursor.execute("SELECT id FROM user WHERE username = %s", (username,))
                    if not cursor.fetchone():
                        break
                    username = f"{username_base}{counter}"
                    counter += 1
                
                # Update user with generated username
                cursor.execute("UPDATE user SET username = %s WHERE id = %s", (username, user_id))
                print(f"✅ Generated username '{username}' for user {user_id}")
            
            # Make username non-nullable and add unique index
            print("🔄 Making username non-nullable and adding unique index...")
            cursor.execute("ALTER TABLE user MODIFY COLUMN username VARCHAR(50) NOT NULL")
            cursor.execute("CREATE UNIQUE INDEX ix_user_username ON user (username)")
        
        # ALWAYS check and add injury status columns (regardless of username column status)
        print("🔍 Checking player table for injury status columns...")
        
        # Add injury status columns to player table
        print("🔄 Adding injury status columns to player table...")
        
        # Check if injury_status column already exists
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'player' AND COLUMN_NAME = 'injury_status'
        """, (conn_params['database'],))
        
        injury_status_exists = cursor.fetchone()
        if not injury_status_exists:
            cursor.execute("ALTER TABLE player ADD COLUMN injury_status VARCHAR(20) NULL")
            print("✅ injury_status column added")
        else:
            print("✅ injury_status column already exists")
        
        # Check if injury_updated_at column already exists
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'player' AND COLUMN_NAME = 'injury_updated_at'
        """, (conn_params['database'],))
        
        injury_updated_at_exists = cursor.fetchone()
        if not injury_updated_at_exists:
            cursor.execute("ALTER TABLE player ADD COLUMN injury_updated_at DATETIME NULL")
            print("✅ injury_updated_at column added")
        else:
            print("✅ injury_updated_at column already exists")
        
        # Commit changes
        connection.commit()
        print("✅ Migration completed successfully!")
        
        # Trigger player sync after migration
        print("🔄 Triggering player sync with injury status...")
        try:
            import subprocess
            import os
            # Set environment variables for the sync
            os.environ['FLASK_APP'] = 'run.py'
            result = subprocess.run(['python', '-c', '''
from app import create_app
from app.services.players import warm_players_cache, sync_active_players_into_db, purge_non_nfl_players
from app.models import Player
from app.extensions import db

app = create_app()
with app.app_context():
    print("Warming players cache...")
    warm_players_cache()
    print("Syncing NFL players to database...")
    removed = purge_non_nfl_players(db, Player)
    added = sync_active_players_into_db(db, Player)
    print(f"Player sync complete: {removed} removed, {added} added")
'''], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("✅ Player sync completed successfully")
                if result.stdout:
                    print(f"Sync output: {result.stdout}")
            else:
                print(f"⚠️ Player sync failed: {result.stderr}")
        except Exception as e:
            print(f"⚠️ Player sync failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    print("🚀 Starting Railway migration (username + injury status)...")
    success = add_username_column()
    if success:
        print("🎉 Railway migration completed successfully!")
    else:
        print("💥 Railway migration failed!")
    sys.exit(0 if success else 1)
