#!/usr/bin/env python3
"""
Language Detector - MVP Chatbot Aly
Detección automática de idioma usando LLM (Español/Inglés/Portugués)
"""

import os
import json
import logging
from typing import Dict, Optional
import requests
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMLanguageDetector:
    """Detector de idioma español/inglés/portugués usando LLM."""
    
    def __init__(self):
        # Configurar OpenRouter para LLM
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not self.openrouter_key:
            raise ValueError("OPENROUTER_API_KEY no encontrada en .env")
        
        self.headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json"
        }
        
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "mistralai/ministral-8b"  # Modelo rápido y económico
        
        logger.info("✅ LLM Language Detector inicializado (ES/EN/PT)")
    
    def detect_language(self, text: str) -> Dict:
        """
        Detecta idioma usando LLM.
        
        Args:
            text: Texto del usuario
            
        Returns:
            Dict con idioma ('spanish'/'english'/'portuguese'), confianza y reasoning
        """
        
        if not text or len(text.strip()) < 2:
            return {
                'language': 'spanish',  # Default
                'confidence': 0.5,
                'reasoning': 'Texto muy corto, usando español por defecto'
            }
        
        # Prompt específico para detección trilingüe
        prompt = f"""Analiza el siguiente texto y determina si está escrito en español, inglés o portugués.

Texto: "{text}"

Responde SOLO con un JSON válido en este formato exacto:
{{
    "language": "spanish" o "english" o "portuguese",
    "confidence": 0.0-1.0,
    "reasoning": "breve explicación"
}}

Reglas:
- Si hay mezcla de idiomas, elige el dominante
- Si es ambiguo, usa "spanish" como default
- Portuguese se diferencia del español por: ção, não, muito, fazer, etc.
- Confidence alta (>0.8) solo si estás muy seguro"""

        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 150,
            "temperature": 0.1  # Baja temperatura para consistencia
        }
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            # Extraer JSON de la respuesta
            return self._parse_llm_response(content)
            
        except Exception as e:
            logger.error(f"Error en detección LLM: {e}")
            # Fallback: detección simple por palabras clave
            return self._simple_fallback(text)
    
    def _parse_llm_response(self, content: str) -> Dict:
        """Parse respuesta del LLM."""
        try:
            # Buscar JSON en la respuesta
            start = content.find('{')
            end = content.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = content[start:end]
                parsed = json.loads(json_str)
                
                # Validar formato
                valid_languages = ['spanish', 'english', 'portuguese']
                if 'language' in parsed and parsed['language'] in valid_languages:
                    return {
                        'language': parsed['language'],
                        'confidence': float(parsed.get('confidence', 0.8)),
                        'reasoning': parsed.get('reasoning', 'Análisis LLM')
                    }
            
            # Si no se puede parsear, extraer idioma de la respuesta
            content_lower = content.lower()
            if 'portuguese' in content_lower or 'português' in content_lower:
                return {
                    'language': 'portuguese',
                    'confidence': 0.7,
                    'reasoning': 'Detectado portugués en respuesta textual'
                }
            elif 'spanish' in content_lower or 'español' in content_lower:
                return {
                    'language': 'spanish',
                    'confidence': 0.7,
                    'reasoning': 'Detectado español en respuesta textual'
                }
            elif 'english' in content_lower or 'inglés' in content_lower:
                return {
                    'language': 'english', 
                    'confidence': 0.7,
                    'reasoning': 'Detectado inglés en respuesta textual'
                }
                
        except Exception as e:
            logger.warning(f"Error parsing LLM response: {e}")
        
        # Default fallback
        return {
            'language': 'spanish',
            'confidence': 0.5,
            'reasoning': 'Error parsing, usando español por defecto'
        }
    
    def _simple_fallback(self, text: str) -> Dict:
        """Detección simple como fallback trilingüe."""
        text_lower = text.lower()
        
        # Palabras muy específicas de cada idioma
        portuguese_indicators = ['não', 'ção', 'muito', 'fazer', 'português', 'como', 'você', 'que', 'mais', 'ter', 'seu', 'ela', 'até', 'pelo']
        spanish_indicators = ['qué', 'cómo', 'dónde', 'cuándo', 'por qué', 'ñ', '¿', '¡', 'también', 'año', 'niño', 'español']
        english_indicators = ['what', 'how', 'where', 'when', 'why', 'the ', ' and ', ' you ', ' can ', 'that', 'with', 'they']
        
        portuguese_count = sum(1 for word in portuguese_indicators if word in text_lower)
        spanish_count = sum(1 for word in spanish_indicators if word in text_lower)
        english_count = sum(1 for word in english_indicators if word in text_lower)
        
        max_count = max(portuguese_count, spanish_count, english_count)
        
        if max_count == 0:
            return {
                'language': 'spanish',
                'confidence': 0.5,
                'reasoning': 'Fallback: no indicadores claros, default español'
            }
        
        if portuguese_count == max_count:
            return {
                'language': 'portuguese',
                'confidence': 0.6,
                'reasoning': f'Fallback: indicadores PT={portuguese_count}, ES={spanish_count}, EN={english_count}'
            }
        elif spanish_count == max_count:
            return {
                'language': 'spanish',
                'confidence': 0.6,
                'reasoning': f'Fallback: indicadores PT={portuguese_count}, ES={spanish_count}, EN={english_count}'
            }
        else:
            return {
                'language': 'english',
                'confidence': 0.6,
                'reasoning': f'Fallback: indicadores PT={portuguese_count}, ES={spanish_count}, EN={english_count}'
            }
    
    def get_response_language(self, text: str) -> str:
        """
        Detecta idioma y retorna código para respuestas.
        
        Returns:
            'es' para español, 'en' para inglés, 'pt' para portugués
        """
        result = self.detect_language(text)
        
        if result['language'] == 'english':
            return 'en'
        elif result['language'] == 'portuguese':
            return 'pt'
        else:
            return 'es'  # Default español
    
    def get_language_config(self, text: str) -> Dict:
        """
        Retorna configuración completa de idioma para respuestas.
        
        Returns:
            Dict con configuración de prompts y mensajes
        """
        lang_code = self.get_response_language(text)
        
        if lang_code == 'en':
            return {
                'code': 'en',
                'name': 'English',
                'response_instruction': "Respond in English.",
                'context_instruction': "Answer based on the provided context in English.",
                'clarification_prompts': {
                    'need_context': "Could you provide more context about your situation?",
                    'target_audience': "Who are your participants? (age, background)",
                    'specific_goal': "What specifically are you trying to adapt or achieve?"
                },
                'greeting': "Hi! I'm Aly, your educational assistant. How can I help you today?",
                'no_context': "I couldn't find relevant information for your question. Could you rephrase or provide more context?",
                'workshop_mode_intro': "Great! Let's brainstorm some ideas for your session."
            }
        elif lang_code == 'pt':
            return {
                'code': 'pt', 
                'name': 'Português',
                'response_instruction': "Responda em português.",
                'context_instruction': "Responda baseado no contexto fornecido em português.",
                'clarification_prompts': {
                    'need_context': "Você poderia me dar mais contexto sobre sua situação?",
                    'target_audience': "Quem são seus participantes? (idade, contexto)",
                    'specific_goal': "O que especificamente você está tentando adaptar ou alcançar?"
                },
                'greeting': "Olá! Eu sou Aly, sua assistente educacional. Como posso te ajudar hoje?",
                'no_context': "Não encontrei informações relevantes para sua pergunta. Você poderia reformular ou dar mais contexto?",
                'workshop_mode_intro': "Ótimo! Vamos pensar em algumas ideias para sua sessão."
            }
        else:  # español
            return {
                'code': 'es',
                'name': 'Español',
                'response_instruction': "Responde en español.",
                'context_instruction': "Responde basándote en el contexto proporcionado en español.",
                'clarification_prompts': {
                    'need_context': "¿Podrías darme más contexto sobre tu situación?",
                    'target_audience': "¿Quiénes son tus participantes? (edad, contexto)",
                    'specific_goal': "¿Qué específicamente estás tratando de adaptar o lograr?"
                },
                'greeting': "¡Hola! Soy Aly, tu asistente educativo. ¿Cómo puedo ayudarte hoy?",
                'no_context': "No encontré información relevante para tu pregunta. ¿Podrías reformular o dar más contexto?",
                'workshop_mode_intro': "¡Perfecto! Vamos a generar algunas ideas para tu sesión."
            }


