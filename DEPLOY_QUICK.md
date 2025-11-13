# Quick Deploy to Vercel (Frontend Only)

Deploy just the frontend to Vercel in 2 minutes while keeping backend local.

## Prerequisites

- Node.js installed
- Vercel CLI: `npm install -g vercel`

## Steps

### 1. Login to Vercel

```bash
vercel login
```

### 2. Deploy Frontend

```bash
cd frontend
vercel
```

Follow prompts:
- Set up and deploy? **Y**
- Which scope? **Your account**
- Link to existing project? **N**
- Project name? **mastery-machine** (or whatever you want)
- Directory? **./** (current directory)
- Override settings? **N**

### 3. Set Environment Variables

```bash
# Set API URL to your local or deployed backend
vercel env add VITE_API_URL

# When prompted, enter:
# Development: http://localhost:8000
# Production: https://your-backend-url.railway.app
# Preview: http://localhost:8000

# Set WebSocket URL
vercel env add VITE_WS_URL

# When prompted, enter:
# Development: ws://localhost:8000
# Production: wss://your-backend-url.railway.app
# Preview: ws://localhost:8000
```

### 4. Redeploy with Environment Variables

```bash
vercel --prod
```

### 5. Done!

Your app is now live at the URL Vercel provides!

## Update Deployment

```bash
cd frontend
vercel --prod
```

## View Deployments

```bash
vercel ls
```

## View Logs

```bash
vercel logs
```

## Using with Local Backend

If you want to test the deployed frontend with your local backend:

1. Make sure your local backend is running: `cd backend && python3 main.py`
2. Set environment variables to use `http://localhost:8000`
3. You'll need to handle CORS - your local backend needs to allow your Vercel domain

## Full Production Deploy

For full production deployment (frontend + backend + database), see [DEPLOYMENT.md](./DEPLOYMENT.md)
