#!/bin/bash

# Setup and Test Script for Healthix Patient Chat

echo "🏥 Setting up Healthix Patient Chat with File Attachments..."

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    echo "❌ Please run this script from the PatientDB root directory"
    exit 1
fi

echo "📦 Installing dependencies..."

# Install Python dependencies
cd backend
pip install -r ../requirements.txt

echo "🚀 Starting backend server..."

# Start the backend server in the background
python main.py &
BACKEND_PID=$!

echo "✅ Backend server started (PID: $BACKEND_PID)"
echo "🌐 Backend API available at: http://localhost:8000"
echo "📖 API Documentation at: http://localhost:8000/docs"

# Wait a moment for server to start
sleep 3

echo ""
echo "🎯 Testing endpoints..."

# Test the main endpoint
curl -s http://localhost:8000/ | python -m json.tool

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Available interfaces:"
echo "   • Standalone Chat: http://localhost:8000/chat"  
echo "   • React Component: frontend/index.html"
echo "   • API Docs: http://localhost:8000/docs"
echo ""
echo "📎 Supported file types for attachment:"
echo "   • Documents: PDF, JPG, PNG, TXT"
echo "   • Tabular: Excel (.xlsx, .xls), CSV, TSV, JSON"
echo ""
echo "💡 To stop the backend server: kill $BACKEND_PID"
echo ""
echo "🔧 Backend endpoints ready:"
echo "   • POST /api/documents/attach-to-chat (File upload)"
echo "   • POST /api/chat/message (Chat with context)"
echo "   • GET /api/documents/chat-attachments/{session_id} (Get attachments)"