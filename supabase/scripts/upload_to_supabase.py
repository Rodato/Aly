#!/usr/bin/env python3
"""
Upload to Supabase - Puddle Assistant
Sube embeddings generados a Supabase
"""

import json
import logging
import os
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseUploader:
    """Subidor de embeddings a Supabase."""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL o SUPABASE_ANON_KEY no configuradas")
        
        self.client = create_client(self.url, self.key)
    
    def upload_document_embeddings(self, embeddings_data: list) -> bool:
        """Sube un documento completo con embeddings."""
        if not embeddings_data:
            logger.error("No hay datos para subir")
            return False
        
        logger.info(f"📤 Subiendo documento con {len(embeddings_data)} chunks...")
        
        try:
            # Obtener metadatos del primer chunk
            first_chunk = embeddings_data[0]["chunk_data"]
            metadata = first_chunk["metadata"]
            
            # 1. Insertar documento
            doc_data = {
                "source_filename": metadata["document_source"],
                "document_title": metadata["document_title"],
                "document_type": metadata["document_type"],
                "document_summary": metadata.get("document_summary", ""),
                "total_chunks": len(embeddings_data),
                "metadata": metadata
            }
            
            doc_result = self.client.table('documents').insert(doc_data).execute()
            
            if not doc_result.data:
                logger.error("Error insertando documento")
                return False
            
            document_id = doc_result.data[0]["id"]
            logger.info(f"✅ Documento insertado: {document_id}")
            
            # 2. Insertar chunks y embeddings
            successful_chunks = 0
            
            for i, item in enumerate(embeddings_data):
                try:
                    chunk_data = item["chunk_data"]
                    chunk_metadata = chunk_data["metadata"]
                    embedding = item["embedding"]
                    embedding_text = item["embedding_text"]
                    
                    # Insertar chunk
                    chunk_insert_data = {
                        "chunk_id": chunk_metadata["chunk_id"],
                        "document_id": document_id,
                        "chunk_index": chunk_metadata["chunk_index"],
                        "section_header": chunk_metadata["section_header"],
                        "content_type": chunk_metadata["content_type"],
                        "content": chunk_data["content"],
                        "chunk_summary": chunk_metadata.get("chunk_summary", ""),
                        "text_length": chunk_metadata["text_length"],
                        "word_count": chunk_metadata["word_count"],
                        "keywords": chunk_metadata.get("keywords", []),
                        "topics": chunk_metadata.get("topics", []),
                        "metadata": chunk_metadata
                    }
                    
                    chunk_result = self.client.table('document_chunks').insert(chunk_insert_data).execute()
                    
                    if not chunk_result.data:
                        logger.warning(f"Error insertando chunk {i+1}")
                        continue
                    
                    chunk_uuid = chunk_result.data[0]["id"]
                    
                    # Insertar embedding
                    embedding_data = {
                        "chunk_id": chunk_uuid,
                        "embedding": embedding,
                        "embedding_model": "text-embedding-ada-002",
                        "embedding_text": embedding_text
                    }
                    
                    embedding_result = self.client.table('chunk_embeddings').insert(embedding_data).execute()
                    
                    if embedding_result.data:
                        successful_chunks += 1
                        if (i + 1) % 10 == 0:
                            logger.info(f"Procesados {i+1}/{len(embeddings_data)} chunks")
                    else:
                        logger.warning(f"Error insertando embedding {i+1}")
                        
                except Exception as e:
                    logger.warning(f"Error procesando chunk {i+1}: {e}")
                    continue
            
            logger.info(f"✅ Subida completada: {successful_chunks}/{len(embeddings_data)} chunks exitosos")
            return successful_chunks > 0
            
        except Exception as e:
            logger.error(f"❌ Error en subida: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Obtiene estadísticas de la base de datos."""
        try:
            # Contar documentos
            docs_result = self.client.table('documents').select("count", count="exact").execute()
            docs_count = docs_result.count if docs_result else 0
            
            # Contar chunks
            chunks_result = self.client.table('document_chunks').select("count", count="exact").execute()
            chunks_count = chunks_result.count if chunks_result else 0
            
            # Contar embeddings
            embeddings_result = self.client.table('chunk_embeddings').select("count", count="exact").execute()
            embeddings_count = embeddings_result.count if embeddings_result else 0
            
            return {
                "documents": docs_count,
                "chunks": chunks_count,
                "embeddings": embeddings_count
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Subir embeddings a Supabase")
    parser.add_argument("--file", required=True, help="Archivo de embeddings a subir")
    parser.add_argument("--stats", action="store_true", help="Mostrar estadísticas")
    
    args = parser.parse_args()
    
    try:
        uploader = SupabaseUploader()
        
        if args.stats:
            stats = uploader.get_stats()
            print("📊 Estadísticas de Supabase:")
            print(f"  📄 Documentos: {stats.get('documents', 0)}")
            print(f"  📝 Chunks: {stats.get('chunks', 0)}")
            print(f"  🔢 Embeddings: {stats.get('embeddings', 0)}")
            return
        
        # Cargar archivo de embeddings
        embeddings_file = Path(f"data/processed/embeddings/{args.file}")
        
        if not embeddings_file.exists():
            print(f"❌ Archivo no encontrado: {args.file}")
            return
        
        with open(embeddings_file, 'r', encoding='utf-8') as f:
            embeddings_data = json.load(f)
        
        print(f"📄 Cargando: {args.file}")
        print(f"📊 Chunks: {len(embeddings_data)}")
        
        # Subir a Supabase
        success = uploader.upload_document_embeddings(embeddings_data)
        
        if success:
            print("🎉 ¡Subida exitosa!")
            
            # Mostrar estadísticas actualizadas
            stats = uploader.get_stats()
            print("\n📊 Estadísticas actualizadas:")
            print(f"  📄 Documentos: {stats.get('documents', 0)}")
            print(f"  📝 Chunks: {stats.get('chunks', 0)}")
            print(f"  🔢 Embeddings: {stats.get('embeddings', 0)}")
        else:
            print("❌ Error en la subida")
            
    except ValueError as e:
        print(f"❌ Error de configuración: {e}")
        print("Verifica las variables SUPABASE_URL y SUPABASE_ANON_KEY en .env")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()