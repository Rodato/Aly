#!/usr/bin/env python3
"""
Agent Orchestrator - MVP System
Orquestador principal del sistema de agentes usando LangGraph
"""

import logging
from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END

from agents.base_agent import AgentState
from agents.language_agent import LanguageAgent
from agents.mode_detection_agent import ModeDetectionAgent
from agents.rag_agent import RAGAgent
from agents.workshop_agent import WorkshopAgent
from agents.brainstorming_agent import BrainstormingAgent
from agents.safe_edge_agent import SafeEdgeAgent
from agents.fallback_agent import FallbackAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GraphState(TypedDict):
    """Estado del grafo de LangGraph."""
    user_input: str
    language: str
    language_config: Dict
    mode: str
    mode_confidence: float
    response: str
    sources: list
    debug_info: Dict

class AgentOrchestrator:
    """
    Orquestador principal del sistema de agentes educativos.
    
    Arquitectura: Educational assistant supporting facilitators in crisis-affected 
    or low-resource environments. Helps them apply, adapt, or generate ideas from 
    trusted programs. Always practical, inclusive, emotionally safe, and grounded 
    in structured curriculum. Avoids speculation, judgment, or therapeutic advice.
    """
    
    def __init__(self):
        # Inicializar agentes educativos
        self.language_agent = LanguageAgent()
        self.mode_agent = ModeDetectionAgent()  # Intent Router
        self.rag_agent = RAGAgent()              # FACTUAL queries
        self.workshop_agent = WorkshopAgent()    # PLAN queries (adapt/implement)
        self.brainstorming_agent = BrainstormingAgent()  # IDEATE queries (new ideas)
        self.safe_edge_agent = SafeEdgeAgent()   # SENSITIVE topics
        self.fallback_agent = FallbackAgent()   # AMBIGUOUS inputs
        
        # Crear grafo de workflow educativo
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile()
        
        logger.info("🎓 Educational Agent Orchestrator inicializado")
    
    def _create_workflow(self) -> StateGraph:
        """Crea el workflow de agentes."""
        
        workflow = StateGraph(GraphState)
        
        # Agregar nodos educativos
        workflow.add_node("detect_language", self._language_node)
        workflow.add_node("detect_intent", self._intent_node)  # Intent Router
        workflow.add_node("factual_response", self._factual_node)     # RAG Agent
        workflow.add_node("plan_response", self._plan_node)           # Workshop Agent  
        workflow.add_node("ideate_response", self._ideate_node)       # Brainstorming Agent
        workflow.add_node("sensitive_response", self._sensitive_node) # Safe Edge Agent
        workflow.add_node("clarify_response", self._clarify_node)     # Fallback Agent
        
        # Definir flujo educativo
        workflow.set_entry_point("detect_language")
        
        # Language -> Intent Detection (Intent Router)
        workflow.add_edge("detect_language", "detect_intent")
        
        # Intent Router -> Conditional routing según nueva arquitectura
        workflow.add_conditional_edges(
            "detect_intent",
            self._route_by_intent,
            {
                "FACTUAL": "factual_response",      # Información específica → RAG
                "PLAN": "plan_response",            # Adaptar/implementar → Workshop
                "IDEATE": "ideate_response",        # Nuevas ideas → Brainstorming  
                "SENSITIVE": "sensitive_response",  # Temas sensibles → Safe Edge
                "AMBIGUOUS": "clarify_response"     # Input ambiguo → Fallback
            }
        )
        
        # Finalizaciones
        workflow.add_edge("factual_response", END)
        workflow.add_edge("plan_response", END)
        workflow.add_edge("ideate_response", END)
        workflow.add_edge("sensitive_response", END)
        workflow.add_edge("clarify_response", END)
        
        return workflow
    
    def _language_node(self, state: GraphState) -> GraphState:
        """Nodo de detección de idioma."""
        agent_state = AgentState(user_input=state["user_input"])
        result = self.language_agent.process(agent_state)
        
        return {
            **state,
            "language": result.language,
            "language_config": result.language_config,
            "debug_info": result.debug_info or {}
        }
    
    def _intent_node(self, state: GraphState) -> GraphState:
        """Nodo Intent Router - detecta PLAN/IDEATE/FACTUAL/AMBIGUOUS/SENSITIVE."""
        agent_state = AgentState(
            user_input=state["user_input"],
            language=state["language"],
            language_config=state["language_config"]
        )
        result = self.mode_agent.process(agent_state)
        
        debug_info = state.get("debug_info", {})
        if result.debug_info:
            debug_info.update(result.debug_info)
        
        return {
            **state,
            "mode": result.mode,
            "mode_confidence": result.mode_confidence,
            "debug_info": debug_info
        }
    
    def _factual_node(self, state: GraphState) -> GraphState:
        """Nodo FACTUAL - información específica usando RAG."""
        agent_state = AgentState(
            user_input=state["user_input"],
            language=state["language"],
            language_config=state["language_config"],
            mode=state["mode"]
        )
        result = self.rag_agent.process(agent_state)
        
        debug_info = state.get("debug_info", {})
        if result.debug_info:
            debug_info.update(result.debug_info)
        
        return {
            **state,
            "response": result.response,
            "sources": result.sources or [],
            "debug_info": debug_info
        }
    
    def _plan_node(self, state: GraphState) -> GraphState:
        """Nodo PLAN - adaptar/implementar algo conocido usando Workshop Agent."""
        agent_state = AgentState(
            user_input=state["user_input"],
            language=state["language"],
            language_config=state["language_config"],
            mode=state["mode"]
        )
        result = self.workshop_agent.process(agent_state)
        
        debug_info = state.get("debug_info", {})
        if result.debug_info:
            debug_info.update(result.debug_info)
        
        return {
            **state,
            "response": result.response,
            "sources": result.sources or [],
            "debug_info": debug_info
        }
    
    def _ideate_node(self, state: GraphState) -> GraphState:
        """Nodo IDEATE - nuevas ideas/inspiración usando Brainstorming Agent."""
        agent_state = AgentState(
            user_input=state["user_input"],
            language=state["language"],
            language_config=state["language_config"],
            mode=state["mode"]
        )
        result = self.brainstorming_agent.process(agent_state)
        
        debug_info = state.get("debug_info", {})
        if result.debug_info:
            debug_info.update(result.debug_info)
        
        return {
            **state,
            "response": result.response,
            "sources": result.sources or [],
            "debug_info": debug_info
        }
    
    def _sensitive_node(self, state: GraphState) -> GraphState:
        """Nodo SENSITIVE - temas sensibles usando Safe Edge Agent."""
        agent_state = AgentState(
            user_input=state["user_input"],
            language=state["language"],
            language_config=state["language_config"],
            mode=state["mode"]
        )
        result = self.safe_edge_agent.process(agent_state)
        
        debug_info = state.get("debug_info", {})
        if result.debug_info:
            debug_info.update(result.debug_info)
        
        return {
            **state,
            "response": result.response,
            "sources": result.sources or [],
            "debug_info": debug_info
        }
    
    def _clarify_node(self, state: GraphState) -> GraphState:
        """Nodo AMBIGUOUS - clarificación usando Fallback Agent."""
        agent_state = AgentState(
            user_input=state["user_input"],
            language=state["language"],
            language_config=state["language_config"],
            mode=state["mode"]
        )
        result = self.fallback_agent.process(agent_state)
        
        debug_info = state.get("debug_info", {})
        if result.debug_info:
            debug_info.update(result.debug_info)
        
        return {
            **state,
            "response": result.response,
            "sources": result.sources or [],
            "debug_info": debug_info
        }
    
    def _route_by_intent(self, state: GraphState) -> str:
        """
        Rutea según el intent detectado por el Intent Router.
        
        INTENT ROUTER LOGIC:
        - PLAN → If user wants to adapt or implement something they already know (route to PLAN_AGENT)
        - IDEATE → If user wants new ideas, variations, or inspiration (route to BRAINSTORM_AGENT) 
        - FACTUAL → If user seeks specific information, definitions, or facts
        - AMBIGUOUS → If input is unclear or broad, return clarification options
        - SENSITIVE → If topic involves gender, religion, family conflict, identity, trauma
        """
        intent = state.get("mode", "FACTUAL")  # Fallback a FACTUAL
        
        logger.info(f"🎓 Intent Router: '{intent}' → Routing to appropriate educational agent")
        
        # Return the intent key which maps to node names in conditional_edges
        # The mapping is defined in _create_workflow() lines 84-90
        return intent
    
    def _get_agent_type(self, intent: str) -> str:
        """Mapea intent a tipo de agente para claridad."""
        mapping = {
            "PLAN": "planning_assistant",      # Workshop Agent  
            "IDEATE": "creative_guide",        # Brainstorming Agent
            "FACTUAL": "knowledge_base",       # RAG Agent
            "SENSITIVE": "safe_edge_handler",  # Safe Edge Agent
            "AMBIGUOUS": "clarification_helper" # Fallback Agent
        }
        return mapping.get(intent, "knowledge_base")
    
    def process_query(self, user_input: str, debug: bool = False) -> Dict[str, Any]:
        """
        Procesa una consulta del usuario a través del sistema de agentes.
        
        Args:
            user_input: Mensaje del usuario
            debug: Si incluir información de debug
            
        Returns:
            Dict con respuesta y metadatos
        """
        logger.info(f"🎓 Educational Assistant: Procesando consulta '{user_input[:50]}...'")
        
        try:
            # Estado inicial para facilitadores educativos
            initial_state = {
                "user_input": user_input,
                "language": None,
                "language_config": {},
                "mode": None,           # Intent: PLAN/IDEATE/FACTUAL/AMBIGUOUS/SENSITIVE
                "mode_confidence": 0.0,
                "response": "",
                "sources": [],
                "debug_info": {}
            }
            
            # Ejecutar workflow educativo: Language → Intent Router → Agent
            final_state = self.app.invoke(initial_state)
            
            # Preparar respuesta educativa
            response = {
                "query": user_input,
                "answer": final_state["response"],
                "language": final_state["language"],
                "language_name": final_state.get("language_config", {}).get("name", "Unknown"),
                "intent": final_state["mode"],           # PLAN/IDEATE/FACTUAL/etc
                "intent_confidence": final_state["mode_confidence"],
                "sources": final_state["sources"],
                "agent_type": self._get_agent_type(final_state["mode"])
            }
            
            if debug:
                response["debug_info"] = final_state["debug_info"]
            
            logger.info(f"✅ Educational query processed: Intent={final_state['mode']}, Language={final_state['language']}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error procesando consulta: {e}")
            
            return {
                "query": user_input,
                "answer": "Error procesando tu consulta. Intenta de nuevo.",
                "language": "es",
                "language_name": "Español",
                "mode": "error",
                "mode_confidence": 0.0,
                "sources": [],
                "error": str(e)
            }
    
    def get_session_greeting(self, user_input: str) -> str:
        """Obtiene saludo inicial basado en idioma detectado."""
        try:
            agent_state = AgentState(user_input=user_input)
            result = self.language_agent.process(agent_state)
            
            if result.language_config and 'greeting' in result.language_config:
                return result.language_config['greeting']
            else:
                return "¡Hola! Soy Aly, tu asistente educativo. ¿Cómo puedo ayudarte hoy?"
        except Exception:
            return "¡Hola! Soy Aly, tu asistente educativo. ¿Cómo puedo ayudarte hoy?"


