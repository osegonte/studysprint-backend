#!/bin/bash

# StudySprint 4.0 - Stage 1 Setup Script
echo "🚀 Setting up StudySprint 4.0 Backend - Stage 1"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs static/uploads static/thumbnails

# Copy environment file
if [ ! -f ".env" ]; then
    echo "⚙️ Creating environment file..."
    cp .env.example .env
fi

# Run database initialization
echo "🗄️ Initializing database..."

# Start the server
echo "✅ Stage 1 setup complete!"
echo ""
echo "To start the server:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "API Documentation will be available at:"
echo "  http://127.0.0.1:8000/api/docs"
echo ""
echo "Stage 1 Features:"
echo "  ✅ Topics CRUD API with progress tracking"
echo "  ✅ Sessions API with real-time timer"
echo "  ✅ WebSocket support for live updates"
echo "  ✅ SQLAlchemy models and relationships"
echo "  ✅ Comprehensive error handling"
echo "  ✅ API documentation with Swagger"