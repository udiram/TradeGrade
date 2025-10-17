#!/usr/bin/env python3
"""
MySQL database initialization script for Railway deployment
This script ensures the database is properly set up with PyMySQL
"""

import os
import sys
from flask import Flask

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def init_mysql_database():
    """Initialize MySQL database with proper connection"""
    try:
        # Import the app factory
        from app import create_app
        
        # Create the app
        app = create_app()
        
        with app.app_context():
            print("🔧 Initializing MySQL database...")
            print("📊 Database URL:", app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set'))
            
            # Import PyMySQL to ensure it's available
            import pymysql
            pymysql.install_as_MySQLdb()
            
            # Create all tables
            from app.extensions import db
            db.create_all()
            
            print("✅ MySQL database initialization completed successfully!")
            
    except Exception as e:
        print(f"❌ MySQL initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_mysql_database()
