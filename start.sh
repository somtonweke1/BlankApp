#!/bin/bash

# Mastery Machine Startup Script
# Runs both backend and frontend

echo "🚀 Starting Mastery Machine..."

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "❌ Error: backend/.env not found"
    echo "Please create it from backend/.env.example and add your OpenAI API key"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Start backend in background
echo "🔧 Starting backend (port 8000)..."
cd backend
python3 main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 2

# Start frontend in background
echo "🎨 Starting frontend (port 5173)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Mastery Machine is running!"
echo ""
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo '👋 Stopping Mastery Machine...'; kill $BACKEND_PID $FRONTEND_PID; exit 0" INT

# Keep script running
wait
