import os
import json
from pathlib import Path
from datetime import datetime
from docling.document_converter import DocumentConverter
import pandas as pd

class DoclingProcessor:
    def __init__(self, 
                 input_folder="documents", 
                 output_folder="DocsMD", 
                 status_file="processing_status.json"):
        
        self.input_path = Path(input_folder)
        self.output_path = Path(output_folder)
        self.status_file = Path(status_file)
        
        # Crear carpeta de salida
        self.output_path.mkdir(exist_ok=True)
        
        # Inicializar conversor
        self.converter = DocumentConverter()
        
        # Cargar estado previo o crear nuevo
        self.status_data = self.load_status()
    
    def load_status(self):
        """Carga el estado de procesamiento anterior."""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error cargando estado: {e}")
        
        return {
            "processed_files": {},
            "last_update": None,
            "stats": {
                "total_processed": 0,
                "successful": 0,
                "failed": 0
            }
        }
    
    def save_status(self):
        """Guarda el estado actual."""
        self.status_data["last_update"] = datetime.now().isoformat()
        
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(self.status_data, f, indent=2, ensure_ascii=False)
    
    def get_supported_files(self):
        """Obtiene lista de archivos soportados."""
        supported_extensions = {'.pdf', '.docx', '.doc', '.pptx'}
        files = []
        
        for file_path in self.input_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                files.append(file_path)
        
        return files
    
    def is_already_processed(self, file_path):
        """Verifica si el archivo ya fue procesado."""
        file_key = str(file_path.name)
        
        if file_key in self.status_data["processed_files"]:
            file_info = self.status_data["processed_files"][file_key]
            
            # Verificar si el archivo MD existe
            md_path = self.output_path / f"{file_path.stem}.md"
            if md_path.exists() and file_info.get("status") == "success":
                return True
        
        return False
    
    def convert_document(self, file_path):
        """Convierte un documento a Markdown."""
        print(f"📄 Procesando: {file_path.name}")
        
        try:
            # Convertir con Docling
            result = self.converter.convert(file_path)
            markdown_content = result.document.export_to_markdown()
            
            # Crear nombre de archivo MD
            md_filename = f"{file_path.stem}.md"
            md_path = self.output_path / md_filename
            
            # Guardar Markdown
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # Actualizar estado
            file_info = {
                "status": "success",
                "md_file": md_filename,
                "processed_at": datetime.now().isoformat(),
                "original_size": file_path.stat().st_size,
                "md_size": md_path.stat().st_size,
                "md_length": len(markdown_content)
            }
            
            self.status_data["processed_files"][file_path.name] = file_info
            self.status_data["stats"]["successful"] += 1
            
            print(f"✅ Convertido: {md_filename} ({len(markdown_content):,} caracteres)")
            return True
            
        except Exception as e:
            # Registrar error
            error_info = {
                "status": "failed",
                "error": str(e),
                "processed_at": datetime.now().isoformat()
            }
            
            self.status_data["processed_files"][file_path.name] = error_info
            self.status_data["stats"]["failed"] += 1
            
            print(f"❌ Error procesando {file_path.name}: {e}")
            return False
    
    def process_all(self, force_reprocess=False):
        """Procesa todos los documentos."""
        print("🚀 Iniciando procesamiento con Docling...")
        print(f"📂 Entrada: {self.input_path}")
        print(f"📂 Salida: {self.output_path}")
        print()
        
        files = self.get_supported_files()
        
        if not files:
            print("❌ No se encontraron archivos soportados")
            return
        
        processed_count = 0
        skipped_count = 0
        
        for file_path in files:
            # Verificar si ya fue procesado
            if not force_reprocess and self.is_already_processed(file_path):
                print(f"⏭️ Ya procesado: {file_path.name}")
                skipped_count += 1
                continue
            
            # Convertir documento
            success = self.convert_document(file_path)
            if success:
                processed_count += 1
            
            self.status_data["stats"]["total_processed"] += 1
        
        # Guardar estado
        self.save_status()
        
        # Mostrar resumen
        print(f"\n📊 Resumen:")
        print(f"  📄 Archivos encontrados: {len(files)}")
        print(f"  ✅ Procesados ahora: {processed_count}")
        print(f"  ⏭️ Ya procesados: {skipped_count}")
        print(f"  ❌ Errores: {self.status_data['stats']['failed']}")
        print(f"  📁 Total en {self.output_path}: {len(list(self.output_path.glob('*.md')))}")
    
    def generate_report(self):
        """Genera tabla de estado de procesamiento."""
        print("\n📋 TABLA DE ESTADO DE PROCESAMIENTO")
        print("=" * 80)
        
        files = self.get_supported_files()
        
        # Datos para la tabla
        table_data = []
        
        for file_path in files:
            file_info = self.status_data["processed_files"].get(file_path.name, {})
            
            md_path = self.output_path / f"{file_path.stem}.md"
            md_exists = md_path.exists()
            
            row = {
                "Archivo": file_path.name,
                "Tamaño Original": f"{file_path.stat().st_size / 1024:.1f} KB",
                "Estado": file_info.get("status", "pendiente"),
                "Archivo MD": file_info.get("md_file", "N/A"),
                "MD Existe": "✅" if md_exists else "❌",
                "Procesado": file_info.get("processed_at", "N/A"),
                "Error": file_info.get("error", "")[:50] if file_info.get("error") else ""
            }
            
            table_data.append(row)
        
        # Crear DataFrame y mostrar
        if table_data:
            df = pd.DataFrame(table_data)
            print(df.to_string(index=False))
            
            # Guardar tabla como CSV
            report_path = "processing_report.csv"
            df.to_csv(report_path, index=False, encoding='utf-8')
            print(f"\n💾 Tabla guardada en: {report_path}")
        else:
            print("No hay archivos para mostrar")
        
        # Estadísticas
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"  Total archivos: {len(files)}")
        print(f"  Exitosos: {self.status_data['stats']['successful']}")
        print(f"  Fallidos: {self.status_data['stats']['failed']}")
        print(f"  Archivos MD: {len(list(self.output_path.glob('*.md')))}")
    
    def list_md_files(self):
        """Lista archivos Markdown generados."""
        md_files = list(self.output_path.glob('*.md'))
        
        print(f"\n📁 ARCHIVOS MARKDOWN EN {self.output_path}:")
        print("-" * 50)
        
        if md_files:
            for md_file in sorted(md_files):
                size = md_file.stat().st_size / 1024
                print(f"  📄 {md_file.name} ({size:.1f} KB)")
        else:
            print("  (No hay archivos Markdown)")


