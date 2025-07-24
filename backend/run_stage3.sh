#!/bin/bash
# backend/run_stage3.sh

# StudySprint 4.0 - Stage 3 Run Script
echo "🚀 Starting StudySprint 4.0 Backend - Stage 3"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Install any new requirements
pip install -r requirements.txt

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
echo "🌟 Starting FastAPI server with Enhanced Sessions & Estimation..."
echo "📊 Topics API: Ready"
echo "🔄 Sessions API: Ready with WebSocket"
echo "📄 PDFs API: Ready with upload & processing"
echo "⏱️ Estimation API: Multi-level time estimation operational"
echo "📈 Analytics API: Advanced session analytics ready"
echo "🔍 PDF Search: Operational"
echo "🎨 PDF Highlights: Supported"
echo "🧠 AI Insights: Learning optimization available"
echo ""
echo "📖 API Docs: http://127.0.0.1:8000/api/docs"
echo "🏥 Health Check: http://127.0.0.1:8000/api/health"
echo "📊 Status: http://127.0.0.1:8000/api/status"
echo ""
echo "🆕 NEW Stage 3 Endpoints:"
echo "⏱️ PDF Estimation: http://127.0.0.1:8000/api/estimation/pdf/{id}"
echo "📈 Reading Analytics: http://127.0.0.1:8000/api/analytics/reading-speed"
echo "🎯 Bottleneck Analysis: http://127.0.0.1:8000/api/analytics/bottlenecks"
echo "💡 Optimization Tips: http://127.0.0.1:8000/api/analytics/optimization-suggestions"
echo ""

python main.py