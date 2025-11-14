"""
Mastery Machine - Main FastAPI Application
"""
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import uuid
from typing import Optional
import json
from pydantic import BaseModel

from models import Base, User, Material, Session as SessionModel
from pdf_processor import PDFProcessor
from concept_extractor import ConceptExtractor
from engagement_engine import EngagementEngine

load_dotenv()


# Pydantic models for request bodies
class UserCreate(BaseModel):
    email: str


# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/mastery_machine")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Global instances
pdf_processor = PDFProcessor()
concept_extractor = ConceptExtractor()
engagement_engines = {}  # Store active engagement engines by session_id


def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    print("🚀 Mastery Machine starting up...")
    yield
    print("👋 Mastery Machine shutting down...")


app = FastAPI(
    title="Mastery Machine API",
    description="Active learning tool that guarantees mastery through adaptive engagement",
    version="1.0.0",
    lifespan=lifespan
)

# CORS - Allow frontend from localhost and Vercel
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
# Add common Vercel patterns
ALLOWED_ORIGINS.extend([
    "https://*.vercel.app",
    "https://*.vercel.com",
])

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "service": "Mastery Machine",
        "version": "1.0.0"
    }


@app.post("/api/users")
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Create or get user"""
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        user = User(email=user_data.email)
        db.add(user)
        db.commit()
        db.refresh(user)

    return {
        "user_id": str(user.id),
        "email": user.email,
        "total_concepts_mastered": user.total_concepts_mastered,
        "total_session_time_minutes": user.total_session_time_minutes
    }


@app.post("/api/upload")
async def upload_material(
    file: UploadFile = File(...),
    user_id: str = None,
    db: Session = Depends(get_db)
):
    """
    Upload PDF material and start background processing
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Get or create user
    if not user_id:
        user = User(email=f"user_{uuid.uuid4()}@temp.com")
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = str(user.id)
    else:
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

    # Save file
    material_id = uuid.uuid4()
    upload_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, f"{material_id}.pdf")

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Create material record
    material = Material(
        id=material_id,
        user_id=uuid.UUID(user_id),
        filename=file.filename,
        file_path=file_path,
        processing_status='uploaded'
    )
    db.add(material)
    db.commit()

    # Start background processing
    try:
        # Extract PDF content
        material.processing_status = 'extracting'
        db.commit()

        pdf_data = pdf_processor.extract(file_path)
        material.total_pages = pdf_data['total_pages']
        material.estimated_time_minutes = pdf_data['estimated_time_minutes']

        # Extract concepts
        material.processing_status = 'extracting_concepts'
        db.commit()

        concepts = await concept_extractor.extract_concepts(pdf_data, material.id, db)

        # Generate questions
        material.processing_status = 'generating_questions'
        db.commit()

        await concept_extractor.generate_questions(concepts, db)

        material.processing_status = 'ready'
        db.commit()

    except Exception as e:
        material.processing_status = 'error'
        material.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    return {
        "material_id": str(material_id),
        "filename": file.filename,
        "status": "ready",
        "total_pages": material.total_pages,
        "estimated_time_minutes": material.estimated_time_minutes,
        "total_concepts": len(concepts)
    }


@app.get("/api/materials/{material_id}/status")
async def get_material_status(material_id: str, db: Session = Depends(get_db)):
    """Check material processing status"""
    material = db.query(Material).filter(Material.id == uuid.UUID(material_id)).first()

    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    # Count concepts
    from models import Concept
    concept_count = db.query(Concept).filter(Concept.material_id == material.id).count()

    return {
        "material_id": str(material.id),
        "filename": material.filename,
        "status": material.processing_status,
        "total_pages": material.total_pages,
        "estimated_time_minutes": material.estimated_time_minutes,
        "total_concepts": concept_count,
        "error_message": material.error_message
    }


