#!/usr/bin/env python3
"""
ALY WhatsApp Bot with Supabase Memory Integration
Bot de WhatsApp que integra el sistema completo ALY con memoria conversacional en Supabase
"""

import os
import sys
import time
from datetime import datetime
from typing import Dict, Optional
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import logging
import asyncio
import concurrent.futures
from dotenv import load_dotenv

# Configurar path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'mvp'))

# Importar sistema de memoria
from supabase_memory_manager import SupabaseMemoryManager, create_memory_from_interaction

# Cargar variables de entorno
load_dotenv(os.path.join(project_root, '.env'))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurar FastAPI
app = FastAPI(title="ALY WhatsApp Bot - Full System with Memory")

# Variables globales
orchestrator: Optional[object] = None
twilio_client: Optional[Client] = None
memory_manager: Optional[SupabaseMemoryManager] = None
executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

def init_aly_system():
    """Inicializar el sistema ALY en thread separado"""
    try:
        from mvp.agent_orchestrator import AgentOrchestrator
        logger.info("🚀 Inicializando sistema de agentes ALY...")
        return AgentOrchestrator()
    except Exception as e:
        logger.error(f"❌ Error inicializando ALY: {e}")
        return None

@app.on_event("startup")
async def startup_event():
    """Inicializar servicios al arrancar"""
    global orchestrator, twilio_client, memory_manager
    
    try:
        # Inicializar Supabase Memory Manager
        logger.info("🗃️ Inicializando Supabase Memory Manager...")
        memory_manager = SupabaseMemoryManager()
        logger.info("✅ Supabase Memory Manager inicializado")
        
        # Inicializar cliente Twilio
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        if not account_sid or not auth_token:
            raise Exception("Faltan credenciales de Twilio en .env")
            
        twilio_client = Client(account_sid, auth_token)
        logger.info("✅ Cliente Twilio inicializado")
        
        # Inicializar ALY en background
        loop = asyncio.get_event_loop()
        orchestrator = await loop.run_in_executor(executor, init_aly_system)
        
        if orchestrator:
            logger.info("✅ Sistema ALY con memoria inicializado exitosamente")
        else:
            logger.warning("⚠️ Sistema ALY no pudo inicializarse - usando modo básico")
        
    except Exception as e:
        logger.error(f"❌ Error inicializando servicios: {e}")

def format_for_whatsapp(response: str) -> str:
    """Formatear respuesta para WhatsApp"""
    # Limpiar formato markdown pesado
    response = response.replace('**', '')
    response = response.replace('##', '')
    response = response.replace('###', '')
    response = response.replace('- ', '• ')

    # Limitar longitud para WhatsApp
    if len(response) > 1500:
        response = response[:1400] + "...\n\n💡 Puedes pedir más detalles si necesitas."

    return response.strip()

async def process_with_aly_and_memory(
    message: str, 
    user_profile: object, 
    conversation: object
) -> Dict:
    """Procesar mensaje con ALY usando memoria conversacional"""
    start_time = time.time()
    
    try:
        logger.info(f"🔄 Procesando con ALY: {message[:50]}...")
        
        # Generar contexto conversacional de Supabase
        conversation_context = ""
        if memory_manager:
            conversation_context = memory_manager.generate_conversation_context(
                conversation.id, user_profile.id
            )
        
        if not orchestrator:
            logger.warning("⚠️ ALY no disponible - respuesta básica")
            return {
                'answer': f"Hola {user_profile.phone_number}! Soy ALY, pero estoy teniendo problemas técnicos. ¿Puedes intentar más tarde?",
                'agent_type': 'fallback',
                'language_detected': user_profile.preferred_language,
                'sources': [],
                'response_time_ms': int((time.time() - start_time) * 1000)
            }
        
        # Crear contexto enriquecido para ALY
        enhanced_message = message
        if conversation_context:
            enhanced_message = f"Contexto de conversación:\n{conversation_context}\n\nPregunta actual: {message}"
        
        # Procesar con ALY
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, orchestrator.process_query, enhanced_message)
        
        # Calcular tiempo de respuesta
        response_time = int((time.time() - start_time) * 1000)
        result['response_time_ms'] = response_time
        
        logger.info(f"✅ ALY procesó exitosamente con agente: {result.get('agent_type', 'unknown')} ({response_time}ms)")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error procesando con ALY: {e}")
        response_time = int((time.time() - start_time) * 1000)
        return {
            'answer': 'Disculpa, tuve un problema procesando tu consulta. ¿Puedes reformular tu pregunta?',
            'agent_type': 'error',
            'language_detected': user_profile.preferred_language,
            'sources': [],
            'response_time_ms': response_time,
            'error': str(e)
        }

