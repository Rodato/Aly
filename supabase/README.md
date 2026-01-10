# 🗄️ SQL Scripts - Puddle Assistant

Scripts SQL para configuración y mantenimiento de la base de datos Supabase.

## 📁 Estructura

```
sql/
├── README.md                    # Este archivo
└── supabase/
    ├── 001_create_tables.sql    # Creación inicial de schema
    └── 002_useful_queries.sql   # Queries útiles para administración
```

## 🚀 Instalación Inicial

### 1. Ejecutar Schema Principal
En el **SQL Editor** de Supabase, ejecuta:

```sql
-- Copiar y ejecutar todo el contenido de:
sql/supabase/001_create_tables.sql
```

Esto creará:
- ✅ Extensión **pgvector**
- ✅ Tabla **documents** (metadatos de documentos)
- ✅ Tabla **document_chunks** (chunks con metadatos enriquecidos)  
- ✅ Tabla **chunk_embeddings** (vectores para búsqueda semántica)
- ✅ **Índices optimizados** para rendimiento
- ✅ **Función de búsqueda** vectorial
- ✅ **Triggers** para mantenimiento

### 2. Verificación Post-Instalación
El script incluye verificaciones automáticas que mostrarán:
- Estado de pgvector
- Tablas creadas
- Índices configurados

## 📊 Administración

### Queries Útiles
El archivo `002_useful_queries.sql` contiene:

#### 📈 **Estadísticas**
- Resumen general del sistema
- Documentos por tipo
- Distribución de contenido

#### 🔍 **Análisis de Contenido**
- Top palabras clave más frecuentes
- Temas principales identificados
- Calidad de chunks

#### 🛠️ **Mantenimiento**
- Detectar chunks sin embeddings
- Limpiar datos huérfanos
- Métricas de rendimiento

#### 🔎 **Búsquedas**
- Buscar por palabras clave
- Filtrar por tipo de documento
- Búsqueda de texto completo

### Ejemplos de Uso Común

```sql
-- Ver estadísticas generales
SELECT tabla, registros FROM estadisticas_sistema;

-- Buscar documentos sobre "educación"
SELECT document_title, chunk_summary 
FROM chunks_por_keyword 
WHERE keyword = 'educación';

-- Ver documentos sin procesar completamente
SELECT * FROM documentos_con_problemas;
```

## 🔧 Schema de Datos

### Tabla: `documents`
Metadatos principales de cada documento:
- `document_title` - Título extraído automáticamente
- `document_type` - Tipo detectado (manual, guía, etc.)
- `document_summary` - Resumen generado por LLM
- `total_chunks` - Número de chunks procesados

### Tabla: `document_chunks`
Chunks de texto con análisis enriquecido:
- `content` - Contenido principal del chunk
- `chunk_summary` - Resumen específico del chunk
- `keywords[]` - Palabras clave extraídas por LLM
- `topics[]` - Temas identificados por LLM
- `section_header` - Ubicación en el documento

### Tabla: `chunk_embeddings`
Vectores para búsqueda semántica:
- `embedding` - Vector de 1536 dimensiones
- `embedding_text` - Texto optimizado usado para generar el vector
- `embedding_model` - Modelo utilizado (text-embedding-ada-002)

## 🚀 Funciones de Búsqueda

### `match_documents()`
Búsqueda vectorial de similitud semántica:

```sql
SELECT * FROM match_documents(
    query_embedding,    -- Vector de consulta
    0.78,              -- Umbral de similitud (0-1)
    5                  -- Máximo resultados
);
```

Retorna chunks ordenados por similitud con contexto completo.

## 📝 Mantenimiento Rutinario

### Verificar Integridad
```sql
-- Chunks sin embeddings
SELECT COUNT(*) FROM chunks_huerfanos;

-- Documentos procesados hoy
SELECT COUNT(*) FROM documentos_procesados_hoy;
```

### Limpiar Datos
```sql
-- Eliminar documento específico (¡CUIDADO!)
DELETE FROM documents 
WHERE document_title = 'nombre_documento';
```

### Monitoreo de Rendimiento
```sql
-- Tamaño de tablas
SELECT tabla, registros, tamaño FROM tamaño_tablas;

-- Índices más utilizados
SELECT * FROM uso_indices;
```

## 🔍 Troubleshooting

### Problemas Comunes

1. **pgvector no habilitado**
   ```sql
   CREATE EXTENSION vector;
   ```

2. **Índice vectorial lento**
   ```sql
   REINDEX INDEX idx_embeddings_cosine;
   ```

3. **Chunks sin embeddings**
   - Verificar logs de procesamiento
   - Re-ejecutar pipeline para documento específico

### Logs y Debugging
- Usar queries de `002_useful_queries.sql`
- Verificar integridad referencial
- Monitorear tamaños de tabla

## 📚 Referencias
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Supabase Vector Guide](https://supabase.com/docs/guides/ai/vector-embeddings)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)