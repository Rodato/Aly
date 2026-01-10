#!/usr/bin/env python3
"""
Upload to MongoDB - Puddle Assistant
Sube embeddings generados a MongoDB con vector search
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

class MongoUploader:
    """Subidor de embeddings a MongoDB Atlas."""
    
    def __init__(self):
        self.uri = os.getenv("MONGODB_URI")
        self.db_name = os.getenv("MONGODB_DB_NAME")
        self.collection_name = os.getenv("MONGODB_COLLECTION_NAME")
        
        if not all([self.uri, self.db_name, self.collection_name]):
            raise ValueError("Variables MongoDB no configuradas en .env")
        
        # Conectar a MongoDB
        self.client = MongoClient(self.uri)
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]
        
        logger.info(f"📡 Conectado a MongoDB: {self.db_name}.{self.collection_name}")
    
    def upload_document_embeddings(self, embeddings_data: list, document_name: str) -> bool:
        """Sube un documento completo con embeddings a MongoDB."""
        if not embeddings_data:
            logger.error("No hay datos para subir")
            return False
        
        logger.info(f"📤 Subiendo {document_name} con {len(embeddings_data)} chunks...")
        
        try:
            # Preparar documentos para MongoDB
            documents_to_insert = []
            
            for i, item in enumerate(embeddings_data):
                chunk_data = item["chunk_data"]
                chunk_metadata = chunk_data["metadata"]
                embedding = item["embedding"]
                embedding_text = item.get("embedding_text", "")
                
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
            
            # Insertar en batch
            result = self.collection.insert_many(documents_to_insert)
            
            logger.info(f"✅ Subida completada: {len(result.inserted_ids)} chunks insertados")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en subida: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Obtiene estadísticas de la base de datos MongoDB."""
        try:
            # Contar documentos totales
            total_chunks = self.collection.count_documents({})
            
            # Contar documentos únicos
            unique_docs = len(self.collection.distinct("document_name"))
            
            # Obtener lista de documentos
            doc_pipeline = [
                {"$group": {
                    "_id": "$document_name", 
                    "chunks": {"$sum": 1},
                    "document_title": {"$first": "$document_title"}
                }}
            ]
            
            docs_info = list(self.collection.aggregate(doc_pipeline))
            
            return {
                "total_chunks": total_chunks,
                "unique_documents": unique_docs,
                "documents": docs_info
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def close(self):
        """Cierra la conexión."""
        if hasattr(self, 'client'):
            self.client.close()


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Subir embeddings a MongoDB")
    parser.add_argument("--file", help="Archivo de embeddings a subir")
    parser.add_argument("--stats", action="store_true", help="Mostrar estadísticas")
    parser.add_argument("--all", action="store_true", help="Subir todos los archivos")
    
    args = parser.parse_args()
    
    try:
        uploader = MongoUploader()
        
        if args.stats:
            stats = uploader.get_stats()
            print("📊 Estadísticas de MongoDB:")
            print(f"  📄 Documentos únicos: {stats.get('unique_documents', 0)}")
            print(f"  📝 Total chunks: {stats.get('total_chunks', 0)}")
            print("\n📋 Detalle por documento:")
            for doc in stats.get('documents', []):
                print(f"  📄 {doc['_id']}: {doc['chunks']} chunks")
                print(f"      Título: {doc['document_title']}")
            return
        
        if args.all:
            # Subir todos los archivos de embeddings
            embeddings_dir = Path("data/processed/embeddings")
            embedding_files = list(embeddings_dir.glob("*_embeddings.json"))
            
            print(f"📁 Encontrados {len(embedding_files)} archivos de embeddings")
            
            for embedding_file in embedding_files:
                if "backup_" in embedding_file.name:
                    continue  # Saltar backups
                    
                print(f"\n📤 Procesando: {embedding_file.name}")
                
                with open(embedding_file, 'r', encoding='utf-8') as f:
                    embeddings_data = json.load(f)
                
                # Extraer nombre del documento del archivo
                document_name = embedding_file.stem.replace("_embeddings", "")
                
                success = uploader.upload_document_embeddings(embeddings_data, document_name)
                
                if success:
                    print(f"✅ {document_name}: {len(embeddings_data)} chunks subidos")
                else:
                    print(f"❌ {document_name}: Error en subida")
            
            # Mostrar estadísticas finales
            print("\n📊 Estadísticas finales:")
            stats = uploader.get_stats()
            print(f"  📄 Documentos: {stats.get('unique_documents', 0)}")
            print(f"  📝 Total chunks: {stats.get('total_chunks', 0)}")
            
        elif args.file:
            # Subir archivo específico
            embeddings_file = Path(f"data/processed/embeddings/{args.file}")
            
            if not embeddings_file.exists():
                print(f"❌ Archivo no encontrado: {args.file}")
                return
            
            with open(embeddings_file, 'r', encoding='utf-8') as f:
                embeddings_data = json.load(f)
            
            # Extraer nombre del documento
            document_name = embeddings_file.stem.replace("_embeddings", "")
            
            print(f"📄 Cargando: {args.file}")
            print(f"📊 Chunks: {len(embeddings_data)}")
            
            success = uploader.upload_document_embeddings(embeddings_data, document_name)
            
            if success:
                print("🎉 ¡Subida exitosa!")
                
                # Mostrar estadísticas
                stats = uploader.get_stats()
                print(f"\n📊 Estadísticas:")
                print(f"  📄 Documentos: {stats.get('unique_documents', 0)}")
                print(f"  📝 Total chunks: {stats.get('total_chunks', 0)}")
            else:
                print("❌ Error en la subida")
        
        else:
            print("Usa --file <archivo>, --all, o --stats")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        if 'uploader' in locals():
            uploader.close()


if __name__ == "__main__":
    main()