def test_detector():
    """Pruebas del detector LLM trilingüe."""
    detector = LLMLanguageDetector()
    
    test_cases = [
        # Español
        "¿Cómo puedo adaptar las actividades para niños de 8 años?",
        "Qué metodologías recomiendas para educación de género",
        "Necesito ayuda con mi programa educativo",
        "Hola, ¿puedes ayudarme?",
        
        # Inglés
        "How can I adapt activities for 8-year-old children?",
        "What methodologies do you recommend for gender education?",
        "I need help with my educational program", 
        "Hello, can you help me?",
        
        # Portugués
        "Como posso adaptar as atividades para crianças de 8 anos?",
        "Que metodologias você recomenda para educação de gênero?",
        "Preciso de ajuda com meu programa educacional",
        "Olá, você pode me ajudar?",
        "Não sei como fazer isso",
        
        # Casos mixtos/ambiguos
        "Help me por favor",
        "What is educação de gênero?",
        "Muito obrigado",
        "Hi",
        "Hola"
    ]
    
    print("🧪 PRUEBAS LLM LANGUAGE DETECTOR (ES/EN/PT)")
    print("=" * 60)
    
    for text in test_cases:
        print(f"📝 Texto: '{text}'")
        
        result = detector.detect_language(text)
        response_lang = detector.get_response_language(text)
        config = detector.get_language_config(text)
        
        print(f"🌍 Idioma: {result['language']} (confianza: {result['confidence']})")
        print(f"📤 Código respuesta: {response_lang}")
        print(f"🧠 Reasoning: {result['reasoning']}")
        print(f"👋 Saludo: {config['greeting']}")
        print("-" * 40)


if __name__ == "__main__":
    test_detector()