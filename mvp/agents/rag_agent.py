#!/usr/bin/env python3
"""
RAG Agent - MVP System  
Agente especializado en consultas factual usando nuestra base de conocimiento MongoDB
"""

import os
import sys
from typing import Dict, List

# Importar el sistema RAG existente
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'mongodb', 'scripts'))
from simple_rag_mongo import SimpleMongoRAG

from .base_agent import BaseAgent, AgentState

class RAGAgent(BaseAgent):
    """Agente que maneja consultas factual usando la base de conocimiento."""
    
    def __init__(self):
        super().__init__(
            name="rag_agent",
            description="Responde consultas factual usando base de conocimiento MongoDB"
        )
        
        # Inicializar sistema RAG
        try:
            self.rag_system = SimpleMongoRAG()
            # NO inicializar detector de idioma aquí ya que se maneja por separado
            self.rag_system.language_detector = None
            self.logger.info("✅ RAG system inicializado")
        except Exception as e:
            self.logger.error(f"❌ Error inicializando RAG: {e}")
            self.rag_system = None
    
    def should_process(self, state: AgentState) -> bool:
        """Solo procesa consultas factual."""
        return state.mode == "FACTUAL" and self.rag_system is not None
    
    def process(self, state: AgentState) -> AgentState:
        """Procesa consulta factual usando RAG."""

        if not self.should_process(state):
            self.log_processing(state, f"Skipping - Mode: {state.mode}, RAG available: {self.rag_system is not None}")
            return state

        self.log_processing(state, f"Procesando consulta factual: '{state.user_input[:50]}...'")

        try:
            # Configurar idioma en el sistema RAG
            if state.language_config:
                self.rag_system.session_language = state.language
                self.rag_system.language_config = state.language_config

            # Extraer filtros detectados (si existen)
            filters = None
            if state.metadata and 'detected_filters' in state.metadata:
                filter_data = state.metadata['detected_filters']
                if filter_data.get('has_filters'):
                    filters = filter_data.get('mongodb_filters')
                    self.log_processing(state, f"Aplicando filtros: {filters}")

            # Buscar información relevante (con filtros si existen)
            chunks = self.rag_system.search_chunks(state.user_input, top_k=3, filters=filters)

            if not chunks:
                # No hay contexto relevante
                no_context_msg = self._get_no_context_message(state.language_config, filters)
                state.response = no_context_msg
                state.sources = []

                self.log_processing(state, "No se encontró contexto relevante")
                self.add_debug_info(state, "chunks_found", 0)
                self.add_debug_info(state, "filters_applied", filters)
            else:
                # Generar respuesta con contexto
                answer_result = self.rag_system.generate_answer(state.user_input, chunks)

                state.response = answer_result['answer']
                state.sources = self._format_sources(chunks)

                self.log_processing(state, f"Respuesta generada con {len(chunks)} chunks")
                self.add_debug_info(state, "chunks_found", len(chunks))
                self.add_debug_info(state, "sources_count", len(state.sources))
                self.add_debug_info(state, "filters_applied", filters)

        except Exception as e:
            self.logger.error(f"❌ Error en RAG: {e}")
            error_msg = self._get_error_message(state.language_config)
            state.response = error_msg
            state.sources = []
            self.add_debug_info(state, "error", str(e))

        return state
    
    def _get_no_context_message(self, language_config: Dict, filters: Dict = None) -> str:
        """Mensaje cuando no hay contexto relevante."""
        if not language_config:
            return "No encontré información relevante para tu pregunta."

        base_msg = language_config.get('no_context', 'No encontré información relevante para tu pregunta.')

        # Si había filtros aplicados, mencionar que no se encontró nada con esos filtros
        if filters:
            if language_config['code'] == 'en':
                base_msg += " Try broadening your search."
            elif language_config['code'] == 'pt':
                base_msg += " Tente ampliar sua busca."
            else:
                base_msg += " Intenta ampliar tu búsqueda."

        return base_msg
    
    def _get_error_message(self, language_config: Dict) -> str:
        """Mensaje de error según idioma."""
        if not language_config:
            return "Error procesando tu consulta. Intenta de nuevo."
        
        if language_config['code'] == 'en':
            return "Error processing your query. Please try again."
        elif language_config['code'] == 'pt':
            return "Erro processando sua consulta. Tente novamente."
        else:
            return "Error procesando tu consulta. Intenta de nuevo."
    
    def _format_sources(self, chunks: List[Dict]) -> List[Dict]:
        """Formatea las fuentes para el usuario."""
        sources = []
        
        for item in chunks[:3]:  # Top 3 fuentes
            chunk = item['chunk']
            sources.append({
                "document": chunk['document_name'],
                "section": chunk['section_header'],
                "similarity": round(item['similarity'], 3),
                "preview": chunk['content'][:200] + "..."
            })
        
        return sources