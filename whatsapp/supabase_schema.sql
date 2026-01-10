-- Supabase Schema for WhatsApp Bot Conversations and Memory
-- ALY Assistant Conversation Management

-- =====================================================
-- USERS TABLE - User profiles and preferences
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    preferred_language VARCHAR(5) DEFAULT 'es' CHECK (preferred_language IN ('es', 'en', 'pt')),
    first_interaction_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_interaction_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_messages INTEGER DEFAULT 0,
    user_context JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- CONVERSATIONS TABLE - Conversation sessions
-- =====================================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    session_started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_ended_at TIMESTAMP WITH TIME ZONE,
    message_count INTEGER DEFAULT 0,
    session_summary TEXT,
    detected_topics TEXT[],
    session_language VARCHAR(5),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- MESSAGES TABLE - Individual messages and interactions
-- =====================================================
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    
    -- Message content
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    
    -- Agent information
    agent_type VARCHAR(50), -- rag, workshop, brainstorming, safe_edge, fallback
    detected_language VARCHAR(5),
    detected_intent VARCHAR(20), -- FACTUAL, PLAN, IDEATE, SENSITIVE, AMBIGUOUS
    
    -- Processing metadata
    response_time_ms INTEGER,
    sources_used JSONB DEFAULT '[]', -- [{document: "", section: "", similarity: 0.8}]
    rag_context JSONB DEFAULT '{}', -- Vector search results
    
    -- Message metadata
    message_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    twilio_message_sid VARCHAR(100),
    
    -- Analytics
    message_length INTEGER, -- Length of user message
    response_length INTEGER, -- Length of bot response
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- CONVERSATION_MEMORY TABLE - Context memory for conversations
-- =====================================================
CREATE TABLE IF NOT EXISTS conversation_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Memory content
    memory_type VARCHAR(50) NOT NULL, -- 'context', 'preference', 'topic', 'goal'
    memory_content TEXT NOT NULL,
    memory_summary TEXT,
    
    -- Relevance and weighting
    importance_score DECIMAL(3,2) DEFAULT 0.5, -- 0.0 to 1.0
    last_referenced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reference_count INTEGER DEFAULT 1,
    
    -- Memory lifecycle
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- USER_PREFERENCES TABLE - User learning preferences and history
-- =====================================================
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Educational context
    role VARCHAR(100), -- 'teacher', 'facilitator', 'coordinator', 'parent', etc.
    organization VARCHAR(200),
    target_audience VARCHAR(100), -- 'adolescents', 'adults', 'fathers', 'mixed', etc.
    geographic_context VARCHAR(100),
    
    -- Interaction preferences
    preferred_response_style VARCHAR(50), -- 'detailed', 'concise', 'practical'
    favorite_agent_types TEXT[], -- ['workshop', 'brainstorming', 'rag']
    frequent_topics TEXT[], -- ['positive_masculinity', 'workshop_planning', etc.]
    
    -- Learning progress
    topics_explored JSONB DEFAULT '{}', -- {topic: count, last_accessed: timestamp}
    successful_implementations TEXT[], -- Activities user has implemented
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- SESSION_ANALYTICS TABLE - Performance and usage analytics
-- =====================================================
CREATE TABLE IF NOT EXISTS session_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    
    -- Performance metrics
    avg_response_time_ms DECIMAL(8,2),
    total_rag_queries INTEGER DEFAULT 0,
    total_agent_switches INTEGER DEFAULT 0,
    
    -- Usage patterns
    peak_activity_hour INTEGER, -- 0-23
    session_duration_minutes INTEGER,
    most_used_agent_type VARCHAR(50),
    
    -- Quality metrics
    error_count INTEGER DEFAULT 0,
    fallback_activations INTEGER DEFAULT 0,
    
    -- Engagement metrics
    user_satisfaction_inferred VARCHAR(20), -- 'high', 'medium', 'low', 'unknown'
    session_completion_status VARCHAR(20), -- 'completed', 'abandoned', 'ongoing'
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEXES for performance optimization
-- =====================================================

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_phone_number ON users(phone_number);
CREATE INDEX IF NOT EXISTS idx_users_last_interaction ON users(last_interaction_at);
CREATE INDEX IF NOT EXISTS idx_users_language ON users(preferred_language);

-- Conversations table indexes
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_phone_number ON conversations(phone_number);
CREATE INDEX IF NOT EXISTS idx_conversations_session_started ON conversations(session_started_at);
CREATE INDEX IF NOT EXISTS idx_conversations_active ON conversations(is_active);

