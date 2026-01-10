#!/usr/bin/env python3
"""
Complete Pipeline - Puddle Assistant
Pipeline completo: MD → Chunks → Embeddings → Supabase
"""

import json
import logging
from pathlib import Path
from typing import List, Dict
import argparse
from datetime import datetime

from enhanced_chunker import EnhancedChunker
from embedding_generator import EmbeddingGenerator, ChunkEmbeddingProcessor
from supabase_connector import SupabaseVectorStore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompletePipeline:
    """Pipeline completo de procesamiento de documentos."""
    
    def __init__(self, enable_supabase: bool = False):
        self.enable_supabase = enable_supabase
        
        # Componentes del pipeline
        self.chunker = EnhancedChunker(enable_summaries=True)
        self.embedding_processor = ChunkEmbeddingProcessor()
        
        # Supabase (opcional)
        self.supabase_store = None
        if enable_supabase:
            try:
                self.supabase_store = SupabaseVectorStore()
                logger.info("✅ Supabase habilitado")
            except Exception as e:
                logger.warning(f"⚠️ Supabase no disponible: {e}")
                self.enable_supabase = False
    
    def process_single_document(self, file_path: Path, upload_to_supabase: bool = False) -> Dict:
        """Procesa un solo documento a través del pipeline completo."""
        logger.info(f"🚀 Iniciando pipeline para: {file_path.name}")
        
        results = {
            "document": file_path.name,
            "status": "started",
            "chunks_generated": 0,
            "embeddings_created": 0,
            "uploaded_to_supabase": False,
            "errors": []
        }
        
        try:
            # 1. Chunking + Resúmenes
            logger.info("📝 Paso 1: Generando chunks con metadatos...")
            embedding_data = self.embedding_processor.process_document(file_path)
            
            if not embedding_data:
                results["errors"].append("No se generaron chunks válidos")
                results["status"] = "failed"
                return results
            
            results["chunks_generated"] = len(embedding_data)
            results["embeddings_created"] = len([e for e in embedding_data if e["embedding"] is not None])
            
            logger.info(f"✅ Generados {results['chunks_generated']} chunks con {results['embeddings_created']} embeddings")
            
            # 2. Guardar localmente
            output_dir = Path("data/processed/embeddings")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = output_dir / f"{file_path.stem}_embeddings.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(embedding_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Guardado localmente: {output_file}")
            
            # 3. Subir a Supabase (si está habilitado)
            if upload_to_supabase and self.enable_supabase and self.supabase_store:
                logger.info("📤 Paso 3: Subiendo a Supabase...")
                
                upload_success = self.supabase_store.upload_document_embeddings(embedding_data)
                results["uploaded_to_supabase"] = upload_success
                
                if upload_success:
                    logger.info("✅ Subida a Supabase exitosa")
                else:
                    results["errors"].append("Error subiendo a Supabase")
                    logger.warning("⚠️ Error en subida a Supabase")
            
            results["status"] = "completed"
            logger.info(f"🎉 Pipeline completado para {file_path.name}")
            
        except Exception as e:
            error_msg = f"Error en pipeline: {str(e)}"
            results["errors"].append(error_msg)
            results["status"] = "failed"
            logger.error(f"❌ {error_msg}")
        
        return results
    
    def process_all_documents(self, 
                            input_path: str = "data/processed/DocsMD",
                            upload_to_supabase: bool = False) -> Dict:
        """Procesa todos los documentos."""
        logger.info("🚀 Iniciando pipeline completo para todos los documentos")
        
        input_dir = Path(input_path)
        md_files = list(input_dir.glob("*.md"))
        
        if not md_files:
            logger.warning(f"❌ No se encontraron archivos MD en {input_path}")
            return {"status": "no_files", "files": []}
        
        logger.info(f"📄 Encontrados {len(md_files)} documentos para procesar")
        
        # Resultados generales
        pipeline_results = {
            "status": "started",
            "total_documents": len(md_files),
            "processed_documents": 0,
            "total_chunks": 0,
            "total_embeddings": 0,
            "uploaded_documents": 0,
            "files": [],
            "errors": [],
            "started_at": datetime.now().isoformat()
        }
        
        # Procesar cada documento
        for i, md_file in enumerate(md_files, 1):
            logger.info(f"[{i}/{len(md_files)}] Procesando {md_file.name}")
            
            try:
                result = self.process_single_document(md_file, upload_to_supabase)
                pipeline_results["files"].append(result)
                
                if result["status"] == "completed":
                    pipeline_results["processed_documents"] += 1
                    pipeline_results["total_chunks"] += result["chunks_generated"]
                    pipeline_results["total_embeddings"] += result["embeddings_created"]
                    
                    if result["uploaded_to_supabase"]:
                        pipeline_results["uploaded_documents"] += 1
                else:
                    pipeline_results["errors"].extend(result["errors"])
                
            except Exception as e:
                error_msg = f"Error procesando {md_file.name}: {str(e)}"
                pipeline_results["errors"].append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        # Finalizar resultados
        pipeline_results["completed_at"] = datetime.now().isoformat()
        pipeline_results["status"] = "completed"
        
        # Guardar resumen del pipeline
        summary_file = Path("data/processed/embeddings/pipeline_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(pipeline_results, f, ensure_ascii=False, indent=2)
        
        logger.info("📊 Resumen del pipeline:")
        logger.info(f"  📄 Documentos procesados: {pipeline_results['processed_documents']}/{pipeline_results['total_documents']}")
        logger.info(f"  📝 Total chunks: {pipeline_results['total_chunks']}")
        logger.info(f"  🔢 Total embeddings: {pipeline_results['total_embeddings']}")
        logger.info(f"  📤 Subidos a Supabase: {pipeline_results['uploaded_documents']}")
        logger.info(f"  ❌ Errores: {len(pipeline_results['errors'])}")
        
        return pipeline_results
    
    def setup_supabase(self) -> bool:
        """Configura las tablas en Supabase."""
        if not self.enable_supabase or not self.supabase_store:
            logger.error("❌ Supabase no está habilitado")
            return False
        
        logger.info("🛠️ Configurando tablas en Supabase...")
        return self.supabase_store.create_tables()
    
    def get_pipeline_stats(self) -> Dict:
        """Obtiene estadísticas del pipeline."""
        stats = {
            "local_embeddings": {},
            "supabase_stats": {},
            "status": "unknown"
        }
        
        # Estadísticas locales
        embeddings_dir = Path("data/processed/embeddings")
        if embeddings_dir.exists():
            embedding_files = list(embeddings_dir.glob("*_embeddings.json"))
            stats["local_embeddings"] = {
                "files": len(embedding_files),
                "documents": []
            }
            
            for file in embedding_files:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if data:
                        doc_info = {
                            "file": file.name,
                            "chunks": len(data),
                            "title": data[0]['chunk_data']['metadata']['document_title'],
                            "type": data[0]['chunk_data']['metadata']['document_type']
                        }
                        stats["local_embeddings"]["documents"].append(doc_info)
                        
                except Exception as e:
                    logger.warning(f"Error leyendo {file}: {e}")
        
        # Estadísticas de Supabase
        if self.enable_supabase and self.supabase_store:
            try:
                stats["supabase_stats"] = self.supabase_store.get_document_stats()
                stats["status"] = "connected"
            except Exception as e:
                stats["supabase_stats"] = {"error": str(e)}
                stats["status"] = "supabase_error"
        else:
            stats["status"] = "local_only"
        
        return stats


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description="Pipeline completo de procesamiento")
    parser.add_argument("--single", help="Procesar un solo archivo")
    parser.add_argument("--all", action="store_true", help="Procesar todos los documentos")
    parser.add_argument("--setup-supabase", action="store_true", help="Configurar Supabase")
    parser.add_argument("--stats", action="store_true", help="Mostrar estadísticas")
    parser.add_argument("--upload", action="store_true", help="Subir también a Supabase")
    parser.add_argument("--no-supabase", action="store_true", help="Deshabilitar Supabase")
    
    args = parser.parse_args()
    
    # Configurar pipeline
    enable_supabase = not args.no_supabase
    pipeline = CompletePipeline(enable_supabase=enable_supabase)
    
    if args.setup_supabase:
        success = pipeline.setup_supabase()
        if success:
            print("✅ Supabase configurado exitosamente")
        else:
            print("❌ Error configurando Supabase")
    
    elif args.stats:
        stats = pipeline.get_pipeline_stats()
        print("📊 Estadísticas del Pipeline:")
        print(f"  Estado: {stats['status']}")
        print(f"  📁 Archivos locales: {stats['local_embeddings'].get('files', 0)}")
        
        for doc in stats['local_embeddings'].get('documents', []):
            print(f"    📄 {doc['title']}: {doc['chunks']} chunks")
        
        if stats['supabase_stats']:
            supabase = stats['supabase_stats']
            if 'error' not in supabase:
                print(f"  📤 Supabase - Docs: {supabase.get('documents', 0)}, Chunks: {supabase.get('chunks', 0)}")
            else:
                print(f"  ❌ Error Supabase: {supabase['error']}")
    
    elif args.single:
        file_path = Path(f"data/processed/DocsMD/{args.single}")
        if file_path.exists():
            result = pipeline.process_single_document(file_path, args.upload)
            print(f"📄 Documento: {result['document']}")
            print(f"📊 Estado: {result['status']}")
            print(f"📝 Chunks: {result['chunks_generated']}")
            print(f"🔢 Embeddings: {result['embeddings_created']}")
            if args.upload:
                print(f"📤 Supabase: {'✅' if result['uploaded_to_supabase'] else '❌'}")
        else:
            print(f"❌ Archivo no encontrado: {args.single}")
    
    elif args.all:
        results = pipeline.process_all_documents(upload_to_supabase=args.upload)
        print(f"📊 Pipeline completado:")
        print(f"  📄 Procesados: {results['processed_documents']}/{results['total_documents']}")
        print(f"  📝 Total chunks: {results['total_chunks']}")
        print(f"  🔢 Total embeddings: {results['total_embeddings']}")
        if args.upload:
            print(f"  📤 Subidos: {results['uploaded_documents']}")
        if results['errors']:
            print(f"  ❌ Errores: {len(results['errors'])}")
    
    else:
        print("Usa --single <archivo>, --all, --stats, o --setup-supabase")
        print("Opcional: --upload (para Supabase), --no-supabase (solo local)")


if __name__ == "__main__":
    main()