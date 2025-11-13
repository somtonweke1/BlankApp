# Deploy to Render (Easiest Option!) 🚀

Render is **easier than Railway** and perfect for this project:
- ✅ **No credit card required** for free tier
- ✅ Free PostgreSQL database included
- ✅ Auto-deploys from GitHub
- ✅ Takes 5 minutes!

---

## Step-by-Step Deployment

### 1. Sign Up for Render

1. Go to https://render.com
2. Click "Get Started"
3. Sign up with your **GitHub account** (easiest!)
4. Authorize Render to access your GitHub

---

### 2. Create New Blueprint (Automatic Deployment)

1. Once logged in, click **"New +"** → **"Blueprint"**

2. Connect your repository:
   - Select **"somtonweke1/BlankApp"**
   - Click "Connect"

3. Render will **automatically detect** the `render.yaml` file and configure everything!

4. You'll see:
   - ✅ Web Service: `mastery-machine-backend`
   - ✅ PostgreSQL Database: `mastery-machine-db`
   - ✅ Auto-linked environment variables

5. Click **"Apply"**

---

### 3. Set OpenAI API Key

1. After deployment starts, go to **Dashboard**

2. Click on **"mastery-machine-backend"** service

3. Go to **"Environment"** tab

4. Find `OPENAI_API_KEY` and click **"Edit"**

5. Paste your OpenAI API key (the one from your .env file)

6. Click **"Save Changes"**

The backend will automatically redeploy with the new environment variable.

---

### 4. Get Your Backend URL

1. In the **mastery-machine-backend** service dashboard

2. Look for the URL at the top (e.g., `https://mastery-machine-backend.onrender.com`)

3. **Copy this URL** - you'll need it for the next step!

4. Wait for the deployment to complete (green "Live" status)

---

### 5. Initialize Database

Once the database is live:

1. Go to **"mastery-machine-db"** in your Render dashboard

2. Scroll down to **"Connections"**

3. Copy the **"External Database URL"**

4. Run this command locally:
   ```bash
   psql "<paste-the-external-database-url-here>" < /Users/somtonweke/BlankApp/mastery-machine/database/schema.sql
   ```

   Example:
   ```bash
   psql "postgresql://mastery_user:xyz123@oregon-postgres.render.com/mastery_machine" < /Users/somtonweke/BlankApp/mastery-machine/database/schema.sql
   ```

---

### 6. Update Vercel Frontend

Now that backend is deployed, update your frontend to use it:

```bash
cd /Users/somtonweke/BlankApp/mastery-machine/frontend

# Set API URL
vercel env add VITE_API_URL production
# When prompted, enter: https://your-backend-url.onrender.com

# Set WebSocket URL
vercel env add VITE_WS_URL production
# When prompted, enter: wss://your-backend-url.onrender.com

# Redeploy frontend
vercel --prod
```

---

### 7. Test Your App! 🎉

1. Go to your Vercel frontend URL:
   https://frontend-k3f9wr4ar-somtonweke1s-projects.vercel.app

2. Enter your email

3. Upload a small PDF (2-3 pages for testing)

4. Watch it process and extract concepts!

5. Start learning session

6. Answer questions and see real-time mastery tracking!

---

## Troubleshooting

### Backend Build Fails
- Check logs in Render dashboard
- Most common issue: Python version
- Fix: Render uses Python 3.10 by default (which we configured)

### Database Connection Error
- Make sure you ran the schema.sql initialization
- Check that DATABASE_URL is set correctly (should be automatic)

### Frontend Can't Connect
- Verify VITE_API_URL and VITE_WS_URL are set in Vercel
- Make sure backend shows "Live" status in Render
- Check CORS settings allow your Vercel domain

### PDF Upload Fails
- Check Render logs for errors
- Verify OPENAI_API_KEY is set correctly
- Free tier has 512MB memory limit - use small PDFs for testing

---

## Free Tier Limits

**Render Free Tier:**
- 512 MB RAM
- Spins down after 15 min of inactivity
- Spins up automatically when accessed (takes ~30 seconds)
- PostgreSQL: 90 days retention, 1GB storage

**Perfect for:**
- ✅ Testing and development
- ✅ Small projects
- ✅ Personal use
- ✅ Portfolios

**Upgrade needed for:**
- ❌ Production with lots of users
- ❌ Instant response time requirement
- ❌ Large PDF processing (100+ pages)

---

## Cost Comparison

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| Render Backend | FREE | $7/month |
| Render Database | FREE (90 days) | $7/month |
| Vercel Frontend | FREE forever | FREE (unlimited) |
| OpenAI API | Pay per use | ~$0.01-0.10 per material |

**Total for testing: $0**
**Total for production: ~$15-20/month**

---

## Monitoring

### View Logs:
1. Go to Render dashboard
2. Click on service
3. Click "Logs" tab
4. See real-time logs

### View Metrics:
1. Click "Metrics" tab
2. See CPU, memory, bandwidth usage

### Database Metrics:
1. Go to database service
2. Click "Metrics"
3. See connection count, storage

---

## Auto-Deployment

Every time you push to GitHub:
1. Render automatically detects changes
2. Builds and deploys new version
3. Zero-downtime deployment
4. Rollback available if needed

To deploy a change:
```bash
git add .
git commit -m "Your changes"
git push
# Render auto-deploys!
```

---

## Alternative: Manual Service Creation

If Blueprint doesn't work, you can create services manually:

### Create Web Service:
1. Dashboard → New + → Web Service
2. Connect GitHub repo
3. Name: `mastery-machine-backend`
4. Root Directory: `backend`
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Create PostgreSQL:
1. Dashboard → New + → PostgreSQL
2. Name: `mastery-machine-db`
3. Database: `mastery_machine`
4. User: `mastery_user`

### Link them:
1. In web service → Environment
2. Add: `DATABASE_URL` = (internal connection string from database)

---

## Need Help?

- Render Docs: https://render.com/docs
- Render Community: https://community.render.com
- Check service logs for errors
- Contact me if stuck!

---

## Success Checklist

- [ ] Signed up for Render
- [ ] Connected GitHub repository
- [ ] Created Blueprint (auto-configured services)
- [ ] Set OPENAI_API_KEY environment variable
- [ ] Backend shows "Live" status
- [ ] Database is provisioned
- [ ] Ran schema.sql to initialize database
- [ ] Updated Vercel environment variables
- [ ] Redeployed frontend
- [ ] Tested PDF upload
- [ ] Tested learning session
- [ ] WebSocket connection working

---

**You're all set! Enjoy your AI-powered learning platform! 🎓🚀**
