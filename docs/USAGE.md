# 📖 Guía de Uso - Puddle Assistant

## 🎯 Guía de Comandos

### 📄 Procesamiento de Documentos

#### Comandos Básicos

```bash
# Procesar todos los documentos nuevos
python3 scripts/document_processor.py

# Ver solo estadísticas
python3 scripts/document_processor.py --stats

# Procesar un archivo específico
python3 scripts/document_processor.py --single "manual.pdf"

# Forzar reprocesamiento completo
python3 scripts/document_processor.py --force
```

#### Ejemplos de Uso

```bash
# Ejemplo 1: Procesamiento inicial
cd /path/to/puddleAsistant
python3 scripts/document_processor.py

# Ejemplo 2: Agregar nuevo documento
cp nuevo_manual.pdf data/raw/documents/
python3 scripts/document_processor.py --single "nuevo_manual.pdf"

# Ejemplo 3: Verificar estado
python3 scripts/document_processor.py --stats
```

### 📊 Generación de Reportes

#### Comandos de Reportes

```bash
# Reporte completo (recomendado)
python3 scripts/status_reporter.py

# Solo resumen ejecutivo
python3 scripts/status_reporter.py --summary

# Solo tabla detallada con CSV
python3 scripts/status_reporter.py --table

# Listar archivos Markdown generados
python3 scripts/status_reporter.py --files

# Tabla sin guardar CSV
python3 scripts/status_reporter.py --table --no-csv
```

## 🔧 Flujos de Trabajo Comunes

### 1. Setup Inicial del Proyecto

```bash
# Paso 1: Clonar y configurar entorno
git clone <repo>
cd puddleAsistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Paso 2: Configurar API keys
echo "OPENROUTER_API_KEY=tu_key" > .env

# Paso 3: Agregar documentos
cp *.pdf data/raw/documents/

# Paso 4: Procesar documentos
python3 scripts/document_processor.py

# Paso 5: Verificar resultados
python3 scripts/status_reporter.py

# Paso 6: Ejecutar interfaz
streamlit run tools/main.py
```

### 2. Agregar Nuevos Documentos

```bash
# Copiar documentos nuevos
cp nuevos_docs/*.pdf data/raw/documents/

# Procesar solo los nuevos (automático)
python3 scripts/document_processor.py

# Verificar procesamiento
python3 scripts/status_reporter.py --summary
```

### 3. Mantenimiento y Limpieza

```bash
# Ver estado actual
python3 scripts/status_reporter.py --summary

# Reprocesar documentos con errores
python3 scripts/document_processor.py --force

# Limpiar logs antiguos
find logs/ -name "*.log" -mtime +30 -delete

# Backup de estado
cp logs/processing_status.json logs/backup_$(date +%Y%m%d).json
```

## 🎮 Uso de la Interfaz Web

### Iniciar Streamlit

```bash
# Método 1: Comando directo
streamlit run tools/main.py

# Método 2: Con configuración específica
streamlit run tools/main.py --server.port 8501
```

### Funcionalidades de la Interfaz

1. **📄 Subida de Documentos**
   - Arrastra archivos PDF/TXT
   - Soporta múltiples archivos
   - Procesamiento automático

2. **🚀 Creación de Base de Datos**
   - Click en "Crear Base de Datos"
   - Esperar procesamiento completo
   - Verificación automática

3. **💬 Chat Interactivo**
   - Escribe preguntas en lenguaje natural
   - Recibe respuestas contextualizadas
   - Ve fuentes de información

4. **🔍 Exploración de Fuentes**
   - Expandir sección "Ver fuentes"
   - Revisar fragmentos relevantes
   - Identificar documentos de origen

## 🧪 Casos de Uso Específicos

### Caso 1: Análisis de Manuales Técnicos

```bash
# Preparar documentos técnicos
mkdir data/raw/documents/manuals
cp manual_*.pdf data/raw/documents/manuals/

# Procesar con logging detallado
python3 scripts/document_processor.py > logs/manual_processing.log 2>&1

# Generar reporte específico
python3 scripts/status_reporter.py --table > logs/manual_report.txt
```

### Caso 2: Base de Conocimiento Corporativa

