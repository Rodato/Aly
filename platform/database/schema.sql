-- ESQUEMA PARA PUDDLE PLATFORM (Gestión Multi-Bot)

-- Habilitar extensión para UUIDs si no existe
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. TABLA DE BOTS (Perfiles de Agentes)
CREATE TABLE IF NOT EXISTS bots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    system_prompt TEXT NOT NULL DEFAULT 'Eres un asistente útil.',
    model_provider TEXT DEFAULT 'openai', -- 'openai', 'anthropic', 'mistral'
    model_name TEXT DEFAULT 'gpt-4o-mini',
    temperature FLOAT DEFAULT 0.7,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. TABLA DE CONFIGURACIÓN DE RAG (Bases de Conocimiento)
CREATE TABLE IF NOT EXISTS bot_knowledge (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bot_id UUID REFERENCES bots(id) ON DELETE CASCADE,
    collection_name TEXT NOT NULL, -- Nombre de la colección en MongoDB/Chroma
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. TABLA DE ARCHIVOS ASOCIADOS (Metadata)
CREATE TABLE IF NOT EXISTS knowledge_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    knowledge_id UUID REFERENCES bot_knowledge(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_url TEXT, -- Link a Supabase Storage u otro
    status TEXT DEFAULT 'pending', -- 'pending', 'processed', 'error'
    chunk_count INTEGER DEFAULT 0,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. TABLA DE INTEGRACIONES (Canales)
CREATE TABLE IF NOT EXISTS bot_integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bot_id UUID REFERENCES bots(id) ON DELETE CASCADE,
    channel_type TEXT NOT NULL, -- 'WHATSAPP_TWILIO', 'WEB_WIDGET', 'API'
    config JSONB NOT NULL DEFAULT '{}', -- Credenciales cifradas o tokens
    is_active BOOLEAN DEFAULT TRUE,
    webhook_url TEXT, -- URL generada para este bot
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. TABLA DE SESIONES (Vinculadas al Bot específico)
CREATE TABLE IF NOT EXISTS platform_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bot_id UUID REFERENCES bots(id) ON DELETE CASCADE,
    user_identifier TEXT, -- Teléfono o Email
    channel TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_message_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Inserta un bot por defecto (puedes migrar ALY aquí después)
INSERT INTO bots (name, description, system_prompt, model_name)
VALUES (
    'ALY (Default)', 
    'Asistente educativo para igualdad de género (Versión Plataforma)', 
    'Eres ALY, un asistente experto en programas educativos de género...',
    'gpt-4o-mini'
);
