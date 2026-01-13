# CLAUDE.md - Memoria del Proyecto Puddle Assistant

## 🎯 Estado Actual del Proyecto

**Proyecto**: Puddle Assistant - Sistema RAG para consulta inteligente de documentos
**Fecha**: 2026-01-12
**Fase**: BOT WHATSAPP FUNCIONANDO EN PRODUCCIÓN ✅
**Arquitectura**: MongoDB (RAG) + Supabase (usuarios/conversaciones) + WhatsApp (Twilio)

## 🏗️ Arquitectura del Sistema

### **MongoDB = RAG Engine**  
- ✅ Vector store para documentos y embeddings OpenAI
- ✅ Búsqueda semántica completamente funcional
- ✅ 36/38 documentos procesados exitosamente

### **Supabase = Datos de Usuario/Conversaciones**
- 👤 Gestión de usuarios
- 💬 Historial de conversaciones  
- 📊 Analytics y métricas de uso

## 🤖 Sistema de Agentes MVP ALY

### **Estado: ✅ COMPLETAMENTE FUNCIONAL**
- **Language Detection**: Automático ES/EN/PT usando LLM
- **Intent Router**: GREETING/FACTUAL/PLAN/IDEATE/SENSITIVE/AMBIGUOUS
- **Specialized Agents**: RAG, Workshop, Brainstorming, SafeEdge, Fallback
- **Filter Detection**: Detección automática de programas (MWB, P+, etc.) y categorías

### **🆕 Sistema de GREETING (2026-01-12)**
- ✅ Detección automática de saludos usando LLM (sin palabras clave)
- ✅ Welcome messages en 3 idiomas (ES/EN/PT)
- ✅ Integrado en flujo de orchestrator
- ✅ Elimina duplicación de bienvenida en bot WhatsApp

### **Formato de Respuestas**
- ✅ **Conversacional y natural** (formato robótico comentado)
- ✅ **Tono**: Cálido, simple, inclusivo, no prescriptivo
- ✅ **Validación**: "You know your group — adapt as needed"

## 📱 WhatsApp Bot - ¡FUNCIONANDO EN PRODUCCIÓN! ✅

### **✅ Estado: COMPLETAMENTE OPERATIVO (2026-01-12)**
- **Bot**: `whatsapp/aly_bot_with_memory.py` en puerto 8002
- **Sistema ALY**: Todos los agentes + GREETING + Memoria Supabase
- **Twilio**: Sandbox configurado y funcionando
- **Arquitectura**: Respuesta asíncrona (sin timeout de 15s)
- **Entorno virtual**: `venv/` configurado con todas las dependencias

### **🚀 Arquitectura Asíncrona Implementada**
**Problema resuelto**: Bot tardaba 20+ segundos procesando → Twilio timeout
**Solución**:
- Webhook responde a Twilio inmediatamente (200 OK vacío)
- ALY procesa en background usando `asyncio.create_task()`
- Bot envía respuesta activamente vía Twilio Client API
- ✅ Sin timeouts, mensajes llegan siempre

### **🔧 Para iniciar el bot:**
```bash
# Terminal 1: Iniciar bot
source venv/bin/activate
cd whatsapp
python3 aly_bot_with_memory.py

# Terminal 2: Exponer con ngrok
ngrok http 8002
# Copiar URL https y actualizar en Twilio Console:
# https://xxxxx.ngrok.io/webhook/whatsapp
```

### **⚙️ Variables de entorno requeridas (.env):**
```bash
# Twilio (Sandbox o número comprado)
TWILIO_ACCOUNT_SID=<tu_account_sid>
TWILIO_AUTH_TOKEN=<tu_auth_token>
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Supabase
SUPABASE_URL=<tu_supabase_url>
SUPABASE_KEY=<tu_anon_key>

# OpenRouter (para agentes)
OPENROUTER_API_KEY=<tu_key>

# MongoDB
MONGODB_CONNECTION_STRING=<tu_connection_string>
```