@app.post("/api/sessions/start/{material_id}")
async def start_session(
    material_id: str,
    user_id: str,
    goal: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Start a learning session"""
    material = db.query(Material).filter(Material.id == uuid.UUID(material_id)).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    if material.processing_status != 'ready':
        raise HTTPException(status_code=400, detail=f"Material not ready: {material.processing_status}")

    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create session
    session = SessionModel(
        user_id=user.id,
        material_id=material.id,
        goal=goal
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Initialize engagement engine
    engine = EngagementEngine(
        session_id=str(session.id),
        user_id=str(user.id),
        material_id=str(material.id),
        db=db
    )
    engagement_engines[str(session.id)] = engine

    # Construct WebSocket URL based on environment
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    ws_protocol = "wss" if backend_url.startswith("https") else "ws"
    ws_host = backend_url.replace("https://", "").replace("http://", "")

    return {
        "session_id": str(session.id),
        "material_id": str(material.id),
        "filename": material.filename,
        "total_concepts": engine.total_concepts,
        "websocket_url": f"{ws_protocol}://{ws_host}/ws/{session.id}"
    }


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time engagement

    Messages from client:
    - {"type": "answer", "answer": "...", "response_time_ms": 1234, "hesitation_ms": 100}
    - {"type": "skip"}
    - {"type": "peek"}
    - {"type": "hint"}

    Messages to client:
    - {"type": "question", "mode": "RAPID_FIRE", "question": "...", "data": {...}}
    - {"type": "feedback", "correct": true, "explanation": "..."}
    - {"type": "mode_switch", "new_mode": "COLLABORATIVE", "reason": "..."}
    - {"type": "mastery", "concept": "...", "mastered": true}
    - {"type": "session_complete", "stats": {...}}
    """
    await websocket.accept()

    engine = engagement_engines.get(session_id)
    if not engine:
        await websocket.send_json({
            "type": "error",
            "message": "Session not found"
        })
        await websocket.close()
        return

    try:
        # Send first question
        question_data = await engine.get_next_question()
        await websocket.send_json(question_data)

        # Main interaction loop
        while True:
            data = await websocket.receive_json()

            if data["type"] == "answer":
                # Process answer
                result = await engine.process_answer(
                    answer=data.get("answer"),
                    response_time_ms=data.get("response_time_ms"),
                    hesitation_ms=data.get("hesitation_ms", 0)
                )

                # Send feedback
                await websocket.send_json({
                    "type": "feedback",
                    "correct": result["correct"],
                    "explanation": result["explanation"],
                    "mastered": result.get("mastered", False),
                    "concept_name": result.get("concept_name")
                })

                # Check for mode switch
                if result.get("mode_switched"):
                    await websocket.send_json({
                        "type": "mode_switch",
                        "new_mode": result["new_mode"],
                        "reason": result["switch_reason"]
                    })

                # Check session completion
                if result.get("session_complete"):
                    await websocket.send_json({
                        "type": "session_complete",
                        "stats": result["stats"]
                    })
                    break

                # Send next question
                question_data = await engine.get_next_question()
                await websocket.send_json(question_data)

            elif data["type"] == "skip":
                result = await engine.process_skip()
                await websocket.send_json(result)

                question_data = await engine.get_next_question()
                await websocket.send_json(question_data)

            elif data["type"] == "peek":
                result = await engine.process_peek()
                await websocket.send_json(result)

            elif data["type"] == "hint":
                result = await engine.get_hint()
                await websocket.send_json(result)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {session_id}")
        # Save session state
        if engine:
            await engine.save_session_state()

    finally:
        if session_id in engagement_engines:
            del engagement_engines[session_id]


@app.get("/api/sessions/{session_id}/stats")
async def get_session_stats(session_id: str, db: Session = Depends(get_db)):
    """Get session statistics"""
    session = db.query(SessionModel).filter(SessionModel.id == uuid.UUID(session_id)).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": str(session.id),
        "duration_minutes": session.duration_minutes,
        "total_questions": session.total_questions,
        "total_correct": session.total_correct,
        "accuracy": session.total_correct / session.total_questions if session.total_questions > 0 else 0,
        "concepts_worked": session.concepts_worked,
        "concepts_mastered_this_session": session.concepts_mastered_this_session
    }


@app.get("/api/users/{user_id}/progress")
async def get_user_progress(user_id: str, db: Session = Depends(get_db)):
    """Get user overall progress"""
    from models import UserConceptState

    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get all concept states
    states = db.query(UserConceptState).filter(UserConceptState.user_id == user.id).all()

    mastered = [s for s in states if s.state == 'mastered']
    learning = [s for s in states if s.state == 'learning']
    struggling = [s for s in states if s.state == 'struggling']

    return {
        "user_id": str(user.id),
        "email": user.email,
        "total_concepts": len(states),
        "mastered": len(mastered),
        "learning": len(learning),
        "struggling": len(struggling),
        "total_session_time_minutes": user.total_session_time_minutes,
        "mastery_rate": len(mastered) / len(states) if states else 0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
