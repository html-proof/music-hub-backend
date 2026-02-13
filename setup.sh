#!/bin/bash
# ============================================================================
# Music Hub Backend - Quick Setup Script
# ============================================================================
set -e

echo "🎵 Music Hub Backend Setup"
echo "=========================="

# Check Python
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python --version 2>&1)
echo "✅ Found $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✅ Dependencies installed"

# Setup .env file
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env from .env.example"
    fi
else
    echo "✅ .env already exists"
fi

# Check Firebase credentials
if [ ! -f "firebase-service-account.json" ]; then
    echo ""
    echo "⚠️  Firebase service account not found!"
    echo "   1. Go to Firebase Console → Project Settings → Service Accounts"
    echo "   2. Click 'Generate New Private Key'"
    echo "   3. Save as: firebase-service-account.json"
    echo ""
fi

# Install yt-dlp system-wide (needed for audio extraction)
if ! command -v yt-dlp &> /dev/null; then
    echo "📦 Installing yt-dlp..."
    pip install yt-dlp -q
fi

echo ""
echo "🚀 Setup complete! Start the server with:"
echo "   python main.py"
echo ""
echo "   Or with uvicorn directly:"
echo "   uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "📖 API docs: http://localhost:8000/docs"
echo "❤️  Health:   http://localhost:8000/health"
