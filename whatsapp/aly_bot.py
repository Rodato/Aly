#!/usr/bin/env python3
"""
ALY WhatsApp Bot with Full System Integration
Bot de WhatsApp que integra el sistema completo de agentes ALY
"""

import os
import sys
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

# Cargar variables de entorno
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Configurar path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'mvp'))

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar FastAPI
app = FastAPI(title="ALY WhatsApp Bot - Full System")

# Variables globales
orchestrator: Optional[object] = None
twilio_client: Optional[Client] = None
session_storage: Dict[str, Dict] = {}
executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

def init_aly_system():
    """Inicializar el sistema ALY en thread separado para evitar bloqueos"""
    try:
        # Importar aquí para evitar problemas de inicialización
        from mvp.agent_orchestrator import AgentOrchestrator
        logger.info("🚀 Inicializando sistema de agentes ALY...")
        return AgentOrchestrator()
    except Exception as e:
        logger.error(f"❌ Error inicializando ALY: {e}")
        return None

@app.on_event("startup")
async def startup_event():
    """Inicializar servicios al arrancar"""
    global orchestrator, twilio_client
    
    try:
        # Inicializar cliente Twilio primero (más rápido)
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
            logger.info("✅ Sistema ALY inicializado exitosamente")
        else:
            logger.warning("⚠️ Sistema ALY no pudo inicializarse - usando modo básico")
        
    except Exception as e:
        logger.error(f"❌ Error inicializando servicios: {e}")
        # No hacer raise - permitir que el bot funcione en modo básico

def get_or_create_session(phone_number: str) -> Dict:
    """Obtener o crear sesión para un usuario"""
    if phone_number not in session_storage:
        session_storage[phone_number] = {
            'created_at': datetime.now(),
            'message_count': 0,
            'language': None,
            'context': []
        }
    return session_storage[phone_number]

def format_for_whatsapp(response: str) -> str:
    """Formatear respuesta para WhatsApp"""
    # Limpiar formato markdown pesado
    response = response.replace('**', '')
    response = response.replace('##', '')
    response = response.replace('###', '')
    
    # Mantener bullets simples
    response = response.replace('- ', '• ')
    
    # Limitar longitud (WhatsApp tiene límites)
    if len(response) > 1500:
        response = response[:1400] + "...\n\n💡 Puedes pedir más detalles si necesitas."
    
    return response.strip()

async def process_with_aly(message: str, session: Dict) -> Dict:
    """Procesar mensaje con el sistema ALY usando thread pool"""
    try:
        logger.info(f"🔄 Procesando con ALY: {message[:50]}...")
        
        if not orchestrator:
            logger.warning("⚠️ ALY no disponible - respuesta básica")
            return {
                'answer': "Hola! Soy ALY, pero estoy teniendo problemas técnicos. ¿Puedes intentar más tarde?",
                'agent_type': 'fallback',
                'language_detected': 'es'
            }
        
        # Ejecutar en thread separado para no bloquear FastAPI
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, orchestrator.process_query, message)
        
        logger.info(f"✅ ALY procesó exitosamente con agente: {result.get('agent_type', 'unknown')}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error procesando con ALY: {e}")
        return {
            'answer': 'Disculpa, tuve un problema procesando tu consulta. ¿Puedes reformular tu pregunta?',
            'agent_type': 'error',
            'error': str(e)
        }

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(None)
):
    """Webhook principal para mensajes de WhatsApp"""
    try:
        # Extraer número y mensaje
        phone_number = From.replace('whatsapp:', '')
        message_body = Body.strip()
        
        logger.info(f"📱 Mensaje de {phone_number}: {message_body}")
        
        # Obtener sesión del usuario
        session = get_or_create_session(phone_number)
        session['message_count'] += 1
        
        # Procesar con ALY
        result = await process_with_aly(message_body, session)
        
        # Extraer respuesta
        if result and 'answer' in result:
            response_text = result['answer']
            
            # Guardar idioma detectado
            if 'language_detected' in result:
                session['language'] = result['language_detected']
        else:
            response_text = "Lo siento, hubo un problema. ¿Puedes intentar de nuevo?"
        
        # Formatear para WhatsApp
        formatted_response = format_for_whatsapp(response_text)
        
        # Crear respuesta TwiML
        resp = MessagingResponse()
        resp.message(formatted_response)
        
        logger.info(f"✅ Respuesta enviada a {phone_number} (agente: {result.get('agent_type', 'unknown')})")
        
        return PlainTextResponse(str(resp), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"❌ Error en webhook: {e}")
        
        # Respuesta de error para el usuario
        resp = MessagingResponse()
        resp.message("Disculpa, tuve un problema técnico. ¿Puedes intentar de nuevo?")
        
        return PlainTextResponse(str(resp), media_type="application/xml")

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "aly_status": "ready" if orchestrator else "initializing",
        "twilio_status": "ready" if twilio_client else "not_ready",
        "active_sessions": len(session_storage)
    }

@app.get("/stats")
async def get_stats():
    """Estadísticas del bot"""
    total_messages = sum(session['message_count'] for session in session_storage.values())
    
    return {
        "total_sessions": len(session_storage),
        "total_messages": total_messages,
        "aly_available": orchestrator is not None,
        "recent_sessions": list(session_storage.keys())[-5:]  # Últimas 5 sesiones
    }

if __name__ == "__main__":
    logger.info("🚀 Iniciando ALY WhatsApp Bot completo...")
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,  # Puerto diferente para no conflicto
        reload=False,
        log_level="info"
    )