#!/usr/bin/env python3
"""
Script automático para procesar documentos con Docling
Convierte PDFs/DOCX a Markdown y genera tabla de seguimiento
"""

import os
import json
from pathlib import Path
from datetime import datetime
from docling.document_converter import DocumentConverter
import pandas as pd

def main():
    print("🚀 PROCESAMIENTO AUTOMÁTICO DE DOCUMENTOS")
    print("="*60)
    
    # Configuración
    input_folder = Path("documents")
    output_folder = Path("DocsMD")
    status_file = Path("processing_status.json")
    
    # Crear carpeta de salida
    output_folder.mkdir(exist_ok=True)
    
    # Inicializar conversor
    converter = DocumentConverter()
    
    # Cargar estado previo
    if status_file.exists():
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                status_data = json.load(f)
        except Exception as e:
            print(f"⚠️ Error cargando estado: {e}")
            status_data = {"processed_files": {}, "stats": {"successful": 0, "failed": 0}}
    else:
        status_data = {"processed_files": {}, "stats": {"successful": 0, "failed": 0}}
    
    # Obtener archivos soportados
    supported_extensions = {'.pdf', '.docx', '.doc', '.pptx'}
    files = [f for f in input_folder.iterdir() 
             if f.is_file() and f.suffix.lower() in supported_extensions]
    
    if not files:
        print("❌ No se encontraron archivos soportados en documents/")
        return
    
    print(f"📂 Entrada: {input_folder}")
    print(f"📂 Salida: {output_folder}")
    print(f"📄 Archivos encontrados: {len(files)}")
    print()
    
    processed_count = 0
    skipped_count = 0
    failed_count = 0
    
    # Procesar cada archivo
    for i, file_path in enumerate(files, 1):
        print(f"[{i}/{len(files)}] 📄 {file_path.name}")
        
        # Verificar si ya fue procesado exitosamente
        md_path = output_folder / f"{file_path.stem}.md"
        file_key = str(file_path.name)
        
        if (file_key in status_data["processed_files"] and 
            status_data["processed_files"][file_key].get("status") == "success" and 
            md_path.exists()):
            print(f"  ⏭️ Ya procesado: {md_path.name}")
            skipped_count += 1
            continue
        
        try:
            # Convertir con Docling
            print("  🔄 Convirtiendo...")
            result = converter.convert(file_path)
            markdown_content = result.document.export_to_markdown()
            
            # Guardar Markdown
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # Actualizar estado
            file_info = {
                "status": "success",
                "md_file": md_path.name,
                "processed_at": datetime.now().isoformat(),
                "original_size": file_path.stat().st_size,
                "md_size": md_path.stat().st_size,
                "md_length": len(markdown_content)
            }
            
            status_data["processed_files"][file_key] = file_info
            status_data["stats"]["successful"] += 1
            
            print(f"  ✅ Convertido: {md_path.name} ({len(markdown_content):,} caracteres)")
            processed_count += 1
            
        except Exception as e:
            # Registrar error
            error_info = {
                "status": "failed",
                "error": str(e),
                "processed_at": datetime.now().isoformat()
            }
            
            status_data["processed_files"][file_key] = error_info
            status_data["stats"]["failed"] += 1
            
            print(f"  ❌ Error: {str(e)[:100]}...")
            failed_count += 1
    
    # Guardar estado actualizado
    status_data["last_update"] = datetime.now().isoformat()
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 RESUMEN DEL PROCESAMIENTO:")
    print(f"  📄 Archivos encontrados: {len(files)}")
    print(f"  ✅ Procesados ahora: {processed_count}")
    print(f"  ⏭️ Ya procesados: {skipped_count}")
    print(f"  ❌ Errores: {failed_count}")
    print(f"  📁 Total archivos MD: {len(list(output_folder.glob('*.md')))}")
    
    # Generar tabla de estado
    print(f"\n📋 TABLA DE ESTADO:")
    print("-" * 80)
    
    table_data = []
    for file_path in files:
        file_info = status_data["processed_files"].get(file_path.name, {})
        md_path = output_folder / f"{file_path.stem}.md"
        
        row = {
            "Archivo": file_path.name,
            "Tamaño (KB)": f"{file_path.stat().st_size / 1024:.1f}",
            "Estado": file_info.get("status", "pendiente"),
            "MD Generado": "✅" if md_path.exists() else "❌",
            "Procesado": file_info.get("processed_at", "N/A")[:19] if file_info.get("processed_at") else "N/A"
        }
        
        if file_info.get("error"):
            row["Error"] = str(file_info["error"])[:50] + "..."
        
        table_data.append(row)
    
    if table_data:
        df = pd.DataFrame(table_data)
        print(df.to_string(index=False))
        
        # Guardar tabla como CSV
        report_path = "processing_report.csv"
        df.to_csv(report_path, index=False, encoding='utf-8')
        print(f"\n💾 Tabla guardada en: {report_path}")
    
    # Listar archivos MD generados
    md_files = sorted(output_folder.glob('*.md'))
    print(f"\n📁 ARCHIVOS MARKDOWN EN {output_folder}:")
    print("-" * 50)
    
    if md_files:
        for md_file in md_files:
            size = md_file.stat().st_size / 1024
            print(f"  📄 {md_file.name} ({size:.1f} KB)")
    else:
        print("  (No hay archivos Markdown)")
    
    print(f"\n✨ ¡Procesamiento completado!")
    if processed_count > 0:
        print(f"Los archivos Markdown están listos en la carpeta '{output_folder}'")

if __name__ == "__main__":
    main()