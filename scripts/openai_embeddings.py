#!/usr/bin/env python3
"""
OpenAI Embeddings Generator - Puddle Assistant
Genera embeddings usando directamente la API de OpenAI
"""

import json
import time
import logging
import os
from typing import List, Dict, Optional
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from enhanced_chunker import EnhancedChunker, EnhancedDocumentChunk

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIEmbeddingGenerator:
    """Generador de embeddings usando OpenAI API v1.0+."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY no encontrada en .env")
        
        # Configurar cliente OpenAI v1.0+
        self.client = OpenAI(api_key=self.api_key)
        self.model = "text-embedding-ada-002"
        
        # Rate limiting más generoso para OpenAI
        self.requests_per_minute = 3000  # OpenAI permite mucho más
        self.request_interval = 60 / self.requests_per_minute
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Controla rate limiting básico."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval:
            sleep_time = self.request_interval - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def generate_embedding(self, text: str, retries: int = 3) -> Optional[List[float]]:
        """Genera embedding para un texto usando OpenAI v1.0+."""
        # Limpiar y truncar texto
        clean_text = text.strip()[:8000]  # Límite conservador
        
        for attempt in range(retries):
            try:
                self._rate_limit()
                
                response = self.client.embeddings.create(
                    input=clean_text,
                    model=self.model
                )
                
                return response.data[0].embedding
                
            except Exception as e:
                error_str = str(e)
                if "rate_limit" in error_str.lower():
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limit OpenAI, esperando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                elif "api" in error_str.lower():
                    logger.error(f"Error API OpenAI: {e}")
                    if attempt < retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return None
                else:
                    logger.error(f"Error generando embedding: {e}")
                    if attempt < retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return None
        
        return None
    
    def generate_batch_embeddings(self, texts: List[str], batch_size: int = 100) -> List[Optional[List[float]]]:
        """Genera embeddings en lotes usando OpenAI."""
        embeddings = []
        
        # OpenAI permite lotes más grandes
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"Procesando lote {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1} ({len(batch)} textos)")
            
            try:
                # Procesar lote completo de una vez
                self._rate_limit()
                
                response = self.client.embeddings.create(
                    input=batch,
                    model=self.model
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
                
                logger.info(f"✅ Lote completado: {len(batch_embeddings)} embeddings")
                
            except Exception as e:
                logger.error(f"Error en lote {i//batch_size + 1}: {e}")
                # Fallback: procesar individualmente
                logger.info("Intentando procesamiento individual...")
                
                batch_embeddings = []
                for text in batch:
                    embedding = self.generate_embedding(text)
                    batch_embeddings.append(embedding)
                
                embeddings.extend(batch_embeddings)
        
        return embeddings


class FastChunkEmbeddingProcessor:
    """Procesador optimizado de chunks a embeddings usando OpenAI."""
    
    def __init__(self, enable_summaries: bool = False):
        # Chunker sin resúmenes para más velocidad
        self.chunker = EnhancedChunker(enable_summaries=enable_summaries)
        self.embedding_generator = OpenAIEmbeddingGenerator()
    
    def create_embedding_text(self, chunk: EnhancedDocumentChunk) -> str:
        """Crea texto optimizado para embedding."""
        parts = []
        
        # Información esencial para el embedding
        parts.append(f"Documento: {chunk.metadata.document_title}")
        parts.append(f"Sección: {chunk.metadata.section_header}")
        
        # Solo agregar resúmenes si están disponibles
        if chunk.metadata.document_summary:
            parts.append(f"Contexto: {chunk.metadata.document_summary}")
        
        if chunk.metadata.chunk_summary:
            parts.append(f"Resumen: {chunk.metadata.chunk_summary}")
        
        # Contenido principal
        parts.append(f"Contenido: {chunk.content}")
        
        return "\n".join(parts)
    
    def process_document(self, file_path: Path) -> List[Dict]:
        """Procesa un documento completo: chunking + embeddings rápidos."""
        logger.info(f"🚀 Procesando documento: {file_path.name}")
        
        # 1. Generar chunks (con o sin resúmenes según configuración)
        chunks = self.chunker.chunk_document(file_path)
        
        if not chunks:
            logger.warning(f"No se generaron chunks para {file_path.name}")
            return []
        
        logger.info(f"📝 Generados {len(chunks)} chunks, creando embeddings...")
        
        # 2. Crear textos para embeddings
        embedding_texts = []
        for chunk in chunks:
            embedding_text = self.create_embedding_text(chunk)
            embedding_texts.append(embedding_text)
        
        # 3. Generar embeddings en lotes (más rápido)
        start_time = time.time()
        embeddings = self.embedding_generator.generate_batch_embeddings(embedding_texts, batch_size=50)
        embedding_time = time.time() - start_time
        
        logger.info(f"⚡ Embeddings completados en {embedding_time:.1f}s")
        
        # 4. Combinar resultados
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
                logger.warning(f"Embedding falló para chunk {i}")
        
        logger.info(f"✅ Completado: {successful_embeddings}/{len(chunks)} embeddings exitosos")
        return results
    
    def process_all_documents(self, 
                            input_path: str = "data/processed/DocsMD",
                            output_path: str = "data/processed/embeddings") -> List[Dict]:
        """Procesa todos los documentos rápidamente."""
        input_dir = Path(input_path)
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        md_files = list(input_dir.glob("*.md"))
        logger.info(f"📄 Procesando {len(md_files)} documentos con OpenAI...")
        
        all_results = []
        
        for i, md_file in enumerate(md_files, 1):
            logger.info(f"[{i}/{len(md_files)}] {md_file.name}")
            
            try:
                results = self.process_document(md_file)
                
                if results:
                    # Guardar resultados individuales
                    output_file = output_dir / f"{md_file.stem}_embeddings.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"💾 Guardado: {output_file.name}")
                    all_results.extend(results)
                    
            except Exception as e:
                logger.error(f"❌ Error procesando {md_file.name}: {e}")
                continue
        
        # Guardar resumen consolidado
        summary = {
            "total_documents": len(md_files),
            "total_chunks": len(all_results),
            "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "embedding_model": "text-embedding-ada-002",
            "api_provider": "openai_direct"
        }
        
        summary_file = output_dir / "embeddings_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"🎉 Procesamiento completado:")
        logger.info(f"  📄 Documentos: {len(md_files)}")
        logger.info(f"  📊 Total chunks: {len(all_results)}")
        logger.info(f"  💾 Guardado en: {output_dir}")
        
        return all_results


def main():
    """Función principal para testing rápido."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generador de embeddings OpenAI")
    parser.add_argument("--single", help="Procesar un solo archivo")
    parser.add_argument("--all", action="store_true", help="Procesar todos los documentos")
    parser.add_argument("--fast", action="store_true", help="Modo rápido (sin resúmenes)")
    parser.add_argument("--stats", action="store_true", help="Mostrar estadísticas")
    
    args = parser.parse_args()
    
    # Configurar procesador
    enable_summaries = not args.fast
    processor = FastChunkEmbeddingProcessor(enable_summaries=enable_summaries)
    
    if args.stats:
        embeddings_dir = Path("data/processed/embeddings")
        if embeddings_dir.exists():
            files = list(embeddings_dir.glob("*_embeddings.json"))
            total_chunks = 0
            
            print("📊 Estadísticas de Embeddings OpenAI:")
            print(f"  Archivos procesados: {len(files)}")
            
            for file in files:
                with open(file, 'r') as f:
                    data = json.load(f)
                    total_chunks += len(data)
                    print(f"    📄 {file.stem}: {len(data)} chunks")
            
            print(f"  📝 Total chunks: {total_chunks}")
        else:
            print("❌ No hay embeddings procesados")
    
    elif args.single:
        file_path = Path(f"data/processed/DocsMD/{args.single}")
        if file_path.exists():
            start_time = time.time()
            results = processor.process_document(file_path)
            total_time = time.time() - start_time
            
            print(f"✅ Procesado en {total_time:.1f}s:")
            print(f"  📄 Archivo: {args.single}")
            print(f"  📊 Chunks: {len(results)}")
            print(f"  ⚡ Modo: {'Con resúmenes' if enable_summaries else 'Rápido'}")
        else:
            print(f"❌ Archivo no encontrado: {args.single}")
    
    elif args.all:
        start_time = time.time()
        results = processor.process_all_documents()
        total_time = time.time() - start_time
        
        print(f"🎉 Procesamiento completo en {total_time:.1f}s:")
        print(f"  📄 Total chunks: {len(results)}")
        print(f"  ⚡ Modo: {'Con resúmenes' if enable_summaries else 'Rápido'}")
    
    else:
        print("Usa --single <archivo>, --all, --fast, o --stats")


if __name__ == "__main__":
    main()