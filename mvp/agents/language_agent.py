#!/usr/bin/env python3
"""
Language Agent - MVP System
Detecta el idioma del usuario una sola vez por sesión
"""

import os
import sys
from typing import Dict, Any

# Importar el detector de idioma existente
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from language_detector import LLMLanguageDetector

from .base_agent import BaseAgent, AgentState

class LanguageAgent(BaseAgent):
    """Agente especializado en detección de idioma."""
    
    def __init__(self):
        super().__init__(
            name="language_agent",
            description="Detecta el idioma del usuario (ES/EN/PT) una sola vez por sesión"
        )
        
        # Inicializar detector de idioma
        try:
            self.language_detector = LLMLanguageDetector()
            self.logger.info("✅ Language detector inicializado")
        except Exception as e:
            self.logger.error(f"❌ Error inicializando detector: {e}")
            self.language_detector = None
    
    def should_process(self, state: AgentState) -> bool:
        """Solo procesa si el idioma no está ya detectado."""
        return state.language is None
    
    def process(self, state: AgentState) -> AgentState:
        """Detecta y establece el idioma del usuario."""
        
        if not self.should_process(state):
            self.log_processing(state, f"Idioma ya detectado: {state.language}")
            return state
        
        self.log_processing(state, f"Detectando idioma para: '{state.user_input[:50]}...'")
        
        # Detectar idioma
        if self.language_detector:
            try:
                language_config = self.language_detector.get_language_config(state.user_input)
                language_code = language_config['code']
                
                # Actualizar estado
                state.language = language_code
                state.language_config = language_config
                
                self.log_processing(state, f"Idioma detectado: {language_config['name']} ({language_code})")
                
                # Debug info
                self.add_debug_info(state, "detected_language", language_code)
                self.add_debug_info(state, "language_name", language_config['name'])
                self.add_debug_info(state, "greeting", language_config.get('greeting', ''))
                
            except Exception as e:
                self.logger.error(f"❌ Error en detección: {e}")
                # Fallback a español
                self._set_fallback_language(state)
        else:
            # Fallback si no hay detector
            self._set_fallback_language(state)
        
        return state
    
    def _set_fallback_language(self, state: AgentState):
        """Establece español como idioma por defecto."""
        state.language = 'es'
        state.language_config = {
            'code': 'es',
            'name': 'Español',
            'greeting': '¡Hola! Soy Aly, tu asistente educativo. ¿Cómo puedo ayudarte hoy?',
            'no_context': 'No encontré información relevante para tu pregunta.',
            'clarification_prompts': {
                'need_context': '¿Podrías darme más contexto sobre tu situación?',
                'target_audience': '¿Quiénes son tus participantes? (edad, contexto)',
                'specific_goal': '¿Qué específicamente estás tratando de adaptar o lograr?'
            }
        }
        
        self.log_processing(state, "Fallback: Idioma establecido como Español")
        self.add_debug_info(state, "fallback_used", True)