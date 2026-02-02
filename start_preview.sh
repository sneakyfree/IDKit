#!/bin/bash
# IDKit Preview Start Script
# Starts both backend (FastAPI) and frontend (Next.js) for preview

set -e

BACKEND_PORT=5857
FRONTEND_PORT=5858
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Starting IDKit Preview..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if ports are available
if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port $BACKEND_PORT is in use. Killing existing process..."
    kill $(lsof -t -i:$BACKEND_PORT) 2>/dev/null || true
    sleep 1
fi

if lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port $FRONTEND_PORT is in use. Killing existing process..."
    kill $(lsof -t -i:$FRONTEND_PORT) 2>/dev/null || true
    sleep 1
fi

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# Start backend
echo "📦 Starting Backend (FastAPI) on port $BACKEND_PORT..."
cd "$SCRIPT_DIR/backend"

# Set environment variables
export DATABASE_URL="sqlite+aiosqlite:///./idkit_preview.db"
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET_KEY="preview-secret-key-do-not-use-in-production"
export ENVIRONMENT="development"

# Run migrations if needed
# python -m alembic upgrade head  # Uncomment when migrations are set up

# Start the backend server
python -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > "$SCRIPT_DIR/logs/backend.log" 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Wait for backend to start
sleep 3
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start. Check logs/backend.log"
    exit 1
fi

# Start frontend
echo "🎨 Starting Frontend (Next.js) on port $FRONTEND_PORT..."
cd "$SCRIPT_DIR/frontend"

# Set frontend API URL
export NEXT_PUBLIC_API_URL="http://localhost:$BACKEND_PORT"

# Install deps if needed
if [ ! -d "node_modules" ]; then
    echo "   Installing frontend dependencies..."
    npm install > "$SCRIPT_DIR/logs/npm-install.log" 2>&1
fi

# Start the frontend server
npm run dev -- -p $FRONTEND_PORT > "$SCRIPT_DIR/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

# Wait for frontend to start
sleep 5
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "❌ Frontend failed to start. Check logs/frontend.log"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ IDKit Preview is running!"
echo ""
echo "   🔧 Backend API:  http://localhost:$BACKEND_PORT"
echo "   📖 API Docs:     http://localhost:$BACKEND_PORT/docs"
echo "   🌐 Frontend:     http://localhost:$FRONTEND_PORT"
echo ""
echo "   📋 Logs:"
echo "      Backend:  logs/backend.log"
echo "      Frontend: logs/frontend.log"
echo ""
echo "   Press Ctrl+C to stop all services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Save PIDs for cleanup
echo "$BACKEND_PID" > "$SCRIPT_DIR/logs/backend.pid"
echo "$FRONTEND_PID" > "$SCRIPT_DIR/logs/frontend.pid"

# Wait and handle cleanup
cleanup() {
    echo ""
    echo "🛑 Stopping IDKit Preview..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    rm -f "$SCRIPT_DIR/logs/*.pid"
    echo "   Done."
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep script running
wait
