#!/usr/bin/env python3
"""
Simple OpenAI Embeddings - Puddle Assistant
Versión simplificada usando requests directamente a OpenAI API
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

load_dotenv()
logging.basicConfig(level=logging.INFO)
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
                logger.warning("Rate limit, esperando...")
                time.sleep(1)
                return self.generate_embedding(text)  # Reintentar
            else:
                logger.error(f"Error OpenAI {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            return None
    
    def generate_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Genera embeddings para una lista de textos."""
        embeddings = []
        
        for i, text in enumerate(texts):
            if i % 10 == 0:
                logger.info(f"Procesando {i+1}/{len(texts)}...")
            
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)
            
            # Pausa pequeña para evitar rate limits
            time.sleep(0.1)
        
        return embeddings

class SimpleProcessor:
    """Procesador simple de documentos a embeddings."""
    
    def __init__(self):
        self.chunker = EnhancedChunker(enable_summaries=False)  # Sin resúmenes para velocidad
        self.embedder = SimpleOpenAIEmbeddings()
    
    def create_embedding_text(self, chunk) -> str:
        """Crea texto optimizado para embedding."""
        parts = [
            f"Documento: {chunk.metadata.document_title}",
            f"Sección: {chunk.metadata.section_header}",
            f"Contenido: {chunk.content}"
        ]
        return "\n".join(parts)
    
    def process_document(self, file_path: Path) -> List[Dict]:
        """Procesa un documento completo."""
        logger.info(f"🚀 Procesando: {file_path.name}")
        
        # Generar chunks
        chunks = self.chunker.chunk_document(file_path)
        if not chunks:
            return []
        
        logger.info(f"📝 Generados {len(chunks)} chunks")
        
        # Crear textos para embeddings
        embedding_texts = [self.create_embedding_text(chunk) for chunk in chunks]
        
        # Generar embeddings
        logger.info("🔢 Generando embeddings...")
        start_time = time.time()
        embeddings = self.embedder.generate_batch(embedding_texts)
        end_time = time.time()
        
        logger.info(f"⚡ Completado en {end_time - start_time:.1f}s")
        
        # Combinar resultados
        results = []
        for chunk, embedding, embedding_text in zip(chunks, embeddings, embedding_texts):
            if embedding:
                results.append({
                    'chunk_data': chunk.to_dict(),
                    'embedding': embedding,
                    'embedding_text': embedding_text
                })
        
        logger.info(f"✅ {len(results)} embeddings exitosos de {len(chunks)} chunks")
        return results
    
    def save_results(self, results: List[Dict], output_path: Path):
        """Guarda resultados en archivo JSON."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Guardado: {output_path}")


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple OpenAI Embeddings")
    parser.add_argument("--single", required=True, help="Archivo a procesar")
    
    args = parser.parse_args()
    
    # Configurar paths
    input_file = Path(f"data/processed/DocsMD/{args.single}")
    output_dir = Path("data/processed/embeddings")
    output_file = output_dir / f"{input_file.stem}_embeddings.json"
    
    if not input_file.exists():
        print(f"❌ Archivo no encontrado: {args.single}")
        return
    
    # Procesar
    try:
        processor = SimpleProcessor()
        results = processor.process_document(input_file)
        
        if results:
            processor.save_results(results, output_file)
            print(f"🎉 Completado:")
            print(f"  📄 Archivo: {args.single}")
            print(f"  📊 Chunks: {len(results)}")
            print(f"  💾 Guardado: {output_file}")
        else:
            print("❌ No se generaron resultados")
            
    except ValueError as e:
        print(f"❌ Error de configuración: {e}")
        print("Verifica que OPENAI_API_KEY esté en tu .env")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()