def test_orchestrator():
    """Función de prueba del orquestador."""
    orchestrator = AgentOrchestrator()
    
    test_cases = [
        "¿Qué es la educación de género?",              # FACTUAL ES
        "¿Cómo adapto esta actividad para niños más pequeños?",  # PLAN ES  
        "Dame ideas creativas para involucrar niños",   # IDEATE ES
        "¿Cómo manejo estudiantes con trauma?",         # SENSITIVE ES
        "Ayúdame con mi clase",                          # AMBIGUOUS ES
        "What is gender education?",                     # FACTUAL EN
        "How do I adapt this activity for younger kids?", # PLAN EN
        "Give me creative ideas to engage children",     # IDEATE EN
        "Help me with my class"                          # AMBIGUOUS EN
    ]
    
    print("🧪 PROBANDO SISTEMA DE AGENTES")
    print("=" * 60)
    
    for i, query in enumerate(test_cases, 1):
        print(f"\n{i}. Query: '{query}'")
        
        result = orchestrator.process_query(query, debug=True)
        
        print(f"   🌍 Idioma: {result['language_name']} ({result['language']})")
        print(f"   🎯 Intent: {result['intent']} (confianza: {result['intent_confidence']})")
        print(f"   🤖 Agente: {result['agent_type']}")
        print(f"   💬 Respuesta: {result['answer'][:100]}...")
        print(f"   📚 Fuentes: {len(result['sources'])}")

if __name__ == "__main__":
    test_orchestrator()