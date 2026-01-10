#!/usr/bin/env python3
"""
Simple RAG with MongoDB - Puddle Assistant
Sistema RAG básico usando MongoDB con detección automática de idioma
"""

import os
import sys
import json
import logging
from typing import List, Dict
import numpy as np
from pymongo import MongoClient
from dotenv import load_dotenv
import requests

# Importar detector de idioma
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'mvp'))
from language_detector import LLMLanguageDetector

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleMongoRAG:
    """RAG simple usando MongoDB para búsqueda semántica."""
    
    def __init__(self):
        # Configurar MongoDB
        self.uri = os.getenv("MONGODB_URI")
        self.db_name = os.getenv("MONGODB_DB_NAME")  
        self.collection_name = os.getenv("MONGODB_COLLECTION_NAME")
        
        if not all([self.uri, self.db_name, self.collection_name]):
            raise ValueError("Variables MongoDB no configuradas")
        
        # Configurar OpenAI para embeddings
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY no encontrada")
        
        # Configurar OpenRouter para LLM
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not self.openrouter_key:
            raise ValueError("OPENROUTER_API_KEY no encontrada")
        
        # Inicializar detector de idioma
        try:
            self.language_detector = LLMLanguageDetector()
            logger.info("✅ Detector de idioma inicializado")
        except Exception as e:
            logger.warning(f"⚠️ Error inicializando detector de idioma: {e}")
            self.language_detector = None
        
        # Estado de idioma fijo para la sesión
        self.session_language = None
        self.language_config = None
        
        # Conectar a MongoDB
        self.client = MongoClient(self.uri)
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]
        
        logger.info(f"🔗 Conectado a MongoDB: {self.db_name}.{self.collection_name}")
        
        # Headers para APIs
        self.openai_headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        
        self.openrouter_headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json"
        }
    
    def generate_embedding(self, text: str) -> List[float]:
        """Genera embedding usando OpenAI."""
        url = "https://api.openai.com/v1/embeddings"
        
        data = {
            "model": "text-embedding-ada-002",
            "input": text.strip()[:8000]  # Límite conservador
        }
        
        try:
            response = requests.post(url, headers=self.openai_headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result["data"][0]["embedding"]
            
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            return None
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcula similitud coseno entre dos vectores."""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def search_chunks(self, query: str, top_k: int = 5) -> List[Dict]:
        """Busca chunks relevantes usando similitud semántica."""
        logger.info(f"🔍 Buscando: '{query}'")
        
        # Generar embedding de la consulta
        query_embedding = self.generate_embedding(query)
        if not query_embedding:
            return []
        
        # Recuperar todos los chunks (en producción usarías vector search)
        # Por ahora simulamos con búsqueda manual
        all_chunks = list(self.collection.find({}, {
            "content": 1,
            "document_name": 1,
            "document_title": 1,
            "section_header": 1,
            "chunk_index": 1,
            "embedding": 1
        }))
        
        logger.info(f"📊 Evaluando {len(all_chunks)} chunks")
        
        # Calcular similitudes
        similarities = []
        for chunk in all_chunks:
            if 'embedding' in chunk and chunk['embedding']:
                similarity = self.cosine_similarity(query_embedding, chunk['embedding'])
                similarities.append({
                    'chunk': chunk,
                    'similarity': similarity
                })
        
        # Ordenar por similitud y tomar top_k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        top_chunks = similarities[:top_k]
        
        logger.info(f"✅ Top {len(top_chunks)} chunks encontrados")
        
        return top_chunks
    
    def detect_and_set_session_language(self, first_message: str) -> Dict:
        """
        Detecta el idioma del primer mensaje y lo fija para toda la sesión.
        
        Args:
            first_message: Primer mensaje del usuario
            
        Returns:
            Dict con información del idioma detectado y configurado
        """
        if self.session_language is not None:
            # Ya está configurado
            return {
                'already_set': True,
                'language': self.session_language,
                'config': self.language_config
            }
        
        # Detectar idioma del primer mensaje
        if self.language_detector:
            try:
                self.language_config = self.language_detector.get_language_config(first_message)
                self.session_language = self.language_config['code']
                
                logger.info(f"🌍 Idioma de sesión establecido: {self.language_config['name']} ({self.session_language})")
                
                return {
                    'detected': True,
                    'language': self.session_language,
                    'config': self.language_config,
                    'greeting': self.language_config['greeting']
                }
                
            except Exception as e:
                logger.warning(f"Error detectando idioma: {e}")
        
        # Fallback a español
        self.session_language = 'es'
        self.language_config = {
            'code': 'es',
            'name': 'Español',
            'greeting': '¡Hola! Soy Aly, tu asistente educativo. ¿Cómo puedo ayudarte hoy?',
            'no_context': 'No encontré información relevante para tu pregunta. ¿Podrías reformular o dar más contexto?'
        }
        
        logger.info("🌍 Idioma de sesión: Español (fallback)")
        
        return {
            'detected': False,
            'language': self.session_language, 
            'config': self.language_config,
            'greeting': self.language_config['greeting']
        }
    
    def generate_answer(self, query: str, context_chunks: List[Dict]) -> Dict:
        """Genera respuesta usando OpenRouter con idioma de sesión fijo."""
        
        # Usar idioma de sesión (ya establecido)
        if not self.language_config:
            # Fallback si no está configurado
            self.language_config = {
                'code': 'es',
                'name': 'Español'
            }
        
        # Preparar contexto
        context = "\\n\\n".join([
            f"**{chunk['chunk']['document_name']}** - {chunk['chunk']['section_header']}\\n{chunk['chunk']['content']}"
            for chunk in context_chunks[:3]  # Usar solo top 3 para no exceder límites
        ])
        
        # Crear prompt específico según idioma de sesión
        if self.language_config['code'] == 'en':
            prompt = f"""You are a specialized assistant in gender education and child development. 
Answer the following question based exclusively on the provided context.

Context:
{context}

Question: {query}

Answer (in English, being specific and citing sources when relevant):"""
        elif self.language_config['code'] == 'pt':
            prompt = f"""Você é um assistente especializado em educação de gênero e desenvolvimento infantil. 
Responda à seguinte pergunta baseando-se exclusivamente no contexto fornecido.

Contexto:
{context}

Pergunta: {query}

Resposta (em português, sendo específico e citando as fontes quando relevante):"""
        else:  # español (default)
            prompt = f"""Eres un asistente especializado en educación de género y desarrollo infantil. 
Responde la siguiente pregunta basándote únicamente en el contexto proporcionado.

Contexto:
{context}

Pregunta: {query}

Respuesta (en español, siendo específico y citando las fuentes cuando sea relevante):"""
        
        # Cambiar a OpenAI GPT-4o-mini
        url = "https://api.openai.com/v1/chat/completions"
        
        # Headers para OpenAI
        openai_headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.3
        }
        
        try:
            response = requests.post(url, headers=openai_headers, json=data, timeout=45)
            response.raise_for_status()
            
            result = response.json()
            answer_text = result["choices"][0]["message"]["content"].strip()
            
            return {
                'answer': answer_text,
                'language_info': self.language_config,
                'prompt_used': prompt[:200] + "..." if len(prompt) > 200 else prompt
            }
            
        except Exception as e:
            logger.error(f"Error generando respuesta: {e}")
            
            # Mensaje de error según idioma de sesión
            if self.language_config['code'] == 'en':
                error_msg = "Error generating response. Please try again."
            elif self.language_config['code'] == 'pt':
                error_msg = "Erro gerando resposta. Tente novamente."
            else:
                error_msg = "Error generando respuesta. Intenta de nuevo."
            
            return {
                'answer': error_msg,
                'language_info': self.language_config,
                'prompt_used': 'Error'
            }
    
    def ask(self, query: str, top_k: int = 5, is_first_message: bool = False) -> Dict:
        """Pregunta completa: búsqueda + generación con idioma de sesión fijo."""
        
        # Si es el primer mensaje, detectar y fijar idioma
        session_info = None
        if is_first_message or self.session_language is None:
            session_info = self.detect_and_set_session_language(query)
        
        # Buscar chunks relevantes
        relevant_chunks = self.search_chunks(query, top_k)
        
        if not relevant_chunks:
            # Mensaje "no encontrado" según idioma de sesión
            if self.language_config['code'] == 'en':
                no_content_msg = "I couldn't find relevant information for your question."
            elif self.language_config['code'] == 'pt':
                no_content_msg = "Não consegui encontrar informações relevantes para sua pergunta."
            else:
                no_content_msg = "No encontré información relevante para tu pregunta."
            
            result = {
                "query": query,
                "answer": no_content_msg,
                "sources": [],
                "language_detected": self.session_language,
                "language_name": self.language_config['name']
            }
            
            # Agregar info de sesión si es primer mensaje
            if session_info:
                result["session_info"] = session_info
                
            return result
        
        # Generar respuesta
        answer_result = self.generate_answer(query, relevant_chunks)
        
        # Preparar fuentes
        sources = []
        for item in relevant_chunks[:3]:
            chunk = item['chunk']
            sources.append({
                "document": chunk['document_name'],
                "section": chunk['section_header'],
                "similarity": round(item['similarity'], 3),
                "content_preview": chunk['content'][:200] + "..."
            })
        
        result = {
            "query": query,
            "answer": answer_result['answer'],
            "sources": sources,
            "language_detected": self.session_language,
            "language_name": self.language_config['name'],
            "greeting": self.language_config.get('greeting', ''),
            "debug_prompt": answer_result.get('prompt_used', '')
        }
        
        # Agregar info de sesión si es primer mensaje
        if session_info:
            result["session_info"] = session_info
            
        return result
    
    def get_stats(self):
        """Estadísticas de la base de datos."""
        stats = {}
        try:
            stats["total_chunks"] = self.collection.count_documents({})
            stats["documents"] = len(self.collection.distinct("document_name"))
            
            # Documentos por nombre
            pipeline = [
                {"$group": {"_id": "$document_name", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            stats["documents_detail"] = list(self.collection.aggregate(pipeline))
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
        
        return stats


def main():
    """Función principal para pruebas."""
    try:
        rag = SimpleMongoRAG()
        
        # Mostrar estadísticas
        stats = rag.get_stats()
        print("📊 Estadísticas MongoDB:")
        print(f"  📝 Total chunks: {stats.get('total_chunks', 0)}")
        print(f"  📄 Documentos: {stats.get('documents', 0)}")
        
        if stats.get('documents_detail'):
            print("\\n📋 Documentos disponibles:")
            for doc in stats['documents_detail']:
                print(f"  📄 {doc['_id']}: {doc['count']} chunks")
        
        print("\\n" + "="*60)
        print("🤖 RAG MongoDB - Puddle Assistant")
        print("Pregunta sobre los documentos educativos")
        print("(Escribe 'salir' para terminar)")
        print("="*60)
        
        while True:
            query = input("\\n❓ Tu pregunta: ").strip()
            
            if query.lower() in ['salir', 'exit', 'quit']:
                print("¡Hasta luego! 👋")
                break
            
            if not query:
                continue
            
            print("\\n🔍 Buscando...")
            result = rag.ask(query)
            
            print(f"\\n🤖 **Respuesta:**")
            print(result['answer'])
            
            if result['sources']:
                print(f"\\n📚 **Fuentes consultadas:**")
                for i, source in enumerate(result['sources'], 1):
                    print(f"  {i}. **{source['document']}** - {source['section']}")
                    print(f"     Similitud: {source['similarity']}")
                    print(f"     Vista previa: {source['content_preview']}")
                    print()
    
    except KeyboardInterrupt:
        print("\\n\\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()