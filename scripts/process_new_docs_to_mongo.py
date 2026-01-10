#!/usr/bin/env python3
"""
Process New Docs to MongoDB - Puddle Assistant
Procesa documentos nuevos (no procesados) y los sube directamente a MongoDB
"""

import json
import time
import logging
import os
import requests
from typing import List, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv
from enhanced_chunker import EnhancedChunker
from pymongo import MongoClient

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleOpenAIEmbeddings:
    """Generador simple de embeddings usando requests a OpenAI API."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY no encontrada en .env")
        
        self.base_url = "https://api.openai.com/v1/embeddings"
        self.model = "text-embedding-ada-002"
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Genera embedding para un texto."""
        clean_text = text.strip()[:8000]  # Límite conservador
        
        data = {
            "model": self.model,
            "input": clean_text
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["data"][0]["embedding"]
            elif response.status_code == 429:
                logger.warning("Rate limit, esperando 2s...")
                time.sleep(2)
                return self.generate_embedding(text)  # Reintentar
            else:
                logger.error(f"Error OpenAI {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            return None


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
    
    def get_processed_documents(self) -> set:
        """Obtiene lista de documentos ya procesados en MongoDB."""
        try:
            processed_docs = set(self.collection.distinct("document_name"))
            logger.info(f"📋 Documentos ya en MongoDB: {len(processed_docs)}")
            return processed_docs
        except Exception as e:
            logger.error(f"Error obteniendo documentos procesados: {e}")
            return set()
    
    def upload_document_chunks(self, embedding_data: list, document_name: str) -> bool:
        """Sube un documento completo con embeddings a MongoDB."""
        if not embedding_data:
            logger.error("No hay datos para subir")
            return False
        
        logger.info(f"📤 Subiendo {document_name} con {len(embedding_data)} chunks...")
        
        try:
            # Preparar documentos para MongoDB
            documents_to_insert = []
            
            for i, item in enumerate(embedding_data):
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


class NewDocProcessor:
    """Procesador de documentos nuevos directo a MongoDB."""
    
    def __init__(self):
        self.chunker = EnhancedChunker(enable_summaries=False)  # Sin resúmenes para velocidad
        self.embedder = SimpleOpenAIEmbeddings()
        self.mongo_uploader = MongoUploader()
    
    def create_embedding_text(self, chunk) -> str:
        """Crea texto optimizado para embedding."""
        parts = [
            f"Documento: {chunk.metadata.document_title}",
            f"Sección: {chunk.metadata.section_header}",
            f"Contenido: {chunk.content}"
        ]
        return "\n".join(parts)
    
    def process_document(self, file_path: Path, document_name: str) -> bool:
        """Procesa un documento completo y lo sube a MongoDB."""
        logger.info(f"🚀 Procesando: {file_path.name}")
        
        try:
            # 1. Generar chunks
            chunks = self.chunker.chunk_document(file_path)
            if not chunks:
                logger.warning(f"No se generaron chunks para {file_path.name}")
                return False
            
            logger.info(f"📝 Generados {len(chunks)} chunks")
            
            # 2. Crear textos para embeddings y generar embeddings
            logger.info("🔢 Generando embeddings...")
            start_time = time.time()
            
            embedding_data = []
            successful_embeddings = 0
            
            for i, chunk in enumerate(chunks):
                if i % 10 == 0:
                    logger.info(f"  Procesando chunk {i+1}/{len(chunks)}...")
                
                # Crear texto para embedding
                embedding_text = self.create_embedding_text(chunk)
                
                # Generar embedding
                embedding = self.embedder.generate_embedding(embedding_text)
                
                if embedding:
                    embedding_data.append({
                        'chunk_data': chunk.to_dict(),
                        'embedding': embedding,
                        'embedding_text': embedding_text
                    })
                    successful_embeddings += 1
                else:
                    logger.warning(f"Embedding falló para chunk {i}")
                
                # Pausa pequeña para evitar rate limits
                time.sleep(0.1)
            
            end_time = time.time()
            logger.info(f"⚡ Embeddings completados en {end_time - start_time:.1f}s")
            logger.info(f"✅ {successful_embeddings} embeddings exitosos de {len(chunks)} chunks")
            
            # 3. Subir a MongoDB
            if embedding_data:
                logger.info("📤 Subiendo a MongoDB...")
                upload_success = self.mongo_uploader.upload_document_chunks(embedding_data, document_name)
                
                if upload_success:
                    logger.info(f"🎉 {document_name} procesado y subido exitosamente")
                    
                    # También guardar copia local
                    backup_dir = Path("data/processed/embeddings")
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    backup_file = backup_dir / f"{file_path.stem}_embeddings.json"
                    
                    with open(backup_file, 'w', encoding='utf-8') as f:
                        json.dump(embedding_data, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"💾 Backup guardado: {backup_file.name}")
                    return True
                else:
                    logger.error(f"❌ Error subiendo {document_name} a MongoDB")
                    return False
            else:
                logger.error(f"❌ No se generaron embeddings válidos para {document_name}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Error procesando {document_name}: {e}")
            return False
    
    def process_new_documents(self, input_path: str = "data/processed/DocsMD") -> Dict:
        """Procesa todos los documentos nuevos (no procesados aún)."""
        logger.info("🚀 Iniciando procesamiento de documentos nuevos")
        
        # Obtener documentos ya procesados
        processed_docs = self.mongo_uploader.get_processed_documents()
        
        # Obtener todos los archivos MD
        input_dir = Path(input_path)
        md_files = list(input_dir.glob("*.md"))
        
        if not md_files:
            logger.warning(f"❌ No se encontraron archivos MD en {input_path}")
            return {"status": "no_files", "processed": 0, "errors": []}
        
        # Filtrar solo los no procesados
        new_files = []
        for md_file in md_files:
            # Extraer nombre del documento del archivo
            document_name = md_file.stem
            
            if document_name not in processed_docs:
                new_files.append((md_file, document_name))
            else:
                logger.info(f"⏭️  Saltando {document_name} (ya procesado)")
        
        if not new_files:
            logger.info("✅ Todos los documentos ya están procesados")
            return {"status": "all_processed", "processed": 0, "errors": []}
        
        logger.info(f"📄 Encontrados {len(new_files)} documentos nuevos para procesar")
        
        # Procesar cada documento nuevo
        results = {
            "status": "processing",
            "total_new": len(new_files),
            "processed": 0,
            "failed": 0,
            "errors": [],
            "processed_files": []
        }
        
        for i, (md_file, document_name) in enumerate(new_files, 1):
            logger.info(f"\n[{i}/{len(new_files)}] Procesando {document_name}")
            
            success = self.process_document(md_file, document_name)
            
            if success:
                results["processed"] += 1
                results["processed_files"].append(document_name)
            else:
                results["failed"] += 1
                results["errors"].append(f"Error procesando {document_name}")
        
        results["status"] = "completed"
        
        logger.info(f"\n🎉 Procesamiento completado:")
        logger.info(f"  📄 Documentos nuevos procesados: {results['processed']}")
        logger.info(f"  ❌ Documentos fallidos: {results['failed']}")
        logger.info(f"  📊 Total en MongoDB: {len(processed_docs) + results['processed']}")
        
        return results


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Procesar documentos nuevos a MongoDB")
    parser.add_argument("--all", action="store_true", help="Procesar todos los documentos nuevos")
    parser.add_argument("--single", help="Procesar un solo documento específico")
    parser.add_argument("--stats", action="store_true", help="Mostrar estadísticas")
    
    args = parser.parse_args()
    
    try:
        if args.stats:
            # Solo mostrar estadísticas
            mongo_uploader = MongoUploader()
            processed_docs = mongo_uploader.get_processed_documents()
            
            input_dir = Path("data/processed/DocsMD")
            md_files = list(input_dir.glob("*.md"))
            
            new_files = [f.stem for f in md_files if f.stem not in processed_docs]
            
            print("📊 Estado de procesamiento:")
            print(f"  📄 Total documentos disponibles: {len(md_files)}")
            print(f"  ✅ Ya procesados en MongoDB: {len(processed_docs)}")
            print(f"  🆕 Pendientes de procesar: {len(new_files)}")
            
            if new_files:
                print("\n📋 Documentos pendientes:")
                for doc in new_files[:10]:  # Mostrar solo primeros 10
                    print(f"  - {doc}")
                if len(new_files) > 10:
                    print(f"  ... y {len(new_files) - 10} más")
        
        elif args.single:
            processor = NewDocProcessor()
            file_path = Path(f"data/processed/DocsMD/{args.single}")
            
            if file_path.exists():
                document_name = file_path.stem
                success = processor.process_document(file_path, document_name)
                
                if success:
                    print(f"🎉 {args.single} procesado exitosamente")
                else:
                    print(f"❌ Error procesando {args.single}")
            else:
                print(f"❌ Archivo no encontrado: {args.single}")
        
        elif args.all:
            processor = NewDocProcessor()
            results = processor.process_new_documents()
            
            print(f"\n📊 Resumen final:")
            print(f"  Estado: {results['status']}")
            print(f"  📄 Documentos nuevos: {results['total_new']}")
            print(f"  ✅ Procesados exitosamente: {results['processed']}")
            print(f"  ❌ Fallidos: {results['failed']}")
            
            if results['errors']:
                print("\n❌ Errores:")
                for error in results['errors']:
                    print(f"  - {error}")
        
        else:
            print("Usa --all, --single <archivo>, o --stats")
            print("\nEjemplos:")
            print("  python3 scripts/process_new_docs_to_mongo.py --stats")
            print("  python3 scripts/process_new_docs_to_mongo.py --all")
            print("  python3 scripts/process_new_docs_to_mongo.py --single archivo.md")
            
    except ValueError as e:
        print(f"❌ Error de configuración: {e}")
        print("Verifica que OPENAI_API_KEY, MONGODB_URI, MONGODB_DB_NAME y MONGODB_COLLECTION_NAME estén en tu .env")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()