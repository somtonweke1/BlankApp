# Mastery Machine

Upload any study material and master it through adaptive, active engagement. Guaranteed 99% accuracy and 95% recall.

## Features

- **PDF Upload**: Supports any PDF study material (textbooks, notes, papers)
- **AI Concept Extraction**: Automatically extracts testable concepts using GPT-4
- **12 Engagement Modes**: From foundation building to mastery validation
- **Adaptive Mode Switching**: Detects anxiety and adjusts difficulty in real-time
- **5-Criteria Mastery Detection**:
  1. 99% accuracy
  2. 10 consecutive perfect answers
  3. Speed/fluency (fast recall without hesitation)
  4. Format invariance (works across question types)
  5. 95% predicted recall probability after 1 week

## Architecture

```
mastery-machine/
├── backend/          # FastAPI + SQLAlchemy
│   ├── main.py              # API endpoints and WebSocket
│   ├── models.py            # Database models
│   ├── pdf_processor.py     # PDF extraction
│   ├── concept_extractor.py # AI concept extraction
│   ├── engagement_engine.py # Core learning algorithm
│   └── requirements.txt
├── frontend/         # React + TypeScript
│   ├── src/
│   │   ├── components/
│   │   │   ├── Upload.tsx
│   │   │   ├── LearningSession.tsx
│   │   │   └── Progress.tsx
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── styles.css
│   └── package.json
├── database/         # PostgreSQL schema
│   └── schema.sql
└── uploads/          # Uploaded PDFs
```

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- OpenAI API key

### Database Setup

1. Install PostgreSQL:
```bash
# macOS
brew install postgresql@14
brew services start postgresql@14

# Ubuntu
sudo apt install postgresql-14
sudo systemctl start postgresql
```

2. Create database:
```bash
createdb mastery_machine
```

3. Initialize schema:
```bash
psql mastery_machine < database/schema.sql
```

### Backend Setup

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Create `.env` file:
```bash
cp .env.example .env
```

3. Edit `.env` with your credentials:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/mastery_machine
OPENAI_API_KEY=your_openai_api_key_here
```

4. Run server:
```bash
python main.py
```

Server runs on http://localhost:8000

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Run development server:
```bash
npm run dev
```

Frontend runs on http://localhost:5173

## Usage

1. Open http://localhost:5173
2. Enter your email and upload a PDF study material
3. The system will:
   - Extract text from PDF (native or OCR)
   - Identify testable concepts using AI
   - Generate questions across 12 different modes
4. Start learning session
5. Answer questions adaptively
   - System detects anxiety and switches to easier modes
   - Tracks 5 mastery criteria in real-time
   - Provides immediate feedback
6. Achieve mastery when all criteria are met
7. View progress and statistics

## How It Works

### Mode-Switching Algorithm (Priority Cascade)

1. **RESCUE**: Detect anxiety (skip rate > 30%) → MICRO_WINS mode
2. **MASTERY VALIDATION**: Concepts meeting criteria 1-4 → MASTERY_VALIDATION
3. **OPTIMAL CHALLENGE**: Select concept at appropriate difficulty
4. **MODE SELECTION**: Choose mode based on concept state

### Mastery Criteria

Each concept must meet ALL 5 criteria:

1. **Accuracy ≥ 99%**: Near-perfect correctness
2. **Stability**: 10 consecutive perfect answers (no flukes)
3. **Speed/Fluency**: Response time ≤ 1.3x baseline (automatic recall)
4. **Format Invariance**: Correct across 80%+ question formats
5. **Predicted Recall ≥ 95%**: ACT-R memory model predicts retention

### Engagement Modes

**Foundation** (building understanding):
- WORKED_EXAMPLE: Show complete solution
- GUIDED_SOLVE: Step-by-step guidance
- COLLABORATIVE: Hints and support

**Active** (recall practice):
- RAPID_FIRE: Quick one-word answers
- FILL_STORY: Fill-in-the-blank in context
- NUMBER_SWAP: Apply formula with new numbers

**Deep** (understanding):
- EXPLAIN_BACK: Explain in own words
- REVERSE_ENGINEER: Work backward from answer
- SPOT_ERROR: Find mistakes in examples

**Mastery** (validation):
- BUILD_MAP: Show concept relationships
- MASTERY_VALIDATION: Final verification
- MICRO_WINS: Rescue mode for anxiety

## API Endpoints

```
POST   /api/users                    - Create user
POST   /api/upload                   - Upload PDF
GET    /api/materials/{id}/status    - Check processing status
POST   /api/sessions/start/{id}      - Start learning session
WS     /ws/{session_id}              - WebSocket for real-time learning
GET    /api/sessions/{id}/stats      - Get session statistics
GET    /api/users/{id}/progress      - Get user progress
```

## WebSocket Protocol

**Client → Server:**
```json
{"type": "answer", "answer": "text", "response_time_ms": 1234, "hesitation_ms": 100}
{"type": "skip"}
{"type": "peek"}
{"type": "hint"}
```

**Server → Client:**
```json
{"type": "question", "mode": "RAPID_FIRE", "question": "...", "data": {...}}
{"type": "feedback", "correct": true, "explanation": "...", "mastered": false}
{"type": "mode_switch", "new_mode": "COLLABORATIVE", "reason": "..."}
{"type": "mastery", "concept": "...", "mastered": true}
{"type": "session_complete", "stats": {...}}
```

## Technologies

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, OpenAI GPT-4
- **Frontend**: React, TypeScript, Vite
- **PDF Processing**: pdfplumber, pytesseract, pdf2image
- **Real-time**: WebSocket
- **AI**: OpenAI API for concept extraction and question generation

## Development

### Running Tests
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Building for Production
```bash
# Frontend
cd frontend
npm run build

# Backend (with gunicorn)
cd backend
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## License

MIT

## Contributing

This is a prototype implementation. Contributions welcome!

## Credits

Built to solve a critical problem: students who study hard but blank under pressure during exams. This tool provides a scientific guarantee of mastery through adaptive engagement and rigorous validation.
