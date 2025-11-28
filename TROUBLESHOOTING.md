# Troubleshooting: "Failed to create inversions"

## What's Happening

Your application is deployed and working, but the **Inversion Mode is failing** with the error:

```
Failed to create inversions. Please try again.
```

## Root Cause

The backend code is deployed, but the **database migration hasn't been run yet**.

The new tables (`inversion_paragraphs`, `gaps`, `patches`) don't exist in your database, so when the backend tries to save inversions, it fails.

---

## The Fix (5 Minutes)

### Step 1: Get Your Database Connection String

You need your production PostgreSQL connection string. It looks like:
```
postgresql://username:password@host:5432/database_name
```

**Where to find it:**

<details>
<summary>If using Neon (neon.tech)</summary>

1. Go to https://console.neon.tech
2. Select your project
3. Click "Connection Details"
4. Copy the **connection string**
</details>

<details>
<summary>If using Supabase</summary>

1. Go to https://app.supabase.com
2. Select your project
3. Settings → Database
4. Copy "Connection string" (use **Connection Pooling** mode)
</details>

<details>
<summary>If using Railway</summary>

1. Go to https://railway.app
2. Select your database
3. Variables tab
4. Copy the `DATABASE_URL` value
</details>

<details>
<summary>If using Render Postgres</summary>

1. Go to https://dashboard.render.com
2. Select your PostgreSQL database
3. Copy "External Database URL"
</details>

### Step 2: Run the Migration

Open your terminal and run:

```bash
cd /Users/somtonweke/BlankApp/mastery-machine/backend

# Set your database URL (replace with your actual URL)
export DATABASE_URL="postgresql://user:password@host:5432/database"

# Run migration
python migrate_db.py
```

**Expected output:**
```
Connecting to database: postgresql://...
Creating tables...
✓ Migration complete!

New tables created:
  - inversion_paragraphs
  - gaps
  - patches

Your database is now ready for Dialectical Learning Mode!
```

### Step 3: Test It

1. Go back to: **https://frontend-13n7sh076-somtonweke1s-projects.vercel.app**
2. Upload a PDF
3. Select "Dialectical Learning Mode"
4. Click "Start Inversion Mode"
5. **It should work now!** ✅

---

## Alternative: Manual SQL (If Python doesn't work)

If you can't run Python, connect to your database directly and run this SQL:

```sql
-- Create inversion_paragraphs table
CREATE TABLE inversion_paragraphs (
    id UUID PRIMARY KEY,
    material_id UUID REFERENCES materials(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    paragraph_number INTEGER NOT NULL,
    page_number INTEGER,
    original_text TEXT NOT NULL,
    inverted_text TEXT NOT NULL,
    gaps_identified BOOLEAN DEFAULT FALSE,
    patch_created BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create gaps table
CREATE TABLE gaps (
    id UUID PRIMARY KEY,
    inversion_paragraph_id UUID REFERENCES inversion_paragraphs(id) ON DELETE CASCADE,
    gap_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    location VARCHAR(50),
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create patches table
CREATE TABLE patches (
    id UUID PRIMARY KEY,
    inversion_paragraph_id UUID REFERENCES inversion_paragraphs(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    patch_name VARCHAR(255),
    patch_description TEXT NOT NULL,
    patch_type VARCHAR(100),
    creativity_score INTEGER,
    addresses_gaps JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**How to run SQL:**
- Neon: Use the SQL Editor in web console
- Supabase: Use the SQL Editor in web console
- Railway: Use the "Query" tab
- psql command line: `psql $DATABASE_URL` then paste SQL

---

## Verify Tables Exist

After running migration, verify with:

```bash
psql "$DATABASE_URL" -c "\dt inversion*"
```

You should see:
```
            List of relations
 Schema |         Name          | Type  | Owner
--------+-----------------------+-------+-------
 public | inversion_paragraphs  | table | ...
```

---

## Other Possible Issues

### Issue: "Command not found: python"

Try: `python3 migrate_db.py`

### Issue: "No module named 'sqlalchemy'"

Install dependencies first:
```bash
pip install -r requirements.txt
# or
pip3 install -r requirements.txt
```

### Issue: "Connection refused"

- Check your DATABASE_URL is correct
- Make sure your database allows connections from your IP
- Some databases require whitelisting IPs - check provider settings

### Issue: Still failing after migration

1. Check backend logs in Render dashboard
2. Make sure OPENAI_API_KEY is set in Render environment variables
3. Try redeploying backend: `git push origin main`

---

## Quick Verification Commands

```bash
# Test database connection
psql "$DATABASE_URL" -c "SELECT version();"

# Check if tables exist
psql "$DATABASE_URL" -c "SELECT tablename FROM pg_tables WHERE tablename LIKE 'inversion%';"

# Count rows (should be 0 after fresh migration)
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM inversion_paragraphs;"
```

---

## After Migration Works

The improved error messages in the new frontend deployment will now show you:
- The exact HTTP status code
- The actual error message from the backend
- A hint if the backend is still deploying

So if you see a different error after migration, it will be more specific!

---

## Still Stuck?

If migration completes but you still get errors:

1. Check what the **actual error message** says now (updated frontend shows details)
2. Check Render logs: https://dashboard.render.com → Your service → Logs
3. Verify environment variables are set:
   - `DATABASE_URL`
   - `OPENAI_API_KEY`
   - `ALLOWED_ORIGINS`

---

## Summary

**Problem**: Database tables don't exist
**Solution**: Run `python migrate_db.py` with production DATABASE_URL
**Time**: 2-5 minutes
**Difficulty**: Easy

Once migration runs successfully, your Inversion Mode will work perfectly! 🎉
