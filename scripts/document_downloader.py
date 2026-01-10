#!/usr/bin/env python3
"""
Document Downloader for Puddle Assistant
Descarga automática de documentos desde CSV con links
"""

import csv
import os
import requests
import time
import logging
from pathlib import Path
from urllib.parse import urlparse
from typing import List, Dict, Optional
import argparse

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/daniel/Desktop/Dev/puddleAsistant/logs/document_downloader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DocumentDownloader:
    def __init__(self, csv_path: str, download_dir: str = None):
        self.csv_path = csv_path
        self.download_dir = download_dir or "/Users/daniel/Desktop/Dev/puddleAsistant/data/raw/documents"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Crear directorio de descarga si no existe
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)
        
        # Obtener archivos ya existentes
        self.existing_files = self.get_existing_files()
        
    def get_existing_files(self) -> set:
        """Obtiene lista de archivos ya existentes en el directorio"""
        existing = set()
        for file in Path(self.download_dir).glob('*'):
            if file.is_file():
                existing.add(file.name.lower())
        logger.info(f"Encontrados {len(existing)} archivos existentes")
        return existing
    
    def is_already_downloaded(self, title: str, url: str) -> bool:
        """Verifica si el documento ya fue descargado por título similar"""
        # Limpiar título para comparación
        clean_title = "".join(c for c in title.lower() if c.isalnum() or c == ' ')
        clean_title = clean_title.replace(' ', '')
        
        # Verificar si algún archivo existente contiene palabras clave del título
        title_words = set(clean_title.split())
        if len(title_words) < 3:  # Títulos muy cortos, usar todo
            title_words = {clean_title}
            
        for existing_file in self.existing_files:
            existing_clean = "".join(c for c in existing_file.lower() if c.isalnum() or c == ' ')
            existing_clean = existing_clean.replace(' ', '')
            
            # Si hay coincidencia sustancial, considerar como ya descargado
            if len(title_words) > 0:
                matches = sum(1 for word in title_words if word in existing_clean and len(word) > 3)
                if matches >= min(2, len(title_words) * 0.6):  # 60% de coincidencia o mínimo 2 palabras
                    logger.info(f"Ya descargado (similar): {title} -> {existing_file}")
                    return True
        return False
    
    def read_csv(self) -> List[Dict]:
        """Lee el CSV y retorna lista de documentos"""
        documents = []
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                # Usar csv.reader para manejar campos multi-línea correctamente
                reader = csv.DictReader(file)
                for row in reader:
                    if row.get('Link') and row.get('Link').strip():
                        documents.append({
                            'title': row.get('Title', '').strip(),
                            'link': row.get('Link', '').strip(),
                            'summary': row.get('Summary', '').strip(),
                            'keywords': row.get('Keywords', '').strip()
                        })
            logger.info(f"Leídos {len(documents)} documentos del CSV")
            return documents
        except Exception as e:
            logger.error(f"Error leyendo CSV: {e}")
            return []
    
    def generate_filename(self, url: str, title: str) -> str:
        """Genera nombre de archivo basado en URL y título"""
        parsed_url = urlparse(url)
        
        # Intentar extraer extensión de la URL
        path = parsed_url.path
        if path:
            ext = os.path.splitext(path)[1].lower()
            if ext in ['.pdf', '.doc', '.docx', '.txt', '.ppt', '.pptx']:
                file_ext = ext
            else:
                file_ext = '.pdf'  # Default a PDF
        else:
            file_ext = '.pdf'
        
        # Limpiar título para nombre de archivo
        clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_title = clean_title.replace(' ', '_')[:100]  # Limitar longitud
        
        if not clean_title:
            clean_title = f"document_{hash(url) % 10000}"
        
        return f"{clean_title}{file_ext}"
    
    def download_document(self, doc: Dict) -> bool:
        """Descarga un documento específico"""
        try:
            url = doc['link']
            title = doc['title']
            
            # Generar nombre de archivo
            filename = self.generate_filename(url, title)
            filepath = os.path.join(self.download_dir, filename)
            
            # Verificar si ya existe
            if os.path.exists(filepath):
                logger.info(f"Ya existe: {filename}")
                return True
            
            logger.info(f"Descargando: {title}")
            logger.info(f"URL: {url}")
            
            # Realizar descarga
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Verificar content-type
            content_type = response.headers.get('content-type', '').lower()
            if 'html' in content_type:
                logger.warning(f"Posible HTML en lugar de documento: {url}")
            
            # Guardar archivo
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = os.path.getsize(filepath)
            logger.info(f"Descargado: {filename} ({file_size} bytes)")
            
            return True
            
        except requests.RequestException as e:
            logger.error(f"Error descargando {doc['title']}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado con {doc['title']}: {e}")
            return False
    
    def download_all(self, limit: Optional[int] = None, delay: float = 1.0) -> Dict:
        """Descarga todos los documentos con control de límite y delay"""
        documents = self.read_csv()
        
        if limit:
            documents = documents[:limit]
            
        results = {
            'total': len(documents),
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
        
        logger.info(f"Iniciando descarga de {len(documents)} documentos")
        
        for i, doc in enumerate(documents, 1):
            logger.info(f"Progreso: {i}/{len(documents)}")
            
            # Verificar si ya existe (por archivo exacto o título similar)
            if self.is_already_downloaded(doc['title'], doc['link']):
                results['skipped'] += 1
                continue
            
            # Descargar
            if self.download_document(doc):
                results['success'] += 1
            else:
                results['failed'] += 1
            
            # Delay entre descargas
            if delay > 0 and i < len(documents):
                time.sleep(delay)
        
        logger.info(f"Resumen: {results}")
        return results
    
    def download_single(self, index: int) -> bool:
        """Descarga un documento específico por índice"""
        documents = self.read_csv()
        
        if 0 <= index < len(documents):
            return self.download_document(documents[index])
        else:
            logger.error(f"Índice {index} fuera de rango (0-{len(documents)-1})")
            return False
    
    def list_documents(self, limit: int = 10) -> None:
        """Lista primeros documentos del CSV"""
        documents = self.read_csv()
        
        print(f"\nPrimeros {min(limit, len(documents))} documentos:")
        print("-" * 80)
        
        for i, doc in enumerate(documents[:limit]):
            title = doc['title'][:60] + "..." if len(doc['title']) > 60 else doc['title']
            print(f"{i:3d}. {title}")
            print(f"     URL: {doc['link']}")
            print()

def main():
    parser = argparse.ArgumentParser(description='Descargador de documentos para Puddle Assistant')
    parser.add_argument('--csv', default='/Users/daniel/Desktop/Dev/puddleAsistant/data/documents_to_include in Bot.csv',
                       help='Ruta al archivo CSV')
    parser.add_argument('--output', default='/Users/daniel/Desktop/Dev/puddleAsistant/data/raw/documents',
                       help='Directorio de descarga')
    parser.add_argument('--limit', type=int, help='Límite de documentos a descargar')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay entre descargas en segundos')
    parser.add_argument('--single', type=int, help='Descargar documento específico por índice')
    parser.add_argument('--list', action='store_true', help='Listar documentos disponibles')
    parser.add_argument('--list-count', type=int, default=10, help='Número de documentos a listar')
    
    args = parser.parse_args()
    
    downloader = DocumentDownloader(args.csv, args.output)
    
    if args.list:
        downloader.list_documents(args.list_count)
    elif args.single is not None:
        downloader.download_single(args.single)
    else:
        downloader.download_all(args.limit, args.delay)

if __name__ == '__main__':
    main()