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

from models import Base, User, Material, Session as SessionModel, Concept, Question, InversionParagraph, Gap, Patch
from pdf_processor import PDFProcessor
from concept_extractor import ConceptExtractor
from engagement_engine import EngagementEngine
from paragraph_inverter import ParagraphInverter

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
paragraph_inverter = ParagraphInverter()
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
    "https://frontend-hxdhdepcy-somtonweke1s-projects.vercel.app",
    "https://*.vercel.app",
    "https://*.vercel.com",
])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check"""
    openai_configured = bool(os.getenv("OPENAI_API_KEY"))
    return {
        "status": "online",
        "service": "Mastery Machine",
        "version": "1.0.0",
        "openai_configured": openai_configured
    }


@app.post("/api/demo/create")
async def create_demo_material(db: Session = Depends(get_db)):
    """Create demo material with sample concepts for testing"""
    # Get or create demo user
    user = db.query(User).filter(User.email == "demo@masterymachine.com").first()
    if not user:
        user = User(email="demo@masterymachine.com")
        db.add(user)
        db.commit()
        db.refresh(user)

    # Create demo material
    material_id = uuid.uuid4()
    material = Material(
        id=material_id,
        user_id=user.id,
        filename="Demo Material - Python Basics.pdf",
        file_path="demo.pdf",
        total_pages=3,
        estimated_time_minutes=10,
        processing_status='ready'
    )
    db.add(material)

    # Create sample concepts
    concepts_data = [
        {
            "name": "Python Variables",
            "type": "concept",
            "full_name": "Variable Assignment in Python",
            "definition": "Variables are containers for storing data values. In Python, you create a variable by assigning a value to a name.",
            "complexity": 2
        },
        {
            "name": "For Loops",
            "type": "concept",
            "full_name": "For Loop Iteration",
            "definition": "A for loop is used for iterating over a sequence (list, tuple, string, or range).",
            "complexity": 3
        },
        {
            "name": "Functions",
            "type": "concept",
            "full_name": "Function Definition and Calling",
            "definition": "A function is a block of reusable code that performs a specific task. Defined with 'def' keyword.",
            "complexity": 4
        }
    ]

    for concept_data in concepts_data:
        concept = Concept(
            material_id=material_id,
            name=concept_data["name"],
            type=concept_data["type"],
            full_name=concept_data["full_name"],
            definition=concept_data["definition"],
            context="Python programming basics",
            complexity=concept_data["complexity"],
            domain="programming"
        )
        db.add(concept)
        db.commit()
        db.refresh(concept)

        # Add sample questions for each concept
        questions = [
            {
                "mode": "RAPID_FIRE",
                "question": f"What is {concept_data['name']}?",
                "answer": concept_data["definition"][:50]
            },
            {
                "mode": "GUIDED_SOLVE",
                "question": f"Explain how {concept_data['name']} works in Python",
                "answer": concept_data["definition"]
            }
        ]

        for q_data in questions:
            question = Question(
                concept_id=concept.id,
                mode=q_data["mode"],
                question_text=q_data["question"],
                answer_text=q_data["answer"],
                difficulty=concept_data["complexity"]
            )
            db.add(question)

    db.commit()

    return {
        "material_id": str(material_id),
        "user_id": str(user.id),
        "filename": material.filename,
        "total_concepts": len(concepts_data),
        "message": "Demo material created! You can now start a learning session."
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
    # Use /tmp on production (Render) or local uploads directory
    if os.getenv("RENDER"):
        upload_dir = "/tmp/uploads"
    else:
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

        print(f"Extracting PDF from: {file_path}")
        pdf_data = pdf_processor.extract(file_path)
        material.total_pages = pdf_data['total_pages']
        material.estimated_time_minutes = pdf_data['estimated_time_minutes']
        print(f"PDF extracted: {material.total_pages} pages, method: {pdf_data.get('extraction_method')}, quality: {pdf_data.get('text_quality')}")

        # Check text quality - reject if we can't read the PDF properly
        if pdf_data.get('text_quality') == 'poor':
            raise HTTPException(
                status_code=400,
                detail="Could not extract readable text from this PDF. This may be because:\n"
                       "1. The PDF uses custom fonts that can't be decoded\n"
                       "2. The PDF is an image/scan with poor quality\n"
                       "3. The PDF is encrypted or protected\n\n"
                       "Try uploading a different PDF or a text-based document."
            )

        # Extract concepts
        material.processing_status = 'extracting_concepts'
        db.commit()

        print(f"Extracting concepts...")
        concepts = await concept_extractor.extract_concepts(pdf_data, material.id, db)
        print(f"Extracted {len(concepts)} concepts")

        # Generate questions
        material.processing_status = 'generating_questions'
        db.commit()

        print(f"Generating questions...")
        await concept_extractor.generate_questions(concepts, db)
        print(f"Questions generated successfully")

        material.processing_status = 'ready'
        db.commit()

    except HTTPException:
        # Re-raise HTTP exceptions (like our quality check) as-is
        raise
    except Exception as e:
        print(f"ERROR during processing: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

        material.processing_status = 'error'
        material.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    return {
        "material_id": str(material_id),
        "user_id": user_id,
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
    # Auto-detect Render deployment
    render_external_url = os.getenv("RENDER_EXTERNAL_URL")
    if render_external_url:
        backend_url = render_external_url
    else:
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
        if not question_data:
            await websocket.send_json({
                "type": "error",
                "message": "No concepts found for this material. Please upload a valid PDF with content."
            })
            await websocket.close()
            return
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
                if not question_data:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No more questions available. Please upload a longer document."
                    })
                    await websocket.close()
                    break
                await websocket.send_json(question_data)

            elif data["type"] == "skip":
                result = await engine.process_skip()
                await websocket.send_json(result)

                question_data = await engine.get_next_question()
                if not question_data:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No more questions available."
                    })
                    await websocket.close()
                    break
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
    except Exception as e:
        print(f"WebSocket error for session {session_id}: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Server error: {str(e)}"
            })
            await websocket.close()
        except:
            pass

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


# ============================================================================
# PARAGRAPH INVERSION ENDPOINTS
# ============================================================================

@app.post("/api/inversion/process/{material_id}")
async def process_inversion(
    material_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Process a material for paragraph inversion.
    Extracts paragraphs and creates inversions for each.
    """
    material = db.query(Material).filter(Material.id == uuid.UUID(material_id)).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # Extract PDF content
        pdf_data = pdf_processor.extract(material.file_path)

        # Get all paragraphs
        paragraphs = []
        for page_idx, page in enumerate(pdf_data['pages']):
            for segment in page['segments']:
                if segment['type'] == 'paragraph':
                    paragraphs.append({
                        'text': segment['text'],
                        'page_number': page_idx + 1
                    })

        # Batch invert paragraphs
        inverted_results = paragraph_inverter.batch_invert([p['text'] for p in paragraphs])

        # Store in database
        inversion_records = []
        for idx, result in enumerate(inverted_results):
            inversion = InversionParagraph(
                material_id=material.id,
                user_id=user.id,
                paragraph_number=idx,
                page_number=paragraphs[idx]['page_number'],
                original_text=result['original'],
                inverted_text=result['inverted']
            )
            db.add(inversion)
            db.commit()
            db.refresh(inversion)

            inversion_records.append({
                'id': str(inversion.id),
                'paragraph_number': idx,
                'page_number': paragraphs[idx]['page_number'],
                'original': result['original'],
                'inverted': result['inverted']
            })

        return {
            'material_id': str(material_id),
            'total_paragraphs': len(inversion_records),
            'inversions': inversion_records
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inversion processing failed: {str(e)}")


@app.get("/api/inversion/{material_id}/paragraphs")
async def get_inversions(
    material_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get all paragraph inversions for a material"""
    inversions = db.query(InversionParagraph).filter(
        InversionParagraph.material_id == uuid.UUID(material_id),
        InversionParagraph.user_id == uuid.UUID(user_id)
    ).order_by(InversionParagraph.paragraph_number).all()

    return {
        'material_id': material_id,
        'total_paragraphs': len(inversions),
        'inversions': [
            {
                'id': str(inv.id),
                'paragraph_number': inv.paragraph_number,
                'page_number': inv.page_number,
                'original': inv.original_text,
                'inverted': inv.inverted_text,
                'gaps_identified': inv.gaps_identified,
                'patch_created': inv.patch_created,
                'gap_count': len(inv.gaps),
                'patch_count': len(inv.patches)
            }
            for inv in inversions
        ]
    }


class GapIdentifyRequest(BaseModel):
    inversion_id: str


@app.post("/api/inversion/identify-gaps")
async def identify_gaps(
    request: GapIdentifyRequest,
    db: Session = Depends(get_db)
):
    """Identify logical gaps between original and inverted paragraph"""
    inversion = db.query(InversionParagraph).filter(
        InversionParagraph.id == uuid.UUID(request.inversion_id)
    ).first()

    if not inversion:
        raise HTTPException(status_code=404, detail="Inversion not found")

    try:
        # Identify gaps
        gaps = paragraph_inverter.identify_gaps(
            inversion.original_text,
            inversion.inverted_text
        )

        # Store gaps in database
        gap_records = []
        for gap_data in gaps:
            gap = Gap(
                inversion_paragraph_id=inversion.id,
                gap_type=gap_data['type'],
                description=gap_data['description'],
                location=gap_data.get('location', 'both')
            )
            db.add(gap)
            db.commit()
            db.refresh(gap)

            gap_records.append({
                'id': str(gap.id),
                'type': gap.gap_type,
                'description': gap.description,
                'location': gap.location
            })

        # Update inversion status
        inversion.gaps_identified = True
        db.commit()

        return {
            'inversion_id': str(inversion.id),
            'gaps': gap_records,
            'total_gaps': len(gap_records)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gap identification failed: {str(e)}")


class PatchCreateRequest(BaseModel):
    inversion_id: str
    patch_name: str
    patch_description: str
    patch_type: str
    creativity_score: Optional[int] = None
    addresses_gaps: Optional[list] = None


@app.post("/api/inversion/create-patch")
async def create_patch(
    request: PatchCreateRequest,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Create a patch that reconciles original and inverted paragraphs"""
    inversion = db.query(InversionParagraph).filter(
        InversionParagraph.id == uuid.UUID(request.inversion_id)
    ).first()

    if not inversion:
        raise HTTPException(status_code=404, detail="Inversion not found")

    # Create patch
    patch = Patch(
        inversion_paragraph_id=inversion.id,
        user_id=uuid.UUID(user_id),
        patch_name=request.patch_name,
        patch_description=request.patch_description,
        patch_type=request.patch_type,
        creativity_score=request.creativity_score,
        addresses_gaps=request.addresses_gaps or []
    )
    db.add(patch)

    # Update inversion status
    inversion.patch_created = True
    db.commit()
    db.refresh(patch)

    return {
        'patch_id': str(patch.id),
        'inversion_id': str(inversion.id),
        'patch_name': patch.patch_name,
        'created_at': patch.created_at.isoformat()
    }


@app.get("/api/inversion/{inversion_id}/gaps")
async def get_gaps(inversion_id: str, db: Session = Depends(get_db)):
    """Get all gaps for a specific inversion paragraph"""
    gaps = db.query(Gap).filter(
        Gap.inversion_paragraph_id == uuid.UUID(inversion_id)
    ).all()

    return {
        'inversion_id': inversion_id,
        'gaps': [
            {
                'id': str(gap.id),
                'type': gap.gap_type,
                'description': gap.description,
                'location': gap.location,
                'resolved': gap.resolved
            }
            for gap in gaps
        ]
    }


@app.get("/api/inversion/{inversion_id}/patches")
async def get_patches(inversion_id: str, db: Session = Depends(get_db)):
    """Get all patches for a specific inversion paragraph"""
    patches = db.query(Patch).filter(
        Patch.inversion_paragraph_id == uuid.UUID(inversion_id)
    ).all()

    return {
        'inversion_id': inversion_id,
        'patches': [
            {
                'id': str(patch.id),
                'patch_name': patch.patch_name,
                'patch_description': patch.patch_description,
                'patch_type': patch.patch_type,
                'creativity_score': patch.creativity_score,
                'addresses_gaps': patch.addresses_gaps,
                'created_at': patch.created_at.isoformat()
            }
            for patch in patches
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
