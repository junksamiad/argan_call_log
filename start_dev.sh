#!/bin/bash

echo "Starting Argan HR Email Management System - Development Mode"
echo "=========================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "WARNING: .env file not found!"
    echo "Please create a .env file with the following content:"
    echo ""
    echo "OPENAI_API_KEY=your-openai-api-key"
    echo "DATABASE_URL=sqlite:///argan_email.db  # For development"
    echo ""
    echo "Press any key to continue without .env file..."
    read -n 1
fi

# Initialize database
echo ""
echo "Initializing database..."
python -c "
import sys
sys.path.append('.')
from backend.utils.database import init_db
init_db()
print('Database initialized successfully!')
"

# Create first user if needed
echo ""
echo "Creating default admin user (if not exists)..."
python -c "
import sys
sys.path.append('.')
from backend.utils.database import SessionLocal
from backend.models.database import User
from backend.api.auth import get_password_hash

db = SessionLocal()
admin = db.query(User).filter_by(username='admin').first()
if not admin:
    admin = User(
        username='admin',
        email='admin@arganhrconsultancy.co.uk',
        full_name='System Administrator',
        role='admin',
        hashed_password=get_password_hash('admin123')
    )
    db.add(admin)
    db.commit()
    print('Admin user created: username=admin, password=admin123')
    print('IMPORTANT: Change this password immediately!')
else:
    print('Admin user already exists')
db.close()
"

# Start the API server
echo ""
echo "Starting API server on http://localhost:8000"
echo "API documentation available at http://localhost:8000/docs"
echo ""
echo "To start background email processing, run in another terminal:"
echo "  celery -A backend.services.celery_app worker --loglevel=info"
echo "  celery -A backend.services.celery_app beat --loglevel=info"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd backend/api
python main.py 