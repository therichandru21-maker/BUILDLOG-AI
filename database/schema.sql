-- ============================================================
-- BuildLog AI - PostgreSQL Database Schema
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- USERS
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) UNIQUE,
    github_username VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- REPOSITORIES
-- ============================================================

CREATE TABLE IF NOT EXISTS repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    github_id BIGINT UNIQUE,
    name VARCHAR(255) NOT NULL,
    full_name VARCHAR(500) NOT NULL,
    description TEXT,
    language VARCHAR(100),
    html_url TEXT,

    stars INTEGER DEFAULT 0,
    forks INTEGER DEFAULT 0,

    is_private BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(user_id, full_name)
);

-- ============================================================
-- GITHUB ACTIVITIES
-- ============================================================

CREATE TABLE IF NOT EXISTS activities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,

    activity_type VARCHAR(50) NOT NULL,

    github_id VARCHAR(255),
    commit_sha VARCHAR(255),

    branch VARCHAR(255),
    title TEXT,
    message TEXT,

    additions INTEGER DEFAULT 0,
    deletions INTEGER DEFAULT 0,
    changed_files INTEGER DEFAULT 0,

    activity_url TEXT,

    occurred_at TIMESTAMPTZ NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(repository_id, commit_sha)
);

-- ============================================================
-- SKILLS
-- ============================================================

CREATE TABLE IF NOT EXISTS skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    name VARCHAR(150) NOT NULL UNIQUE,

    category VARCHAR(100),

    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- USER SKILLS
-- ============================================================

CREATE TABLE IF NOT EXISTS user_skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    skill_id UUID REFERENCES skills(id) ON DELETE CASCADE,

    proficiency_score NUMERIC(5,2) DEFAULT 0,

    evidence_count INTEGER DEFAULT 0,

    last_detected_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(user_id, skill_id)
);

-- ============================================================
-- AI ANALYSES
-- ============================================================

CREATE TABLE IF NOT EXISTS ai_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    analysis_type VARCHAR(100) NOT NULL,

    title VARCHAR(255),

    summary TEXT,

    achievements JSONB DEFAULT '[]'::jsonb,

    detected_skills JSONB DEFAULT '[]'::jsonb,

    problems JSONB DEFAULT '[]'::jsonb,

    recommendations JSONB DEFAULT '[]'::jsonb,

    raw_response JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- WEEKLY REPORTS
-- ============================================================

CREATE TABLE IF NOT EXISTS weekly_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    week_start DATE NOT NULL,
    week_end DATE NOT NULL,

    total_commits INTEGER DEFAULT 0,
    total_additions INTEGER DEFAULT 0,
    total_deletions INTEGER DEFAULT 0,

    repositories_active INTEGER DEFAULT 0,

    projects_completed INTEGER DEFAULT 0,

    productivity_score NUMERIC(5,2),

    summary TEXT,

    achievements JSONB DEFAULT '[]'::jsonb,

    skills_improved JSONB DEFAULT '[]'::jsonb,

    improvement_areas JSONB DEFAULT '[]'::jsonb,

    recommendations JSONB DEFAULT '[]'::jsonb,

    linkedin_draft TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(user_id, week_start, week_end)
);

-- ============================================================
-- GOALS
-- ============================================================

CREATE TABLE IF NOT EXISTS goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    title VARCHAR(255) NOT NULL,

    description TEXT,

    category VARCHAR(100),

    target_date DATE,

    progress NUMERIC(5,2) DEFAULT 0,

    status VARCHAR(50) DEFAULT 'active',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- LEARNING LOGS
-- ============================================================

CREATE TABLE IF NOT EXISTS learning_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    topic VARCHAR(255) NOT NULL,

    description TEXT,

    source VARCHAR(255),

    duration_minutes INTEGER DEFAULT 0,

    difficulty VARCHAR(50),

    notes TEXT,

    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- PROJECTS
-- ============================================================

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    name VARCHAR(255) NOT NULL,

    description TEXT,

    status VARCHAR(50) DEFAULT 'active',

    technology_stack JSONB DEFAULT '[]'::jsonb,

    started_at DATE,

    completed_at DATE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_activities_user_id
ON activities(user_id);

CREATE INDEX IF NOT EXISTS idx_activities_repository_id
ON activities(repository_id);

CREATE INDEX IF NOT EXISTS idx_activities_occurred_at
ON activities(occurred_at);

CREATE INDEX IF NOT EXISTS idx_weekly_reports_user_id
ON weekly_reports(user_id);

CREATE INDEX IF NOT EXISTS idx_learning_logs_user_id
ON learning_logs(user_id);

CREATE INDEX IF NOT EXISTS idx_learning_logs_occurred_at
ON learning_logs(occurred_at);

CREATE INDEX IF NOT EXISTS idx_projects_user_id
ON projects(user_id);

CREATE INDEX IF NOT EXISTS idx_goals_user_id
ON goals(user_id);

-- ============================================================
-- INITIAL SKILLS
-- ============================================================

INSERT INTO skills (name, category)
VALUES
    ('Python', 'Programming'),
    ('Java', 'Programming'),
    ('JavaScript', 'Programming'),
    ('TypeScript', 'Programming'),
    ('C', 'Programming'),
    ('C++', 'Programming'),
    ('React', 'Frontend'),
    ('FastAPI', 'Backend'),
    ('Node.js', 'Backend'),
    ('PostgreSQL', 'Database'),
    ('Docker', 'DevOps'),
    ('Git', 'DevOps'),
    ('GitHub', 'DevOps'),
    ('REST API', 'Backend'),
    ('Artificial Intelligence', 'AI'),
    ('Machine Learning', 'AI'),
    ('Generative AI', 'AI'),
    ('AI Agents', 'AI'),
    ('n8n', 'Automation'),
    ('Cybersecurity', 'Security'),
    ('Cloud', 'DevOps')
ON CONFLICT (name) DO NOTHING;

-- ============================================================
-- DONE
-- ============================================================