#!/usr/bin/env python3
"""
Enhanced Chunker - Puddle Assistant
Chunking semántico con resúmenes de documento y chunk
"""

import re
import json
import logging
import requests
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EnhancedChunkMetadata:
    """Metadatos enriquecidos para cada chunk."""
    # Identificación
    chunk_id: str
    document_source: str
    document_title: str          # Título extraído del documento
    document_type: str
    
    # Resúmenes
    document_summary: str        # Resumen del documento completo
    chunk_summary: str          # Resumen específico del chunk
    
    # Estructura
    section_header: str
    subsection_header: Optional[str]
    content_type: str
    chunk_index: int
    total_chunks: int
    
    # Métricas del contenido
    text_length: int
    word_count: int
    
    # Características detectadas
    has_code: bool
    has_numbers: bool
    has_bullets: bool
    has_tables: bool
    has_images: bool
    
    # Contexto
    parent_section: Optional[str]
    previous_chunk: Optional[str]
    next_chunk: Optional[str]
    
    # Análisis semántico
    keywords: List[str]
    topics: List[str]
    
    # Metadatos de procesamiento
    processed_at: str
    chunk_hash: str

@dataclass 
class EnhancedDocumentChunk:
    """Chunk con metadatos completos."""
    content: str
    metadata: EnhancedChunkMetadata
    
    def to_dict(self) -> Dict:
        return {
            'content': self.content,
            'metadata': asdict(self.metadata)
        }

class TitleExtractor:
    """Extrae títulos de documentos MD usando LLM."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            self.use_llm = False
        else:
            self.use_llm = True
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            self.base_url = "https://openrouter.ai/api/v1/chat/completions"
            self.model = "mistralai/ministral-8b"
    
    def extract_title_with_llm(self, content: str, filename: str) -> str:
        """Extrae título usando LLM basado en contenido y nombre de archivo."""
        
        # Tomar solo el comienzo del documento
        content_start = content[:1500]
        
        prompt = f"""Analiza este documento y extrae el título más apropiado basándote en:
1. El nombre del archivo: "{filename}"
2. El contenido inicial del documento

Contenido inicial:
{content_start}

Genera un título descriptivo y específico de 3-8 palabras que identifique claramente este documento PARTICULAR (no genérico).

Ejemplos de buenos títulos:
- "Manual de Facilitación A+P"
- "Guía para Educadores" 
- "Currículum Club de Niños"
- "Recursos para Padres"
- "Manual GBI México"

Responde SOLO con el título, sin explicaciones:"""

        try:
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 50,
                "temperature": 0.1
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                title = result["choices"][0]["message"]["content"].strip()
                # Limpiar y validar
                title = re.sub(r'["\'\*\#]', '', title).strip()
                if len(title) > 5 and len(title) < 100:
                    return title
                    
        except Exception as e:
            logger.warning(f"Error extrayendo título con LLM: {e}")
        
        # Fallback
        return self.extract_title_fallback(filename)
    
    def extract_title_fallback(self, filename: str) -> str:
        """Extrae título del nombre del archivo."""
        name = Path(filename).stem
        
        # Mapeo específico por nombres conocidos
        title_mapping = {
            "MANUAL Borrador GBI Mexico": "Manual GBI México", 
            "Revisions Complete_BOYS CLUB CURRICULUM": "Currículum Club de Niños",
            "Revisions Complete_CLASSROOM RESOURCE-Revised Aug 2025.docx": "Recursos para el Aula",
            "Revisions Complete_EDUCATOR'S GUIDE-Revised Aug 2025": "Guía para Educadores",
            "Revisions Complete_PARENTS GUIDE RESOURCE_Revised Aug 2025": "Guía para Padres",
            "3. MANUAL A+P_vICBF.docx": "Manual de Facilitación A+P"
        }
        
        if name in title_mapping:
            return title_mapping[name]
        
        # Limpieza genérica
        title = name.replace('_', ' ').replace('-', ' ')
        title = re.sub(r'\b(Revisions?|Complete|docx?|pdf)\b', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s+', ' ', title).strip().title()
        return title[:80]
    
    def extract_title(self, content: str, filename: str) -> str:
        """Extrae título del documento usando LLM o fallback."""
        if self.use_llm:
            return self.extract_title_with_llm(content, filename)
        else:
            return self.extract_title_fallback(filename)

class LLMSummarizer:
    """Generador de resúmenes usando OpenRouter."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY no encontrada")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "mistralai/ministral-8b"
    
    def generate_document_summary(self, content: str, title: str) -> str:
        """Genera resumen ejecutivo del documento completo."""
        prompt = f"""Analiza este documento y crea un resumen ejecutivo de 2-3 oraciones que incluya:
1. El tema principal
2. El tipo de contenido (manual, guía, currículum)
3. La audiencia objetivo

Título: "{title}"
Contenido inicial:
{content[:4000]}

Resumen ejecutivo:"""
        
        return self._call_llm(prompt, max_tokens=200)
    
    def generate_chunk_summary(self, content: str, section: str, doc_title: str) -> str:
        """Genera resumen específico del chunk/sección."""
        prompt = f"""Resume en 1-2 oraciones qué información específica contiene esta sección.

Documento: "{doc_title}"
Sección: "{section}"
Contenido:
{content[:1800]}

Resumen de la sección:"""
        
        return self._call_llm(prompt, max_tokens=120)
    
    def extract_keywords_topics(self, content: str) -> Tuple[List[str], List[str]]:
        """Extrae palabras clave y temas."""
        prompt = f"""Del siguiente contenido, extrae:
1. 5-7 palabras clave principales (conceptos importantes)
2. 2-3 temas centrales

Contenido:
{content[:2000]}

Responde en formato JSON:
{{"keywords": ["palabra1", "palabra2"], "topics": ["tema1", "tema2"]}}"""
        
        response = self._call_llm(prompt, max_tokens=150)
        
        try:
            result = json.loads(response)
            return (
                result.get('keywords', [])[:7], 
                result.get('topics', [])[:3]
            )
        except:
            return [], []
    
    def _call_llm(self, prompt: str, max_tokens: int) -> str:
        """Llama al LLM con manejo de errores."""
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.2
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=data,
                timeout=45
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            logger.warning(f"Error en LLM: {e}")
            return "Resumen no disponible"

