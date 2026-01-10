-- ============================================================================
-- Puddle Assistant - Supabase Database Schema
-- Archivo: 001_create_tables.sql
-- Propósito: Crear tablas para almacenamiento de documentos, chunks y embeddings
-- Fecha: 2024-12-01
-- ============================================================================

-- Habilitar extensión pgvector para manejo de embeddings
-- IMPORTANTE: Ejecutar primero para soporte de vectores
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- TABLA: documents
-- Propósito: Almacenar metadatos de documentos principales
-- ============================================================================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_filename TEXT NOT NULL,                    -- Nombre del archivo original
    document_title TEXT NOT NULL,                     -- Título extraído del documento
    document_type TEXT NOT NULL,                      -- Tipo: manual, guia, curriculum, etc.
    document_summary TEXT,                            -- Resumen generado por LLM del documento completo
    total_chunks INTEGER DEFAULT 0,                   -- Número total de chunks generados
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',                      -- Metadatos adicionales en JSON
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- TABLA: document_chunks  
-- Propósito: Almacenar chunks de texto con metadatos enriquecidos
-- ============================================================================
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id TEXT UNIQUE NOT NULL,                    -- ID único del chunk (hash-based)
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Estructura del chunk
    chunk_index INTEGER NOT NULL,                     -- Índice secuencial en el documento
    section_header TEXT,                              -- Header de la sección
    subsection_header TEXT,                           -- Sub-header si existe
    content_type TEXT,                                -- Tipo: texto, lista, tabla, imagen, codigo
    
    -- Contenido
    content TEXT NOT NULL,                            -- Contenido principal del chunk
    chunk_summary TEXT,                               -- Resumen generado por LLM del chunk específico
    
    -- Métricas de contenido
    text_length INTEGER,                              -- Longitud del texto en caracteres
    word_count INTEGER,                               -- Cantidad de palabras
    
    -- Análisis semántico
    keywords TEXT[] DEFAULT '{}',                     -- Palabras clave extraídas por LLM
    topics TEXT[] DEFAULT '{}',                       -- Temas principales identificados por LLM
    
    -- Características detectadas
    has_code BOOLEAN DEFAULT FALSE,                   -- Contiene código
    has_numbers BOOLEAN DEFAULT FALSE,                -- Contiene números/datos
    has_bullets BOOLEAN DEFAULT FALSE,                -- Contiene listas con bullets
    has_tables BOOLEAN DEFAULT FALSE,                 -- Contiene tablas
    has_images BOOLEAN DEFAULT FALSE,                 -- Contiene imágenes
    
    -- Contexto y navegación
    parent_section TEXT,                              -- Sección padre
    previous_chunk_id TEXT,                           -- ID del chunk anterior
    next_chunk_id TEXT,                               -- ID del chunk siguiente
    
    -- Metadatos adicionales
    metadata JSONB DEFAULT '{}',                      -- Metadatos completos en JSON
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- TABLA: chunk_embeddings
-- Propósito: Almacenar vectores de embeddings para búsqueda semántica
-- ============================================================================
CREATE TABLE IF NOT EXISTS chunk_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
    
    -- Vector embedding (1536 dimensiones para text-embedding-ada-002)
    embedding vector(1536) NOT NULL,                 -- Vector de embedding
    embedding_model TEXT DEFAULT 'text-embedding-ada-002', -- Modelo usado
    
    -- Texto usado para generar el embedding
    embedding_text TEXT,                             -- Texto optimizado usado para embedding
    
    -- Métricas de calidad
    embedding_tokens INTEGER,                        -- Número de tokens procesados
    embedding_cost DECIMAL(10,6),                    -- Costo del embedding (si aplica)
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- ============================================================================

-- Índices para document_chunks
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_section ON document_chunks(section_header);
CREATE INDEX IF NOT EXISTS idx_chunks_type ON document_chunks(content_type);
CREATE INDEX IF NOT EXISTS idx_chunks_keywords ON document_chunks USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_chunks_topics ON document_chunks USING GIN(topics);

-- Índices para documents
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents(source_filename);

-- Índice vectorial para búsqueda de similitud coseno
-- IMPORTANTE: Este índice mejora significativamente el rendimiento de búsquedas vectoriales
CREATE INDEX IF NOT EXISTS idx_embeddings_cosine 
ON chunk_embeddings USING ivfflat (embedding vector_cosine_ops);

-- Índice adicional para búsqueda por distancia L2 (opcional)
-- CREATE INDEX IF NOT EXISTS idx_embeddings_l2 
-- ON chunk_embeddings USING ivfflat (embedding vector_l2_ops);

-- ============================================================================
-- FUNCIONES AUXILIARES
-- ============================================================================

-- Función para búsqueda de documentos similares
CREATE OR REPLACE FUNCTION match_documents (
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.78,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  chunk_id uuid,
  document_id uuid,
  document_title text,
  section_header text,
  content text,
  chunk_summary text,
  keywords text[],
  topics text[],
  similarity float
)
LANGUAGE sql
STABLE
AS $$
  SELECT
    dc.id AS chunk_id,
    d.id AS document_id,
    d.document_title,
    dc.section_header,
    dc.content,
    dc.chunk_summary,
    dc.keywords,
    dc.topics,
    1 - (ce.embedding <=> query_embedding) AS similarity
  FROM chunk_embeddings ce
  JOIN document_chunks dc ON dc.id = ce.chunk_id
  JOIN documents d ON d.id = dc.document_id
  WHERE 1 - (ce.embedding <=> query_embedding) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
$$;

-- ============================================================================
-- TRIGGERS PARA MANTENIMIENTO AUTOMÁTICO
-- ============================================================================

-- Trigger para actualizar updated_at en documents
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON documents 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMENTARIOS EN TABLAS
-- ============================================================================

COMMENT ON TABLE documents IS 'Metadatos de documentos procesados por Puddle Assistant';
COMMENT ON TABLE document_chunks IS 'Chunks de texto con metadatos enriquecidos y análisis semántico';
COMMENT ON TABLE chunk_embeddings IS 'Vectores de embeddings para búsqueda semántica con pgvector';

COMMENT ON COLUMN chunk_embeddings.embedding IS 'Vector de 1536 dimensiones generado por text-embedding-ada-002';
COMMENT ON FUNCTION match_documents IS 'Búsqueda de documentos similares usando similitud coseno';

-- ============================================================================
-- VERIFICACIONES POST-INSTALACIÓN
-- ============================================================================

-- Verificar que pgvector está habilitado
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') 
        THEN '✅ Extensión pgvector habilitada'
        ELSE '❌ ERROR: pgvector no está habilitado'
    END AS status;

-- Verificar tablas creadas
SELECT 
    schemaname, 
    tablename, 
    tableowner 
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename IN ('documents', 'document_chunks', 'chunk_embeddings')
ORDER BY tablename;

-- Mostrar índices creados
SELECT 
    indexname, 
    tablename, 
    indexdef 
FROM pg_indexes 
WHERE schemaname = 'public' 
    AND tablename IN ('documents', 'document_chunks', 'chunk_embeddings')
ORDER BY tablename, indexname;