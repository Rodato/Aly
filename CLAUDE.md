# CLAUDE.md - Memoria del Proyecto Puddle Assistant

## 🎯 Estado Actual del Proyecto

**Proyecto**: Puddle Assistant - Sistema RAG para consulta inteligente de documentos
**Fecha**: 2025-12-16 
**Fase**: SISTEMA RAG COMPLETO Y OPERATIVO
**Arquitectura**: MongoDB (RAG) + Supabase (usuarios/conversaciones)

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
- **Language Detection**: Automático ES/EN/PT
- **Intent Router**: FACTUAL/PLAN/IDEATE/SENSITIVE/AMBIGUOUS  
- **Specialized Agents**: RAG, Workshop, Brainstorming, SafeEdge, Fallback

### **Formato de Respuestas**
- ✅ **Conversacional y natural** (formato robótico comentado)
- ✅ **Tono**: Cálido, simple, inclusivo, no prescriptivo
- ✅ **Validación**: "You know your group — adapt as needed"

## 📱 WhatsApp Bot - ¡COMPLETADO!

### **✅ Estado: FUNCIONANDO COMPLETAMENTE**
- **FastAPI bot**: `whatsapp/aly_bot.py` corriendo en puerto 8001
- **Sistema ALY completo**: Todos los agentes integrados y funcionando
- **Twilio**: Configurado con webhook
- **ngrok**: Para exposición local
- **Comando para ejecutar**: 
  ```bash
  cd whatsapp && nohup python aly_bot.py > aly_bot.log 2>&1 &
  ngrok http 8001
  ```

### **🔧 Para reactivar el bot:**
**Bot Básico:**
1. `cd whatsapp && python aly_bot.py` (puerto 8001)

**Bot con Memoria Supabase:**
1. `cd whatsapp && python aly_bot_with_memory.py` (puerto 8002)
2. `ngrok http 8002` y copiar URL
3. Actualizar webhook en Twilio Console
4. ¡ALY responde con memoria conversacional!

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

1. **Procesar 2 documentos fallidos:**
   - `Addressing_the_impact_of_Masculinity_Influencers_on_Teenage_Boys...`
   - `Manual_de_Facilitación_Programa_Apapáchar.pdf`

2. **Testing final WhatsApp + Supabase** (listo para implementar)

## 🚀 Comandos Clave

**Ejecutar Sistema MVP ALY:**
```bash
cd /Users/daniel/Desktop/Dev/puddleAsistant/mvp
python agent_console.py
```

**RAG Simple MongoDB:**
```bash
cd /Users/daniel/Desktop/Dev/puddleAsistant/mongodb/scripts  
python rag_console.py
```