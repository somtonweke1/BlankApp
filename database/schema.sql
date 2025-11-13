-- MASTERY MACHINE DATABASE SCHEMA

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    total_concepts_mastered INT DEFAULT 0,
    total_session_time_minutes INT DEFAULT 0
);

-- Uploaded materials
CREATE TABLE IF NOT EXISTS materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    upload_date TIMESTAMP DEFAULT NOW(),
    total_pages INT,
    processing_status VARCHAR(50) DEFAULT 'uploaded',
    estimated_time_minutes INT,
    error_message TEXT
);

-- Extracted concepts
CREATE TABLE IF NOT EXISTS concepts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_id UUID REFERENCES materials(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50),
    full_name TEXT,
    definition TEXT,
    context TEXT,
    complexity INT DEFAULT 1,
    domain VARCHAR(100),
    formulas JSONB DEFAULT '[]'::jsonb,
    examples JSONB DEFAULT '[]'::jsonb,
    related_concepts JSONB DEFAULT '[]'::jsonb,
    dependencies JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Generated questions
CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    concept_id UUID REFERENCES concepts(id) ON DELETE CASCADE,
    mode VARCHAR(50) NOT NULL,
    question_text TEXT NOT NULL,
    answer_text TEXT,
    difficulty INT DEFAULT 5,
    question_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

-- User concept state (THE CORE STATE TRACKER)
CREATE TABLE IF NOT EXISTS user_concept_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    concept_id UUID REFERENCES concepts(id) ON DELETE CASCADE,

    -- State
    state VARCHAR(50) DEFAULT 'untouched',

    -- Criterion 1: Accuracy
    accuracy FLOAT DEFAULT 0.0,
    total_attempts INT DEFAULT 0,
    correct_attempts INT DEFAULT 0,

    -- Criterion 2: Stability
    consecutive_perfect INT DEFAULT 0,
    max_streak INT DEFAULT 0,

    -- Criterion 3: Speed/Fluency
    avg_response_time_ms INT,
    baseline_response_time_ms INT,
    hesitation_count INT DEFAULT 0,

    -- Criterion 4: Format Invariance
    formats_tested JSONB DEFAULT '[]'::jsonb,
    formats_passed JSONB DEFAULT '[]'::jsonb,

    -- Criterion 5: Predicted Recall
    predicted_recall_probability FLOAT DEFAULT 0.0,
    last_tested_at TIMESTAMP,
    next_review_at TIMESTAMP,

    -- Mastery
    mastered_at TIMESTAMP,
    last_revalidation_at TIMESTAMP,

    -- Current session state
    current_mode VARCHAR(50),
    mode_start_time TIMESTAMP,

    UNIQUE(user_id, concept_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Response log (every interaction)
CREATE TABLE IF NOT EXISTS responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    concept_id UUID REFERENCES concepts(id) ON DELETE CASCADE,
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    session_id UUID,

    mode VARCHAR(50) NOT NULL,

    -- Response
    user_answer TEXT,
    is_correct BOOLEAN NOT NULL,
    is_partial BOOLEAN DEFAULT FALSE,

    -- Timing
    response_time_ms INT NOT NULL,
    time_to_first_keystroke_ms INT,

    -- Context
    difficulty_at_time INT,
    sequence_number INT,

    -- Actions
    skipped BOOLEAN DEFAULT FALSE,
    peeked BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT NOW()
);

-- Sessions
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    material_id UUID REFERENCES materials(id) ON DELETE CASCADE,

    start_time TIMESTAMP DEFAULT NOW(),
    end_time TIMESTAMP,
    duration_minutes INT,

    total_questions INT DEFAULT 0,
    total_correct INT DEFAULT 0,
    concepts_worked INT DEFAULT 0,
    concepts_mastered_this_session INT DEFAULT 0,

    goal VARCHAR(100),
    goal_deadline TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_concepts_material ON concepts(material_id);
CREATE INDEX IF NOT EXISTS idx_questions_concept ON questions(concept_id);
CREATE INDEX IF NOT EXISTS idx_user_concept_states_user ON user_concept_states(user_id);
CREATE INDEX IF NOT EXISTS idx_user_concept_states_concept ON user_concept_states(concept_id);
CREATE INDEX IF NOT EXISTS idx_responses_user ON responses(user_id);
CREATE INDEX IF NOT EXISTS idx_responses_session ON responses(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for user_concept_states
CREATE TRIGGER update_user_concept_states_updated_at BEFORE UPDATE ON user_concept_states
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
