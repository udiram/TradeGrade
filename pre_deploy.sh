#!/bin/bash
set -e

echo "🚀 Starting pre-deploy setup..."

# Set Flask app
export FLASK_APP=run.py

# Initialize PyMySQL
echo "🔧 Setting up MySQL support..."
python -c "import pymysql; pymysql.install_as_MySQLdb()"

# Initialize Flask-Migrate if migrations folder doesn't exist
if [ ! -d "migrations" ]; then
    echo "📁 Initializing Flask-Migrate..."
    flask db init
fi

# Run migrations if they exist
if [ -d "migrations/versions" ] && [ "$(ls -A migrations/versions)" ]; then
    echo "📊 Running database migrations..."
    flask db upgrade
else
    echo "📊 No migrations found, creating tables directly..."
    python -c "
from app import create_app
from app.extensions import db
app = create_app()
with app.app_context():
    db.create_all()
    print('✅ Database tables created')
"
fi

echo "✅ Pre-deploy setup completed!"