-- Messages table indexes
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_phone_number ON messages(phone_number);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(message_timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_agent_type ON messages(agent_type);
CREATE INDEX IF NOT EXISTS idx_messages_intent ON messages(detected_intent);

-- Memory table indexes
CREATE INDEX IF NOT EXISTS idx_memory_conversation_id ON conversation_memory(conversation_id);
CREATE INDEX IF NOT EXISTS idx_memory_user_id ON conversation_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_type ON conversation_memory(memory_type);
CREATE INDEX IF NOT EXISTS idx_memory_importance ON conversation_memory(importance_score);
CREATE INDEX IF NOT EXISTS idx_memory_active ON conversation_memory(is_active);

-- =====================================================
-- FUNCTIONS for automated data management
-- =====================================================

-- Function to update user's last interaction
CREATE OR REPLACE FUNCTION update_user_last_interaction()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE users 
    SET last_interaction_at = NEW.message_timestamp,
        total_messages = total_messages + 1,
        updated_at = NOW()
    WHERE id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to auto-update conversation message count
CREATE OR REPLACE FUNCTION update_conversation_message_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations 
    SET message_count = message_count + 1,
        updated_at = NOW()
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to clean old memory entries (older than 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_memory()
RETURNS void AS $$
BEGIN
    UPDATE conversation_memory 
    SET is_active = false
    WHERE created_at < NOW() - INTERVAL '30 days'
    AND importance_score < 0.3
    AND memory_type = 'context';
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TRIGGERS for automated data management
-- =====================================================

-- Trigger to update user interaction timestamp
CREATE TRIGGER tr_update_user_interaction
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_user_last_interaction();

-- Trigger to update conversation message count
CREATE TRIGGER tr_update_conversation_count
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_message_count();

-- =====================================================
-- ROW LEVEL SECURITY (Optional - for multi-tenant setup)
-- =====================================================

-- Enable RLS on all tables (uncomment if needed)
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE conversation_memory ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- INITIAL DATA SETUP
-- =====================================================

-- Insert sample user types for reference (optional)
-- INSERT INTO user_preferences (user_id, role) 
-- VALUES (uuid_generate_v4(), 'system_reference') 
-- ON CONFLICT DO NOTHING;

-- =====================================================
-- VIEWS for common queries
-- =====================================================

-- View for active conversations with user info
CREATE OR REPLACE VIEW active_conversations AS
SELECT 
    c.id as conversation_id,
    c.phone_number,
    u.preferred_language,
    c.session_started_at,
    c.message_count,
    c.detected_topics,
    u.total_messages as user_total_messages
FROM conversations c
JOIN users u ON c.user_id = u.id
WHERE c.is_active = true;

-- View for recent conversation memory
CREATE OR REPLACE VIEW recent_memory AS
SELECT 
    cm.conversation_id,
    cm.memory_type,
    cm.memory_content,
    cm.importance_score,
    cm.last_referenced_at
FROM conversation_memory cm
WHERE cm.is_active = true 
AND cm.last_referenced_at > NOW() - INTERVAL '7 days'
ORDER BY cm.importance_score DESC, cm.last_referenced_at DESC;

-- View for user conversation summary
CREATE OR REPLACE VIEW user_conversation_summary AS
SELECT 
    u.phone_number,
    u.preferred_language,
    COUNT(DISTINCT c.id) as total_conversations,
    u.total_messages,
    u.first_interaction_at,
    u.last_interaction_at,
    ARRAY_AGG(DISTINCT m.agent_type) FILTER (WHERE m.agent_type IS NOT NULL) as used_agent_types,
    ARRAY_AGG(DISTINCT m.detected_intent) FILTER (WHERE m.detected_intent IS NOT NULL) as interaction_types
FROM users u
LEFT JOIN conversations c ON u.id = c.user_id
LEFT JOIN messages m ON c.id = m.conversation_id
GROUP BY u.id, u.phone_number, u.preferred_language, u.total_messages, 
         u.first_interaction_at, u.last_interaction_at;

-- =====================================================
-- COMMENTS for documentation
-- =====================================================

COMMENT ON TABLE users IS 'User profiles and basic information from WhatsApp interactions';
COMMENT ON TABLE conversations IS 'Conversation sessions grouping related messages';
COMMENT ON TABLE messages IS 'Individual message exchanges between user and ALY bot';
COMMENT ON TABLE conversation_memory IS 'Contextual memory for maintaining conversation continuity';
COMMENT ON TABLE user_preferences IS 'User learning preferences and educational context';
COMMENT ON TABLE session_analytics IS 'Performance and usage analytics per conversation session';

COMMENT ON COLUMN users.user_context IS 'JSONB field for flexible user data storage';
COMMENT ON COLUMN messages.sources_used IS 'RAG sources used for generating the response';
COMMENT ON COLUMN conversation_memory.importance_score IS 'Relevance score 0.0-1.0 for memory prioritization';
COMMENT ON COLUMN user_preferences.topics_explored IS 'JSONB tracking user learning progress';