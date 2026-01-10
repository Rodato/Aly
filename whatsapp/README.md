# WhatsApp Bot ALY + Twilio

Bot de WhatsApp que integra el sistema de agentes ALY con Twilio para responder consultas educativas.

## 🚀 Instalación

```bash
# Instalar dependencias
cd whatsapp
pip install -r requirements.txt
```

## ⚙️ Configuración

Las credenciales ya están en `.env`:
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN` 
- `TWILIO_WHATSAPP_NUMBER`

## 🔧 Ejecución

```bash
# Ejecutar el servidor
python whatsapp_bot.py

# O con uvicorn
uvicorn whatsapp_bot:app --reload --port 8000
```

## 🌐 Endpoints

- `POST /webhook/whatsapp` - Webhook para Twilio
- `GET /health` - Health check
- `GET /stats` - Estadísticas del bot
- `POST /send_message` - Enviar mensajes programáticamente

## 📱 Testing Local

1. **Ejecutar el bot**: `python whatsapp_bot.py`
2. **Exponer con ngrok**: `ngrok http 8000`
3. **Configurar webhook en Twilio** con la URL de ngrok
4. **Probar desde WhatsApp** enviando mensajes al sandbox

## 🔗 URL del Webhook

Para Twilio usar: `https://tu-ngrok-url.ngrok-free.app/webhook/whatsapp`