```bash
# Estructura para departamentos
mkdir -p data/raw/documents/{hr,legal,tech,finance}

# Procesar por lotes
for dept in hr legal tech finance; do
    cp ${dept}_docs/* data/raw/documents/${dept}/
    python3 scripts/document_processor.py
done

# Reporte consolidado
python3 scripts/status_reporter.py --all > logs/corporate_kb_report.txt
```

### Caso 3: Investigación Académica

```bash
# Documentos de investigación
cp papers/*.pdf data/raw/documents/
cp theses/*.pdf data/raw/documents/

# Procesamiento con métricas
time python3 scripts/document_processor.py

# Análisis de contenido
python3 scripts/status_reporter.py --summary
streamlit run tools/main.py
```

## ⚠️ Resolución de Problemas

### Problemas Comunes

#### 1. Error de API Key

```bash
# Verificar configuración
cat .env | grep OPENROUTER

# Reconfigurar si es necesario
echo "OPENROUTER_API_KEY=nueva_key" > .env
```

#### 2. Documentos No se Procesan

```bash
# Verificar permisos de archivos
ls -la data/raw/documents/

# Verificar formato soportado
file data/raw/documents/*.pdf

# Intentar procesamiento individual
python3 scripts/document_processor.py --single "problema.pdf"
```

#### 3. Base de Datos Corrupta

```bash
# Backup actual
mv data/chroma_db data/chroma_db.backup

# Reprocesar desde Markdown
python3 tools/rag_assistant.py  # crear nueva base
```

#### 4. Streamlit No Inicia

```bash
# Verificar puerto disponible
netstat -tulpn | grep :8501

# Usar puerto diferente
streamlit run tools/main.py --server.port 8502

# Verificar dependencias
pip install --upgrade streamlit
```

### Logs de Diagnóstico

```bash
# Ver logs recientes
tail -f logs/processing.log

# Buscar errores específicos
grep -i error logs/processing.log

# Analizar estado de procesamiento
python3 -c "
import json
with open('logs/processing_status.json') as f:
    data = json.load(f)
    failed = [k for k,v in data['processed_files'].items() if v.get('status') == 'failed']
    print('Archivos fallidos:', failed)
"
```

## 🔄 Automatización

### Cron Jobs para Procesamiento Automático

```bash
# Editar crontab
crontab -e

# Agregar tarea diaria a las 2 AM
0 2 * * * /path/to/puddleAsistant/venv/bin/python /path/to/puddleAsistant/scripts/document_processor.py >> /path/to/puddleAsistant/logs/cron.log 2>&1

# Reporte semanal los lunes a las 9 AM
0 9 * * 1 /path/to/puddleAsistant/venv/bin/python /path/to/puddleAsistant/scripts/status_reporter.py --all > /path/to/puddleAsistant/logs/weekly_report_$(date +\%Y\%m\%d).txt
```

### Script de Monitoreo

```bash
#!/bin/bash
# monitor.sh - Monitoreo automático

PROJ_DIR="/path/to/puddleAsistant"
cd $PROJ_DIR

# Verificar documentos nuevos
NEW_DOCS=$(find data/raw/documents -name "*.pdf" -newer logs/last_check.timestamp 2>/dev/null | wc -l)

if [ $NEW_DOCS -gt 0 ]; then
    echo "Encontrados $NEW_DOCS documentos nuevos"
    python3 scripts/document_processor.py
    python3 scripts/status_reporter.py --summary
fi

# Actualizar timestamp
touch logs/last_check.timestamp
```

## 📈 Optimización de Rendimiento

### Configuración para Documentos Grandes

```python
# En tools/rag_assistant.py
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,        # Aumentar para docs grandes
    chunk_overlap=300,      # Más overlap para mejor contexto
    length_function=len
)
```

### Procesamiento en Lotes

```bash
# Procesar documentos en grupos pequeños
find data/raw/documents -name "*.pdf" | head -5 | while read file; do
    python3 scripts/document_processor.py --single "$(basename "$file")"
    sleep 2  # Pausa entre archivos
done
```

### Limpieza de Cache

```bash
# Limpiar cache de Streamlit
streamlit cache clear

# Limpiar archivos temporales
find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete
```