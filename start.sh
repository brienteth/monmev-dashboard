#!/bin/bash

# Brick3 MEV Dashboard - Start Script
# ====================================

echo "🧱 Brick3 MEV Dashboard Launcher"
echo "================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt --quiet

# Check .env file
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found, creating from template..."
    cp .env.example .env
fi

echo ""
echo "Choose what to run:"
echo "  1) API Server only (port 8000)"
echo "  2) Dashboard only (port 8501)"
echo "  3) Both API + Dashboard"
echo "  4) aPriori Integration"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        echo "🚀 Starting API Server..."
        python api.py
        ;;
    2)
        echo "🚀 Starting Streamlit Dashboard..."
        streamlit run app.py
        ;;
    3)
        echo "🚀 Starting both services..."
        python api.py &
        API_PID=$!
        sleep 2
        streamlit run app.py &
        STREAMLIT_PID=$!
        
        echo ""
        echo "✅ Services running:"
        echo "   API: http://localhost:8000 (PID: $API_PID)"
        echo "   Dashboard: http://localhost:8501 (PID: $STREAMLIT_PID)"
        echo ""
        echo "Press Ctrl+C to stop all services"
        
        trap "kill $API_PID $STREAMLIT_PID 2>/dev/null; exit" INT
        wait
        ;;
    4)
        echo "🚀 Starting aPriori Integration..."
        python apriori_integration.py
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
