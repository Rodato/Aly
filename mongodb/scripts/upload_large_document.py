#!/usr/bin/env python3
"""
Upload Large Document - Sube documentos grandes a MongoDB por lotes
"""

import json
import logging
import os
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LargeDocumentUploader:
    """Subidor de documentos grandes por lotes."""
    
    def __init__(self):
        self.uri = os.getenv("MONGODB_URI")
        self.db_name = os.getenv("MONGODB_DB_NAME")
        self.collection_name = os.getenv("MONGODB_COLLECTION_NAME")
        
        if not all([self.uri, self.db_name, self.collection_name]):
            raise ValueError("Variables MongoDB no configuradas")
        
        # Conectar a MongoDB
        self.client = MongoClient(self.uri)
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]
        
        logger.info(f"📡 Conectado a MongoDB: {self.db_name}.{self.collection_name}")
    
    def upload_document_in_batches(self, embeddings_data: list, document_name: str, batch_size: int = 10) -> bool:
        """Sube documento en lotes pequeños."""
        if not embeddings_data:
            logger.error("No hay datos para subir")
            return False
        
        logger.info(f"📤 Subiendo {document_name} en lotes de {batch_size}")
        logger.info(f"📊 Total chunks: {len(embeddings_data)}")
        
        total_batches = (len(embeddings_data) + batch_size - 1) // batch_size
        successful_chunks = 0
        
        try:
            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, len(embeddings_data))
                batch_data = embeddings_data[start_idx:end_idx]
                
                logger.info(f"📦 Lote {batch_num + 1}/{total_batches}: chunks {start_idx + 1}-{end_idx}")
                
                # Preparar documentos para este lote
                documents_to_insert = []
                
                for item in batch_data:
                    chunk_data = item["chunk_data"]
                    chunk_metadata = chunk_data["metadata"]
                    embedding = item["embedding"]
                    embedding_text = item.get("embedding_text", "")
                    
                    # Verificar si ya existe
                    existing = self.collection.find_one({"chunk_id": chunk_metadata["chunk_id"]})
                    if existing:
                        logger.info(f"⚠️  Chunk ya existe: {chunk_metadata['chunk_id']}")
                        continue
                    
                    # Documento para MongoDB
                    mongo_doc = {
                        # Identificación
                        "document_name": document_name,
                        "chunk_id": chunk_metadata["chunk_id"],
                        "chunk_index": chunk_metadata["chunk_index"],
                        
                        # Metadatos del documento  
                        "document_source": chunk_metadata["document_source"],
                        "document_title": chunk_metadata["document_title"],
                        "document_type": chunk_metadata["document_type"],
                        
                        # Contenido del chunk
                        "content": chunk_data["content"],
                        "section_header": chunk_metadata["section_header"],
                        "content_type": chunk_metadata["content_type"],
                        
                        # Métricas
                        "text_length": chunk_metadata["text_length"],
                        "word_count": chunk_metadata["word_count"],
                        "total_chunks": chunk_metadata["total_chunks"],
                        
                        # Vector embedding
                        "embedding": embedding,
                        "embedding_text": embedding_text,
                        "embedding_model": "text-embedding-ada-002",
                        
                        # Metadatos adicionales
                        "has_code": chunk_metadata.get("has_code", False),
                        "has_numbers": chunk_metadata.get("has_numbers", False),
                        "has_bullets": chunk_metadata.get("has_bullets", False),
                        "has_tables": chunk_metadata.get("has_tables", False),
                        "has_images": chunk_metadata.get("has_images", False),
                        
                        # Contexto
                        "parent_section": chunk_metadata.get("parent_section"),
                        "previous_chunk": chunk_metadata.get("previous_chunk"),
                        "next_chunk": chunk_metadata.get("next_chunk"),
                        
                        # Timestamps
                        "processed_at": chunk_metadata.get("processed_at"),
                        "chunk_hash": chunk_metadata.get("chunk_hash")
                    }
                    
                    documents_to_insert.append(mongo_doc)
                
                # Insertar lote si tiene documentos
                if documents_to_insert:
                    try:
                        result = self.collection.insert_many(documents_to_insert)
                        batch_inserted = len(result.inserted_ids)
                        successful_chunks += batch_inserted
                        logger.info(f"✅ Lote insertado: {batch_inserted} chunks")
                        
                    except Exception as e:
                        logger.error(f"❌ Error en lote {batch_num + 1}: {e}")
                        # Intentar insertar uno por uno
                        logger.info("🔄 Intentando inserción individual...")
                        for doc in documents_to_insert:
                            try:
                                self.collection.insert_one(doc)
                                successful_chunks += 1
                            except Exception as doc_error:
                                logger.error(f"❌ Error insertando chunk individual: {doc_error}")
                else:
                    logger.info(f"⚠️  Lote {batch_num + 1} vacío (chunks ya existían)")
            
            logger.info(f"✅ Subida completada: {successful_chunks}/{len(embeddings_data)} chunks")
            return successful_chunks > 0
            
        except Exception as e:
            logger.error(f"❌ Error general en subida: {e}")
            return False
    
    def close(self):
        """Cierra conexión."""
        if hasattr(self, 'client'):
            self.client.close()


def main():
    """Función principal."""
    try:
        uploader = LargeDocumentUploader()
        
        # Subir Manual GBI México
        embeddings_file = Path("data/processed/embeddings/MANUAL Borrador GBI Mexico _embeddings.json")
        
        if not embeddings_file.exists():
            print(f"❌ Archivo no encontrado: {embeddings_file}")
            return
        
        print(f"📄 Cargando: {embeddings_file.name}")
        
        with open(embeddings_file, 'r', encoding='utf-8') as f:
            embeddings_data = json.load(f)
        
        print(f"📊 Chunks a subir: {len(embeddings_data)}")
        
        # Extraer título del primer chunk
        if embeddings_data:
            first_chunk = embeddings_data[0]["chunk_data"]
            document_title = first_chunk["metadata"].get("document_title", "Manual GBI México")
            print(f"📝 Título: {document_title}")
        
        # Subir en lotes pequeños  
        document_name = "MANUAL Borrador GBI Mexico"
        success = uploader.upload_document_in_batches(embeddings_data, document_name, batch_size=5)
        
        if success:
            print("🎉 ¡Subida exitosa!")
        else:
            print("❌ Error en la subida")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        if 'uploader' in locals():
            uploader.close()


if __name__ == "__main__":
    main()