#!/usr/bin/env python3
"""
Workshop Agent - MVP System
Agente especializado en modo workshop: ideas creativas, brainstorming, adaptaciones
"""

import os
import sys
import requests
from dotenv import load_dotenv
from typing import Dict, List

# Importar sistema RAG para contexto
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'mongodb', 'scripts'))
from simple_rag_mongo import SimpleMongoRAG

# Importar configuración de personalidad ALY
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from aly_personality import ALYPersonality

from .base_agent import BaseAgent, AgentState

load_dotenv()

class WorkshopAgent(BaseAgent):
    """Agente especializado en modo workshop estructurado y metodológico con personalidad ALY."""
    
    def __init__(self):
        super().__init__(
            name="workshop_agent",
            description="Proporciona orientación metodológica estructurada y mejores prácticas con personalidad ALY"
        )
        
        # Configurar OpenAI API para GPT-4o-mini
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY no encontrada")
        
        self.headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4o-mini"
        
        # Inicializar sistema RAG para obtener contexto
        try:
            self.rag_system = SimpleMongoRAG()
            self.rag_system.language_detector = None
            self.logger.info("✅ RAG system for context inicializado")
        except Exception as e:
            self.logger.warning(f"⚠️ RAG system no disponible: {e}")
            self.rag_system = None
        
        self.logger.info("✅ Workshop Agent inicializado")
    
    def should_process(self, state: AgentState) -> bool:
        """Solo procesa consultas PLAN (ex-workshop)."""
        return state.mode == "PLAN"
    
    def process(self, state: AgentState) -> AgentState:
        """Procesa consulta en modo workshop creativo."""
        
        if not self.should_process(state):
            self.log_processing(state, f"Skipping - Mode: {state.mode}")
            return state
        
        self.log_processing(state, f"Procesando workshop mode: '{state.user_input[:50]}...'")
        
        try:
            # Obtener contexto relevante de la base de conocimiento
            context_info = self._get_relevant_context(state)
            
            # Generar respuesta creativa
            creative_response = self._generate_creative_response(state, context_info)
            
            state.response = creative_response['answer']
            state.sources = context_info.get('sources', [])
            
            self.log_processing(state, "Respuesta workshop generada exitosamente")
            self.add_debug_info(state, "context_chunks", len(context_info.get('chunks', [])))
            self.add_debug_info(state, "creative_approach", "workshop_mode")
            
        except Exception as e:
            self.logger.error(f"❌ Error en Workshop Agent: {e}")
            error_msg = self._get_error_message(state.language_config)
            state.response = error_msg
            self.add_debug_info(state, "error", str(e))
        
        return state
    
    def _get_relevant_context(self, state: AgentState) -> Dict:
        """Obtiene contexto relevante de la base de conocimiento."""

        if not self.rag_system:
            return {'chunks': [], 'sources': [], 'context_text': ''}

        try:
            # Configurar idioma
            if state.language_config:
                self.rag_system.session_language = state.language
                self.rag_system.language_config = state.language_config

            # Extraer filtros detectados (si existen)
            filters = None
            if state.metadata and 'detected_filters' in state.metadata:
                filter_data = state.metadata['detected_filters']
                if filter_data.get('has_filters'):
                    filters = filter_data.get('mongodb_filters')
                    self.logger.info(f"Aplicando filtros en Workshop: {filters}")

            # Buscar contexto relevante (con filtros si existen)
            chunks = self.rag_system.search_chunks(state.user_input, top_k=3, filters=filters)

            if not chunks:
                return {'chunks': [], 'sources': [], 'context_text': ''}

            # Formatear contexto para inspiración
            context_text = "\n\n".join([
                f"**{chunk['chunk']['document_name']}**\n{chunk['chunk']['content']}"
                for chunk in chunks[:2]  # Solo top 2 para no saturar
            ])

            sources = []
            for item in chunks[:3]:
                chunk = item['chunk']
                sources.append({
                    "document": chunk['document_name'],
                    "section": chunk['section_header'],
                    "similarity": round(item['similarity'], 3),
                    "preview": chunk['content'][:150] + "..."
                })

            return {
                'chunks': chunks,
                'sources': sources,
                'context_text': context_text
            }

        except Exception as e:
            self.logger.warning(f"Error obteniendo contexto: {e}")
            return {'chunks': [], 'sources': [], 'context_text': ''}
    
    def _generate_creative_response(self, state: AgentState, context_info: Dict) -> Dict:
        """Genera respuesta creativa usando contexto como inspiración."""
        
        # Crear prompt especializado para workshop
        prompt = self._create_workshop_prompt(state, context_info)
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 600,  # Suficientes tokens para orientación detallada
            "temperature": 0.5  # Creatividad moderada para metodología
        }
        
        response = requests.post(self.api_url, headers=self.headers, json=data, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        answer = result["choices"][0]["message"]["content"].strip()
        
        return {
            'answer': answer,
            'prompt_used': prompt[:200] + "..." if len(prompt) > 200 else prompt
        }
    
    def _create_workshop_prompt(self, state: AgentState, context_info: Dict) -> str:
        """Crea prompt estructurado para facilitadores en contextos educativos."""
        
        language_code = state.language_config.get('code', 'es')
        context_text = context_info.get('context_text', '')
        user_input = state.user_input
        
        # Prompt específico por idioma siguiendo el meta prompt spec
        if language_code == 'en':
            return f"""You are a planning assistant for educators in crisis-affected or low-resource environments. Help the user turn a known activity, challenge, or lesson into a small, clear, realistic plan they can apply in their next session.

**Context from trusted programs:**
{context_text}

**User's planning need:** {user_input}

Structure your response as:

**Topic:** [Brief summary of what they want to adapt/implement]

**Suggested Plan:**
1. [First concrete step]
2. [Second step] 
3. [Third step - keep it realistic]

**Tips:**
- [Practical adaptation tip]
- [Cultural/context consideration]
- [Time/resource management tip]

**Sample Phrase:** "[Something they could actually say to students]"

**Reminder:** You can adjust this based on your students' needs.

**Safety Layer:**
- If this seems overwhelming, let's break it into one small thing you could try first.
- If this touches sensitive topics, here's one way to invite reflection without forcing disclosure.

Remember: Only adapt what's already known from trusted curricula. Do not invent new strategies or give advice on family/therapy issues."""

        elif language_code == 'pt':
            return f"""Você é um assistente de planejamento para educadores em ambientes afetados por crises ou com poucos recursos. Ajude o usuário a transformar uma atividade, desafio ou lição conhecida em um plano pequeno, claro e realista que podem aplicar em sua próxima sessão.

**Contexto de programas confiáveis:**
{context_text}

**Necessidade de planejamento do usuário:** {user_input}

Estruture sua resposta como:

**Tópico:** [Resumo breve do que querem adaptar/implementar]

**Plano Sugerido:**
1. [Primeiro passo concreto]
2. [Segundo passo]
3. [Terceiro passo - mantenha realista]

**Dicas:**
- [Dica de adaptação prática]
- [Consideração cultural/contextual]
- [Dica de gestão de tempo/recursos]

**Frase de Exemplo:** "[Algo que realmente poderiam dizer aos estudantes]"

**Lembrete:** Você pode ajustar isso baseado nas necessidades de seus estudantes.

**Camada de Segurança:**
- Se isso parecer demais, vamos quebrar em uma coisa pequena que você poderia tentar primeiro.
- Se isso toca tópicos sensíveis, aqui está uma forma de convidar reflexão sem forçar revelação.

Lembre-se: Apenas adapte o que já é conhecido de currículos confiáveis. Não invente novas estratégias ou dê conselhos sobre questões familiares/terapia."""

        else:  # Spanish
            return f"""Eres un asistente de planificación para educadores en ambientes afectados por crisis o con pocos recursos. Ayuda al usuario a convertir una actividad, desafío o lección conocida en un plan pequeño, claro y realista que puedan aplicar en su próxima sesión.

**Contexto de programas confiables:**
{context_text}

**Necesidad de planificación del usuario:** {user_input}

Estructura tu respuesta como:

**Tema:** [Resumen breve de lo que quieren adaptar/implementar]

**Plan Sugerido:**
1. [Primer paso concreto]
2. [Segundo paso]
3. [Tercer paso - manténlo realista]

**Tips:**
- [Consejo de adaptación práctica]
- [Consideración cultural/contextual]
- [Consejo de manejo de tiempo/recursos]

**Frase de Ejemplo:** "[Algo que realmente podrían decir a los estudiantes]"

**Recordatorio:** Puedes ajustar esto según las necesidades de tus estudiantes.

**Capa de Seguridad:**
- Si esto parece abrumador, dividamos esto en una cosa pequeña que podrías intentar primero.
- Si esto toca temas sensibles, aquí hay una forma de invitar reflexión sin forzar revelación.

Recuerda: Solo adapta lo que ya es conocido de currículos confiables. No inventes nuevas estrategias o des consejos sobre temas familiares/terapia."""
    
    def _get_error_message(self, language_config: Dict) -> str:
        """Mensaje de error según idioma con personalidad ALY."""
        if not language_config:
            return "Disculpa, tuve un problema al preparar la guía metodológica. ¿Intentamos de nuevo?"
        
        if language_config['code'] == 'en':
            return "Sorry, I had trouble preparing the methodological guidance. Shall we try again?"
        elif language_config['code'] == 'pt':
            return "Desculpe, tive problemas preparando a orientação metodológica. Tentamos novamente?"
        else:
            return "Disculpa, tuve un problema al preparar la guía metodológica. ¿Intentamos de nuevo?"