"""
Database models for Mastery Machine
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, ForeignKey, TIMESTAMP, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    total_concepts_mastered = Column(Integer, default=0)
    total_session_time_minutes = Column(Integer, default=0)

    # Relationships
    materials = relationship("Material", back_populates="user")
    sessions = relationship("Session", back_populates="user")
    concept_states = relationship("UserConceptState", back_populates="user")


class Material(Base):
    __tablename__ = 'materials'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    upload_date = Column(TIMESTAMP, server_default=func.now())
    total_pages = Column(Integer)
    processing_status = Column(String(50), default='uploaded')
    estimated_time_minutes = Column(Integer)
    error_message = Column(Text)

    # Relationships
    user = relationship("User", back_populates="materials")
    concepts = relationship("Concept", back_populates="material")


class Concept(Base):
    __tablename__ = 'concepts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    material_id = Column(UUID(as_uuid=True), ForeignKey('materials.id', ondelete='CASCADE'))
    name = Column(String(255), nullable=False)
    type = Column(String(50))
    full_name = Column(Text)
    definition = Column(Text)
    context = Column(Text)
    complexity = Column(Integer, default=1)
    domain = Column(String(100))
    formulas = Column(JSONB, default=list)
    examples = Column(JSONB, default=list)
    related_concepts = Column(JSONB, default=list)
    dependencies = Column(JSONB, default=list)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    material = relationship("Material", back_populates="concepts")
    questions = relationship("Question", back_populates="concept")
    user_states = relationship("UserConceptState", back_populates="concept")


class Question(Base):
    __tablename__ = 'questions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concept_id = Column(UUID(as_uuid=True), ForeignKey('concepts.id', ondelete='CASCADE'))
    mode = Column(String(50), nullable=False)
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text)
    difficulty = Column(Integer, default=5)
    question_data = Column(JSONB, default=dict)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    concept = relationship("Concept", back_populates="questions")


class UserConceptState(Base):
    __tablename__ = 'user_concept_states'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    concept_id = Column(UUID(as_uuid=True), ForeignKey('concepts.id', ondelete='CASCADE'))

    # State
    state = Column(String(50), default='untouched')

    # Criterion 1: Accuracy
    accuracy = Column(Float, default=0.0)
    total_attempts = Column(Integer, default=0)
    correct_attempts = Column(Integer, default=0)

    # Criterion 2: Stability
    consecutive_perfect = Column(Integer, default=0)
    max_streak = Column(Integer, default=0)

    # Criterion 3: Speed/Fluency
    avg_response_time_ms = Column(Integer)
    baseline_response_time_ms = Column(Integer)
    hesitation_count = Column(Integer, default=0)

    # Criterion 4: Format Invariance
    formats_tested = Column(JSONB, default=list)
    formats_passed = Column(JSONB, default=list)

    # Criterion 5: Predicted Recall
    predicted_recall_probability = Column(Float, default=0.0)
    last_tested_at = Column(TIMESTAMP)
    next_review_at = Column(TIMESTAMP)

    # Mastery
    mastered_at = Column(TIMESTAMP)
    last_revalidation_at = Column(TIMESTAMP)

    # Current session
    current_mode = Column(String(50))
    mode_start_time = Column(TIMESTAMP)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="concept_states")
    concept = relationship("Concept", back_populates="user_states")


class Response(Base):
    __tablename__ = 'responses'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    concept_id = Column(UUID(as_uuid=True), ForeignKey('concepts.id', ondelete='CASCADE'))
    question_id = Column(UUID(as_uuid=True), ForeignKey('questions.id', ondelete='CASCADE'))
    session_id = Column(UUID(as_uuid=True))

    mode = Column(String(50), nullable=False)

    # Response
    user_answer = Column(Text)
    is_correct = Column(Boolean, nullable=False)
    is_partial = Column(Boolean, default=False)

    # Timing
    response_time_ms = Column(Integer, nullable=False)
    time_to_first_keystroke_ms = Column(Integer)

    # Context
    difficulty_at_time = Column(Integer)
    sequence_number = Column(Integer)

    # Actions
    skipped = Column(Boolean, default=False)
    peeked = Column(Boolean, default=False)

    created_at = Column(TIMESTAMP, server_default=func.now())


class Session(Base):
    __tablename__ = 'sessions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    material_id = Column(UUID(as_uuid=True), ForeignKey('materials.id', ondelete='CASCADE'))

    start_time = Column(TIMESTAMP, server_default=func.now())
    end_time = Column(TIMESTAMP)
    duration_minutes = Column(Integer)

    total_questions = Column(Integer, default=0)
    total_correct = Column(Integer, default=0)
    concepts_worked = Column(Integer, default=0)
    concepts_mastered_this_session = Column(Integer, default=0)

    goal = Column(String(100))
    goal_deadline = Column(TIMESTAMP)

    # Relationships
    user = relationship("User", back_populates="sessions")


class InversionParagraph(Base):
    """Stores paragraph inversion data for the dialectical learning mode."""
    __tablename__ = 'inversion_paragraphs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    material_id = Column(UUID(as_uuid=True), ForeignKey('materials.id', ondelete='CASCADE'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))

    # Content
    paragraph_number = Column(Integer, nullable=False)
    page_number = Column(Integer)
    original_text = Column(Text, nullable=False)
    inverted_text = Column(Text, nullable=False)

    # Status
    gaps_identified = Column(Boolean, default=False)
    patch_created = Column(Boolean, default=False)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    gaps = relationship("Gap", back_populates="inversion_paragraph", cascade="all, delete-orphan")
    patches = relationship("Patch", back_populates="inversion_paragraph", cascade="all, delete-orphan")


class Gap(Base):
    """Logical gaps identified between original and inverted paragraphs."""
    __tablename__ = 'gaps'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inversion_paragraph_id = Column(UUID(as_uuid=True), ForeignKey('inversion_paragraphs.id', ondelete='CASCADE'))

    # Gap details
    gap_type = Column(String(100), nullable=False)  # assumption, contradiction, edge_case, etc.
    description = Column(Text, nullable=False)
    location = Column(String(50))  # 'original', 'inverted', or 'both'

    # User interaction
    resolved = Column(Boolean, default=False)

    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    inversion_paragraph = relationship("InversionParagraph", back_populates="gaps")


class Patch(Base):
    """User-created patches that reconcile opposites and resolve gaps."""
    __tablename__ = 'patches'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inversion_paragraph_id = Column(UUID(as_uuid=True), ForeignKey('inversion_paragraphs.id', ondelete='CASCADE'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))

    # Patch content
    patch_name = Column(String(255))
    patch_description = Column(Text, nullable=False)
    patch_type = Column(String(100))  # function, rule, principle, exception, etc.

    # Innovation metadata
    creativity_score = Column(Integer)  # 1-10 subjective rating by user
    addresses_gaps = Column(JSONB, default=list)  # List of gap IDs this patch addresses

    # Quality scoring (AI-evaluated)
    quality_score = Column(Float)  # 1.0-10.0 AI-evaluated quality
    passed = Column(Boolean, default=False)  # True if score >= 7.0
    strengths = Column(JSONB, default=list)  # What the patch does well
    weaknesses = Column(JSONB, default=list)  # What needs improvement
    feedback = Column(Text)  # Specific feedback from AI
    next_steps = Column(JSONB, default=list)  # Suggestions for improvement
    addresses_all_gaps = Column(Boolean, default=False)  # Verified by AI

    # Revision tracking
    revision_number = Column(Integer, default=1)  # How many times revised
    previous_version_id = Column(UUID(as_uuid=True))  # Link to previous attempt

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    inversion_paragraph = relationship("InversionParagraph", back_populates="patches")


class MasteryCheckpoint(Base):
    """Tracks user progress through mastery verification system."""
    __tablename__ = 'mastery_checkpoints'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    inversion_paragraph_id = Column(UUID(as_uuid=True), ForeignKey('inversion_paragraphs.id', ondelete='CASCADE'))

    # Checkpoint details
    checkpoint_type = Column(String(50))  # 'initial', 'review_1day', 'review_3day', 'review_1week', 'final_exam'
    passed = Column(Boolean, default=False)
    score = Column(Float)  # Performance score
    confidence_level = Column(Integer)  # User's self-reported confidence (1-10)

    # Timing
    attempted_at = Column(TIMESTAMP, server_default=func.now())
    next_review_at = Column(TIMESTAMP)  # When next review is scheduled

    # Struggle indicators
    time_spent_seconds = Column(Integer)  # How long they spent
    revisions_needed = Column(Integer, default=0)  # How many times they revised
    needed_help = Column(Boolean, default=False)  # Whether they used AI tutor

    created_at = Column(TIMESTAMP, server_default=func.now())


class UserMasteryProgress(Base):
    """Overall mastery progress for a user on a material."""
    __tablename__ = 'user_mastery_progress'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    material_id = Column(UUID(as_uuid=True), ForeignKey('materials.id', ondelete='CASCADE'))

    # Progress metrics
    paragraphs_total = Column(Integer, default=0)
    paragraphs_completed = Column(Integer, default=0)
    paragraphs_mastered = Column(Integer, default=0)  # Passed all reviews

    # Quality metrics
    avg_patch_quality = Column(Float)  # Average score across all patches
    avg_confidence = Column(Float)  # Average self-reported confidence
    avg_actual_performance = Column(Float)  # Average checkpoint scores

    # Time tracking
    total_time_minutes = Column(Integer, default=0)
    last_activity_at = Column(TIMESTAMP)

    # Mastery status
    mastery_certified = Column(Boolean, default=False)
    certification_date = Column(TIMESTAMP)
    final_exam_score = Column(Float)

    # Struggle points (for remediation)
    weak_paragraphs = Column(JSONB, default=list)  # IDs of paragraphs they struggled with
    strong_paragraphs = Column(JSONB, default=list)  # IDs of paragraphs they excelled at

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
