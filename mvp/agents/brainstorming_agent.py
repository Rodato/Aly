#!/usr/bin/env python3
"""
Brainstorming Agent - MVP System
Agente especializado en modo brainstorming: pensamiento lateral, ideas innovadoras, conexiones inesperadas
"""

import os
import sys
import requests
from dotenv import load_dotenv
from typing import Dict, List

# Importar sistema RAG para inspiración
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'mongodb', 'scripts'))
from simple_rag_mongo import SimpleMongoRAG

# Importar configuración de personalidad
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from aly_personality import ALYPersonality

from .base_agent import BaseAgent, AgentState

load_dotenv()

class BrainstormingAgent(BaseAgent):
    """Agente especializado en modo brainstorming creativo e innovador."""
    
    def __init__(self):
        super().__init__(
            name="brainstorming_agent",
            description="Genera ideas innovadoras, pensamiento lateral y conexiones inesperadas para facilitadores"
        )
        
        # Configurar OpenRouter para Google Gemini 2.5-flash
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not self.openrouter_key:
            raise ValueError("OPENROUTER_API_KEY no encontrada")
        
        self.headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json"
        }
        
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "google/gemini-2.5-flash"
        
        # Inicializar sistema RAG para inspiración
        try:
            self.rag_system = SimpleMongoRAG()
            self.rag_system.language_detector = None
            self.logger.info("✅ RAG system for inspiration inicializado")
        except Exception as e:
            self.logger.warning(f"⚠️ RAG system no disponible: {e}")
            self.rag_system = None
        
        self.logger.info("✅ Brainstorming Agent inicializado")
    
    def should_process(self, state: AgentState) -> bool:
        """Solo procesa consultas IDEATE (ex-brainstorming)."""
        return state.mode == "IDEATE"
    
    def process(self, state: AgentState) -> AgentState:
        """Procesa consulta en modo brainstorming innovador."""
        
        if not self.should_process(state):
            self.log_processing(state, f"Skipping - Mode: {state.mode}")
            return state
        
        self.log_processing(state, f"Procesando brainstorming mode: '{state.user_input[:50]}...'")
        
        try:
            # Obtener inspiración diversa de múltiples fuentes
            inspiration_sources = self._get_diverse_inspiration(state)
            
            # Generar respuesta innovadora con ALY personality
            innovative_response = self._generate_innovative_response(state, inspiration_sources)
            
            state.response = innovative_response['answer']
            state.sources = inspiration_sources.get('sources', [])
            
            self.log_processing(state, "Respuesta brainstorming generada exitosamente")
            self.add_debug_info(state, "inspiration_sources", len(inspiration_sources.get('chunks', [])))
            self.add_debug_info(state, "creative_approach", "brainstorming_mode")
            self.add_debug_info(state, "temperature", "0.7 (alta creatividad)")
            
        except Exception as e:
            self.logger.error(f"❌ Error en Brainstorming Agent: {e}")
            error_msg = self._get_error_message(state.language_config)
            state.response = error_msg
            self.add_debug_info(state, "error", str(e))
        
        return state
    
    def _get_diverse_inspiration(self, state: AgentState) -> Dict:
        """Obtiene inspiración diversa de múltiples perspectivas."""
        
        if not self.rag_system:
            return {'chunks': [], 'sources': [], 'context_text': ''}
        
        try:
            # Configurar idioma
            if state.language_config:
                self.rag_system.session_language = state.language
                self.rag_system.language_config = state.language_config
            
            # Buscar inspiración con diferentes enfoques
            primary_chunks = self.rag_system.search_chunks(state.user_input, top_k=2)
            
            # Buscar perspectivas adicionales con términos relacionados
            related_terms = self._generate_related_terms(state.user_input)
            additional_chunks = []
            
            for term in related_terms[:2]:  # Solo 2 términos adicionales
                chunks = self.rag_system.search_chunks(term, top_k=1)
                if chunks:
                    additional_chunks.extend(chunks)
            
            # Combinar todas las fuentes de inspiración
            all_chunks = primary_chunks + additional_chunks
            
            if not all_chunks:
                return {'chunks': [], 'sources': [], 'context_text': ''}
            
            # Formatear inspiración para brainstorming
            inspiration_text = self._format_inspiration_sources(all_chunks[:4])
            
            sources = []
            for item in all_chunks[:4]:
                chunk = item['chunk']
                sources.append({
                    "document": chunk['document_name'],
                    "section": chunk['section_header'], 
                    "similarity": round(item['similarity'], 3),
                    "preview": chunk['content'][:100] + "...",
                    "inspiration_type": "primary" if item in primary_chunks else "lateral"
                })
            
            return {
                'chunks': all_chunks,
                'sources': sources,
                'context_text': inspiration_text
            }
            
        except Exception as e:
            self.logger.warning(f"Error obteniendo inspiración: {e}")
            return {'chunks': [], 'sources': [], 'context_text': ''}
    
    def _generate_related_terms(self, user_input: str) -> List[str]:
        """Genera términos relacionados para búsqueda lateral."""
        
        # Términos relacionados comunes en educación de género
        related_concepts = {
            "actividad": ["dinámica", "ejercicio", "metodología", "técnica"],
            "niños": ["adolescentes", "jóvenes", "participantes", "estudiantes"],
            "género": ["masculinidades", "feminidades", "identidad", "roles"],
            "educación": ["formación", "capacitación", "aprendizaje", "enseñanza"],
            "facilitación": ["moderación", "conducción", "liderazgo", "guía"]
        }
        
        related_terms = []
        user_lower = user_input.lower()
        
        for key, synonyms in related_concepts.items():
            if key in user_lower:
                related_terms.extend(synonyms[:2])  # Solo 2 sinónimos por concepto
        
        return related_terms[:3]  # Máximo 3 términos relacionados
    
    def _format_inspiration_sources(self, chunks: List) -> str:
        """Formatea las fuentes de inspiración para brainstorming."""
        
        formatted_sources = []
        for i, chunk in enumerate(chunks[:3], 1):
            content = chunk['chunk']['content']
            doc_name = chunk['chunk']['document_name']
            
            formatted_sources.append(
                f"**Inspiración {i} - {doc_name}**\n{content[:200]}..."
            )
        
        return "\n\n".join(formatted_sources)
    
    def _generate_innovative_response(self, state: AgentState, inspiration_sources: Dict) -> Dict:
        """Genera respuesta innovadora usando personalidad ALY."""
        
        # Crear prompt especializado para brainstorming con personalidad ALY
        prompt = self._create_brainstorming_prompt(state, inspiration_sources)
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 700,  # Más tokens para exploración creativa
            "temperature": 0.7  # Alta creatividad para brainstorming
        }
        
        response = requests.post(self.api_url, headers=self.headers, json=data, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        answer = result["choices"][0]["message"]["content"].strip()
        
        return {
            'answer': answer,
            'prompt_used': prompt[:200] + "..." if len(prompt) > 200 else prompt
        }
    
    def _create_brainstorming_prompt(self, state: AgentState, inspiration_sources: Dict) -> str:
        """Crea prompt especializado para generación de ideas siguiendo meta prompt spec."""
        
        language_code = state.language_config.get('code', 'es')
        inspiration_text = inspiration_sources.get('context_text', '')
        user_input = state.user_input
        
        # Prompt específico por idioma siguiendo BRAINSTORMING AGENT PROMPT spec
        if language_code == 'en':
            return f"""You are a creative facilitator guide for educators in crisis-affected or low-resource environments. Offer 3–5 inclusive and safe activity ideas based on the user's topic or goal. Your job is to spark options, not provide a final answer.

**Inspiration from trusted programs:**
{inspiration_text}

**User's creative goal:** {user_input}

Structure:

**Topic:** [Brief summary of their creative goal]

Here are some ideas to explore:

1. **[Activity Title]** — [1-line summary of the approach]
   Try: [Short example or specific phrasing they could use]

2. **[Activity Title]** — [1-line summary]
   Try: [Concrete example]

3. **[Activity Title]** — [1-line summary]
   Try: [Practical example]

4. **[Activity Title]** — [1-line summary]  
   Try: [Actionable example]

5. **[Activity Title]** — [1-line summary]
   Try: [Realistic example]

**Tone Guidelines:**
- Curious, supportive, and flexible
- Never judgmental or moralizing  
- Don't use academic terms like "intervention" or "learning objective"
- Keep it practical and doable

**Edge Handling:**
- If topic involves gender/religion/family: "Let's try a version that leaves space for different perspectives."
- If input is too vague: "Here are a few ways this could go — which one fits your setting?"

Remember: Spark creative options from trusted educational approaches, but don't prescribe final solutions."""

        elif language_code == 'pt':
            return f"""Você é um guia facilitador criativo para educadores em ambientes afetados por crises ou com poucos recursos. Ofereça 3-5 ideias de atividades inclusivas e seguras baseadas no tópico ou objetivo do usuário. Seu trabalho é gerar opções, não fornecer uma resposta final.

**Inspiração de programas confiáveis:**
{inspiration_text}

**Objetivo criativo do usuário:** {user_input}

Estrutura:

**Tópico:** [Resumo breve do objetivo criativo]

Aqui estão algumas ideias para explorar:

1. **[Título da Atividade]** — [Resumo de 1 linha da abordagem]
   Tente: [Exemplo curto ou frase específica que poderiam usar]

2. **[Título da Atividade]** — [Resumo de 1 linha]
   Tente: [Exemplo concreto]

3. **[Título da Atividade]** — [Resumo de 1 linha]
   Tente: [Exemplo prático]

4. **[Título da Atividade]** — [Resumo de 1 linha]
   Tente: [Exemplo acionável]

5. **[Título da Atividade]** — [Resumo de 1 linha]
   Tente: [Exemplo realista]

**Diretrizes de Tom:**
- Curioso, apoiador e flexível
- Nunca julgador ou moralizador
- Não use termos acadêmicos como "intervenção" ou "objetivo de aprendizagem"
- Mantenha prático e realizável

**Manejo de Casos Sensíveis:**
- Se o tópico envolve gênero/religião/família: "Vamos tentar uma versão que deixe espaço para diferentes perspectivas."
- Se entrada é muito vaga: "Aqui estão algumas formas que isso poderia seguir — qual se adapta ao seu contexto?"

Lembre-se: Gere opções criativas de abordagens educacionais confiáveis, mas não prescreva soluções finais."""

        else:  # Spanish
            return f"""Eres un guía facilitador creativo para educadores en ambientes afectados por crisis o con pocos recursos. Ofrece 3-5 ideas de actividades inclusivas y seguras basadas en el tema o objetivo del usuario. Tu trabajo es generar opciones, no proporcionar una respuesta final.

**Inspiración de programas confiables:**
{inspiration_text}

**Objetivo creativo del usuario:** {user_input}

Estructura:

**Tema:** [Resumen breve de su objetivo creativo]

Aquí hay algunas ideas para explorar:

1. **[Título de Actividad]** — [Resumen de 1 línea del enfoque]
   Prueba: [Ejemplo corto o frase específica que podrían usar]

2. **[Título de Actividad]** — [Resumen de 1 línea]
   Prueba: [Ejemplo concreto]

3. **[Título de Actividad]** — [Resumen de 1 línea]
   Prueba: [Ejemplo práctico]

4. **[Título de Actividad]** — [Resumen de 1 línea]
   Prueba: [Ejemplo accionable]

5. **[Título de Actividad]** — [Resumen de 1 línea]
   Prueba: [Ejemplo realista]

**Pautas de Tono:**
- Curioso, solidario y flexible
- Nunca juzgador o moralizador
- No uses términos académicos como "intervención" u "objetivo de aprendizaje"
- Manténlo práctico y factible

**Manejo de Casos Sensibles:**
- Si el tema involucra género/religión/familia: "Probemos una versión que deje espacio para diferentes perspectivas."
- Si la entrada es muy vaga: "Aquí hay algunas formas en que esto podría ir — ¿cuál se adapta a tu contexto?"

Recuerda: Genera opciones creativas de enfoques educativos confiables, pero no prescribas soluciones finales."""
    
    def _get_error_message(self, language_config: Dict) -> str:
        """Mensaje de error según idioma con personalidad ALY."""
        if not language_config:
            return "¡Ups! Tuve un problema generando ideas innovadoras. ¿Intentamos de nuevo?"
        
        if language_config['code'] == 'en':
            return "Oops! I had trouble generating innovative ideas. Shall we try again?"
        elif language_config['code'] == 'pt':
            return "Ops! Tive problemas gerando ideias inovadoras. Tentamos novamente?"
        else:
            return "¡Ups! Tuve un problema generando ideas innovadoras. ¿Intentamos de nuevo?"