# Deployment Guide - Mastery Machine

Complete guide to deploy Mastery Machine to production.

## Architecture

- **Frontend**: Vercel (React + Vite)
- **Backend**: Railway or Render (FastAPI + WebSocket)
- **Database**: Railway PostgreSQL or Render PostgreSQL

## Prerequisites

1. GitHub account
2. Vercel account (free tier works)
3. Railway account OR Render account (free tier works)
4. OpenAI API key

---

## Step 1: Push Code to GitHub

```bash
cd /Users/somtonweke/BlankApp/mastery-machine

# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit - Mastery Machine"

# Create repo on GitHub and push
git remote add origin https://github.com/YOUR_USERNAME/mastery-machine.git
git branch -M main
git push -u origin main
```

---

## Step 2: Deploy Backend (Choose One)

### Option A: Railway (Recommended - Easiest)

1. **Go to Railway**: https://railway.app
2. **Click "Start a New Project"**
3. **Select "Deploy from GitHub repo"**
4. **Select your repository**
5. **Railway will auto-detect Python and deploy**

6. **Add PostgreSQL Database**:
   - Click "New" → "Database" → "PostgreSQL"
   - Railway will automatically provision database
   - DATABASE_URL will be auto-injected

7. **Set Environment Variables**:
   - Go to your backend service
   - Click "Variables" tab
   - Add:
     ```
     OPENAI_API_KEY=sk-your-key-here
     ```

8. **Configure Start Command**:
   - Go to "Settings" → "Deploy"
   - Root Directory: `backend`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

9. **Get Your Backend URL**:
   - Go to "Settings" → "Domains"
   - Copy the generated URL (e.g., `https://mastery-machine-backend.up.railway.app`)
   - **Save this URL - you'll need it for the frontend!**

10. **Initialize Database**:
```bash
# Connect to Railway PostgreSQL
railway login
railway link
railway run psql $DATABASE_URL < database/schema.sql
```

### Option B: Render

1. **Go to Render**: https://render.com
2. **Click "New +" → "Web Service"**
3. **Connect your GitHub repo**
4. **Configure**:
   - Name: `mastery-machine-backend`
   - Root Directory: `backend`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

5. **Add PostgreSQL Database**:
   - Click "New +" → "PostgreSQL"
   - Name: `mastery-machine-db`
   - Copy the "Internal Database URL"

6. **Set Environment Variables** (in web service):
   ```
   DATABASE_URL=<paste internal database URL>
   OPENAI_API_KEY=sk-your-key-here
   ```

7. **Get Your Backend URL**:
   - Copy the web service URL (e.g., `https://mastery-machine-backend.onrender.com`)
   - **Save this URL - you'll need it for the frontend!**

8. **Initialize Database**:
```bash
# Get connection string from Render dashboard
psql <render-database-url> < database/schema.sql
```

---

## Step 3: Deploy Frontend to Vercel

1. **Go to Vercel**: https://vercel.com
2. **Click "Add New" → "Project"**
3. **Import your GitHub repository**
4. **Configure Project**:
   - Framework Preset: `Vite`
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`

5. **Set Environment Variables**:
   - Click "Environment Variables"
   - Add:
     ```
     VITE_API_URL=https://your-backend-url.railway.app
     VITE_WS_URL=wss://your-backend-url.railway.app
     ```
   - **IMPORTANT**: Replace with YOUR actual backend URL from Step 2
   - **IMPORTANT**: Use `wss://` (not `ws://`) for WebSocket in production

6. **Deploy**:
   - Click "Deploy"
   - Wait for deployment to complete
   - Vercel will give you a URL like `https://mastery-machine.vercel.app`

7. **Test Your Deployment**:
   - Visit your Vercel URL
   - Upload a small PDF
   - Verify it processes and starts a learning session

---

## Step 4: Update CORS Settings (Backend)

After deploying frontend, update backend CORS to allow your Vercel domain:

Edit `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://your-app.vercel.app",  # Add your Vercel URL
        "https://*.vercel.app",  # Allow all Vercel preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Commit and push - your backend will auto-redeploy.

---

## Environment Variables Summary

### Backend (Railway/Render):
```
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-...
```

### Frontend (Vercel):
```
VITE_API_URL=https://your-backend-url.railway.app
VITE_WS_URL=wss://your-backend-url.railway.app
```

---

## Database Initialization

After deploying backend with database, initialize schema:

### Railway:
```bash
railway login
railway link
railway run psql $DATABASE_URL < database/schema.sql
```

### Render:
```bash
# Get connection string from dashboard
psql <your-render-db-url> < database/schema.sql
```

---

## Verification Checklist

- [ ] Backend is deployed and running
- [ ] Database is provisioned and schema is initialized
- [ ] Frontend is deployed to Vercel
- [ ] Environment variables are set correctly
- [ ] CORS is configured with frontend URL
- [ ] Can upload PDF successfully
- [ ] WebSocket connection works
- [ ] Learning session starts correctly

---

## Troubleshooting

### Backend Won't Start
- Check logs in Railway/Render dashboard
- Verify all dependencies in requirements.txt
- Ensure DATABASE_URL is set
- Check Python version (needs 3.10+)

### Frontend Can't Connect to Backend
- Check VITE_API_URL environment variable
- Verify CORS settings in backend
- Check backend is actually running
- Look at browser console for errors

### WebSocket Connection Fails
- Use `wss://` not `ws://` in production
- Check VITE_WS_URL environment variable
- Verify backend supports WebSocket (Railway and Render both do)
- Check browser console for connection errors

### Database Connection Failed
- Verify DATABASE_URL format
- Check database is actually provisioned
- Ensure schema.sql was run successfully
- Check database logs

### PDF Upload Fails
- Check backend logs
- Verify OpenAI API key is set
- Check file size limits (Railway: 100MB, Render Free: 35MB)
- Ensure uploads directory exists and is writable

---

## Cost Estimation

### Free Tier (Perfect for Testing):
- **Railway**: $5 free credit/month
  - ~500 hours of backend runtime
  - PostgreSQL database included
- **Vercel**: Unlimited hobby deployments
- **Total**: $0 (stays within free tier)

### Production (After Free Tier):
- **Railway**: ~$5-10/month (backend + database)
- **Vercel**: $0 (frontend stays free)
- **OpenAI API**: Pay per use (~$0.002 per concept extracted)
- **Total**: ~$5-20/month depending on usage

---

## Custom Domain (Optional)

### Vercel Frontend:
1. Go to Project → Settings → Domains
2. Add your domain
3. Configure DNS (Vercel provides instructions)

### Railway Backend:
1. Go to Service → Settings → Domains
2. Add custom domain
3. Configure DNS as instructed
4. Update VITE_API_URL and VITE_WS_URL in Vercel

---

## Continuous Deployment

Both platforms auto-deploy on git push:
- Push to `main` branch → auto-deploys to production
- Open PR → Vercel creates preview deployment
- Railway deploys all branches automatically

---

## Monitoring

### Railway:
- Logs: Service → Logs tab
- Metrics: Service → Metrics tab
- Database: Database → Metrics

### Render:
- Logs: Service → Logs
- Metrics: Service → Metrics

### Vercel:
- Analytics: Project → Analytics
- Logs: Deployment → Functions logs

---

## Scaling

When you need more resources:

### Railway:
- Automatically scales
- Pay for what you use
- Can set limits in Settings

### Render:
- Upgrade to paid plan for auto-scaling
- Free tier: 1 instance, sleeps after 15 min inactivity
- Paid: Auto-scale based on traffic

---

## Quick Deploy Commands

```bash
# Push to GitHub
git add .
git commit -m "Deploy to production"
git push origin main

# Both Vercel and Railway/Render will auto-deploy!
```

---

## Support

- Railway: https://docs.railway.app
- Render: https://render.com/docs
- Vercel: https://vercel.com/docs
- Issues: https://github.com/YOUR_USERNAME/mastery-machine/issues
