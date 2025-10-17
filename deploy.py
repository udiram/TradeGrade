#!/usr/bin/env python3
"""
Complete deployment script for Railway
Handles MySQL initialization, Flask-Migrate setup, and migrations
"""

import os
import sys
import subprocess
from flask import Flask

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def setup_flask_migrate():
    """Initialize Flask-Migrate if needed"""
    migrations_dir = "migrations"
    
    if not os.path.exists(migrations_dir):
        print("📁 Migrations folder not found. Initializing Flask-Migrate...")
        
        # Set Flask app environment variable
        os.environ['FLASK_APP'] = 'run.py'
        
        # Initialize migrations
        if not run_command("flask db init", "Initialize Flask-Migrate"):
            return False
            
        print("✅ Flask-Migrate initialized")
    else:
        print("📁 Migrations folder already exists")
    
    return True

def run_deployment():
    """Run complete deployment process"""
    try:
        print("🚀 Starting Railway deployment process...")
        
        # Step 1: Initialize PyMySQL
        print("🔧 Setting up MySQL support...")
        import pymysql
        pymysql.install_as_MySQLdb()
        print("✅ PyMySQL configured")
        
        # Step 2: Setup Flask-Migrate
        if not setup_flask_migrate():
            print("❌ Flask-Migrate setup failed")
            return False
        
        # Step 3: Create database tables (if migrations don't exist)
        print("🏗️ Setting up database...")
        from app import create_app
        from app.extensions import db
        
        app = create_app()
        with app.app_context():
            # Check if we have any migration files
            versions_dir = os.path.join("migrations", "versions")
            if os.path.exists(versions_dir) and os.listdir(versions_dir):
                print("📊 Running migrations...")
                os.environ['FLASK_APP'] = 'run.py'
                if not run_command("flask db upgrade", "Run database migrations"):
                    print("⚠️ Migration failed, trying to create tables directly...")
                    db.create_all()
                    print("✅ Database tables created directly")
            else:
                print("📊 No migrations found, creating tables directly...")
                db.create_all()
                print("✅ Database tables created")
        
        print("🎉 Deployment completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return False

if __name__ == "__main__":
    success = run_deployment()
    sys.exit(0 if success else 1)
