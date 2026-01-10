#!/usr/bin/env python3
"""
Embedding Generator - Puddle Assistant
Genera embeddings para chunks usando OpenRouter API
"""

import json
import time
import logging
import requests
from pathlib import Path
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
from enhanced_chunker import EnhancedChunker, EnhancedDocumentChunk

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Generador de embeddings usando OpenRouter."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY no encontrada")
        
        self.base_url = "https://openrouter.ai/api/v1/embeddings"
        self.model = "openai/text-embedding-ada-002"
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Configuración de rate limiting
        self.requests_per_minute = 60
        self.request_interval = 60 / self.requests_per_minute
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Controla rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval:
            sleep_time = self.request_interval - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def generate_embedding(self, text: str, retries: int = 3) -> Optional[List[float]]:
        """Genera embedding para un texto."""
        # Limpiar y truncar texto si es muy largo
        clean_text = text.strip()[:8000]  # Límite de tokens
        
        data = {
            "model": self.model,
            "input": clean_text
        }
        
        for attempt in range(retries):
            try:
                self._rate_limit()
                
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["data"][0]["embedding"]
                    
                elif response.status_code == 429:  # Rate limit
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limit, esperando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                    
                else:
                    logger.error(f"Error {response.status_code}: {response.text}")
                    if attempt < retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return None
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout en intento {attempt + 1}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return None
                
            except Exception as e:
                logger.error(f"Error generando embedding: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return None
        
        return None
    
    def generate_batch_embeddings(self, texts: List[str], batch_size: int = 10) -> List[Optional[List[float]]]:
        """Genera embeddings en lotes."""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"Procesando lote {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
            
            batch_embeddings = []
            for text in batch:
                embedding = self.generate_embedding(text)
                batch_embeddings.append(embedding)
                
                # Pausa entre requests del lote
                time.sleep(0.1)
            
            embeddings.extend(batch_embeddings)
        
        return embeddings

class ChunkEmbeddingProcessor:
    """Procesador completo de chunks a embeddings."""
    
    def __init__(self):
        self.chunker = EnhancedChunker(enable_summaries=True)
        self.embedding_generator = EmbeddingGenerator()
    
    def create_embedding_text(self, chunk: EnhancedDocumentChunk) -> str:
        """Crea texto optimizado para embedding combinando contenido y metadatos."""
        # Combinar información relevante para el embedding
        parts = []
        
        # Título del documento
        parts.append(f"Documento: {chunk.metadata.document_title}")
        
        # Resumen del documento para contexto
        if chunk.metadata.document_summary:
            parts.append(f"Contexto: {chunk.metadata.document_summary}")
        
        # Sección actual
        parts.append(f"Sección: {chunk.metadata.section_header}")
        
        # Resumen del chunk específico
        if chunk.metadata.chunk_summary:
            parts.append(f"Resumen: {chunk.metadata.chunk_summary}")
        
        # Contenido principal
        parts.append(f"Contenido: {chunk.content}")
        
        # Palabras clave si están disponibles
        if chunk.metadata.keywords:
            parts.append(f"Palabras clave: {', '.join(chunk.metadata.keywords)}")
        
        return "\n".join(parts)
    
    def process_document(self, file_path: Path) -> List[Dict]:
        """Procesa un documento completo: chunking + embeddings."""
        logger.info(f"Procesando documento completo: {file_path.name}")
        
        # 1. Generar chunks con metadatos enriquecidos
        chunks = self.chunker.chunk_document(file_path)
        
        if not chunks:
            logger.warning(f"No se generaron chunks para {file_path.name}")
            return []
        
        logger.info(f"Generados {len(chunks)} chunks, creando embeddings...")
        
        # 2. Crear textos optimizados para embeddings
        embedding_texts = []
        for chunk in chunks:
            embedding_text = self.create_embedding_text(chunk)
            embedding_texts.append(embedding_text)
        
        # 3. Generar embeddings
        embeddings = self.embedding_generator.generate_batch_embeddings(embedding_texts)
        
        # 4. Combinar chunks con embeddings
        results = []
        successful_embeddings = 0
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            if embedding is not None:
                result = {
                    'chunk_data': chunk.to_dict(),
                    'embedding': embedding,
                    'embedding_text': embedding_texts[i]
                }
                results.append(result)
                successful_embeddings += 1
            else:
                logger.warning(f"Embedding falló para chunk {i}: {chunk.metadata.chunk_id}")
        
        logger.info(f"Completado: {successful_embeddings}/{len(chunks)} embeddings exitosos")
        return results
    
    def process_all_documents(self, 
                            input_path: str = "data/processed/DocsMD",
                            output_path: str = "data/processed/embeddings") -> List[Dict]:
        """Procesa todos los documentos y guarda resultados."""
        input_dir = Path(input_path)
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        md_files = list(input_dir.glob("*.md"))
        logger.info(f"Encontrados {len(md_files)} documentos para procesar")
        
        all_results = []
        
        for i, md_file in enumerate(md_files, 1):
            logger.info(f"[{i}/{len(md_files)}] Procesando {md_file.name}")
            
            try:
                results = self.process_document(md_file)
                
                if results:
                    # Guardar resultados individuales
                    output_file = output_dir / f"{md_file.stem}_embeddings.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"Guardado: {output_file.name} con {len(results)} chunks")
                    all_results.extend(results)
                else:
                    logger.warning(f"No se generaron resultados para {md_file.name}")
                    
            except Exception as e:
                logger.error(f"Error procesando {md_file.name}: {e}")
                continue
        
        # Guardar resumen consolidado
        summary_file = output_dir / "embeddings_summary.json"
        summary = {
            "total_documents": len(md_files),
            "total_chunks": len(all_results),
            "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "documents": [
                {
                    "source": result['chunk_data']['metadata']['document_source'],
                    "title": result['chunk_data']['metadata']['document_title'],
                    "type": result['chunk_data']['metadata']['document_type'],
                    "chunks": 1
                }
                for result in all_results[:10]  # Primeros 10 como ejemplo
            ]
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Procesamiento completado:")
        logger.info(f"  📄 Documentos: {len(md_files)}")
        logger.info(f"  📊 Total chunks: {len(all_results)}")
        logger.info(f"  💾 Embeddings guardados en: {output_dir}")
        
        return all_results
    
    def get_processing_stats(self) -> Dict:
        """Obtiene estadísticas del procesamiento."""
        embeddings_dir = Path("data/processed/embeddings")
        
        if not embeddings_dir.exists():
            return {"status": "no_processed"}
        
        embedding_files = list(embeddings_dir.glob("*_embeddings.json"))
        
        stats = {
            "embedding_files": len(embedding_files),
            "total_chunks": 0,
            "documents": []
        }
        
        for file in embedding_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    stats["total_chunks"] += len(data)
                    
                    if data:
                        doc_info = {
                            "file": file.name,
                            "chunks": len(data),
                            "title": data[0]['chunk_data']['metadata']['document_title'],
                            "type": data[0]['chunk_data']['metadata']['document_type']
                        }
                        stats["documents"].append(doc_info)
                        
            except Exception as e:
                logger.warning(f"Error leyendo {file}: {e}")
        
        return stats


def main():
    """Función principal para testing y procesamiento."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generador de embeddings")
    parser.add_argument("--single", help="Procesar un solo archivo")
    parser.add_argument("--all", action="store_true", help="Procesar todos los documentos")
    parser.add_argument("--stats", action="store_true", help="Mostrar estadísticas")
    
    args = parser.parse_args()
    
    processor = ChunkEmbeddingProcessor()
    
    if args.stats:
        stats = processor.get_processing_stats()
        print("📊 Estadísticas de Embeddings:")
        print(f"  Archivos procesados: {stats.get('embedding_files', 0)}")
        print(f"  Total chunks: {stats.get('total_chunks', 0)}")
        
        for doc in stats.get('documents', []):
            print(f"  📄 {doc['title']}: {doc['chunks']} chunks")
    
    elif args.single:
        file_path = Path(f"data/processed/DocsMD/{args.single}")
        if file_path.exists():
            results = processor.process_document(file_path)
            print(f"✅ Procesado: {len(results)} chunks con embeddings")
        else:
            print(f"❌ Archivo no encontrado: {args.single}")
    
    elif args.all:
        results = processor.process_all_documents()
        print(f"✅ Procesamiento completo: {len(results)} chunks totales")
    
    else:
        print("Usa --single <archivo>, --all, o --stats")


if __name__ == "__main__":
    main()