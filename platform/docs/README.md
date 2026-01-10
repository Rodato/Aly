# 🏭 Puddle Platform - Documentación Técnica

## 🎯 Visión General

Puddle Platform es una interfaz de gestión **LLMOps (Large Language Model Operations)** diseñada para crear, configurar y desplegar múltiples agentes conversacionales personalizados. Permite abstraer la lógica de "un solo bot" (como ALY) hacia una "fábrica de bots" donde cada agente tiene su propia personalidad, base de conocimiento y canales de integración.

---

## 🏗️ Arquitectura del Sistema

La plataforma sigue una arquitectura de microservicios monolíticos separada del bot original de WhatsApp.

### 1. Estructura de Directorios (`/platform`)
```
platform/
├── backend/            # API REST (FastAPI)
│   ├── main.py         # Endpoints principales
│   ├── services/       # Lógica de negocio (Ingestión, RAG)
│   └── tmp_uploads/    # Almacenamiento temporal de archivos
├── frontend/           # Interfaz de Usuario (Next.js 14)
│   ├── src/app/        # Rutas (App Router)
│   │   ├── page.tsx    # Dashboard Principal
│   │   └── bots/[id]/  # Editor de Bot (Builder)
├── database/           # Scripts SQL
│   └── schema.sql      # Definición de tablas Supabase
└── docs/               # Esta documentación
```

### 2. Stack Tecnológico

*   **Frontend:** Next.js 14 (React), TypeScript, Tailwind CSS, Lucide Icons.
*   **Backend:** Python 3.11, FastAPI, Uvicorn.
*   **Base de Datos:** PostgreSQL (vía Supabase) con `pgvector` (planeado para RAG).
*   **Almacenamiento:** Supabase Storage (para PDFs/DOCX).

---

## 💾 Modelo de Datos (Supabase)

El esquema relacional (`platform/database/schema.sql`) soporta la multi-tenencia de bots:

### Tablas Principales
1.  **`bots`**: La entidad central.
    *   `id`: UUID único.
    *   `name`: Nombre del agente (ej. "ALY", "Soporte IT").
    *   `system_prompt`: La "personalidad" e instrucciones base.
    *   `model_name`: Modelo LLM a usar (ej. `gpt-4o-mini`).
    *   `temperature`: Nivel de creatividad (0.0 - 1.0).

2.  **`bot_knowledge`**: Agrupa documentos por bot.
    *   Permite que el Bot A no sepa lo que sabe el Bot B.

3.  **`bot_integrations`** (Planeado):
    *   Gestiona credenciales de Twilio/WhatsApp por bot.

---

## 🔌 API Reference (Backend)

El backend corre en `http://localhost:8000`.

### Gestión de Bots
*   `GET /bots`: Lista todos los agentes creados.
*   `POST /bots`: Crea un nuevo agente.
    *   Body: `{ "name": "...", "system_prompt": "..." }`
*   `GET /bots/{id}`: Obtiene la configuración completa de un agente.

### Gestión de Conocimiento
*   `POST /bots/{id}/documents`: Sube un archivo para ser indexado.
    *   Format: `multipart/form-data`
    *   Process: Guarda en disco -> Dispara tarea en background (Docling + Embeddings).

---

## 🖥️ Interfaz de Usuario (Frontend)

El frontend corre en `http://localhost:3000`.

### 1. Dashboard (`/`)
*   Vista general de todos los bots.
*   Indicadores de estado (Activo/Inactivo).
*   Acceso rápido a crear nuevos agentes.

### 2. Bot Builder (`/bots/[id]`)
Interfaz de edición con navegación por pestañas:

*   **Pestaña Configuración:**
    *   Editor de System Prompt con área de texto amplia.
    *   Selectores para Modelo y Sliders para Temperatura.
    *   Feedback visual de guardado.

*   **Pestaña Conocimiento:**
    *   **Drag & Drop:** Zona interactiva para subir archivos.
    *   **Lista de Archivos:** Muestra estado (`processing`, `indexed`) y metadatos.
    *   Integración real con el endpoint de subida del backend.

---

## 🚀 Guía de Instalación y Ejecución

### Prerrequisitos
*   Node.js 18+
*   Python 3.11+
*   Cuenta de Supabase (URL y Key)

### 1. Configurar Backend
```bash
cd platform/backend
# Crear entorno virtual si es necesario
pip install -r requirements.txt
cp ../../.env .env  # Copiar credenciales
uvicorn main:app --reload --port 8000
```

### 2. Configurar Frontend
```bash
cd platform/frontend
npm install
npm run dev
```

### 3. Configurar Base de Datos
Ejecutar el script `platform/database/schema.sql` en el Editor SQL de Supabase para crear las tablas necesarias.

---

## 📝 Estado Actual y Próximos Pasos

### ✅ Completado
*   [x] Diseño de arquitectura desacoplada.
*   [x] API CRUD básica para Bots.
*   [x] UI moderna con Tailwind y Next.js.
*   [x] Integración Frontend-Backend (Fetch real).
*   [x] Sistema de subida de archivos (Upload Pipeline).

### 🚧 Pendiente
*   [ ] **Pipeline RAG Real:** Conectar el `background_task` de subida con el script `complete_pipeline.py` para generar embeddings reales.
*   [ ] **Chat Playground:** Widget de chat en el frontend para probar el bot.
*   [ ] **Integración WhatsApp Dinámica:** Hacer que el webhook de Twilio enrute mensajes al bot correcto según el número de destino.

---
*Documentación generada automáticamente el 2026-01-02*
