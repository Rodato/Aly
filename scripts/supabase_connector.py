#!/usr/bin/env python3
"""
Supabase Connector - Puddle Assistant
Configuración y conexión a Supabase con pgvector
"""

import json
import logging
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

try:
    from supabase import create_client, Client
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("❌ Dependencias faltantes. Instala con:")
    print("pip install supabase psycopg2-binary")
    exit(1)

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseVectorStore:
    """Conector para almacenar embeddings en Supabase con pgvector."""
    
    def __init__(self):
        # Configuración de Supabase
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self.database_url = os.getenv("SUPABASE_DB_URL")  # Para conexión directa a PostgreSQL
        
        if not all([self.supabase_url, self.supabase_key]):
            raise ValueError("Variables de Supabase no configuradas en .env")
        
        # Cliente Supabase
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Configuración de tablas
        self.documents_table = "documents"
        self.chunks_table = "document_chunks"
        self.embeddings_table = "chunk_embeddings"
    
    def create_tables(self) -> bool:
        """Crea las tablas necesarias en Supabase."""
        
        # SQL para crear tablas
        sql_commands = [
            # Habilitar extensión pgvector
            "CREATE EXTENSION IF NOT EXISTS vector;",
            
            # Tabla de documentos
            f"""
            CREATE TABLE IF NOT EXISTS {self.documents_table} (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                source_filename TEXT NOT NULL,
                document_title TEXT NOT NULL,
                document_type TEXT NOT NULL,
                document_summary TEXT,
                total_chunks INTEGER DEFAULT 0,
                processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                metadata JSONB DEFAULT '{{}}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            
            # Tabla de chunks
            f"""
            CREATE TABLE IF NOT EXISTS {self.chunks_table} (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                chunk_id TEXT UNIQUE NOT NULL,
                document_id UUID REFERENCES {self.documents_table}(id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                section_header TEXT,
                subsection_header TEXT,
                content_type TEXT,
                content TEXT NOT NULL,
                chunk_summary TEXT,
                text_length INTEGER,
                word_count INTEGER,
                keywords TEXT[] DEFAULT '{{}}',
                topics TEXT[] DEFAULT '{{}}',
                metadata JSONB DEFAULT '{{}}',
                processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            
            # Tabla de embeddings con pgvector
            f"""
            CREATE TABLE IF NOT EXISTS {self.embeddings_table} (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                chunk_id UUID REFERENCES {self.chunks_table}(id) ON DELETE CASCADE,
                embedding vector(1536),  -- Dimensión para text-embedding-ada-002
                embedding_model TEXT DEFAULT 'text-embedding-ada-002',
                embedding_text TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            
            # Índices para optimizar búsquedas
            f"CREATE INDEX IF NOT EXISTS idx_chunks_document ON {self.chunks_table}(document_id);",
            f"CREATE INDEX IF NOT EXISTS idx_chunks_section ON {self.chunks_table}(section_header);",
            f"CREATE INDEX IF NOT EXISTS idx_embeddings_cosine ON {self.embeddings_table} USING ivfflat (embedding vector_cosine_ops);",
            f"CREATE INDEX IF NOT EXISTS idx_documents_type ON {self.documents_table}(document_type);",
            f"CREATE INDEX IF NOT EXISTS idx_chunks_keywords ON {self.chunks_table} USING GIN(keywords);",
        ]
        
        try:
            if self.database_url:
                # Usar conexión directa a PostgreSQL para comandos DDL
                with psycopg2.connect(self.database_url) as conn:
                    with conn.cursor() as cur:
                        for sql in sql_commands:
                            logger.info(f"Ejecutando: {sql[:50]}...")
                            cur.execute(sql)
                        conn.commit()
            else:
                # Usar cliente Supabase (puede tener limitaciones para DDL)
                for sql in sql_commands:
                    self.client.rpc('execute_sql', {'sql': sql}).execute()
            
            logger.info("✅ Tablas creadas/actualizadas exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando tablas: {e}")
            return False
    
    def insert_document(self, doc_metadata: Dict) -> Optional[str]:
        """Inserta un documento y retorna su ID."""
        try:
            doc_data = {
                "source_filename": doc_metadata["document_source"],
                "document_title": doc_metadata["document_title"],
                "document_type": doc_metadata["document_type"],
                "document_summary": doc_metadata.get("document_summary", ""),
                "total_chunks": doc_metadata.get("total_chunks", 0),
                "metadata": doc_metadata
            }
            
            result = self.client.table(self.documents_table).insert(doc_data).execute()
            
            if result.data and len(result.data) > 0:
                doc_id = result.data[0]["id"]
                logger.info(f"✅ Documento insertado: {doc_id}")
                return doc_id
            else:
                logger.error("❌ No se pudo insertar documento")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error insertando documento: {e}")
            return None
    
    def insert_chunk(self, chunk_data: Dict, document_id: str) -> Optional[str]:
        """Inserta un chunk y retorna su ID."""
        try:
            metadata = chunk_data["metadata"]
            
            chunk_insert_data = {
                "chunk_id": metadata["chunk_id"],
                "document_id": document_id,
                "chunk_index": metadata["chunk_index"],
                "section_header": metadata["section_header"],
                "subsection_header": metadata.get("subsection_header"),
                "content_type": metadata["content_type"],
                "content": chunk_data["content"],
                "chunk_summary": metadata.get("chunk_summary", ""),
                "text_length": metadata["text_length"],
                "word_count": metadata["word_count"],
                "keywords": metadata.get("keywords", []),
                "topics": metadata.get("topics", []),
                "metadata": metadata
            }
            
            result = self.client.table(self.chunks_table).insert(chunk_insert_data).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]["id"]
            else:
                logger.error(f"❌ No se pudo insertar chunk {metadata['chunk_id']}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error insertando chunk: {e}")
            return None
    
    def insert_embedding(self, chunk_uuid: str, embedding: List[float], embedding_text: str) -> bool:
        """Inserta un embedding."""
        try:
            embedding_data = {
                "chunk_id": chunk_uuid,
                "embedding": embedding,
                "embedding_model": "text-embedding-ada-002",
                "embedding_text": embedding_text
            }
            
            result = self.client.table(self.embeddings_table).insert(embedding_data).execute()
            
            return result.data is not None and len(result.data) > 0
            
        except Exception as e:
            logger.error(f"❌ Error insertando embedding: {e}")
            return False
    
    def upload_document_embeddings(self, embeddings_data: List[Dict]) -> bool:
        """Sube un documento completo con sus embeddings."""
        if not embeddings_data:
            logger.warning("❌ No hay datos de embeddings para subir")
            return False
        
        logger.info(f"📤 Subiendo documento con {len(embeddings_data)} chunks...")
        
        try:
            # Obtener metadatos del primer chunk para el documento
            first_chunk = embeddings_data[0]["chunk_data"]
            doc_metadata = first_chunk["metadata"].copy()
            doc_metadata["total_chunks"] = len(embeddings_data)
            
            # 1. Insertar documento
            document_id = self.insert_document(doc_metadata)
            if not document_id:
                return False
            
            # 2. Insertar chunks y embeddings
            successful_chunks = 0
            
            for i, item in enumerate(embeddings_data):
                chunk_data = item["chunk_data"]
                embedding = item["embedding"]
                embedding_text = item["embedding_text"]
                
                # Insertar chunk
                chunk_uuid = self.insert_chunk(chunk_data, document_id)
                if not chunk_uuid:
                    logger.warning(f"⚠️ Falló chunk {i+1}/{len(embeddings_data)}")
                    continue
                
                # Insertar embedding
                if self.insert_embedding(chunk_uuid, embedding, embedding_text):
                    successful_chunks += 1
                else:
                    logger.warning(f"⚠️ Falló embedding para chunk {i+1}")
            
            logger.info(f"✅ Subida completada: {successful_chunks}/{len(embeddings_data)} chunks exitosos")
            return successful_chunks > 0
            
        except Exception as e:
            logger.error(f"❌ Error en subida de documento: {e}")
            return False
    
    def search_similar_chunks(self, 
                            query_embedding: List[float], 
                            limit: int = 5,
                            similarity_threshold: float = 0.7,
                            document_type: Optional[str] = None) -> List[Dict]:
        """Busca chunks similares usando búsqueda vectorial."""
        try:
            # Construir query base
            query = self.client.rpc('match_documents', {
                'query_embedding': query_embedding,
                'match_threshold': similarity_threshold,
                'match_count': limit
            })
            
            # Filtrar por tipo de documento si se especifica
            if document_type:
                query = query.eq('document_type', document_type)
            
            result = query.execute()
            
            if result.data:
                logger.info(f"🔍 Encontrados {len(result.data)} chunks similares")
                return result.data
            else:
                logger.info("🔍 No se encontraron chunks similares")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error en búsqueda: {e}")
            return []
    
    def get_document_stats(self) -> Dict:
        """Obtiene estadísticas de la base de datos."""
        try:
            # Contar documentos
            docs_result = self.client.table(self.documents_table).select("count", count="exact").execute()
            docs_count = docs_result.count if docs_result else 0
            
            # Contar chunks
            chunks_result = self.client.table(self.chunks_table).select("count", count="exact").execute()
            chunks_count = chunks_result.count if chunks_result else 0
            
            # Contar embeddings
            embeddings_result = self.client.table(self.embeddings_table).select("count", count="exact").execute()
            embeddings_count = embeddings_result.count if embeddings_result else 0
            
            # Documentos por tipo
            types_result = self.client.table(self.documents_table).select("document_type").execute()
            doc_types = {}
            if types_result.data:
                for doc in types_result.data:
                    doc_type = doc["document_type"]
                    doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            return {
                "documents": docs_count,
                "chunks": chunks_count,
                "embeddings": embeddings_count,
                "document_types": doc_types,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {}


def main():
    """Función principal para testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Conector Supabase")
    parser.add_argument("--setup", action="store_true", help="Crear tablas")
    parser.add_argument("--stats", action="store_true", help="Mostrar estadísticas")
    parser.add_argument("--upload", help="Subir archivo de embeddings")
    
    args = parser.parse_args()
    
    try:
        connector = SupabaseVectorStore()
        
        if args.setup:
            success = connector.create_tables()
            if success:
                print("✅ Configuración de Supabase completada")
            else:
                print("❌ Error en configuración")
        
        elif args.stats:
            stats = connector.get_document_stats()
            print("📊 Estadísticas de Supabase:")
            print(f"  📄 Documentos: {stats.get('documents', 0)}")
            print(f"  📝 Chunks: {stats.get('chunks', 0)}")
            print(f"  🔢 Embeddings: {stats.get('embeddings', 0)}")
            print(f"  📋 Tipos de documentos: {stats.get('document_types', {})}")
        
        elif args.upload:
            from pathlib import Path
            file_path = Path(f"data/processed/embeddings/{args.upload}")
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    embeddings_data = json.load(f)
                
                success = connector.upload_document_embeddings(embeddings_data)
                if success:
                    print(f"✅ Archivo subido: {args.upload}")
                else:
                    print(f"❌ Error subiendo: {args.upload}")
            else:
                print(f"❌ Archivo no encontrado: {args.upload}")
        
        else:
            print("Usa --setup, --stats, o --upload <archivo>")
            
    except ValueError as e:
        print(f"❌ Error de configuración: {e}")
        print("\nConfigura las variables en .env:")
        print("SUPABASE_URL=https://tu-proyecto.supabase.co")
        print("SUPABASE_ANON_KEY=tu_anon_key")
        print("SUPABASE_DB_URL=postgresql://user:pass@host:port/db")
    
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()