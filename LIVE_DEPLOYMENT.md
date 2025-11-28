# 🚀 Live Deployment - Mastery Machine with Dialectical Learning

## Your Live Application

### Frontend (Vercel)
**URL**: https://frontend-92bgsfo8g-somtonweke1s-projects.vercel.app

**Status**: ✅ Deployed and Live

**Features**:
- Material upload interface
- Mode selection (Question-based vs Dialectical Learning)
- InversionTable with side-by-side comparison
- Gap identification modals
- Patch creation interface
- Complete UI styling

### Backend (Render)
**URL**: https://mastery-machine-backend.onrender.com

**Status**: ✅ Deployed (Auto-deploying from GitHub)

**Features**:
- All original API endpoints (upload, sessions, progress)
- 7 new inversion endpoints
- Paragraph inversion with GPT-4
- Gap identification with AI
- Patch creation and storage
- Database persistence

---

## Testing Your Deployment

### Quick Health Check
```bash
# Test backend
curl https://mastery-machine-backend.onrender.com/

# Expected response:
# {"status":"online","service":"Mastery Machine","version":"1.0.0","openai_configured":true}
```

### Full Integration Test
1. Visit: https://frontend-92bgsfo8g-somtonweke1s-projects.vercel.app
2. Upload a PDF
3. Select **"Dialectical Learning (Inversion Mode)"**
4. Click "Start Inversion Mode"
5. Wait for processing (AI generates inversions)
6. Click "Identify Gaps" on any paragraph
7. Click "Create Patch" and write your reconciliation

---

## What's Deployed

### New Backend Files
- ✅ `paragraph_inverter.py` - Inversion engine with GPT-4
- ✅ `models.py` - Updated with InversionParagraph, Gap, Patch models
- ✅ `main.py` - 7 new API endpoints added
- ✅ `migrate_db.py` - Database migration script

### New Frontend Files
- ✅ `InversionTable.tsx` - Main table component
- ✅ `InversionMode.tsx` - Entry point component
- ✅ `App.tsx` - Mode selection integration
- ✅ `styles.css` - Complete inversion UI styling

### New API Endpoints
1. `POST /api/inversion/process/{material_id}` - Create inversions
2. `GET /api/inversion/{material_id}/paragraphs` - Get all inversions
3. `POST /api/inversion/identify-gaps` - Identify gaps
4. `POST /api/inversion/create-patch` - Create patch
5. `GET /api/inversion/{inversion_id}/gaps` - Get gaps
6. `GET /api/inversion/{inversion_id}/patches` - Get patches

---

## Database Migration Required

The backend has deployed, but you need to run the database migration to create the new tables.

### Option 1: Local Migration to Production DB

```bash
cd backend

# Set production database URL temporarily
export DATABASE_URL="your_production_postgres_url_here"

# Run migration
python migrate_db.py

# Unset or restore local DB URL
unset DATABASE_URL
```

### Option 2: SSH into Render (if available)

Check Render dashboard for SSH access to run:
```bash
python migrate_db.py
```

### What Gets Created
- `inversion_paragraphs` table
- `gaps` table
- `patches` table

**Important**: The inversion mode won't work until migration is run!

---

## Environment Variables Check

### Render Backend
Make sure these are set in Render Dashboard:

1. **DATABASE_URL** - PostgreSQL connection string
2. **OPENAI_API_KEY** - Your OpenAI API key (for GPT-4)
3. **ALLOWED_ORIGINS** - Should include:
   - `https://frontend-92bgsfo8g-somtonweke1s-projects.vercel.app`
   - Or just `*` for testing

### How to Set in Render
1. Go to https://dashboard.render.com
2. Select "mastery-machine-backend" service
3. Go to "Environment" tab
4. Add/Update variables
5. Click "Save Changes" (will auto-redeploy)

---

## Deployment Status

| Component | Platform | Status | URL |
|-----------|----------|--------|-----|
| Frontend | Vercel | ✅ Live | https://frontend-92bgsfo8g-somtonweke1s-projects.vercel.app |
| Backend | Render | ✅ Deploying | https://mastery-machine-backend.onrender.com |
| Database | (Your provider) | ⚠️ Migration needed | - |

---

