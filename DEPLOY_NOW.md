# Deploy Mastery Machine RIGHT NOW 🚀

Everything is ready to deploy! Here's what to do:

## Quick Option: Frontend Only to Vercel (2 minutes)

```bash
cd /Users/somtonweke/BlankApp/mastery-machine
./deploy-vercel.sh
```

This deploys the frontend to Vercel. You'll still need to deploy the backend separately.

---

## Full Production Deployment (15 minutes)

### 1. Push to GitHub (2 min)

```bash
cd /Users/somtonweke/BlankApp/mastery-machine

# Initialize git
git init
git add .
git commit -m "Initial commit - Mastery Machine"

# Create repo on GitHub then:
git remote add origin https://github.com/YOUR_USERNAME/mastery-machine.git
git branch -M main
git push -u origin main
```

### 2. Deploy Backend to Railway (5 min)

1. Go to https://railway.app
2. Sign in with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select `mastery-machine`
5. Railway auto-detects Python and deploys
6. Add PostgreSQL: "New" → "Database" → "PostgreSQL"
7. Set environment variables:
   - Go to backend service → "Variables"
   - Add: `OPENAI_API_KEY=sk-your-key-here`
8. Configure deploy settings:
   - Go to "Settings"
   - Root Directory: `backend`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
9. Copy your backend URL from "Settings" → "Domains"

### 3. Initialize Database (2 min)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and link
railway login
railway link

# Initialize database
railway run psql $DATABASE_URL < database/schema.sql
```

### 4. Deploy Frontend to Vercel (3 min)

1. Go to https://vercel.com
2. Click "New Project"
3. Import your GitHub repo
4. Configure:
   - Framework: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. Add environment variables:
   ```
   VITE_API_URL=https://your-backend-url.railway.app
   VITE_WS_URL=wss://your-backend-url.railway.app
   ```
6. Deploy!

### 5. Done! 🎉

Your app is live at:
- Frontend: `https://your-app.vercel.app`
- Backend: `https://your-app.railway.app`

---

## Files Created for Deployment

✅ `frontend/vercel.json` - Vercel configuration
✅ `frontend/src/config.ts` - API/WebSocket URL configuration
✅ `backend/Procfile` - Process file for deployment
✅ `backend/railway.json` - Railway configuration
✅ `backend/render.yaml` - Render configuration (alternative)
✅ `DEPLOYMENT.md` - Complete deployment guide
✅ `DEPLOY_QUICK.md` - Quick Vercel CLI guide
✅ `deploy-vercel.sh` - Automated Vercel deploy script

---

## Environment Variables Needed

### Backend (Railway):
```
DATABASE_URL=<auto-set-by-railway>
OPENAI_API_KEY=sk-your-openai-key-here
```

### Frontend (Vercel):
```
VITE_API_URL=https://your-backend-url.railway.app
VITE_WS_URL=wss://your-backend-url.railway.app
```

---

## What Happens After Deployment

1. **User uploads PDF** → Stored in backend, processed by AI
2. **AI extracts concepts** → OpenAI GPT-4 analyzes content
3. **Questions generated** → Multiple modes created
4. **Learning session starts** → WebSocket connection established
5. **Adaptive engagement** → Real-time mode switching based on performance
6. **Mastery validation** → 5 criteria tracked continuously
7. **Certificate of mastery** → When all criteria met

---

## Cost

**Free Tier** (Perfect for testing):
- Railway: $5 free credit/month
- Vercel: Unlimited free
- **Total: $0**

**After Free Tier**:
- Railway: ~$5-10/month
- Vercel: Still free
- OpenAI: ~$0.002 per concept
- **Total: ~$5-20/month**

---

## Need Help?

- **Full deployment guide**: See `DEPLOYMENT.md`
- **Quick Vercel deploy**: See `DEPLOY_QUICK.md`
- **Railway docs**: https://docs.railway.app
- **Vercel docs**: https://vercel.com/docs

---

## Verification

After deployment, test:
1. ✅ Visit frontend URL
2. ✅ Enter email
3. ✅ Upload a small PDF
4. ✅ Wait for processing
5. ✅ Start learning session
6. ✅ Answer questions
7. ✅ See mastery progress

---

## Next Steps After Deployment

1. **Add custom domain** (optional)
2. **Set up monitoring** (Railway/Vercel dashboards)
3. **Configure alerts** for errors
4. **Set up backups** for database
5. **Enable analytics** in Vercel

---

## Deploy NOW! 🚀

```bash
# Option 1: Use automated script
./deploy-vercel.sh

# Option 2: Manual Vercel CLI
cd frontend && vercel --prod

# Option 3: Full GitHub → Railway + Vercel
# Follow steps 1-4 above
```

**Your students will thank you!** 🎓
