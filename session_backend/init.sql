-- Database initialization script for Session Backend API
-- This script creates the database schema and initial setup

-- Create the sessions database if it doesn't exist
-- (This is handled by POSTGRES_DB environment variable in docker-compose)

-- Create session type enum
CREATE TYPE session_type_enum AS ENUM ('AGENT');

-- Create sessions table (Strands-compatible schema)
CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    session_type session_type_enum NOT NULL DEFAULT 'AGENT',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create session_agents table
CREATE TABLE IF NOT EXISTS session_agents (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    state JSONB NOT NULL,
    conversation_manager_state JSONB NOT NULL,
    internal_state JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraint
    CONSTRAINT fk_session_agents_session_id 
        FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    
    -- Unique constraint for session_id + agent_id combination
    CONSTRAINT uk_session_agents_session_agent 
        UNIQUE (session_id, agent_id)
);

-- Create session_messages table
CREATE TABLE IF NOT EXISTS session_messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    message_id INTEGER NOT NULL,
    message JSONB NOT NULL,
    redact_message JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT fk_session_messages_session_agent 
        FOREIGN KEY (session_id, agent_id) 
        REFERENCES session_agents(session_id, agent_id) ON DELETE CASCADE,
    
    -- Unique constraint for session_id + agent_id + message_id combination
    CONSTRAINT uk_session_messages_session_agent_message 
        UNIQUE (session_id, agent_id, message_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_session_agents_session_id ON session_agents(session_id);
CREATE INDEX IF NOT EXISTS idx_session_messages_session_agent ON session_messages(session_id, agent_id);
CREATE INDEX IF NOT EXISTS idx_session_messages_created_at ON session_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_pagination ON session_messages(session_id, agent_id, message_id);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at timestamps
CREATE TRIGGER update_sessions_updated_at 
    BEFORE UPDATE ON sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_session_agents_updated_at 
    BEFORE UPDATE ON session_agents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_session_messages_updated_at 
    BEFORE UPDATE ON session_messages 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (optional, for specific user scenarios)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;