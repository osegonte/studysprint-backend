#!/bin/bash

# StudySprint 4.0 - Stage 1 Run Script
echo "🚀 Starting StudySprint 4.0 Backend - Stage 1"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup_stage1.sh first."
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
echo "🌟 Starting FastAPI server..."
echo "📊 Topics API: Ready"
echo "🔄 Sessions API: Ready with WebSocket"
echo "📄 PDFs API: Placeholder ready"
echo ""
echo "📖 API Docs: http://127.0.0.1:8000/api/docs"
echo "🏥 Health Check: http://127.0.0.1:8000/api/health"
echo "📊 Status: http://127.0.0.1:8000/api/status"
echo ""

python main.py