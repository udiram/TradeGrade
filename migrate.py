#!/usr/bin/env python3
"""
Database migration script for Railway deployment
Run this script to apply database migrations on Railway
"""

import os
import sys
from flask import Flask
from flask_migrate import upgrade

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def run_migrations():
    """Run database migrations"""
    try:
        # Import the app factory
        from app import create_app
        
        # Create the app
        app = create_app()
        
        with app.app_context():
            print("🚀 Starting database migration...")
            print("📊 Current database URL:", app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set'))
            
            # Run all pending migrations
            upgrade()
            
            print("✅ Database migration completed successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()
