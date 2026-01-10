#!/usr/bin/env python3
"""
Minimal WhatsApp Bot - Solo para probar la conexión con Twilio
"""

import os
from fastapi import FastAPI, Form
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
import uvicorn
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar FastAPI
app = FastAPI(title="Minimal ALY WhatsApp Bot")

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(None)
):
    """
    Webhook mínimo para probar Twilio
    """
    try:
        # Extraer número de teléfono
        phone_number = From.replace('whatsapp:', '')
        message_body = Body.strip()
        
        logger.info(f"📱 Mensaje recibido de {phone_number}: {message_body}")
        
        # Respuesta simple por ahora
        if 'hola' in message_body.lower() or 'hello' in message_body.lower():
            response_text = "¡Hola! Soy ALY, tu asistente educativa. Estoy en modo de prueba. 🤖"
        else:
            response_text = f"Recibí tu mensaje: '{message_body}'. Estoy funcionando correctamente ✅"
        
        # Crear respuesta TwiML
        resp = MessagingResponse()
        resp.message(response_text)
        
        logger.info(f"✅ Respuesta enviada a {phone_number}")
        
        return PlainTextResponse(str(resp), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"❌ Error procesando webhook: {e}")
        
        # Respuesta de error
        resp = MessagingResponse()
        resp.message("Error técnico. Estoy en modo de prueba.")
        
        return PlainTextResponse(str(resp), media_type="application/xml")

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "message": "Minimal bot running"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "ALY Minimal WhatsApp Bot is running"}

if __name__ == "__main__":
    logger.info("🚀 Iniciando bot mínimo...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )