# Vercel Deployment Guide

## Quick Deploy Commands

### Prerequisites
1. Install Vercel CLI: `npm install -g vercel`
2. Login to Vercel: `vercel login`
3. Have a PostgreSQL database ready (recommended: [Neon](https://neon.tech) or [Supabase](https://supabase.com))

---

## Deploy Backend (API)

### Step 1: Navigate to Backend
```bash
cd /Users/somtonweke/BlankApp/mastery-machine/backend
```

### Step 2: Deploy to Vercel
```bash
vercel --prod
```

Follow the prompts:
- **Set up and deploy?** Yes
- **Which scope?** Your account
- **Link to existing project?** No (first time) or Yes (subsequent)
- **Project name?** `mastery-machine-backend` (or your choice)
- **Directory?** `.` (current directory)
- **Override settings?** No

### Step 3: Set Environment Variables

After deployment, set these in Vercel Dashboard or via CLI:

```bash
vercel env add DATABASE_URL
# Paste your PostgreSQL connection string
# Example: postgresql://user:password@host:5432/database

vercel env add OPENAI_API_KEY
# Paste your OpenAI API key
# Example: sk-...

vercel env add ALLOWED_ORIGINS
# Set to your frontend URL (after frontend deployment)
# Example: https://your-frontend.vercel.app
```

Or set in Vercel Dashboard:
1. Go to https://vercel.com/dashboard
2. Select your backend project
3. Go to Settings → Environment Variables
4. Add:
   - `DATABASE_URL` = Your PostgreSQL connection string
   - `OPENAI_API_KEY` = Your OpenAI API key
   - `ALLOWED_ORIGINS` = Your frontend URL (or `*` for testing)

### Step 4: Redeploy After Setting Variables
```bash
vercel --prod
```

**Save the deployment URL** (e.g., `https://mastery-machine-backend.vercel.app`)

---

## Deploy Frontend

### Step 1: Update Backend URL

Edit `frontend/src/config.ts`:

```typescript
export const API_URL = import.meta.env.PROD
  ? 'https://YOUR-BACKEND-URL.vercel.app'  // Replace with your backend URL
  : 'http://localhost:8000'
```

Or check if it already uses environment variables:

```bash
cd /Users/somtonweke/BlankApp/mastery-machine/frontend
cat src/config.ts
```

### Step 2: Deploy Frontend
```bash
cd /Users/somtonweke/BlankApp/mastery-machine/frontend
vercel --prod
```

Follow the prompts:
- **Set up and deploy?** Yes
- **Which scope?** Your account
- **Link to existing project?** No (first time)
- **Project name?** `mastery-machine-frontend` (or your choice)
- **Directory?** `.` (current directory)
- **Override settings?** No

**Save the deployment URL** (e.g., `https://mastery-machine-frontend.vercel.app`)

### Step 3: Update ALLOWED_ORIGINS in Backend

Go back and update the backend's `ALLOWED_ORIGINS`:

```bash
vercel env add ALLOWED_ORIGINS production
# Paste your frontend URL: https://your-frontend.vercel.app
```

Then redeploy backend:
```bash
cd ../backend
vercel --prod
```

---

## Database Setup

### Option 1: Neon (Recommended - Free Tier)

1. Go to https://neon.tech
2. Sign up / Log in
3. Create new project
4. Copy connection string
5. Add to backend environment variables

### Option 2: Supabase

1. Go to https://supabase.com
2. Create new project
3. Go to Settings → Database
4. Copy connection string (use "Connection Pooling" mode)
5. Add to backend environment variables

### Option 3: Railway

1. Go to https://railway.app
2. Create PostgreSQL database
3. Copy connection string
4. Add to backend environment variables

### Run Migration

After deploying backend with database connected:

```bash
# SSH into Vercel (not possible directly)
# Instead, run migration locally pointing to production DB:

cd backend
# Temporarily set DATABASE_URL to production in .env
python migrate_db.py
# Restore .env to local DB
```

Or use a one-time script:

```bash
DATABASE_URL="postgresql://..." python migrate_db.py
```

---

## Environment Variables Checklist

### Backend (`mastery-machine-backend`)
- ✅ `DATABASE_URL` - PostgreSQL connection string
- ✅ `OPENAI_API_KEY` - OpenAI API key (for GPT-4 inversions)
- ✅ `ALLOWED_ORIGINS` - Frontend URL (e.g., `https://your-app.vercel.app`)

### Frontend (`mastery-machine-frontend`)
- ✅ Backend URL set in `src/config.ts` or environment variable

---

## Testing Your Deployment

### 1. Test Backend Health
```bash
curl https://YOUR-BACKEND-URL.vercel.app/
```

Expected response:
```json
{
  "status": "online",
  "service": "Mastery Machine",
  "version": "1.0.0",
  "openai_configured": true
}
```

### 2. Test Frontend
Visit: `https://YOUR-FRONTEND-URL.vercel.app`

You should see the Mastery Machine upload screen.

### 3. Full Integration Test
1. Upload a PDF
2. Select "Dialectical Learning Mode"
3. Click "Start Inversion Mode"
4. Verify inversions appear
5. Test gap identification
6. Test patch creation

---

## Troubleshooting

### Backend Issues

**"Module not found" errors:**
- Check `requirements.txt` is in backend directory
- Redeploy: `vercel --prod`

**Database connection failed:**
- Verify `DATABASE_URL` is set correctly
- Check database is publicly accessible
- Run migration: `DATABASE_URL="..." python migrate_db.py`

**CORS errors:**
- Update `ALLOWED_ORIGINS` to include frontend URL
- Redeploy backend after changing env vars

### Frontend Issues

**API requests fail:**
- Check `src/config.ts` has correct backend URL
- Verify backend is deployed and accessible
- Check browser console for errors

**Build fails:**
- Run `npm install` locally first
- Check for TypeScript errors: `npm run build`
- Fix errors and redeploy

### OpenAI Issues

**Inversions are poor quality:**
- Verify `OPENAI_API_KEY` is set
- Check you have GPT-4 API access
- System falls back to basic inversion without API key

---

## Deployment URLs

After deployment, you'll have:

**Frontend**: `https://mastery-machine-frontend-<random>.vercel.app`
**Backend**: `https://mastery-machine-backend-<random>.vercel.app`

You can customize these in Vercel Dashboard → Project Settings → Domains

---

## Custom Domain (Optional)

### Frontend
1. Go to Vercel Dashboard → Frontend Project → Settings → Domains
2. Add your domain (e.g., `mastermachine.com`)
3. Update DNS records as instructed
4. Update backend `ALLOWED_ORIGINS`

### Backend
1. Go to Vercel Dashboard → Backend Project → Settings → Domains
2. Add your API domain (e.g., `api.mastermachine.com`)
3. Update DNS records
4. Update frontend `config.ts` with new backend URL

---

## Cost Estimates

### Vercel (Free Tier)
- Frontend: Free (100GB bandwidth)
- Backend: Free (100GB bandwidth, 100 hours serverless execution)

### Database
- Neon: Free tier (0.5GB storage)
- Supabase: Free tier (500MB storage, 2GB transfer)

### OpenAI API
- GPT-4: ~$0.03/1K input tokens, ~$0.06/1K output tokens
- 100-paragraph document: ~$1-2 for full inversion + gap analysis
- Consider GPT-3.5-turbo for cost savings (~10x cheaper)

---

## Monitoring

### View Logs

**Backend:**
```bash
cd backend
vercel logs https://YOUR-BACKEND-URL.vercel.app
```

**Frontend:**
```bash
cd frontend
vercel logs https://YOUR-FRONTEND-URL.vercel.app
```

### Analytics
- Vercel Dashboard → Project → Analytics
- View traffic, performance, errors

---

## Updating After Deployment

### Backend Changes
```bash
cd backend
# Make your changes
vercel --prod
```

### Frontend Changes
```bash
cd frontend
# Make your changes
vercel --prod
```

---

## One-Command Deployment Script

Create `deploy.sh` in project root:

```bash
#!/bin/bash
echo "🚀 Deploying Mastery Machine..."

echo "📦 Deploying Backend..."
cd backend
vercel --prod --yes
BACKEND_URL=$(vercel inspect --prod | grep -o 'https://[^"]*')
echo "✅ Backend deployed: $BACKEND_URL"

echo "📦 Deploying Frontend..."
cd ../frontend
vercel --prod --yes
FRONTEND_URL=$(vercel inspect --prod | grep -o 'https://[^"]*')
echo "✅ Frontend deployed: $FRONTEND_URL"

echo ""
echo "🎉 Deployment Complete!"
echo "Frontend: $FRONTEND_URL"
echo "Backend: $BACKEND_URL"
echo ""
echo "⚠️  Don't forget to:"
echo "1. Update ALLOWED_ORIGINS in backend to: $FRONTEND_URL"
echo "2. Update API_URL in frontend config to: $BACKEND_URL"
echo "3. Redeploy after making these changes"
```

Make executable and run:
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## Success Checklist

- [ ] Backend deployed to Vercel
- [ ] Frontend deployed to Vercel
- [ ] Database connected (PostgreSQL)
- [ ] Environment variables set
- [ ] Migration run on production database
- [ ] CORS configured (frontend URL in backend ALLOWED_ORIGINS)
- [ ] Frontend pointing to backend URL
- [ ] OpenAI API key configured
- [ ] Test: Upload PDF works
- [ ] Test: Question mode works
- [ ] Test: Inversion mode works
- [ ] Test: Gap identification works
- [ ] Test: Patch creation works

---

## Support

If you encounter issues:
1. Check Vercel logs: `vercel logs [URL]`
2. Check browser console (F12)
3. Verify environment variables are set
4. Test backend health endpoint
5. Check database connectivity

Happy deploying! 🚀
