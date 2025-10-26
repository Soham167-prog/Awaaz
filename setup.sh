#!/bin/bash

# Awaaz Setup Script
echo "🚀 Setting up Awaaz - AI-Powered Pothole Detection System"
echo "=================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "🗄️ Running database migrations..."
python manage.py migrate

# Install Jupyter for notebook demo (optional)
echo "📓 Installing Jupyter Notebook for AI model demo..."
pip install jupyter

# Create superuser
echo "👤 Creating superuser account..."
echo "Please enter details for the admin account:"
python manage.py createsuperuser

echo ""
echo "🎉 Setup complete!"
echo "=================================================="
echo "To start the development server:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run server: python manage.py runserver"
echo "3. Open browser: http://127.0.0.1:8000/"
echo ""
echo "Admin panel: http://127.0.0.1:8000/admin/"
echo "Custom admin: http://127.0.0.1:8000/custom-admin/"
echo ""
echo "To run AI Model Demo Notebook:"
echo "jupyter notebook AI_Model_Demo.ipynb"
echo "=================================================="
