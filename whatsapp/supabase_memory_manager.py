#!/usr/bin/env python3
"""
Supabase Memory Manager for WhatsApp ALY Bot
Gestiona conversaciones, usuarios y memoria contextual
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# Configurar logging
logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    """Perfil de usuario con preferencias y contexto"""
    id: str
    phone_number: str
    preferred_language: str = 'es'
    total_messages: int = 0
    user_context: dict = None
    first_interaction: datetime = None
    last_interaction: datetime = None

@dataclass
class ConversationSession:
    """Sesión de conversación con metadatos"""
    id: str
    user_id: str
    phone_number: str
    session_started_at: datetime
    message_count: int = 0
    detected_topics: List[str] = None
    session_language: str = 'es'
    is_active: bool = True

@dataclass
class ConversationMemory:
    """Entrada de memoria conversacional"""
    id: str
    conversation_id: str
    memory_type: str
    memory_content: str
    importance_score: float = 0.5
    last_referenced: datetime = None

class SupabaseMemoryManager:
    """
    Administrador de memoria conversacional usando Supabase
    """
    
    def __init__(self):
        """Inicializar conexión a Supabase"""
        # Cargar variables de entorno
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
        
        # Configurar cliente Supabase
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("Faltan credenciales de Supabase en .env")
        
        self.client: Client = create_client(supabase_url, supabase_key)
        logger.info("✅ Supabase Memory Manager inicializado")
    
    # ===============================================================
    # USER MANAGEMENT
    # ===============================================================
    
    def get_or_create_user(self, phone_number: str, preferred_language: str = 'es') -> UserProfile:
        """
        Obtener usuario existente o crear uno nuevo
        """
        try:
            # Buscar usuario existente
            result = self.client.table('users').select('*').eq('phone_number', phone_number).execute()
            
            if result.data:
                user_data = result.data[0]
                return UserProfile(
                    id=user_data['id'],
                    phone_number=user_data['phone_number'],
                    preferred_language=user_data['preferred_language'],
                    total_messages=user_data['total_messages'],
                    user_context=user_data['user_context'] or {},
                    first_interaction=datetime.fromisoformat(user_data['first_interaction_at'].replace('Z', '+00:00')),
                    last_interaction=datetime.fromisoformat(user_data['last_interaction_at'].replace('Z', '+00:00'))
                )
            
            # Crear nuevo usuario
            new_user = {
                'phone_number': phone_number,
                'preferred_language': preferred_language,
                'user_context': {}
            }
            
            result = self.client.table('users').insert(new_user).execute()
            
            if result.data:
                user_data = result.data[0]
                logger.info(f"👤 Nuevo usuario creado: {phone_number}")
                return UserProfile(
                    id=user_data['id'],
                    phone_number=user_data['phone_number'],
                    preferred_language=user_data['preferred_language'],
                    total_messages=0,
                    user_context={},
                    first_interaction=datetime.now(),
                    last_interaction=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"❌ Error gestionando usuario {phone_number}: {e}")
            raise
    
    def update_user_language(self, user_id: str, language: str):
        """Actualizar idioma preferido del usuario"""
        try:
            self.client.table('users').update({
                'preferred_language': language,
                'updated_at': datetime.now().isoformat()
            }).eq('id', user_id).execute()
            
            logger.info(f"🌍 Idioma actualizado para usuario {user_id}: {language}")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando idioma: {e}")
    
    # ===============================================================
    # CONVERSATION MANAGEMENT
    # ===============================================================
    
    def get_or_create_conversation(self, user_id: str, phone_number: str, language: str = 'es') -> ConversationSession:
        """
        Obtener conversación activa o crear nueva
        """
        try:
            # Buscar conversación activa del usuario
            result = self.client.table('conversations').select('*').eq('user_id', user_id).eq('is_active', True).execute()
            
            if result.data:
                conv_data = result.data[0]
                return ConversationSession(
                    id=conv_data['id'],
                    user_id=conv_data['user_id'],
                    phone_number=conv_data['phone_number'],
                    session_started_at=datetime.fromisoformat(conv_data['session_started_at'].replace('Z', '+00:00')),
                    message_count=conv_data['message_count'],
                    detected_topics=conv_data['detected_topics'] or [],
                    session_language=conv_data['session_language'],
                    is_active=conv_data['is_active']
                )
            
            # Crear nueva conversación
            new_conversation = {
                'user_id': user_id,
                'phone_number': phone_number,
                'session_language': language
            }
            
            result = self.client.table('conversations').insert(new_conversation).execute()
            
            if result.data:
                conv_data = result.data[0]
                logger.info(f"💬 Nueva conversación creada para usuario {user_id}")
                return ConversationSession(
                    id=conv_data['id'],
                    user_id=conv_data['user_id'],
                    phone_number=conv_data['phone_number'],
                    session_started_at=datetime.now(),
                    message_count=0,
                    detected_topics=[],
                    session_language=language,
                    is_active=True
                )
                
        except Exception as e:
            logger.error(f"❌ Error gestionando conversación: {e}")
            raise
    
    def end_conversation(self, conversation_id: str, summary: str = None):
        """Terminar conversación activa"""
        try:
            update_data = {
                'is_active': False,
                'session_ended_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            if summary:
                update_data['session_summary'] = summary
            
            self.client.table('conversations').update(update_data).eq('id', conversation_id).execute()
            
            logger.info(f"🔚 Conversación {conversation_id} finalizada")
            
        except Exception as e:
            logger.error(f"❌ Error finalizando conversación: {e}")
    
    # ===============================================================
    # MESSAGE STORAGE
    # ===============================================================
    
    def store_message_interaction(
        self,
        conversation_id: str,
        user_id: str,
        phone_number: str,
        user_message: str,
        bot_response: str,
        agent_type: str,
        detected_language: str,
        detected_intent: str,
        response_time_ms: int,
        sources_used: List[Dict] = None,
        rag_context: Dict = None,
        twilio_message_sid: str = None
    ) -> str:
        """
        Almacenar interacción completa de mensaje
        """
        try:
            message_data = {
                'conversation_id': conversation_id,
                'user_id': user_id,
                'phone_number': phone_number,
                'user_message': user_message,
                'bot_response': bot_response,
                'agent_type': agent_type,
                'detected_language': detected_language,
                'detected_intent': detected_intent,
                'response_time_ms': response_time_ms,
                'sources_used': sources_used or [],
                'rag_context': rag_context or {},
                'message_length': len(user_message),
                'response_length': len(bot_response),
                'twilio_message_sid': twilio_message_sid
            }
            
            result = self.client.table('messages').insert(message_data).execute()
            
            if result.data:
                message_id = result.data[0]['id']
                logger.info(f"📝 Mensaje almacenado: {message_id}")
                return message_id
                
        except Exception as e:
            logger.error(f"❌ Error almacenando mensaje: {e}")
            return None
    
    # ===============================================================
    # CONVERSATION MEMORY
    # ===============================================================
    
    def add_memory(
        self,
        conversation_id: str,
        user_id: str,
        memory_type: str,
        memory_content: str,
        importance_score: float = 0.5
    ) -> str:
        """
        Agregar entrada a memoria conversacional
        """
        try:
            memory_data = {
                'conversation_id': conversation_id,
                'user_id': user_id,
                'memory_type': memory_type,
                'memory_content': memory_content,
                'memory_summary': memory_content[:200] + '...' if len(memory_content) > 200 else memory_content,
                'importance_score': importance_score
            }
            
            result = self.client.table('conversation_memory').insert(memory_data).execute()
            
            if result.data:
                memory_id = result.data[0]['id']
                logger.info(f"🧠 Memoria agregada: {memory_type} - {memory_id}")
                return memory_id
                
        except Exception as e:
            logger.error(f"❌ Error agregando memoria: {e}")
            return None
    
    def get_conversation_context(self, conversation_id: str, user_id: str, limit: int = 10) -> List[ConversationMemory]:
        """
        Obtener contexto de memoria para conversación
        """
        try:
            # Obtener memoria relevante ordenada por importancia
            result = self.client.table('conversation_memory')\
                .select('*')\
                .eq('conversation_id', conversation_id)\
                .eq('is_active', True)\
                .order('importance_score', desc=True)\
                .order('last_referenced_at', desc=True)\
                .limit(limit)\
                .execute()
            
            memory_entries = []
            for mem_data in result.data:
                memory_entries.append(ConversationMemory(
                    id=mem_data['id'],
                    conversation_id=mem_data['conversation_id'],
                    memory_type=mem_data['memory_type'],
                    memory_content=mem_data['memory_content'],
                    importance_score=mem_data['importance_score'],
                    last_referenced=datetime.fromisoformat(mem_data['last_referenced_at'].replace('Z', '+00:00'))
                ))
            
            return memory_entries
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo contexto de memoria: {e}")
            return []
    
    def get_recent_messages(self, conversation_id: str, limit: int = 5) -> List[Dict]:
        """
        Obtener mensajes recientes de la conversación
        """
        try:
            result = self.client.table('messages')\
                .select('user_message, bot_response, agent_type, message_timestamp')\
                .eq('conversation_id', conversation_id)\
                .order('message_timestamp', desc=True)\
                .limit(limit)\
                .execute()
            
            # Ordenar cronológicamente (más antiguo primero)
            messages = list(reversed(result.data))
            
            return messages
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo mensajes recientes: {e}")
            return []
    
    def update_memory_importance(self, memory_id: str, new_score: float):
        """Actualizar puntuación de importancia de memoria"""
        try:
            self.client.table('conversation_memory').update({
                'importance_score': new_score,
                'last_referenced_at': datetime.now().isoformat(),
                'reference_count': self.client.table('conversation_memory')\
                    .select('reference_count')\
                    .eq('id', memory_id)\
                    .execute().data[0]['reference_count'] + 1,
                'updated_at': datetime.now().isoformat()
            }).eq('id', memory_id).execute()
            
        except Exception as e:
            logger.error(f"❌ Error actualizando importancia de memoria: {e}")
    
    # ===============================================================
    # CONTEXT GENERATION FOR ALY
    # ===============================================================
    
    def generate_conversation_context(self, conversation_id: str, user_id: str) -> str:
        """
        Generar contexto de conversación para ALY
        """
        try:
            # Obtener mensajes recientes
            recent_messages = self.get_recent_messages(conversation_id, limit=3)
            
            # Obtener memoria relevante
            memory_entries = self.get_conversation_context(conversation_id, user_id, limit=5)
            
            context_parts = []
            
            # Agregar historial reciente si existe
            if recent_messages:
                context_parts.append("📚 **Contexto de conversación reciente:**")
                for msg in recent_messages[-3:]:  # Últimos 3 mensajes
                    context_parts.append(f"Usuario: {msg['user_message'][:100]}...")
                    context_parts.append(f"ALY ({msg['agent_type']}): {msg['bot_response'][:100]}...")
            
            # Agregar memoria importante
            if memory_entries:
                context_parts.append("\n🧠 **Memoria conversacional:**")
                for memory in memory_entries[:3]:  # Top 3 entradas de memoria
                    context_parts.append(f"- {memory.memory_type}: {memory.memory_content[:150]}...")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"❌ Error generando contexto: {e}")
            return ""
    
    # ===============================================================
    # ANALYTICS AND INSIGHTS
    # ===============================================================
    
    def get_user_interaction_patterns(self, user_id: str) -> Dict:
        """
        Obtener patrones de interacción del usuario
        """
        try:
            # Agentes más utilizados
            agent_usage = self.client.table('messages')\
                .select('agent_type')\
                .eq('user_id', user_id)\
                .execute()
            
            # Tipos de intención más comunes
            intent_usage = self.client.table('messages')\
                .select('detected_intent')\
                .eq('user_id', user_id)\
                .execute()
            
            # Estadísticas básicas
            total_messages = len(agent_usage.data)
            agent_counts = {}
            intent_counts = {}
            
            for msg in agent_usage.data:
                agent_type = msg['agent_type']
                if agent_type:
                    agent_counts[agent_type] = agent_counts.get(agent_type, 0) + 1
            
            for msg in intent_usage.data:
                intent = msg['detected_intent']
                if intent:
                    intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
            return {
                'total_messages': total_messages,
                'favorite_agents': agent_counts,
                'common_intents': intent_counts,
                'most_used_agent': max(agent_counts.items(), key=lambda x: x[1])[0] if agent_counts else None,
                'primary_intent': max(intent_counts.items(), key=lambda x: x[1])[0] if intent_counts else None
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo patrones de usuario: {e}")
            return {}
    
    # ===============================================================
    # MAINTENANCE FUNCTIONS
    # ===============================================================
    
    def cleanup_old_conversations(self, days_threshold: int = 30):
        """Limpiar conversaciones antiguas e inactivas"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_threshold)).isoformat()
            
            self.client.table('conversations').update({
                'is_active': False
            }).lt('session_started_at', cutoff_date).eq('is_active', True).execute()
            
            logger.info(f"🧹 Limpieza de conversaciones > {days_threshold} días completada")
            
        except Exception as e:
            logger.error(f"❌ Error en limpieza: {e}")
    
    def get_system_stats(self) -> Dict:
        """Obtener estadísticas del sistema"""
        try:
            # Contar usuarios únicos
            users_count = self.client.table('users').select('id', count='exact').execute()
            
            # Contar conversaciones activas
            active_convs = self.client.table('conversations').select('id', count='exact')\
                .eq('is_active', True).execute()
            
            # Contar mensajes hoy
            today = datetime.now().date().isoformat()
            messages_today = self.client.table('messages').select('id', count='exact')\
                .gte('message_timestamp', today).execute()
            
            return {
                'total_users': users_count.count if hasattr(users_count, 'count') else 0,
                'active_conversations': active_convs.count if hasattr(active_convs, 'count') else 0,
                'messages_today': messages_today.count if hasattr(messages_today, 'count') else 0,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {}

# ===============================================================
# HELPER FUNCTIONS
# ===============================================================

def create_memory_from_interaction(
    user_message: str,
    bot_response: str,
    agent_type: str,
    intent: str
) -> Tuple[str, str, float]:
    """
    Crear entrada de memoria basada en la interacción
    """
    # Determinar tipo de memoria basado en el agente
    memory_type_mapping = {
        'rag': 'context',
        'workshop': 'goal',
        'brainstorming': 'preference',
        'safe_edge': 'sensitive_topic',
        'fallback': 'clarification'
    }
    
    memory_type = memory_type_mapping.get(agent_type, 'context')
    
    # Crear resumen de la interacción
    if len(user_message) > 200:
        memory_content = f"Consulta sobre: {user_message[:200]}... | Respuesta tipo: {agent_type}"
    else:
        memory_content = f"Consulta: {user_message} | Respuesta: {agent_type} - {intent}"
    
    # Asignar importancia basada en tipo de agente e intención
    importance_score = 0.5  # Default
    
    if agent_type == 'safe_edge':
        importance_score = 0.9  # Temas sensibles son muy importantes
    elif intent in ['PLAN', 'IDEATE']:
        importance_score = 0.7  # Planificación e ideas son importantes
    elif agent_type == 'workshop':
        importance_score = 0.8  # Talleres prácticos son muy relevantes
    elif intent == 'FACTUAL':
        importance_score = 0.6  # Información factual es moderadamente importante
    
    return memory_type, memory_content, importance_score