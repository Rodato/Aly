#!/usr/bin/env python3
"""
Document Processor - Puddle Assistant
Convierte documentos PDF/DOCX a Markdown usando Docling
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from docling.document_converter import DocumentConverter

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Procesador de documentos con Docling."""
    
    def __init__(self, 
                 input_path: str = "data/raw/documents",
                 output_path: str = "data/processed/DocsMD",
                 status_file: str = "logs/processing_status.json"):
        
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.status_file = Path(status_file)
        
        # Crear directorios necesarios
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializar conversor
        self.converter = DocumentConverter()
        
        # Cargar estado previo
        self.status_data = self._load_status()
        
        # Extensiones soportadas
        self.supported_extensions = {'.pdf', '.docx', '.doc', '.pptx'}
    
    def _load_status(self) -> Dict:
        """Carga el estado de procesamiento anterior."""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error cargando estado: {e}")
        
        return {
            "processed_files": {},
            "last_update": None,
            "stats": {
                "total_processed": 0,
                "successful": 0,
                "failed": 0
            }
        }
    
    def _save_status(self):
        """Guarda el estado actual."""
        self.status_data["last_update"] = datetime.now().isoformat()
        
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(self.status_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Estado guardado en {self.status_file}")
    
    def get_supported_files(self) -> List[Path]:
        """Obtiene lista de archivos soportados."""
        if not self.input_path.exists():
            logger.error(f"Directorio de entrada no existe: {self.input_path}")
            return []
        
        files = [f for f in self.input_path.iterdir() 
                if f.is_file() and f.suffix.lower() in self.supported_extensions]
        
        logger.info(f"Encontrados {len(files)} archivos soportados")
        return files
    
    def is_already_processed(self, file_path: Path) -> bool:
        """Verifica si el archivo ya fue procesado exitosamente."""
        file_key = str(file_path.name)
        
        if file_key in self.status_data["processed_files"]:
            file_info = self.status_data["processed_files"][file_key]
            
            # Verificar si el archivo MD existe
            md_path = self.output_path / f"{file_path.stem}.md"
            if md_path.exists() and file_info.get("status") == "success":
                return True
        
        return False
    
    def convert_document(self, file_path: Path) -> bool:
        """Convierte un documento a Markdown."""
        logger.info(f"Procesando: {file_path.name}")
        
        try:
            # Convertir con Docling
            result = self.converter.convert(file_path)
            markdown_content = result.document.export_to_markdown()
            
            # Crear nombre de archivo MD
            md_filename = f"{file_path.stem}.md"
            md_path = self.output_path / md_filename
            
            # Guardar Markdown
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # Actualizar estado
            file_info = {
                "status": "success",
                "md_file": md_filename,
                "processed_at": datetime.now().isoformat(),
                "original_size": file_path.stat().st_size,
                "md_size": md_path.stat().st_size,
                "md_length": len(markdown_content)
            }
            
            self.status_data["processed_files"][file_path.name] = file_info
            self.status_data["stats"]["successful"] += 1
            
            logger.info(f"Convertido exitosamente: {md_filename} ({len(markdown_content):,} caracteres)")
            return True
            
        except Exception as e:
            # Registrar error
            error_info = {
                "status": "failed",
                "error": str(e),
                "processed_at": datetime.now().isoformat()
            }
            
            self.status_data["processed_files"][file_path.name] = error_info
            self.status_data["stats"]["failed"] += 1
            
            logger.error(f"Error procesando {file_path.name}: {e}")
            return False
    
    def process_all(self, force_reprocess: bool = False) -> Dict:
        """Procesa todos los documentos."""
        logger.info("=== Iniciando procesamiento de documentos ===")
        logger.info(f"Entrada: {self.input_path}")
        logger.info(f"Salida: {self.output_path}")
        
        files = self.get_supported_files()
        
        if not files:
            logger.warning("No se encontraron archivos soportados")
            return {"processed": 0, "skipped": 0, "failed": 0}
        
        processed_count = 0
        skipped_count = 0
        failed_count = 0
        
        for file_path in files:
            # Verificar si ya fue procesado
            if not force_reprocess and self.is_already_processed(file_path):
                logger.info(f"Ya procesado: {file_path.name}")
                skipped_count += 1
                continue
            
            # Convertir documento
            if self.convert_document(file_path):
                processed_count += 1
            else:
                failed_count += 1
            
            self.status_data["stats"]["total_processed"] += 1
        
        # Guardar estado
        self._save_status()
        
        # Resultados
        results = {
            "processed": processed_count,
            "skipped": skipped_count, 
            "failed": failed_count,
            "total_files": len(files)
        }
        
        logger.info("=== Resumen de procesamiento ===")
        logger.info(f"Archivos encontrados: {results['total_files']}")
        logger.info(f"Procesados: {results['processed']}")
        logger.info(f"Ya procesados: {results['skipped']}")
        logger.info(f"Errores: {results['failed']}")
        
        return results
    
    def process_single(self, filename: str) -> bool:
        """Procesa un solo archivo."""
        file_path = self.input_path / filename
        
        if not file_path.exists():
            logger.error(f"Archivo no encontrado: {filename}")
            return False
        
        success = self.convert_document(file_path)
        self._save_status()
        
        return success
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas de procesamiento."""
        md_files = list(self.output_path.glob('*.md'))
        
        return {
            "total_files": len(self.get_supported_files()),
            "processed_files": len(md_files),
            "success_count": self.status_data["stats"]["successful"],
            "failed_count": self.status_data["stats"]["failed"],
            "last_update": self.status_data.get("last_update")
        }


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Procesador de documentos Docling")
    parser.add_argument("--single", help="Procesar un solo archivo")
    parser.add_argument("--force", action="store_true", help="Forzar reprocesamiento")
    parser.add_argument("--stats", action="store_true", help="Mostrar solo estadísticas")
    
    args = parser.parse_args()
    
    processor = DocumentProcessor()
    
    if args.stats:
        stats = processor.get_stats()
        print(f"📊 Estadísticas:")
        print(f"  Total archivos: {stats['total_files']}")
        print(f"  Procesados: {stats['processed_files']}")
        print(f"  Exitosos: {stats['success_count']}")
        print(f"  Fallidos: {stats['failed_count']}")
        print(f"  Última actualización: {stats['last_update']}")
        
    elif args.single:
        success = processor.process_single(args.single)
        if success:
            print(f"✅ Archivo procesado: {args.single}")
        else:
            print(f"❌ Error procesando: {args.single}")
            
    else:
        results = processor.process_all(force_reprocess=args.force)
        print(f"\n✅ Procesamiento completado:")
        print(f"  Procesados: {results['processed']}")
        print(f"  Ya procesados: {results['skipped']}")
        print(f"  Errores: {results['failed']}")


if __name__ == "__main__":
    main()