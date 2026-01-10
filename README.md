# 🎓 Puddle Assistant - Sistema RAG Educativo

Sistema RAG (Retrieval-Augmented Generation) especializado en educación de género y desarrollo infantil.

## 🎯 Descripción

Puddle Assistant es un asistente inteligente que permite consultar documentos educativos especializados usando tecnologías de búsqueda semántica y generación de respuestas contextualizadas.

## 📊 Estado del Proyecto

✅ **SISTEMA COMPLETAMENTE FUNCIONAL**

- **6 documentos procesados** (1544 chunks)
- **Base de datos vectorial MongoDB** con embeddings OpenAI
- **RAG funcional** con respuestas contextualizadas
- **Títulos únicos** extraídos con LLM

## 🏗️ Arquitectura

```
📄 Documentos PDF/DOCX → 🔄 Docling → 📝 Markdown → ✂️ Chunking → 🧠 OpenAI Embeddings → 🗄️ MongoDB → 🤖 RAG
```

### Stack Tecnológico

- **Procesamiento:** Docling (OCR avanzado)
- **Chunking:** Semántico con metadatos enriquecidos
- **Embeddings:** OpenAI text-embedding-ada-002
- **Vector DB:** MongoDB Atlas con vector search
- **LLM:** OpenRouter Mistral 8B
- **Interfaz:** Python console

## 📁 Estructura del Proyecto

```
puddleAsistant/
├── 📄 README.md                 # Esta documentación
├── 📄 CLAUDE.md                 # Memoria del proyecto para Claude
├── 📄 requirements.txt          # Dependencias Python
├── 📄 puddle.py                 # Script principal unificado
├── 📄 .env                      # Variables de entorno
│
├── 🗂️ data/                    # Datos del proyecto
│   ├── raw/documents/           # PDFs/DOCX originales (6 archivos)
│   ├── processed/
│   │   ├── DocsMD/             # Archivos Markdown procesados
│   │   ├── embeddings/         # Embeddings JSON (6 archivos)
│   │   └── backups/            # Archivos de respaldo
│   └── chroma_db/              # Base de datos ChromaDB (legacy)
│
├── 🗂️ scripts/                # Scripts de procesamiento
│   ├── document_processor.py   # Procesador principal Docling
│   ├── enhanced_chunker.py     # Chunking semántico avanzado
│   ├── simple_openai_embeddings.py  # Pipeline embeddings OpenAI
│   └── [otros scripts]
│
├── 🗂️ mongodb/                # Sistema MongoDB
│   └── scripts/
│       ├── upload_to_mongodb.py      # Uploader principal
│       ├── upload_large_document.py  # Para documentos grandes
│       ├── update_titles_mongo.py    # Actualizar títulos
│       ├── simple_rag_mongo.py       # Motor RAG
│       └── rag_console.py            # Interfaz de consola
│
├── 🗂️ supabase/               # Sistema Supabase (alternativo)
│   ├── scripts/               # Scripts de Supabase
│   └── [archivos SQL]
│
├── 🗂️ rag/                    # Testing RAG
│   └── testing/
│       ├── test_rag.py
│       └── test_title_extraction.py
│
├── 🗂️ tools/                  # Herramientas adicionales
├── 🗂️ logs/                   # Logs y reportes
├── 🗂️ docs/                   # Documentación
├── 🗂️ config/                 # Configuraciones
└── 🗂️ venv/                   # Entorno virtual Python
```

## 🚀 Uso Rápido

### 1. Configuración Inicial

```bash
# Clonar y configurar
git clone <repo>
cd puddleAsistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys
```

### 2. Usar el RAG

```bash
# Consola interactiva
python3 mongodb/scripts/rag_console.py
```

**Ejemplos de preguntas:**
- "¿Qué estrategias recomienda para involucrar a los niños?"
- "¿Cómo pueden los padres apoyar la educación?"
- "¿Qué actividades se sugieren para el club de niños?"