async def process_and_send_response(
    phone_number: str,
    message_body: str,
    user_profile: object,
    conversation: object,
    twilio_message_sid: str
):
    """Procesa el mensaje con ALY y envía la respuesta activamente via Twilio"""
    try:
        # Procesar con ALY usando memoria
        result = await process_with_aly_and_memory(message_body, user_profile, conversation)
        
        # Extraer respuesta
        if result and 'answer' in result:
            response_text = result['answer']

            # Actualizar idioma detectado si es diferente
            detected_language = result.get('language_detected', user_profile.preferred_language)
            if detected_language != user_profile.preferred_language:
                memory_manager.update_user_language(user_profile.id, detected_language)
                logger.info(f"🌍 Idioma actualizado: {detected_language}")
        else:
            response_text = "Lo siento, hubo un problema. ¿Puedes intentar de nuevo?"
            result = {'agent_type': 'error', 'language_detected': user_profile.preferred_language}

        # Almacenar interacción en Supabase
        try:
            message_id = memory_manager.store_message_interaction(
                conversation_id=conversation.id,
                user_id=user_profile.id,
                phone_number=phone_number,
                user_message=message_body,
                bot_response=response_text,
                agent_type=result.get('agent_type', 'unknown'),
                detected_language=result.get('language_detected', user_profile.preferred_language),
                detected_intent=result.get('intent', 'UNKNOWN'),
                response_time_ms=result.get('response_time_ms', 0),
                sources_used=result.get('sources', []),
                rag_context=result.get('rag_context', {}),
                twilio_message_sid=twilio_message_sid
            )

            # Crear entrada de memoria si es relevante
            if result.get('agent_type') in ['workshop', 'brainstorming', 'safe_edge']:
                memory_type, memory_content, importance_score = create_memory_from_interaction(
                    message_body,
                    response_text,
                    result.get('agent_type', 'unknown'),
                    result.get('intent', 'UNKNOWN')
                )

                memory_manager.add_memory(
                    conversation_id=conversation.id,
                    user_id=user_profile.id,
                    memory_type=memory_type,
                    memory_content=memory_content,
                    importance_score=importance_score
                )
                logger.info(f"🧠 Memoria creada: {memory_type} (importancia: {importance_score})")

        except Exception as e:
            logger.error(f"⚠️ Error almacenando en Supabase: {e}")

        # Formatear y enviar respuesta activamente via Twilio
        formatted_response = format_for_whatsapp(response_text)

        whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
        twilio_client.messages.create(
            body=formatted_response,
            from_=whatsapp_number,
            to=f"whatsapp:{phone_number}"
        )

        logger.info(f"✅ Respuesta enviada activamente a {phone_number} (agente: {result.get('agent_type', 'unknown')})")

    except Exception as e:
        logger.error(f"❌ Error procesando mensaje background: {e}")

        # Enviar mensaje de error
        try:
            whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
            twilio_client.messages.create(
                body="Disculpa, tuve un problema técnico. ¿Puedes intentar de nuevo?",
                from_=whatsapp_number,
                to=f"whatsapp:{phone_number}"
            )
        except:
            pass

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(None)
):
    """Webhook principal - responde inmediatamente y procesa en background"""
    try:
        # Extraer número y mensaje
        phone_number = From.replace('whatsapp:', '')
        message_body = Body.strip()

        logger.info(f"📱 Mensaje de {phone_number}: {message_body}")

        if not memory_manager:
            logger.error("❌ Memory Manager no disponible")
            resp = MessagingResponse()
            resp.message("Sistema no disponible temporalmente.")
            return PlainTextResponse(str(resp), media_type="application/xml")

        # Obtener o crear usuario
        user_profile = memory_manager.get_or_create_user(phone_number)
        logger.info(f"👤 Usuario: {user_profile.id}")

        # Obtener o crear conversación
        conversation = memory_manager.get_or_create_conversation(
            user_profile.id,
            phone_number,
            user_profile.preferred_language
        )
        logger.info(f"💬 Conversación: {conversation.id} (msg #{conversation.message_count + 1})")

        # Lanzar procesamiento en background
        asyncio.create_task(
            process_and_send_response(
                phone_number,
                message_body,
                user_profile,
                conversation,
                MessageSid
            )
        )

        # Responder inmediatamente a Twilio (vacío - la respuesta se enviará activamente)
        return PlainTextResponse("", media_type="text/plain")

    except Exception as e:
        logger.error(f"❌ Error en webhook: {e}")
        return PlainTextResponse("", media_type="text/plain")

