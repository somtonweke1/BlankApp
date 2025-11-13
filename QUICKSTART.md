# Quick Start Guide

Get Mastery Machine running in 5 minutes.

## Prerequisites Check

```bash
# Check Python version (need 3.10+)
python3 --version

# Check Node version (need 18+)
node --version

# Check PostgreSQL (need 14+)
psql --version
```

## 1. Database Setup (2 minutes)

```bash
# Create database
createdb mastery_machine

# Initialize schema
psql mastery_machine < database/schema.sql
```

## 2. Backend Setup (2 minutes)

```bash
cd backend

# Install dependencies
pip3 install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env with your OpenAI API key
nano .env  # or use your favorite editor
```

Required in `.env`:
```
DATABASE_URL=postgresql://localhost/mastery_machine
OPENAI_API_KEY=sk-your-key-here
```

## 3. Frontend Setup (1 minute)

```bash
cd ../frontend

# Install dependencies
npm install
```

## 4. Run (30 seconds)

Open two terminal windows:

**Terminal 1 - Backend:**
```bash
cd backend
python3 main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## 5. Use

1. Open http://localhost:5173
2. Enter email
3. Upload a PDF
4. Start learning!

## Troubleshooting

### Database connection error
```bash
# Make sure PostgreSQL is running
brew services start postgresql@14  # macOS
sudo systemctl start postgresql    # Linux
```

### OpenAI API error
- Check your API key in `backend/.env`
- Verify you have credits: https://platform.openai.com/account/usage

### Port already in use
- Backend (8000): `lsof -ti:8000 | xargs kill`
- Frontend (5173): `lsof -ti:5173 | xargs kill`

### PDF processing fails
Make sure these are installed:
```bash
# macOS
brew install tesseract poppler

# Ubuntu
sudo apt install tesseract-ocr poppler-utils
```

## What It Does

1. **Extracts concepts** from your PDF using AI
2. **Generates questions** across 12 different modes
3. **Adapts to you** in real-time:
   - Detects anxiety → easier questions
   - Detects mastery → validation questions
   - Tracks 5 criteria continuously
4. **Guarantees mastery**:
   - 99% accuracy
   - 10 consecutive perfect
   - Fast recall
   - Works across formats
   - 95% retention predicted

## Example Flow

```
Upload "Calculus Textbook.pdf" (50 pages)
  ↓
System extracts 120 concepts
  ↓
Start session
  ↓
RAPID_FIRE: "What is the derivative of x²?"
You: "2x" ✓
  ↓
EXPLAIN_BACK: "Explain the chain rule"
You: [explanation] ✓
  ↓
MASTERY_VALIDATION: [final test]
  ↓
MASTERY ACHIEVED for "Chain Rule"
  ↓
Continue until all 120 concepts mastered
```

## Performance

- PDF processing: 1-2 min per 50 pages
- Concept extraction: 2-3 min per 50 pages
- Learning: 2-5 min per concept (avg 3 min)
- Full textbook (300 pages, 600 concepts): 30-50 hours total learning time

## Need Help?

Check the full README.md for detailed documentation.
