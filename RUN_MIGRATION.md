# Database Migration Instructions

## The Problem

Your backend is deployed and working, but the **inversion mode endpoints are failing** because the new database tables don't exist yet.

You need to run the migration to create:
- `inversion_paragraphs` table
- `gaps` table
- `patches` table

---

## Solution: Run Migration

### Option 1: From Your Local Machine (Easiest)

1. **Get your production database URL**
   - Go to your database provider (Neon, Supabase, Railway, etc.)
   - Copy the **connection string** (starts with `postgresql://...`)

2. **Run the migration**:
   ```bash
   cd /Users/somtonweke/BlankApp/mastery-machine/backend

   # Set the production database URL
   export DATABASE_URL="postgresql://user:password@host:5432/database"

   # Run migration
   python migrate_db.py

   # You should see:
   # ✓ Migration complete!
   # New tables created:
   #   - inversion_paragraphs
   #   - gaps
   #   - patches
   ```

3. **Done!** Try the inversion mode again.

---

### Option 2: Via Render Shell (If Available)

Some Render plans allow shell access:

1. Go to https://dashboard.render.com
2. Select your backend service
3. Click "Shell" tab (if available)
4. Run:
   ```bash
   python migrate_db.py
   ```

---

### Option 3: Manual SQL (Advanced)

If you can't run Python, execute this SQL directly:

```sql
-- Create inversion_paragraphs table
CREATE TABLE IF NOT EXISTS inversion_paragraphs (
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
CREATE TABLE IF NOT EXISTS gaps (
    id UUID PRIMARY KEY,
    inversion_paragraph_id UUID REFERENCES inversion_paragraphs(id) ON DELETE CASCADE,
    gap_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    location VARCHAR(50),
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create patches table
CREATE TABLE IF NOT EXISTS patches (
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

---

## How to Get Your Database URL

### If using Neon:
1. Go to https://console.neon.tech
2. Select your project
3. Click "Connection Details"
4. Copy the connection string

### If using Supabase:
1. Go to https://app.supabase.com
2. Select your project
3. Settings → Database → Connection String
4. Use the "Connection Pooling" string

### If using Railway:
1. Go to https://railway.app
2. Select your database service
3. Variables tab → Copy `DATABASE_URL`

### If using Render Postgres:
1. Go to https://dashboard.render.com
2. Select your database
3. Copy "External Database URL"

---

## Verify Migration Worked

After running migration, test the endpoint:

```bash
curl -X POST "https://mastery-machine-backend.onrender.com/api/inversion/process/test?user_id=test"
```

If migration worked:
- You'll get a 404 or 500 (because test IDs don't exist)
- **BUT** it won't be a database table error

If migration didn't work:
- You'll get an error about missing tables

---

## After Migration

1. Go back to: https://frontend-92bgsfo8g-somtonweke1s-projects.vercel.app
2. Upload a PDF
3. Select "Dialectical Learning Mode"
4. Click "Start Inversion Mode"
5. It should work now!

---

## Quick Test Script

```bash
#!/bin/bash
# Save as test-migration.sh

echo "Testing if migration is needed..."

# Try to query the table
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM inversion_paragraphs;" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Tables exist! Migration already done."
else
    echo "❌ Tables missing. Run migration:"
    echo "   python migrate_db.py"
fi
```

---

## Still Having Issues?

Check:
1. ✅ Database URL is correct (test with: `psql $DATABASE_URL -c "SELECT 1;"`)
2. ✅ You're in the `backend` directory when running `migrate_db.py`
3. ✅ Python can import sqlalchemy: `python -c "import sqlalchemy; print('OK')"`
4. ✅ The DATABASE_URL includes the database name at the end

Need help? Check the error message carefully - it will tell you what's wrong.
