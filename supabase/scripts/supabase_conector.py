import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd

# Cargar variables de entorno
load_dotenv()

# Configurar Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

# Verificar conexión a Supabase

def test_connection():
    """Probar conexión a Supabase"""
    try:
          # Verificar que las credenciales están configuradas
          if not url or not key:
              print("❌ SUPABASE_URL o SUPABASE_ANON_KEY no configuradas")
              return False
          
          print(f"🔗 URL: {url}")
          print(f"🔑 Key configurada: {'Sí' if key else 'No'}")
          print("✅ Conexión a Supabase configurada correctamente")
          return True
    except Exception as e:
          print(f"❌ Error conectando a Supabase: {e}")
          return False
    
def create_tables():
    """Crear tablas necesarias para el vector store"""
    try:
        print("🛠️ Creando tablas para embeddings...")
        
        # Tabla de documentos
        documents_result = supabase.table('documents').insert({
            'source_filename': 'test',
            'document_title': 'test',  
            'document_type': 'test'
        }).execute()
        
        if documents_result.data:
            print("✅ Tabla 'documents' accesible")
            # Limpiar registro de prueba
            supabase.table('documents').delete().eq('source_filename', 'test').execute()
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        if 'does not exist' in error_msg or 'PGRST205' in error_msg:
            print("⚠️ Las tablas no existen. Necesitan crearse manualmente en Supabase")
            print("📋 Ejecuta este SQL en el SQL Editor de Supabase:")
            print_create_tables_sql()
            return False
        else:
            print(f"❌ Error verificando tablas: {e}")
            return False

def print_create_tables_sql():
    """Imprime el SQL para crear las tablas"""
    sql = """
-- Habilitar extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabla de documentos
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_filename TEXT NOT NULL,
    document_title TEXT NOT NULL,
    document_type TEXT NOT NULL,
    document_summary TEXT,
    total_chunks INTEGER DEFAULT 0,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de chunks
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id TEXT UNIQUE NOT NULL,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    section_header TEXT,
    content_type TEXT,
    content TEXT NOT NULL,
    chunk_summary TEXT,
    text_length INTEGER,
    word_count INTEGER,
    keywords TEXT[] DEFAULT '{}',
    topics TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de embeddings
CREATE TABLE chunk_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID REFERENCES document_chunks(id) ON DELETE CASCADE,
    embedding vector(1536),
    embedding_model TEXT DEFAULT 'text-embedding-ada-002',
    embedding_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_embeddings_cosine ON chunk_embeddings USING ivfflat (embedding vector_cosine_ops);
"""
    print(sql)

# Test de conexión y verificación de tablas
if not test_connection():
    sys.exit(1)

print("\n📋 Verificando tablas...")
create_tables()
