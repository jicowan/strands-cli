-- Migration script to update sessions table to Strands-compatible schema
-- Run this after stopping containers and before restarting

-- Create session type enum if it doesn't exist
DO $$ BEGIN
    CREATE TYPE session_type_enum AS ENUM ('AGENT');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Add session_type column with default value
ALTER TABLE sessions 
ADD COLUMN IF NOT EXISTS session_type session_type_enum NOT NULL DEFAULT 'AGENT';

-- Drop the old multi_agent_state column
ALTER TABLE sessions 
DROP COLUMN IF EXISTS multi_agent_state;

-- Update any existing sessions to have AGENT type (should already be default)
UPDATE sessions SET session_type = 'AGENT' WHERE session_type IS NULL;