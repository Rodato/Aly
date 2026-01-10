-- ============================================================================
-- Puddle Assistant - Queries Útiles para Supabase
-- Archivo: 002_useful_queries.sql
-- Propósito: Queries comunes para administración y debugging
-- Fecha: 2024-12-01
-- ============================================================================

-- ============================================================================
-- ESTADÍSTICAS GENERALES
-- ============================================================================

-- Ver resumen completo del sistema
SELECT 
    'Documentos' as tabla, COUNT(*) as registros,
    ROUND(AVG(total_chunks)::numeric, 2) as promedio_chunks
FROM documents
UNION ALL
SELECT 
    'Chunks' as tabla, COUNT(*) as registros,
    ROUND(AVG(word_count)::numeric, 2) as promedio_palabras
FROM document_chunks
UNION ALL
SELECT 
    'Embeddings' as tabla, COUNT(*) as registros,
    NULL as extra
FROM chunk_embeddings;

-- Documentos por tipo
SELECT 
    document_type,
    COUNT(*) as cantidad,
    SUM(total_chunks) as total_chunks,
    ROUND(AVG(total_chunks)::numeric, 2) as promedio_chunks_por_doc
FROM documents 
GROUP BY document_type 
ORDER BY cantidad DESC;

-- ============================================================================
-- ANÁLISIS DE CONTENIDO
-- ============================================================================

-- Top palabras clave más frecuentes
SELECT 
    keyword,
    COUNT(*) as frecuencia
FROM (
    SELECT UNNEST(keywords) as keyword 
    FROM document_chunks 
    WHERE keywords IS NOT NULL
) t
WHERE keyword != ''
GROUP BY keyword
ORDER BY frecuencia DESC
LIMIT 20;

-- Top temas más frecuentes
SELECT 
    topic,
    COUNT(*) as frecuencia
FROM (
    SELECT UNNEST(topics) as topic 
    FROM document_chunks 
    WHERE topics IS NOT NULL
) t
WHERE topic != ''
GROUP BY topic
ORDER BY frecuencia DESC
LIMIT 15;

-- Distribución de tipos de contenido
SELECT 
    content_type,
    COUNT(*) as cantidad,
    ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM document_chunks))::numeric, 2) as porcentaje
FROM document_chunks 
GROUP BY content_type 
ORDER BY cantidad DESC;

-- ============================================================================
-- ANÁLISIS DE CALIDAD
-- ============================================================================

-- Chunks con más palabras clave (los más ricos semánticamente)
SELECT 
    d.document_title,
    dc.section_header,
    dc.chunk_summary,
    array_length(dc.keywords, 1) as num_keywords,
    dc.keywords,
    dc.word_count
FROM document_chunks dc
JOIN documents d ON d.id = dc.document_id
WHERE array_length(dc.keywords, 1) > 3
ORDER BY num_keywords DESC
LIMIT 10;

-- Chunks más largos por documento
SELECT 
    d.document_title,
    dc.section_header,
    dc.word_count,
    dc.text_length,
    LEFT(dc.content, 100) || '...' as preview
FROM document_chunks dc
JOIN documents d ON d.id = dc.document_id
ORDER BY dc.word_count DESC
LIMIT 10;

-- Documentos con chunks sin resumen (problemas de procesamiento)
SELECT 
    d.document_title,
    COUNT(*) as chunks_sin_resumen,
    d.total_chunks,
    ROUND((COUNT(*) * 100.0 / d.total_chunks)::numeric, 2) as porcentaje_sin_resumen
FROM documents d
JOIN document_chunks dc ON dc.document_id = d.id
WHERE dc.chunk_summary IS NULL OR dc.chunk_summary = ''
GROUP BY d.id, d.document_title, d.total_chunks
HAVING COUNT(*) > 0
ORDER BY porcentaje_sin_resumen DESC;

-- ============================================================================
-- BÚSQUEDAS Y FILTROS
-- ============================================================================

-- Buscar chunks por palabra clave específica
-- Ejemplo de uso: cambiar 'educación' por el término que buscas
SELECT 
    d.document_title,
    dc.section_header,
    dc.chunk_summary,
    dc.keywords
FROM document_chunks dc
JOIN documents d ON d.id = dc.document_id
WHERE 'educación' = ANY(dc.keywords)
ORDER BY d.document_title, dc.chunk_index;

-- Buscar en contenido de chunks (texto completo)
-- Ejemplo de uso: cambiar '%pedagogía%' por el término que buscas
SELECT 
    d.document_title,
    dc.section_header,
    LEFT(dc.content, 200) || '...' as preview,
    dc.chunk_summary
FROM document_chunks dc
JOIN documents d ON d.id = dc.document_id
WHERE dc.content ILIKE '%pedagogía%'
ORDER BY d.document_title;