class EnhancedChunker:
    """Chunker con metadatos y resúmenes enriquecidos."""
    
    def __init__(self, 
                 max_chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 enable_summaries: bool = True):
        
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap
        self.enable_summaries = enable_summaries
        
        self.title_extractor = TitleExtractor()
        self.summarizer = LLMSummarizer() if enable_summaries else None
        
        # Patrones de contenido
        self.patterns = {
            'headers': {
                'h1': re.compile(r'^# (.+)$', re.MULTILINE),
                'h2': re.compile(r'^## (.+)$', re.MULTILINE), 
                'h3': re.compile(r'^### (.+)$', re.MULTILINE),
            },
            'content': {
                'table': re.compile(r'\|.*\|', re.MULTILINE),
                'bullet_list': re.compile(r'^- (.+)$', re.MULTILINE),
                'numbered_list': re.compile(r'^\d+\. (.+)$', re.MULTILINE),
                'code': re.compile(r'```.*?```', re.DOTALL),
                'image': re.compile(r'!\[.*?\]\(.*?\)'),
            }
        }
    
    def detect_document_type(self, filename: str, content: str) -> str:
        """Detecta tipo de documento."""
        name = filename.lower()
        text = content[:1000].lower()
        
        if 'manual' in name or 'manual' in text:
            return 'manual'
        elif 'guide' in name or 'guia' in name or 'guide' in text:
            return 'guia'
        elif 'curriculum' in name or 'curriculum' in text:
            return 'curriculum'
        elif 'resource' in name or 'recurso' in name:
            return 'recurso'
        elif 'parent' in name or 'padre' in name:
            return 'guia_padres'
        elif 'educator' in name or 'educador' in name:
            return 'guia_educadores'
        else:
            return 'documento'
    
    def identify_content_type(self, text: str) -> str:
        """Identifica tipo de contenido del chunk."""
        if self.patterns['content']['code'].search(text):
            return 'codigo'
        elif self.patterns['content']['table'].search(text):
            return 'tabla'
        elif self.patterns['content']['bullet_list'].search(text):
            return 'lista_bullets'
        elif self.patterns['content']['numbered_list'].search(text):
            return 'lista_numerada'
        elif self.patterns['content']['image'].search(text):
            return 'imagen'
        else:
            return 'texto'
    
    def analyze_features(self, text: str) -> Dict[str, bool]:
        """Analiza características del contenido."""
        return {
            'has_code': bool(self.patterns['content']['code'].search(text)),
            'has_numbers': bool(re.search(r'\d+', text)),
            'has_bullets': bool(self.patterns['content']['bullet_list'].search(text)),
            'has_tables': bool(self.patterns['content']['table'].search(text)),
            'has_images': bool(self.patterns['content']['image'].search(text)),
        }
    
    def extract_sections(self, text: str) -> List[Tuple[str, str]]:
        """Extrae secciones basadas en headers."""
        sections = []
        
        # Buscar todos los headers
        headers = []
        for level, pattern in self.patterns['headers'].items():
            for match in pattern.finditer(text):
                headers.append((match.start(), match.group(1).strip(), level))
        
        headers.sort(key=lambda x: x[0])
        
        if not headers:
            return [('Introducción', text)]
        
        # Dividir contenido por headers
        for i, (pos, title, level) in enumerate(headers):
            start = pos
            end = headers[i + 1][0] if i + 1 < len(headers) else len(text)
            
            content = text[start:end].strip()
            if content:
                sections.append((title, content))
        
        return sections
    
    def split_large_section(self, text: str) -> List[str]:
        """Divide secciones grandes manteniendo coherencia."""
        if len(text) <= self.max_chunk_size:
            return [text]
        
        chunks = []
        paragraphs = text.split('\n\n')
        current = ''
        
        for para in paragraphs:
            if len(current) + len(para) > self.max_chunk_size:
                if current:
                    chunks.append(current.strip())
                current = para
            else:
                current += '\n\n' + para if current else para
        
        if current.strip():
            chunks.append(current.strip())
        
        return chunks
    
    def chunk_document(self, file_path: Path) -> List[EnhancedDocumentChunk]:
        """Procesa documento completo con resúmenes."""
        logger.info(f"Procesando: {file_path.name}")
        
        # Leer contenido
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error leyendo {file_path}: {e}")
            return []
        
        # Extraer metadatos del documento
        doc_title = self.title_extractor.extract_title(content, file_path.name)
        doc_type = self.detect_document_type(file_path.name, content)
        
        # Solo título, sin resumen de documento completo para velocidad
        doc_summary = ""
        
        # Dividir en secciones
        sections = self.extract_sections(content)
        
        chunks = []
        chunk_index = 0
        
        for section_header, section_text in sections:
            # Dividir sección si es muy larga
            section_chunks = self.split_large_section(section_text)
            
            for chunk_text in section_chunks:
                # Analizar contenido del chunk
                content_type = self.identify_content_type(chunk_text)
                features = self.analyze_features(chunk_text)
                
                # Generar resumen específico del chunk
                chunk_summary = ""
                keywords = []
                topics = []
                
                if self.enable_summaries and self.summarizer:
                    chunk_summary = self.summarizer.generate_chunk_summary(
                        chunk_text, section_header, doc_title
                    )
                    keywords, topics = self.summarizer.extract_keywords_topics(chunk_text)
                
                # Crear metadatos
                chunk_id = f"{Path(file_path.name).stem}_{chunk_index:04d}_{hashlib.md5(chunk_text.encode()).hexdigest()[:8]}"
                
                metadata = EnhancedChunkMetadata(
                    chunk_id=chunk_id,
                    document_source=file_path.name,
                    document_title=doc_title,
                    document_type=doc_type,
                    document_summary=doc_summary,
                    chunk_summary=chunk_summary,
                    section_header=section_header,
                    subsection_header=None,
                    content_type=content_type,
                    chunk_index=chunk_index,
                    total_chunks=0,  # Se actualiza después
                    text_length=len(chunk_text),
                    word_count=len(chunk_text.split()),
                    has_code=features['has_code'],
                    has_numbers=features['has_numbers'],
                    has_bullets=features['has_bullets'],
                    has_tables=features['has_tables'],
                    has_images=features['has_images'],
                    parent_section=section_header,
                    previous_chunk=None,
                    next_chunk=None,
                    keywords=keywords,
                    topics=topics,
                    processed_at=datetime.now().isoformat(),
                    chunk_hash=hashlib.md5(chunk_text.encode()).hexdigest()
                )
                
                chunk = EnhancedDocumentChunk(content=chunk_text, metadata=metadata)
                chunks.append(chunk)
                chunk_index += 1
        
        # Actualizar contexto entre chunks
        for i, chunk in enumerate(chunks):
            chunk.metadata.total_chunks = len(chunks)
            if i > 0:
                chunk.metadata.previous_chunk = chunks[i-1].metadata.chunk_id
            if i < len(chunks) - 1:
                chunk.metadata.next_chunk = chunks[i+1].metadata.chunk_id
        
        logger.info(f"Completado: {len(chunks)} chunks con resúmenes")
        return chunks
    
    def process_all_documents(self, input_path: str = "data/processed/DocsMD") -> List[EnhancedDocumentChunk]:
        """Procesa todos los documentos MD."""
        input_dir = Path(input_path)
        all_chunks = []
        
        md_files = list(input_dir.glob("*.md"))
        logger.info(f"Procesando {len(md_files)} documentos...")
        
        for i, md_file in enumerate(md_files, 1):
            logger.info(f"[{i}/{len(md_files)}] {md_file.name}")
            chunks = self.chunk_document(md_file)
            all_chunks.extend(chunks)
        
        logger.info(f"Total procesado: {len(all_chunks)} chunks")
        return all_chunks


def main():
    """Test del chunker mejorado."""
    chunker = EnhancedChunker(max_chunk_size=800, enable_summaries=True)
    
    # Procesar documento de prueba
    test_file = Path("data/processed/DocsMD/MANUAL Borrador GBI Mexico .md")
    if test_file.exists():
        chunks = chunker.chunk_document(test_file)
        
        if chunks:
            first_chunk = chunks[0]
            print(f"📄 Documento: {first_chunk.metadata.document_title}")
            print(f"📊 Total chunks: {len(chunks)}")
            print(f"📝 Resumen documento: {first_chunk.metadata.document_summary}")
            print(f"\n🔍 Primer chunk:")
            print(f"   Sección: {first_chunk.metadata.section_header}")
            print(f"   Resumen chunk: {first_chunk.metadata.chunk_summary}")
            print(f"   Palabras clave: {first_chunk.metadata.keywords}")
            print(f"   Temas: {first_chunk.metadata.topics}")
            print(f"   Contenido: {first_chunk.content[:200]}...")
    else:
        print("❌ Archivo de prueba no encontrado")


if __name__ == "__main__":
    main()