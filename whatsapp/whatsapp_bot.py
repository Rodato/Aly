#!/usr/bin/env python3
"""
WhatsApp Bot with FastAPI + Twilio
Integra el sistema MVP ALY con WhatsApp via Twilio
"""

import os
import sys
from datetime import datetime
from typing import Dict, Optional
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import PlainTextResponse
import uvicorn
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from pydantic import BaseModel
import logging

# Configurar path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'mvp'))

# Importar el sistema de agentes existente
from mvp.agent_orchestrator import AgentOrchestrator

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar FastAPI
app = FastAPI(title="ALY WhatsApp Bot", description="ALY Assistant via WhatsApp + Twilio")

# Variables globales
orchestrator: Optional[AgentOrchestrator] = None
twilio_client: Optional[Client] = None
session_storage: Dict[str, Dict] = {}  # Almacena sesiones por número de teléfono

class WhatsAppMessage(BaseModel):
    """Modelo para mensajes de WhatsApp"""
    from_number: str
    message_body: str
    timestamp: datetime

@app.on_event("startup")
async def startup_event():
    """Inicializar servicios al arrancar"""
    global orchestrator, twilio_client
    
    try:
        # Inicializar AgentOrchestrator
        logger.info("🚀 Inicializando sistema de agentes ALY...")
        orchestrator = AgentOrchestrator()
        logger.info("✅ Sistema de agentes inicializado")
        
        # Inicializar cliente Twilio
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        if not account_sid or not auth_token:
            raise Exception("Faltan credenciales de Twilio en .env")
            
        twilio_client = Client(account_sid, auth_token)
        logger.info("✅ Cliente Twilio inicializado")
        
    except Exception as e:
        logger.error(f"❌ Error inicializando servicios: {e}")
        raise

def get_or_create_session(phone_number: str) -> Dict:
    """Obtener o crear sesión para un usuario"""
    if phone_number not in session_storage:
        session_storage[phone_number] = {
            'created_at': datetime.now(),
            'message_count': 0,
            'language': None,  # Se detectará automáticamente
            'context': []
        }
    return session_storage[phone_number]

def format_for_whatsapp(response: str) -> str:
    """
    Formatear respuesta para WhatsApp
    - Eliminar markdown excesivo
    - Mantener formato legible
    """
    # Limpiar formato markdown pesado
    response = response.replace('**', '')
    response = response.replace('##', '')
    response = response.replace('###', '')
    
    # Mantener bullets simples
    response = response.replace('- ', '• ')
    
    # Limpiar espacios extra
    lines = [line.strip() for line in response.split('\n') if line.strip()]
    return '\n\n'.join(lines)

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(None),
    AccountSid: str = Form(None)
):
    """
    Webhook principal para recibir mensajes de WhatsApp vía Twilio
    """
    try:
        # Extraer número de teléfono (quitar prefijo whatsapp:)
        phone_number = From.replace('whatsapp:', '')
        message_body = Body.strip()
        
        logger.info(f"📱 Mensaje de {phone_number}: {message_body}")
        
        # Obtener sesión del usuario
        session = get_or_create_session(phone_number)
        session['message_count'] += 1
        
        # Procesar con el sistema de agentes ALY
        if not orchestrator:
            raise HTTPException(status_code=500, detail="Sistema de agentes no inicializado")
        
        logger.info("🧠 Procesando con sistema ALY...")
        
        # Llamar al orquestador de agentes
        result = await process_with_aly(message_body, session)
        
        if not result or 'answer' not in result:
            response_text = "Lo siento, hubo un problema procesando tu mensaje. ¿Puedes intentar de nuevo?"
        else:
            response_text = result['answer']
            
            # Guardar idioma detectado en la sesión
            if 'language_detected' in result:
                session['language'] = result['language_detected']
        
        # Formatear para WhatsApp
        formatted_response = format_for_whatsapp(response_text)
        
        # Crear respuesta TwiML
        resp = MessagingResponse()
        resp.message(formatted_response)
        
        logger.info(f"✅ Respuesta enviada a {phone_number}")
        
        return PlainTextResponse(str(resp), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"❌ Error procesando webhook: {e}")
        
        # Respuesta de error para el usuario
        resp = MessagingResponse()
        resp.message("Disculpa, tuve un problema técnico. ¿Puedes intentar de nuevo en un momento?")
        
        return PlainTextResponse(str(resp), media_type="application/xml")

async def process_with_aly(message: str, session: Dict) -> Dict:
    """
    Procesar mensaje con el sistema ALY
    """
    try:
        logger.info(f"🔄 Iniciando procesamiento con ALY para: {message[:50]}...")
        
        # El orchestrator es síncrono, pero FastAPI es async
        # Ejecutar en el hilo principal por ahora
        result = orchestrator.process_query(message)
        
        logger.info(f"✅ ALY procesó exitosamente")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error procesando con ALY: {e}", exc_info=True)
        return {
            'answer': 'Lo siento, hubo un error procesando tu consulta. ¿Puedes reformular tu pregunta?',
            'error': str(e)
        }

@app.get("/health")
async def health_check():
    """Health check para verificar que el servicio está funcionando"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "aly_status": "ready" if orchestrator else "not_initialized",
        "twilio_status": "ready" if twilio_client else "not_initialized",
        "active_sessions": len(session_storage)
    }

@app.get("/stats")
async def get_stats():
    """Estadísticas del bot"""
    total_messages = sum(session['message_count'] for session in session_storage.values())
    
    return {
        "total_sessions": len(session_storage),
        "total_messages": total_messages,
        "sessions": {
            phone: {
                "message_count": session['message_count'],
                "language": session.get('language'),
                "created_at": session['created_at'].isoformat()
            }
            for phone, session in session_storage.items()
        }
    }

@app.post("/send_message")
async def send_message(from_number: str, message: str):
    """Endpoint para enviar mensajes programáticamente (testing)"""
    try:
        if not twilio_client:
            raise HTTPException(status_code=500, detail="Cliente Twilio no inicializado")
        
        whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
        
        message = twilio_client.messages.create(
            body=message,
            from_=whatsapp_number,
            to=f"whatsapp:{from_number}"
        )
        
        return {"status": "sent", "message_sid": message.sid}
        
    except Exception as e:
        logger.error(f"❌ Error enviando mensaje: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Ejecutar servidor FastAPI
    uvicorn.run(
        "whatsapp_bot:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )