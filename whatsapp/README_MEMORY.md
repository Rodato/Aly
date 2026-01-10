# 🧠 ALY WhatsApp Bot with Supabase Memory

Bot de WhatsApp con sistema de memoria conversacional completo usando Supabase.

## 🏗️ **Arquitectura de Memoria**

```
User Message → ALY Processing → Response + Memory Storage → WhatsApp
                   ↓
Supabase: Users + Conversations + Messages + Memory + Analytics
```

## 📋 **Componentes Implementados**

### **1. Base de Datos Supabase**
- **Users**: Perfiles de usuario y preferencias
- **Conversations**: Sesiones de conversación  
- **Messages**: Mensajes individuales con metadatos
- **Conversation_Memory**: Memoria contextual para continuidad
- **User_Preferences**: Preferencias educativas y progreso
- **Session_Analytics**: Métricas de performance y uso

### **2. Memory Manager**
- **SupabaseMemoryManager**: Administrador completo de memoria
- **Gestión de usuarios**: Crear/obtener perfiles
- **Contexto conversacional**: Generar memoria para ALY
- **Analíticas**: Patrones de interacción y estadísticas

### **3. Bot con Memoria**
- **aly_bot_with_memory.py**: Bot integrado con Supabase
- **Memoria conversacional**: Contexto para respuestas
- **Persistencia**: Todas las interacciones guardadas
- **Analytics**: Estadísticas en tiempo real

## 🚀 **Setup e Instalación**

### **1. Configurar Supabase**
```bash
# 1. Crear proyecto en Supabase
# 2. Ejecutar schema SQL
psql -h [supabase-host] -U postgres -d postgres -f supabase_schema.sql

# 3. Agregar credenciales a .env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
```

### **2. Instalar Dependencias**
```bash
cd whatsapp
pip install -r requirements.txt  # Incluye supabase>=2.0.0
```

### **3. Ejecutar Bot con Memoria**
```bash
# Bot con memoria (puerto 8002)
python aly_bot_with_memory.py

# Exponer con ngrok
ngrok http 8002
```

## 🧠 **Funcionalidades de Memoria**

### **Memoria Conversacional**
- **Contexto reciente**: Últimos 3 mensajes de la conversación
- **Memoria importante**: Entradas de alta relevancia
- **Continuidad**: Referencia a temas anteriores
- **Personalización**: Adaptación a patrones de usuario

### **Gestión de Usuarios**
- **Perfiles automáticos**: Creación al primer contacto
- **Preferencias de idioma**: Detección y actualización automática
- **Historial completo**: Todas las interacciones almacenadas
- **Patrones de uso**: Agentes favoritos, temas frecuentes

### **Analytics Integradas**
- **Performance**: Tiempos de respuesta, uso de agentes
- **Engagement**: Patrones de conversación, satisfacción
- **Insights**: Temas populares, eficacia de agentes

## 📊 **Endpoints del Bot**

### **Core Endpoints**
```bash
# Health check con memoria
GET /health
Response: {
  "aly_status": "ready",
  "memory_status": "ready", 
  "system_stats": {...}
}

# Estadísticas avanzadas
GET /stats
Response: {
  "bot_status": {...},
  "usage_stats": {...},
  "features": {...}
}

# Perfil de usuario
GET /user/{phone_number}/profile
Response: {
  "user_profile": {...},
  "interaction_patterns": {...}
}
```

### **Admin Endpoints**
```bash
# Limpieza de datos antiguos
POST /admin/cleanup?days=30

# Envío manual de mensajes
POST /send_message
Body: {"from_number": "+1234567890", "message": "test"}
```

## 🗃️ **Schema de Base de Datos**

### **Tabla Users**
```sql
- id (UUID, PK)
- phone_number (VARCHAR, UNIQUE)
- preferred_language (es/en/pt)
- total_messages (INTEGER)
- first_interaction_at, last_interaction_at
- user_context (JSONB)
```

### **Tabla Messages**  
```sql
- conversation_id (UUID, FK)
- user_message, bot_response (TEXT)
- agent_type, detected_intent
- sources_used (JSONB)
- response_time_ms
- message_timestamp
```

### **Tabla Conversation_Memory**
```sql
- conversation_id (UUID, FK)
- memory_type (context/preference/topic/goal)
- memory_content (TEXT)
- importance_score (0.0-1.0)
- last_referenced_at
```

## 🎯 **Tipos de Memoria**

### **Por Agente**
- **RAG Agent** → `context` memory (score: 0.6)
- **Workshop Agent** → `goal` memory (score: 0.8)  
- **Brainstorming Agent** → `preference` memory (score: 0.7)
- **Safe Edge Agent** → `sensitive_topic` memory (score: 0.9)
- **Fallback Agent** → `clarification` memory (score: 0.5)

### **Por Intención**
- **PLAN**, **IDEATE** → Alta importancia (0.7-0.8)
- **SENSITIVE** → Máxima importancia (0.9)
- **FACTUAL** → Importancia media (0.6)
- **AMBIGUOUS** → Baja importancia (0.5)

## 🔧 **Configuración de Memoria**

### **Parámetros de Contexto**
```python
RECENT_MESSAGES_LIMIT = 3      # Mensajes recientes para contexto
MEMORY_ENTRIES_LIMIT = 5       # Entradas de memoria por consulta  
MEMORY_RETENTION_DAYS = 30     # Días antes de limpiar memoria
IMPORTANCE_THRESHOLD = 0.3     # Umbral mínimo de importancia
```

### **Generación Automática**
- **Contexto conversacional**: Automático en cada interacción
- **Entradas de memoria**: Basado en tipo de agente e intención
- **Puntuación de importancia**: Algoritmo dinámico
- **Limpieza automática**: Trigger de 30 días para entradas irrelevantes

## 📈 **Performance y Escalabilidad**

### **Optimizaciones**
- **Índices Supabase**: Optimizados para consultas frecuentes
- **Memory pooling**: Límite de entradas por consulta
- **Async processing**: Thread pools para operaciones DB
- **Cache temporal**: Contexto en memoria durante sesión

### **Monitoring**
- **Response times**: Tracking en tiempo real
- **Memory usage**: Estadísticas de memoria por usuario
- **Error rates**: Monitoreo de fallos DB
- **User engagement**: Métricas de satisfacción inferidas

## 🔄 **Flujo de Memoria**

1. **Mensaje llega** → Obtener usuario y conversación
2. **Generar contexto** → Mensajes recientes + memoria importante  
3. **Procesar con ALY** → Contexto enriquecido para mejor respuesta
4. **Almacenar interacción** → Mensaje, respuesta, metadatos
5. **Crear memoria** → Si es relevante según agente/intención
6. **Responder** → Con contexto personalizado

## 🛡️ **Seguridad y Privacidad**

### **Protección de Datos**
- **PII mínimo**: Solo número de teléfono como identificador
- **Retención controlada**: Limpieza automática de datos antiguos
- **Encriptación**: TLS para todas las comunicaciones
- **Acceso controlado**: RLS configurado en Supabase

### **Gestión de Memoria**
- **Importancia dinámica**: Contenido sensible priorizado
- **Expiración automática**: Memoria irrelevante se desactiva
- **Anonymización**: Contenidos personales protegidos
- **Auditoría**: Tracking completo de acceso a memoria

---

**Status**: ✅ **Totalmente implementado y listo para pruebas**
**Puerto**: 8002 (evita conflicto con bot básico en 8001)  
**Next**: Configurar Supabase schema y probar memoria conversacional