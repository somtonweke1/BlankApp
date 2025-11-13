#!/bin/bash

# Mastery Machine - Vercel Deployment Script

echo "🚀 Deploying Mastery Machine Frontend to Vercel..."
echo ""

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Check if we're in the right directory
if [ ! -d "frontend" ]; then
    echo "❌ Error: frontend directory not found"
    echo "Please run this script from the mastery-machine root directory"
    exit 1
fi

echo "📦 Building frontend..."
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

echo ""
echo "🔑 Make sure you have set these environment variables in Vercel:"
echo ""
echo "VITE_API_URL=https://your-backend-url.railway.app"
echo "VITE_WS_URL=wss://your-backend-url.railway.app"
echo ""
echo "Set them now? (You can also do this later in Vercel dashboard)"
echo ""

# Deploy to Vercel
echo "Deploying to Vercel..."
vercel --prod

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Set environment variables in Vercel dashboard if you haven't already"
echo "2. Deploy backend to Railway or Render (see DEPLOYMENT.md)"
echo "3. Update CORS in backend to allow your Vercel domain"
echo ""