@app.get("/health")
async def health_check():
    """Health check con estado de memoria"""
    memory_status = "ready" if memory_manager else "not_ready"
    
    # Obtener estadísticas del sistema si está disponible
    system_stats = {}
    if memory_manager:
        try:
            system_stats = memory_manager.get_system_stats()
        except:
            system_stats = {"error": "Could not fetch stats"}
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "aly_status": "ready" if orchestrator else "initializing",
        "twilio_status": "ready" if twilio_client else "not_ready",
        "memory_status": memory_status,
        "system_stats": system_stats
    }

@app.get("/stats")
async def get_stats():
    """Estadísticas avanzadas del bot con memoria"""
    if not memory_manager:
        return {"error": "Memory manager not available"}
    
    try:
        system_stats = memory_manager.get_system_stats()
        
        return {
            "bot_status": {
                "aly_available": orchestrator is not None,
                "memory_available": memory_manager is not None,
                "twilio_available": twilio_client is not None
            },
            "usage_stats": system_stats,
            "features": {
                "conversation_memory": True,
                "user_profiles": True,
                "multi_language": True,
                "agent_routing": True
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        return {"error": str(e)}

@app.get("/user/{phone_number}/profile")
async def get_user_profile(phone_number: str):
    """Obtener perfil de usuario y patrones de interacción"""
    if not memory_manager:
        return {"error": "Memory manager not available"}
    
    try:
        # Obtener perfil básico
        user_profile = memory_manager.get_or_create_user(phone_number)
        
        # Obtener patrones de interacción
        interaction_patterns = memory_manager.get_user_interaction_patterns(user_profile.id)
        
        return {
            "user_profile": {
                "phone_number": user_profile.phone_number,
                "preferred_language": user_profile.preferred_language,
                "total_messages": user_profile.total_messages,
                "first_interaction": user_profile.first_interaction.isoformat() if user_profile.first_interaction else None,
                "last_interaction": user_profile.last_interaction.isoformat() if user_profile.last_interaction else None
            },
            "interaction_patterns": interaction_patterns
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo perfil de usuario: {e}")
        return {"error": str(e)}

@app.post("/admin/cleanup")
async def cleanup_old_data(days: int = 30):
    """Endpoint administrativo para limpiar datos antiguos"""
    if not memory_manager:
        return {"error": "Memory manager not available"}
    
    try:
        memory_manager.cleanup_old_conversations(days_threshold=days)
        return {
            "status": "success",
            "message": f"Cleanup completed for conversations older than {days} days"
        }
        
    except Exception as e:
        logger.error(f"❌ Error en limpieza: {e}")
        return {"error": str(e)}

@app.post("/send_message")
async def send_message(from_number: str, message: str):
    """Endpoint para enviar mensajes programáticamente (testing)"""
    try:
        if not twilio_client:
            raise HTTPException(status_code=500, detail="Cliente Twilio no inicializado")
        
        whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
        
        message_obj = twilio_client.messages.create(
            body=message,
            from_=whatsapp_number,
            to=f"whatsapp:{from_number}"
        )
        
        return {"status": "sent", "message_sid": message_obj.sid}
        
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info("🚀 Iniciando ALY WhatsApp Bot con memoria Supabase...")
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,  # Puerto diferente para evitar conflictos
        reload=False,
        log_level="info"
    )