## Next Steps

### 1. Check Backend Deployment
Visit Render dashboard to see if latest deployment is live:
- Go to https://dashboard.render.com
- Check "mastery-machine-backend"
- View deployment logs
- Should see "Running on..." message

### 2. Run Database Migration
Use Option 1 above to create new tables.

### 3. Test Full Workflow
1. Visit frontend URL
2. Upload a test PDF
3. Try both modes:
   - Question-Based Learning (existing feature)
   - Dialectical Learning (new feature)

### 4. Monitor Logs
```bash
# Render backend logs
# Visit: https://dashboard.render.com → Your Service → Logs

# Vercel frontend logs
vercel logs https://frontend-92bgsfo8g-somtonweke1s-projects.vercel.app
```

---

## Known Issues & Solutions

### Issue: "Failed to create inversions"
**Cause**: Database migration not run
**Solution**: Run `migrate_db.py` with production DATABASE_URL

### Issue: Backend takes forever to respond
**Cause**: Render free tier has cold starts
**Solution**: First request after inactivity takes ~30 seconds (normal)

### Issue: CORS errors in browser console
**Cause**: Frontend URL not in ALLOWED_ORIGINS
**Solution**: Add frontend URL to backend environment variables

### Issue: Inversions are low quality
**Cause**: OPENAI_API_KEY not set or invalid
**Solution**: Set valid API key in Render dashboard

---

## Cost Breakdown

### Current Setup
- **Vercel Frontend**: Free tier (100GB bandwidth)
- **Render Backend**: Free tier (750 hours/month)
- **Database**: Depends on your provider
- **OpenAI API**: Pay-per-use (~$1-2 per document)

### Estimated Monthly Cost
- Hosting: **$0** (using free tiers)
- Database: **$0-10** (depending on provider)
- OpenAI API: **Variable** (based on usage)

**Total**: **$0-20/month** for moderate usage

---

## Updating Your Deployment

All future updates:

1. **Make changes locally**
2. **Commit**: `git add -A && git commit -m "your message"`
3. **Push**: `git push origin main`
4. **Wait**:
   - Render auto-deploys backend (~2-3 min)
   - Vercel needs manual redeploy for frontend

### Redeploy Frontend After Changes
```bash
cd frontend
vercel --prod --yes
```

---

## Custom Domain (Optional)

### Add Custom Domain to Frontend
1. Vercel Dashboard → frontend project → Settings → Domains
2. Add your domain (e.g., `mastermachine.app`)
3. Update DNS records as shown
4. Update backend ALLOWED_ORIGINS

### Add Custom Domain to Backend
1. Render Dashboard → service → Settings
2. Add custom domain (e.g., `api.mastermachine.app`)
3. Update DNS records
4. Update frontend `config.ts` with new URL

---

## Support & Debugging

### View Backend Logs
- Render Dashboard → Service → Logs tab
- Or: Realtime logs via Render CLI

### View Frontend Logs
```bash
vercel logs https://frontend-92bgsfo8g-somtonweke1s-projects.vercel.app
```

### Test API Endpoints
```bash
# Health check
curl https://mastery-machine-backend.onrender.com/

# Test after upload (replace material_id and user_id)
curl https://mastery-machine-backend.onrender.com/api/inversion/MATERIAL_ID/paragraphs?user_id=USER_ID
```

---

## Success! 🎉

Your Mastery Machine with Dialectical Learning is now LIVE!

**Try it now**: https://frontend-92bgsfo8g-somtonweke1s-projects.vercel.app

**Don't forget to**:
1. ✅ Run database migration
2. ✅ Verify OPENAI_API_KEY is set
3. ✅ Check Render deployment completed
4. ✅ Test a full workflow
5. ✅ Share the link!

---

## Quick Reference

```bash
# Frontend URL
https://frontend-92bgsfo8g-somtonweke1s-projects.vercel.app

# Backend URL
https://mastery-machine-backend.onrender.com

# GitHub Repo
https://github.com/somtonweke1/BlankApp

# Redeploy Frontend
cd frontend && vercel --prod --yes

# Update Backend
git push origin main  # Auto-deploys on Render

# Run Migration
DATABASE_URL="..." python backend/migrate_db.py
```
