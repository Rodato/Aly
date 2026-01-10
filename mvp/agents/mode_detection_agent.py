#!/usr/bin/env python3
"""
Mode Detection Agent - MVP System
Detecta el modo de interacción: factual vs workshop vs research
"""

import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any
import json

from .base_agent import BaseAgent, AgentState

load_dotenv()

class ModeDetectionAgent(BaseAgent):
    """Agente que detecta el modo de interacción del usuario."""
    
    def __init__(self):
        super().__init__(
            name="mode_detection_agent", 
            description="Detecta si el usuario busca información factual, workshop estructurado, brainstorming innovador, o research web"
        )
        
        # Configurar OpenRouter
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not self.openrouter_key:
            raise ValueError("OPENROUTER_API_KEY no encontrada")
        
        self.headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json"
        }
        
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "mistralai/ministral-8b"
        
        self.logger.info("✅ Mode Detection Agent inicializado")
    
    def process(self, state: AgentState) -> AgentState:
        """Detecta el modo de interacción del usuario."""
        
        self.log_processing(state, f"Detectando modo para: '{state.user_input[:50]}...'")
        
        # Crear prompt de detección según idioma
        detection_prompt = self._create_detection_prompt(state.user_input, state.language_config)
        
        try:
            # Llamar al LLM
            response = self._call_llm(detection_prompt)
            mode_info = self._parse_mode_response(response)
            
            # Actualizar estado
            state.mode = mode_info['mode']
            state.mode_confidence = mode_info['confidence']
            
            self.log_processing(state, f"Modo detectado: {mode_info['mode']} (confianza: {mode_info['confidence']})")
            
            # Debug info
            self.add_debug_info(state, "detected_mode", mode_info['mode'])
            self.add_debug_info(state, "mode_confidence", mode_info['confidence'])
            self.add_debug_info(state, "mode_reasoning", mode_info['reasoning'])
            
        except Exception as e:
            self.logger.error(f"❌ Error detectando modo: {e}")
            # Fallback a modo FACTUAL
            state.mode = "FACTUAL"
            state.mode_confidence = 0.5
            self.add_debug_info(state, "fallback_used", True)
            self.log_processing(state, "Fallback: Modo establecido como 'factual'")
        
        return state
    
    def _create_detection_prompt(self, user_input: str, language_config: Dict) -> str:
        """Crea el prompt de detección según nueva arquitectura educativa."""
        
        if language_config['code'] == 'en':
            return f"""You are helping facilitators in crisis-affected or low-resource environments. Classify this input intent:

User input: "{user_input}"

Intent Classification:
- PLAN → User wants to adapt or implement something they already know  
- IDEATE → User wants new ideas, variations, or inspiration
- FACTUAL → User seeks specific information, definitions, or facts from curriculum
- AMBIGUOUS → Input is unclear or too broad
- SENSITIVE → Topic involves gender, religion, family conflict, identity, trauma

Respond with ONLY valid JSON:
{{
    "intent": "PLAN|IDEATE|FACTUAL|AMBIGUOUS|SENSITIVE",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}

Examples:
- "How do I adapt this activity for younger kids?" → PLAN
- "Give me creative ideas for engaging boys" → IDEATE  
- "What is gender-transformative education?" → FACTUAL
- "Help me with my class" → AMBIGUOUS
- "How do I handle students with trauma?" → SENSITIVE"""

        elif language_config['code'] == 'pt':
            return f"""Você está ajudando facilitadores em ambientes afetados por crises ou com poucos recursos. Classifique esta intenção:

Entrada do usuário: "{user_input}"

Classificação de Intenção:
- PLAN → Usuário quer adaptar ou implementar algo que já conhece
- IDEATE → Usuário quer novas ideias, variações ou inspiração
- FACTUAL → Usuário busca informação específica, definições, ou fatos do currículo
- AMBIGUOUS → Entrada é pouco clara ou muito ampla
- SENSITIVE → Tópico envolve gênero, religião, conflito familiar, identidade, trauma

Responda APENAS com JSON válido:
{{
    "intent": "PLAN|IDEATE|FACTUAL|AMBIGUOUS|SENSITIVE",
    "confidence": 0.0-1.0,
    "reasoning": "explicação breve"
}}

Exemplos:
- "Como adapto esta atividade para crianças menores?" → PLAN
- "Me dê ideias criativas para engajar meninos" → IDEATE
- "O que é educação transformadora de gênero?" → FACTUAL
- "Me ajude com minha turma" → AMBIGUOUS
- "Como lido com alunos com trauma?" → SENSITIVE"""

        else:  # español
            return f"""Estás ayudando a facilitadores en ambientes afectados por crisis o con pocos recursos. Clasifica esta intención:

Entrada del usuario: "{user_input}"

Clasificación de Intención:
- PLAN → Usuario quiere adaptar o implementar algo que ya conoce
- IDEATE → Usuario quiere nuevas ideas, variaciones o inspiración
- FACTUAL → Usuario busca información específica, definiciones, o hechos del currículo
- AMBIGUOUS → Entrada es poco clara o demasiado amplia
- SENSITIVE → Tópico involucra género, religión, conflicto familiar, identidad, trauma

Responde SOLO con JSON válido:
{{
    "intent": "PLAN|IDEATE|FACTUAL|AMBIGUOUS|SENSITIVE",
    "confidence": 0.0-1.0,
    "reasoning": "explicación breve"
}}

Ejemplos:
- "¿Cómo adapto esta actividad para niños más pequeños?" → PLAN
- "Dame ideas creativas para involucrar a los niños" → IDEATE
- "¿Qué es la educación transformadora de género?" → FACTUAL
- "Ayúdame con mi clase" → AMBIGUOUS
- "¿Cómo manejo estudiantes con trauma?" → SENSITIVE"""
    
    def _call_llm(self, prompt: str) -> str:
        """Llama al LLM para detección de modo."""
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 200,
            "temperature": 0.1
        }
        
        response = requests.post(self.api_url, headers=self.headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    
    def _parse_mode_response(self, response: str) -> Dict:
        """Parsea la respuesta del LLM."""
        
        try:
            # Buscar JSON en la respuesta
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response[start:end]
                parsed = json.loads(json_str)
                
                # Validar formato
                valid_intents = ['PLAN', 'IDEATE', 'FACTUAL', 'AMBIGUOUS', 'SENSITIVE']
                intent_field = parsed.get('intent') or parsed.get('mode')  # backward compatibility
                
                if intent_field and intent_field in valid_intents:
                    return {
                        'mode': intent_field,
                        'confidence': float(parsed.get('confidence', 0.7)),
                        'reasoning': parsed.get('reasoning', 'LLM analysis')
                    }
            
            # Si no se puede parsear, buscar palabras clave
            response_lower = response.lower()
            if 'ideate' in response_lower or 'ideas' in response_lower or 'creativ' in response_lower:
                return {
                    'mode': 'IDEATE',
                    'confidence': 0.6,
                    'reasoning': 'Detected from response keywords'
                }
            elif 'plan' in response_lower or 'adapt' in response_lower or 'implement' in response_lower:
                return {
                    'mode': 'PLAN',
                    'confidence': 0.6,
                    'reasoning': 'Detected from response keywords'
                }
            elif 'sensitive' in response_lower or 'trauma' in response_lower or 'religion' in response_lower:
                return {
                    'mode': 'SENSITIVE', 
                    'confidence': 0.7,
                    'reasoning': 'Detected sensitive topic'
                }
            elif 'ambiguous' in response_lower or 'unclear' in response_lower:
                return {
                    'mode': 'AMBIGUOUS',
                    'confidence': 0.6,
                    'reasoning': 'Detected ambiguous input'
                }
            else:
                return {
                    'mode': 'FACTUAL',
                    'confidence': 0.5,
                    'reasoning': 'Default fallback'
                }
                
        except Exception as e:
            self.logger.warning(f"Error parsing mode response: {e}")
            return {
                'mode': 'FACTUAL',
                'confidence': 0.5,
                'reasoning': 'Parse error fallback'
            }