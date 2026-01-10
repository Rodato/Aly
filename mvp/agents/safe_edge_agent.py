#!/usr/bin/env python3
"""
Safe Edge Agent - MVP System
Maneja temas sensibles con redirección segura y apropiada
"""

import os
import requests
from dotenv import load_dotenv
from typing import Dict, List

from .base_agent import BaseAgent, AgentState

load_dotenv()

class SafeEdgeAgent(BaseAgent):
    """Agente que maneja temas sensibles con redirección segura."""
    
    def __init__(self):
        super().__init__(
            name="safe_edge_agent",
            description="Maneja temas sensibles (trauma, religión, familia) con redirección a actividades de aula seguras"
        )
        
        # Configurar OpenAI GPT-4o-mini para respuestas sensibles y cuidadosas
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY no encontrada")
        
        self.headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4o-mini"
        
        self.logger.info("✅ Safe Edge Agent inicializado")
    
    def should_process(self, state: AgentState) -> bool:
        """Solo procesa consultas SENSITIVE."""
        return state.mode == "SENSITIVE"
    
    def process(self, state: AgentState) -> AgentState:
        """Procesa consulta sensible con redirección segura."""
        
        if not self.should_process(state):
            self.log_processing(state, f"Skipping - Mode: {state.mode}")
            return state
        
        self.log_processing(state, f"Procesando tema sensible: '{state.user_input[:50]}...'")
        
        try:
            # Generar respuesta de redirección segura
            safe_response = self._generate_safe_redirect(state)
            
            state.response = safe_response['answer']
            state.sources = []  # No sources para temas sensibles
            
            self.log_processing(state, "Respuesta de redirección segura generada")
            self.add_debug_info(state, "safe_redirect_used", True)
            self.add_debug_info(state, "sensitive_topic_handled", True)
            
        except Exception as e:
            self.logger.error(f"❌ Error en Safe Edge Agent: {e}")
            error_msg = self._get_error_message(state.language_config)
            state.response = error_msg
            self.add_debug_info(state, "error", str(e))
        
        return state
    
    def _generate_safe_redirect(self, state: AgentState) -> Dict:
        """Genera respuesta de redirección segura con actividad de aula."""
        
        # Crear prompt especializado para redirección segura
        prompt = self._create_safe_redirect_prompt(state)
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 400,  # Respuestas moderadas para temas sensibles
            "temperature": 0.3  # Baja creatividad para mantener seguridad
        }
        
        response = requests.post(self.api_url, headers=self.headers, json=data, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        answer = result["choices"][0]["message"]["content"].strip()
        
        return {
            'answer': answer,
            'prompt_used': prompt[:200] + "..." if len(prompt) > 200 else prompt
        }
    
    def _create_safe_redirect_prompt(self, state: AgentState) -> str:
        """Crea prompt para redirección segura según SAFE_EDGE_HANDLER spec."""
        
        language_code = state.language_config.get('code', 'es')
        user_input = state.user_input
        
        # Prompt específico por idioma siguiendo SAFE_EDGE_HANDLER spec
        if language_code == 'en':
            return f"""You are helping educators in crisis-affected environments handle sensitive topics safely. When users ask about topics that go beyond classroom practice (trauma, religion, discipline at home, family conflict, identity issues), provide an affirming redirect to safe classroom activities.

**User's sensitive topic:** {user_input}

**Your response should follow this structure:**

1. **Affirming acknowledgment:** "That's a really important issue."

2. **Safe boundary setting:** "While I can't guide you directly on that, here's one way to support students safely through your sessions."

3. **Classroom-focused redirect:** Offer a related, safe classroom activity, reflection, or strategy that:
   - Keeps focus on the educational setting
   - Avoids direct personal disclosure
   - Creates supportive environment
   - Uses activities from trusted curricula

**Guidelines:**
- Never provide therapy or family counseling advice
- Don't ask students to share personal trauma
- Focus on building general resilience and support
- Suggest activities that create safe spaces for reflection
- Keep recommendations within educator's scope

**Tone:** Empathetic, professional, boundary-aware, supportive

Remember: Redirect to what they CAN do safely in their classroom setting, not what they cannot address."""

        elif language_code == 'pt':
            return f"""Você está ajudando educadores em ambientes afetados por crises a lidar com tópicos sensíveis com segurança. Quando usuários perguntam sobre tópicos que vão além da prática de sala de aula (trauma, religião, disciplina em casa, conflito familiar, questões de identidade), forneça um redirecionamento afirmativo para atividades seguras de sala de aula.

**Tópico sensível do usuário:** {user_input}

**Sua resposta deve seguir esta estrutura:**

1. **Reconhecimento afirmativo:** "Essa é uma questão muito importante."

2. **Estabelecimento de limites seguros:** "Embora eu não possa orientar você diretamente sobre isso, aqui está uma forma de apoiar os estudantes com segurança através de suas sessões."

3. **Redirecionamento focado na sala de aula:** Ofereça uma atividade, reflexão ou estratégia relacionada e segura que:
   - Mantenha foco no ambiente educacional
   - Evite revelação pessoal direta
   - Crie ambiente de apoio
   - Use atividades de currículos confiáveis

**Diretrizes:**
- Nunca forneça terapia ou conselhos de aconselhamento familiar
- Não peça aos estudantes para compartilhar trauma pessoal
- Foque em construir resiliência geral e apoio
- Sugira atividades que criem espaços seguros para reflexão
- Mantenha recomendações dentro do escopo do educador

**Tom:** Empático, profissional, consciente de limites, solidário

Lembre-se: Redirecione para o que eles PODEM fazer com segurança em sua sala de aula, não o que não podem abordar."""

        else:  # Spanish
            return f"""Estás ayudando a educadores en ambientes afectados por crisis a manejar temas sensibles de manera segura. Cuando los usuarios preguntan sobre temas que van más allá de la práctica del aula (trauma, religión, disciplina en casa, conflicto familiar, temas de identidad), proporciona una redirección afirmativa hacia actividades seguras de aula.

**Tema sensible del usuario:** {user_input}

**Tu respuesta debe seguir esta estructura:**

1. **Reconocimiento afirmativo:** "Ese es un tema muy importante."

2. **Establecimiento de límites seguros:** "Aunque no puedo orientarte directamente sobre eso, aquí hay una forma de apoyar a los estudiantes de manera segura a través de tus sesiones."

3. **Redirección centrada en el aula:** Ofrece una actividad, reflexión o estrategia relacionada y segura que:
   - Mantenga el foco en el entorno educativo
   - Evite la revelación personal directa
   - Cree un ambiente de apoyo
   - Use actividades de currículos confiables

**Pautas:**
- Nunca proporciones terapia o consejos de consejería familiar
- No pidas a los estudiantes que compartan trauma personal
- Enfócate en construir resistencia general y apoyo
- Sugiere actividades que creen espacios seguros para reflexión
- Mantén las recomendaciones dentro del ámbito del educador

**Tono:** Empático, profesional, consciente de límites, solidario

Recuerda: Redirige hacia lo que SÍ PUEDEN hacer de manera segura en su entorno de aula, no lo que no pueden abordar."""
    
    def _get_error_message(self, language_config: Dict) -> str:
        """Mensaje de error según idioma."""
        if not language_config:
            return "Estoy aquí para ayudarte con estrategias de aula seguras. ¿Podrías reformular tu pregunta?"
        
        if language_config['code'] == 'en':
            return "I'm here to help with safe classroom strategies. Could you rephrase your question?"
        elif language_config['code'] == 'pt':
            return "Estou aqui para ajudar com estratégias seguras de sala de aula. Você poderia reformular sua pergunta?"
        else:
            return "Estoy aquí para ayudarte con estrategias de aula seguras. ¿Podrías reformular tu pregunta?"