## 📋 Documentos Disponibles

1. **Semillas de Igualdad** (Manual GBI México) - 78 chunks
2. **Manual de Facilitación A+P** - 437 chunks  
3. **Guía para Implementar Clubes de Niños** - 567 chunks
4. **Guía para Educadores: Engaging Boys in Education** - 161 chunks
5. **Guía de Clase para Engajar Niños en la Educación** - 252 chunks
6. **Guía para Padres y Cuidadores** - 49 chunks

**Total:** 1544 chunks con embeddings semánticos

## 🛠️ Scripts Principales

### Procesamiento de Documentos
```bash
# Procesar documentos con Docling
python3 scripts/document_processor.py

# Generar embeddings
python3 scripts/simple_openai_embeddings.py --single "archivo.md"

# Subir a MongoDB
python3 mongodb/scripts/upload_to_mongodb.py --file "archivo_embeddings.json"
```

### RAG y Consultas
```bash
# Interfaz de consola
python3 mongodb/scripts/rag_console.py

# Estadísticas de la base de datos
python3 mongodb/scripts/upload_to_mongodb.py --stats

# Tests del sistema
python3 rag/testing/test_rag.py
```

## ⚙️ Configuración

### Variables de Entorno (.env)
```env
# APIs
OPENAI_API_KEY=tu_openai_key
OPENROUTER_API_KEY=tu_openrouter_key

# MongoDB
MONGODB_URI=mongodb+srv://usuario:password@cluster.mongodb.net/
MONGODB_DB_NAME=embeddgins_puddle
MONGODB_COLLECTION_NAME=embeddings_1

# Supabase (opcional)
SUPABASE_URL=tu_supabase_url
SUPABASE_ANON_KEY=tu_supabase_key
```

### Dependencias Principales
- `docling>=2.63.0` - Conversión avanzada PDF/DOCX
- `openai>=1.30.1` - Embeddings y API
- `pymongo` - Cliente MongoDB
- `requests` - HTTP requests
- `python-dotenv` - Variables de entorno

## 🧪 Testing

```bash
# Test completo del RAG
python3 rag/testing/test_rag.py

# Test de extracción de títulos
python3 rag/testing/test_title_extraction.py
```

## 📈 Métricas del Sistema

- **Precisión semántica:** >82% similitud promedio
- **Tiempo de respuesta:** 5-8 segundos por consulta
- **Cobertura:** 99.94% del dataset (1544/1545 chunks)
- **Documentos:** 6 guías educativas especializadas

## 🔧 Resolución de Problemas

### Error de conexión MongoDB
```bash
# Verificar configuración
python3 mongodb/scripts/upload_to_mongodb.py --stats
```

### Regenerar embeddings
```bash
# Para un documento específico
python3 scripts/simple_openai_embeddings.py --single "nombre_archivo.md"
```

### Actualizar títulos
```bash
python3 mongodb/scripts/update_titles_mongo.py
```

## 🎯 Casos de Uso

- **Educadores:** Consultar estrategias pedagógicas específicas
- **Padres:** Obtener guías de apoyo educativo  
- **Facilitadores:** Acceder a metodologías de talleres
- **Investigadores:** Explorar contenido sobre género en educación

## 🚨 Notas Importantes

1. **API Keys:** Asegurar que todas las keys estén configuradas en `.env`
2. **MongoDB:** Requiere cluster Atlas configurado
3. **Tamaño documentos:** Límite 16MB por chunk en MongoDB
4. **Embeddings:** Usa OpenAI ada-002 (1536 dimensiones)

## 📞 Soporte

Para problemas o mejoras:
1. Revisar logs en `logs/`
2. Verificar configuración en `.env`
3. Consultar `CLAUDE.md` para contexto técnico

---

**Estado:** ✅ Sistema completamente funcional (Diciembre 2025)  
**Versión:** 1.0 - RAG MongoDB Pipeline