def main():
    """Función principal con menú interactivo."""
    processor = DoclingProcessor()
    
    while True:
        print("\n" + "="*60)
        print("🤖 DOCLING PROCESSOR - PUDDLE ASSISTANT")
        print("="*60)
        print("1. 📄 Procesar documentos nuevos")
        print("2. 🔄 Re-procesar todos (forzar)")
        print("3. 📋 Ver tabla de estado")
        print("4. 📁 Listar archivos Markdown")
        print("5. 📊 Ver estadísticas")
        print("6. 🚪 Salir")
        print()
        
        choice = input("Selecciona una opción (1-6): ").strip()
        
        if choice == "1":
            processor.process_all(force_reprocess=False)
            processor.generate_report()
            
        elif choice == "2":
            confirm = input("⚠️ ¿Re-procesar TODOS los archivos? (y/n): ").strip().lower()
            if confirm == 'y':
                processor.process_all(force_reprocess=True)
                processor.generate_report()
            
        elif choice == "3":
            processor.generate_report()
            
        elif choice == "4":
            processor.list_md_files()
            
        elif choice == "5":
            print(f"\n📊 ESTADÍSTICAS:")
            print(f"  Total procesados: {processor.status_data['stats']['total_processed']}")
            print(f"  Exitosos: {processor.status_data['stats']['successful']}")
            print(f"  Fallidos: {processor.status_data['stats']['failed']}")
            print(f"  Última actualización: {processor.status_data.get('last_update', 'N/A')}")
            
        elif choice == "6":
            print("👋 ¡Hasta luego!")
            break
            
        else:
            print("❌ Opción inválida")


if __name__ == "__main__":
    main()