-- Chunks de un documento específico ordenados
-- Ejemplo: cambiar el título por el documento que quieres ver
SELECT 
    dc.chunk_index,
    dc.section_header,
    dc.content_type,
    dc.word_count,
    LEFT(dc.chunk_summary, 100) || '...' as resumen_corto
FROM document_chunks dc
JOIN documents d ON d.id = dc.document_id
WHERE d.document_title ILIKE '%manual%'
ORDER BY dc.chunk_index;

-- ============================================================================
-- MANTENIMIENTO Y LIMPIEZA
-- ============================================================================

-- Eliminar documento específico y todos sus chunks/embeddings
-- CUIDADO: Esta query es destructiva, úsala con precaución
/*
DELETE FROM documents 
WHERE document_title = 'NOMBRE_DEL_DOCUMENTO_A_ELIMINAR';
-- Los chunks y embeddings se eliminarán automáticamente por CASCADE
*/

-- Ver chunks huérfanos (sin embeddings)
SELECT 
    d.document_title,
    dc.chunk_id,
    dc.section_header
FROM document_chunks dc
JOIN documents d ON d.id = dc.document_id
LEFT JOIN chunk_embeddings ce ON ce.chunk_id = dc.id
WHERE ce.id IS NULL
ORDER BY d.document_title;

-- Contar registros por tabla
SELECT 
    'documents' as tabla, 
    COUNT(*) as registros,
    pg_size_pretty(pg_total_relation_size('documents')) as tamaño
FROM documents
UNION ALL
SELECT 
    'document_chunks' as tabla, 
    COUNT(*) as registros,
    pg_size_pretty(pg_total_relation_size('document_chunks')) as tamaño
FROM document_chunks
UNION ALL
SELECT 
    'chunk_embeddings' as tabla, 
    COUNT(*) as registros,
    pg_size_pretty(pg_total_relation_size('chunk_embeddings')) as tamaño
FROM chunk_embeddings;

-- ============================================================================
-- PRUEBAS DE BÚSQUEDA VECTORIAL
-- ============================================================================

-- Ejemplo de búsqueda vectorial (requiere un vector de prueba)
-- Nota: Esto es solo un ejemplo, necesitarás un vector real para usar
/*
SELECT 
    d.document_title,
    dc.section_header,
    dc.chunk_summary,
    similarity
FROM match_documents(
    '[0.1,0.2,0.3,...]'::vector(1536),  -- Vector de consulta
    0.5,  -- Umbral de similitud mínimo
    5     -- Número máximo de resultados
) result
JOIN document_chunks dc ON dc.id = result.chunk_id
JOIN documents d ON d.id = result.document_id;
*/

-- Verificar que todos los chunks tienen embeddings
SELECT 
    COUNT(CASE WHEN ce.id IS NOT NULL THEN 1 END) as chunks_con_embeddings,
    COUNT(dc.id) as total_chunks,
    ROUND((COUNT(CASE WHEN ce.id IS NOT NULL THEN 1 END) * 100.0 / COUNT(dc.id))::numeric, 2) as porcentaje_completado
FROM document_chunks dc
LEFT JOIN chunk_embeddings ce ON ce.chunk_id = dc.id;

-- ============================================================================
-- MÉTRICAS DE RENDIMIENTO
-- ============================================================================

-- Tamaño promedio de embeddings y chunks por documento
SELECT 
    d.document_title,
    d.document_type,
    COUNT(dc.id) as num_chunks,
    ROUND(AVG(dc.word_count)::numeric, 2) as promedio_palabras_chunk,
    ROUND(AVG(dc.text_length)::numeric, 2) as promedio_caracteres_chunk,
    COUNT(ce.id) as num_embeddings
FROM documents d
LEFT JOIN document_chunks dc ON dc.document_id = d.id
LEFT JOIN chunk_embeddings ce ON ce.chunk_id = dc.id
GROUP BY d.id, d.document_title, d.document_type
ORDER BY num_chunks DESC;

-- ============================================================================
-- ANÁLISIS TEMPORAL
-- ============================================================================

-- Documentos procesados por fecha
SELECT 
    DATE(created_at) as fecha,
    COUNT(*) as documentos_procesados,
    STRING_AGG(document_title, '; ') as titulos
FROM documents
GROUP BY DATE(created_at)
ORDER BY fecha DESC;

-- Últimos chunks procesados
SELECT 
    d.document_title,
    dc.section_header,
    dc.created_at,
    LEFT(dc.chunk_summary, 100) || '...' as resumen
FROM document_chunks dc
JOIN documents d ON d.id = dc.document_id
ORDER BY dc.created_at DESC
LIMIT 10;