### **📊 Flujo del Bot:**
1. Usuario envía mensaje → Twilio webhook
2. Bot responde 200 OK inmediatamente
3. Background: Language → Filter Detection → Intent Router
4. Intent GREETING → Welcome message
5. Intent FACTUAL/PLAN/IDEATE → Agentes especializados
6. Bot envía respuesta activamente vía Twilio API
7. Todo se guarda en Supabase (memoria conversacional)

## 🧠 Sistema de Memoria Supabase - ¡COMPLETADO!

### **✅ Estado: COMPLETAMENTE IMPLEMENTADO**
- **Base de datos**: 6 tablas (Users, Conversations, Messages, Memory, Preferences, Analytics)
- **Memory Manager**: Sistema completo de gestión de memoria conversacional
- **Bot con memoria**: `aly_bot_with_memory.py` con contexto persistente
- **Analytics**: Patrones de usuario, performance, engagement

### **🎯 Funcionalidades de Memoria:**
- **Contexto conversacional**: Últimos mensajes + memoria importante
- **Puntuación inteligente**: Temas sensibles = alta prioridad
- **Persistencia**: 30 días con limpieza automática
- **Personalización**: Preferencias de idioma y patrones de uso
- **Analytics**: Estadísticas en tiempo real por usuario

### **📊 Endpoints de Memoria:**
- `GET /user/{phone}/profile` - Perfil y patrones de usuario
- `GET /stats` - Estadísticas avanzadas con memoria
- `POST /admin/cleanup` - Limpieza de datos antiguos

## 📋 Tareas Pendientes

### **Prioridad Alta:**
1. **Ajustar recuperación de información RAG**
   - Optimizar búsqueda semántica
   - Mejorar relevancia de chunks
   - Ajustar filtros de programas

2. **Migrar de Sandbox a Número Twilio Comprado**
   - Configurar número comprado
   - Actualizar webhook
   - Probar en producción

### **Backlog:**
1. **Procesar 2 documentos fallidos:**
   - `Addressing_the_impact_of_Masculinity_Influencers_on_Teenage_Boys...`
   - `Manual_de_Facilitación_Programa_Apapáchar.pdf`

2. **Optimizaciones de performance:**
   - Reducir tiempo de respuesta RAG (actualmente 20-25s)
   - Cache de embeddings frecuentes
   - Optimizar queries MongoDB

## 🚀 Comandos Clave

**Ejecutar Bot WhatsApp (PRODUCCIÓN):**
```bash
source venv/bin/activate
cd whatsapp
python3 aly_bot_with_memory.py
# En otra terminal: ngrok http 8002
```

**Ejecutar Sistema MVP ALY (consola local):**
```bash
cd mvp
python3 agent_console.py
```

**Test de GREETING:**
```bash
cd mvp
python3 test_greeting.py
```

**RAG Simple MongoDB:**
```bash
cd mongodb/scripts
python3 rag_console.py
```

## 🎉 Logros Recientes (2026-01-12)

### **✅ Bot WhatsApp Funcionando Completamente**
1. Sistema de GREETING implementado y funcionando
2. Arquitectura asíncrona para evitar timeouts de Twilio
3. Credenciales de Twilio correctas configuradas
4. Memoria conversacional Supabase activa
5. Todos los agentes (RAG, Workshop, Brainstorming, SafeEdge, Fallback) operativos
6. Detección automática de idioma (ES/EN/PT)
7. Filter Detection para programas y categorías

### **🔧 Soluciones Técnicas Implementadas**
- **Problema**: Bot tardaba 20+ segundos → Twilio timeout
- **Solución**: Webhook responde inmediatamente, procesamiento en background
- **Problema**: Mensaje de bienvenida duplicado
- **Solución**: Orchestrator maneja GREETING, bot solo envía respuesta
- **Problema**: Credenciales incorrectas de Twilio
- **Solución**: Configurar Account SID y Auth Token correctos en .env