#!/bin/bash

# StudySprint 4.0 - Stage 2 Run Script
echo "🚀 Starting StudySprint 4.0 Backend - Stage 2"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup_stage2.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if database exists, if not initialize
if [ ! -f "data/studysprint.db" ]; then
    echo "🗄️ Initializing database..."
    python -c "
import asyncio
from database import init_database
asyncio.run(init_database())
print('✅ Database initialized')
"
fi

# Start the server
echo "🌟 Starting FastAPI server with PDF support..."
echo "📊 Topics API: Ready"
echo "🔄 Sessions API: Ready with WebSocket"
echo "📄 PDFs API: Ready with upload & processing"
echo "🔍 PDF Search: Operational"
echo "🎨 PDF Highlights: Supported"
echo ""
echo "📖 API Docs: http://127.0.0.1:8000/api/docs"
echo "🏥 Health Check: http://127.0.0.1:8000/api/health"
echo "📊 Status: http://127.0.0.1:8000/api/status"
echo ""
echo "📁 Upload Directory: $(pwd)/static/uploads/"
echo "🖼️ Thumbnail Directory: $(pwd)/static/thumbnails/"
echo ""

python main.py