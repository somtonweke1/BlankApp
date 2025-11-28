#!/bin/bash

echo "🚀 Mastery Machine - Final Deployment Steps"
echo ""
echo "This script will finish your deployment after Render is set up."
echo ""

# Get backend URL from user
echo "📋 Step 1: Get your Render backend URL"
echo "Go to: https://dashboard.render.com"
echo "Click on 'mastery-machine-backend' service"
echo "Copy the URL at the top (e.g., https://mastery-machine-backend.onrender.com)"
echo ""
read -p "Paste your backend URL here: " BACKEND_URL

# Remove trailing slash if present
BACKEND_URL=${BACKEND_URL%/}

# Convert http to https and create wss URL
BACKEND_URL=${BACKEND_URL/http:/https:}
WS_URL=${BACKEND_URL/https:/wss:}

echo ""
echo "✅ Backend URL: $BACKEND_URL"
echo "✅ WebSocket URL: $WS_URL"
echo ""

# Get database URL
echo "📋 Step 2: Get your database URL"
echo "In Render dashboard, click on 'mastery-machine-db'"
echo "Go to 'Connect' tab"
echo "Copy the 'External Database URL'"
echo ""
read -p "Paste your database URL here: " DATABASE_URL

echo ""
echo "🔄 Step 3: Initializing database schema..."
echo ""

# Initialize database
psql "$DATABASE_URL" < /Users/somtonweke/BlankApp/mastery-machine/database/schema.sql

if [ $? -eq 0 ]; then
    echo "✅ Database initialized successfully!"
else
    echo "❌ Database initialization failed. Make sure PostgreSQL client is installed."
    echo "Install with: brew install postgresql"
    exit 1
fi

echo ""
echo "🔄 Step 4: Updating Vercel environment variables..."
echo ""

cd /Users/somtonweke/BlankApp/mastery-machine/frontend

# Set environment variables in Vercel
echo "$BACKEND_URL" | vercel env add VITE_API_URL production
echo "$WS_URL" | vercel env add VITE_WS_URL production

echo ""
echo "🔄 Step 5: Redeploying frontend..."
echo ""

vercel --prod

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Your Mastery Machine is now LIVE! 🚀"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Frontend: https://frontend-k3f9wr4ar-somtonweke1s-projects.vercel.app"
echo "Backend:  $BACKEND_URL"
echo "Database: Connected ✅"
echo ""
echo "Test it now:"
echo "1. Visit your frontend URL"
echo "2. Upload a small PDF"
echo "3. Start learning!"
echo ""
echo "🎓 Happy learning! Your students will love this!"
echo ""
