#!/usr/bin/env python3
"""
Fallback Agent - MVP System
Maneja inputs ambiguos ofreciendo clarificaciones útiles
"""

import os
import requests
from dotenv import load_dotenv
from typing import Dict, List

from .base_agent import BaseAgent, AgentState

load_dotenv()

class FallbackAgent(BaseAgent):
    """Agente que maneja inputs ambiguos con opciones de clarificación."""
    
    def __init__(self):
        super().__init__(
            name="fallback_agent",
            description="Maneja inputs ambiguos ofreciendo opciones de clarificación útiles"
        )
        
        # Configurar Ministral-8b para clarificaciones rápidas
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not self.openrouter_key:
            raise ValueError("OPENROUTER_API_KEY no encontrada")
        
        self.headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json"
        }
        
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "mistralai/ministral-8b"
        
        self.logger.info("✅ Fallback Agent inicializado")
    
    def should_process(self, state: AgentState) -> bool:
        """Solo procesa consultas AMBIGUOUS."""
        return state.mode == "AMBIGUOUS"
    
    def process(self, state: AgentState) -> AgentState:
        """Procesa consulta ambigua ofreciendo opciones de clarificación."""
        
        if not self.should_process(state):
            self.log_processing(state, f"Skipping - Mode: {state.mode}")
            return state
        
        self.log_processing(state, f"Procesando input ambiguo: '{state.user_input[:50]}...'")
        
        try:
            # Generar respuesta de clarificación
            clarification_response = self._generate_clarification_options(state)
            
            state.response = clarification_response['answer']
            state.sources = []  # No sources para clarificaciones
            
            self.log_processing(state, "Opciones de clarificación generadas")
            self.add_debug_info(state, "clarification_provided", True)
            self.add_debug_info(state, "ambiguous_input_handled", True)
            
        except Exception as e:
            self.logger.error(f"❌ Error en Fallback Agent: {e}")
            error_msg = self._get_error_message(state.language_config)
            state.response = error_msg
            self.add_debug_info(state, "error", str(e))
        
        return state
    
    def _generate_clarification_options(self, state: AgentState) -> Dict:
        """Genera opciones de clarificación para input ambiguo."""
        
        # Crear prompt especializado para clarificación
        prompt = self._create_clarification_prompt(state)
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 250,  # Respuestas concisas para clarificación
            "temperature": 0.2  # Baja temperatura para claridad
        }
        
        response = requests.post(self.api_url, headers=self.headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        answer = result["choices"][0]["message"]["content"].strip()
        
        return {
            'answer': answer,
            'prompt_used': prompt[:200] + "..." if len(prompt) > 200 else prompt
        }
    
    def _create_clarification_prompt(self, state: AgentState) -> str:
        """Crea prompt para clarificación según FALLBACK PROMPT spec."""
        
        language_code = state.language_config.get('code', 'es')
        user_input = state.user_input
        
        # Prompt específico por idioma siguiendo FALLBACK PROMPT spec
        if language_code == 'en':
            return f"""You are helping educators clarify their needs. The user's input is unclear or too broad.

**Unclear input:** {user_input}

**Your response should:**

1. Acknowledge their request warmly
2. Offer specific clarification options

**Format:**
"Just to be sure — are you looking to:
1) **Explore ideas** for [specific topic they mentioned]? or  
2) **Adapt something** you're already using for [context]?"

If still unclear after this, suggest:
"Would you like to see a few activities others have used for this topic?"

**Guidelines:**
- Keep tone supportive and non-judgmental
- Offer 2 clear, actionable options
- Don't overwhelm with too many choices
- Make options specific to educational contexts
- Help them narrow down to either planning (PLAN) or ideating (IDEATE)

**Example:**
Input: "Help me with my class"
Response: "Just to be sure — are you looking to: 1) Explore ideas for engaging your students? or 2) Adapt a specific activity you're already using?"

Keep it conversational and helpful."""

        elif language_code == 'pt':
            return f"""Você está ajudando educadores a esclarecer suas necessidades. A entrada do usuário é pouco clara ou muito ampla.

**Entrada pouco clara:** {user_input}

**Sua resposta deve:**

1. Reconhecer a solicitação com cordialidade
2. Oferecer opções específicas de esclarecimento

**Formato:**
"Só para ter certeza — você está procurando:
1) **Explorar ideias** para [tópico específico que mencionaram]? ou
2) **Adaptar algo** que já está usando para [contexto]?"

Se ainda não estiver claro, sugira:
"Gostaria de ver algumas atividades que outros usaram para este tópico?"

**Diretrizes:**
- Mantenha tom solidário e sem julgamento
- Ofereça 2 opções claras e acionáveis
- Não sobrecarregue com muitas escolhas
- Torne as opções específicas para contextos educacionais
- Ajude-os a definir entre planejamento (PLAN) ou ideação (IDEATE)

**Exemplo:**
Entrada: "Me ajude com minha turma"
Resposta: "Só para ter certeza — você está procurando: 1) Explorar ideias para engajar seus estudantes? ou 2) Adaptar uma atividade específica que já está usando?"

Mantenha conversacional e útil."""

        else:  # Spanish
            return f"""Estás ayudando a educadores a aclarar sus necesidades. La entrada del usuario es poco clara o demasiado amplia.

**Entrada poco clara:** {user_input}

**Tu respuesta debe:**

1. Reconocer su solicitud con cordialidad
2. Ofrecer opciones específicas de aclaración

**Formato:**
"Solo para estar seguro — ¿estás buscando:
1) **Explorar ideas** para [tópico específico que mencionaron]? o
2) **Adaptar algo** que ya estás usando para [contexto]?"

Si aún no está claro, sugiere:
"¿Te gustaría ver algunas actividades que otros han usado para este tema?"

**Pautas:**
- Mantén tono solidario y sin juicio
- Ofrece 2 opciones claras y accionables
- No sobrecargues con demasiadas opciones
- Haz las opciones específicas para contextos educativos
- Ayúdalos a definir entre planificación (PLAN) o ideación (IDEATE)

**Ejemplo:**
Entrada: "Ayúdame con mi clase"
Respuesta: "Solo para estar seguro — ¿estás buscando: 1) Explorar ideas para involucrar a tus estudiantes? o 2) Adaptar una actividad específica que ya estás usando?"

Manténlo conversacional y útil."""
    
    def _get_error_message(self, language_config: Dict) -> str:
        """Mensaje de error según idioma."""
        if not language_config:
            return "¿Podrías contarme un poco más sobre lo que necesitas ayuda?"
        
        if language_config['code'] == 'en':
            return "Could you tell me a bit more about what you need help with?"
        elif language_config['code'] == 'pt':
            return "Você poderia me contar um pouco mais sobre o que precisa de ajuda?"
        else:
            return "¿Podrías contarme un poco más sobre lo que necesitas ayuda?"