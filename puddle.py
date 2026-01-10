#!/usr/bin/env python3
"""
Puddle Assistant - Script Principal
Herramienta unificada para gestión completa del sistema RAG
"""

import sys
import argparse
from pathlib import Path

# Agregar paths del proyecto
sys.path.append(str(Path(__file__).parent / "scripts"))
sys.path.append(str(Path(__file__).parent / "tools"))
sys.path.append(str(Path(__file__).parent / "config"))

def main():
    """Script principal con subcomandos."""
    parser = argparse.ArgumentParser(
        description="🤖 Puddle Assistant - Sistema RAG Inteligente",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s process                    # Procesar documentos nuevos
  %(prog)s process --single doc.pdf  # Procesar un documento específico
  %(prog)s status                     # Ver reporte de estado
  %(prog)s status --summary           # Solo resumen
  %(prog)s web                        # Ejecutar interfaz Streamlit
  %(prog)s setup                      # Configuración inicial
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # Subcomando: process (procesar documentos)
    process_parser = subparsers.add_parser('process', help='Procesar documentos')
    process_parser.add_argument('--single', help='Procesar un solo archivo')
    process_parser.add_argument('--force', action='store_true', help='Forzar reprocesamiento')
    process_parser.add_argument('--stats', action='store_true', help='Mostrar solo estadísticas')
    
    # Subcomando: status (reportes)
    status_parser = subparsers.add_parser('status', help='Generar reportes de estado')
    status_parser.add_argument('--summary', action='store_true', help='Solo resumen')
    status_parser.add_argument('--table', action='store_true', help='Solo tabla')
    status_parser.add_argument('--files', action='store_true', help='Listar archivos')
    status_parser.add_argument('--no-csv', action='store_true', help='No guardar CSV')
    
    # Subcomando: web (interfaz Streamlit)
    web_parser = subparsers.add_parser('web', help='Ejecutar interfaz web')
    web_parser.add_argument('--port', type=int, default=8501, help='Puerto (default: 8501)')
    web_parser.add_argument('--host', default='localhost', help='Host (default: localhost)')
    
    # Subcomando: setup (configuración inicial)
    setup_parser = subparsers.add_parser('setup', help='Configuración inicial del proyecto')
    setup_parser.add_argument('--check', action='store_true', help='Solo verificar configuración')
    
    # Subcomando: clean (limpieza)
    clean_parser = subparsers.add_parser('clean', help='Limpiar archivos temporales')
    clean_parser.add_argument('--logs', action='store_true', help='Limpiar logs antiguos')
    clean_parser.add_argument('--cache', action='store_true', help='Limpiar cache')
    clean_parser.add_argument('--all', action='store_true', help='Limpiar todo')
    
    args = parser.parse_args()
    
    # Mostrar ayuda si no se especifica comando
    if args.command is None:
        parser.print_help()
        return
    
    # Ejecutar comando correspondiente
    try:
        if args.command == 'process':
            run_process_command(args)
        elif args.command == 'status':
            run_status_command(args)
        elif args.command == 'web':
            run_web_command(args)
        elif args.command == 'setup':
            run_setup_command(args)
        elif args.command == 'clean':
            run_clean_command(args)
        else:
            print(f"❌ Comando desconocido: {args.command}")
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\n🛑 Operación cancelada por el usuario")
    except Exception as e:
        print(f"❌ Error ejecutando comando: {e}")
        sys.exit(1)

def run_process_command(args):
    """Ejecuta comandos de procesamiento."""
    from document_processor import DocumentProcessor
    
    processor = DocumentProcessor()
    
    if args.stats:
        stats = processor.get_stats()
        print("📊 Estadísticas de Procesamiento:")
        print(f"  Total archivos: {stats['total_files']}")
        print(f"  Procesados: {stats['processed_files']}")
        print(f"  Exitosos: {stats['success_count']}")
        print(f"  Fallidos: {stats['failed_count']}")
        print(f"  Última actualización: {stats['last_update']}")
        
    elif args.single:
        print(f"🔄 Procesando archivo: {args.single}")
        success = processor.process_single(args.single)
        if success:
            print(f"✅ Archivo procesado exitosamente")
        else:
            print(f"❌ Error procesando archivo")
            
    else:
        print("🚀 Iniciando procesamiento de documentos...")
        results = processor.process_all(force_reprocess=args.force)
        
        print(f"\n📊 Resultados:")
        print(f"  ✅ Procesados: {results['processed']}")
        print(f"  ⏭️ Ya procesados: {results['skipped']}")
        print(f"  ❌ Errores: {results['failed']}")
        print(f"  📄 Total archivos: {results['total_files']}")

def run_status_command(args):
    """Ejecuta comandos de reporte."""
    from status_reporter import StatusReporter
    
    reporter = StatusReporter()
    
    if args.summary:
        reporter.print_summary_report()
    elif args.table:
        reporter.generate_detailed_table(save_csv=not args.no_csv)
    elif args.files:
        reporter.list_output_files()
    else:
        # Reporte completo por defecto
        reporter.print_summary_report()
        reporter.generate_detailed_table(save_csv=not args.no_csv)
        reporter.list_output_files()

def run_web_command(args):
    """Ejecuta la interfaz web."""
    import subprocess
    import os
    
    print(f"🌐 Iniciando interfaz web en http://{args.host}:{args.port}")
    print("💡 Presiona Ctrl+C para detener el servidor")
    
    # Cambiar al directorio del proyecto
    os.chdir(Path(__file__).parent)
    
    cmd = [
        "streamlit", "run", "tools/main.py",
        "--server.port", str(args.port),
        "--server.address", args.host
    ]
    
    try:
        subprocess.run(cmd)
    except FileNotFoundError:
        print("❌ Streamlit no encontrado. Instala con: pip install streamlit")
    except KeyboardInterrupt:
        print("\n🛑 Servidor web detenido")

def run_setup_command(args):
    """Ejecuta configuración inicial."""
    import os
    from pathlib import Path
    
    print("🛠️ Configuración inicial de Puddle Assistant")
    print("=" * 50)
    
    # Verificar estructura de directorios
    dirs_to_check = [
        "data/raw/documents",
        "data/processed/DocsMD", 
        "logs",
        "config",
        "docs",
        "scripts",
        "tools"
    ]
    
    print("📁 Verificando estructura de directorios...")
    for dir_path in dirs_to_check:
        path = Path(dir_path)
        if path.exists():
            print(f"  ✅ {dir_path}")
        else:
            if not args.check:
                path.mkdir(parents=True, exist_ok=True)
                print(f"  ✨ Creado: {dir_path}")
            else:
                print(f"  ❌ Faltante: {dir_path}")
    
    # Verificar archivo .env
    env_file = Path(".env")
    print(f"\n🔑 Verificando configuración de API...")
    if env_file.exists():
        print("  ✅ Archivo .env encontrado")
        with open(env_file) as f:
            content = f.read()
            if "OPENROUTER_API_KEY" in content:
                print("  ✅ OPENROUTER_API_KEY configurado")
            else:
                print("  ⚠️ OPENROUTER_API_KEY no encontrado en .env")
    else:
        print("  ❌ Archivo .env no encontrado")
        if not args.check:
            with open(env_file, 'w') as f:
                f.write("OPENROUTER_API_KEY=tu_api_key_aqui\n")
            print("  ✨ Creado archivo .env de ejemplo")
    
    # Verificar dependencias
    print(f"\n📦 Verificando dependencias...")
    try:
        import docling
        print("  ✅ Docling instalado")
    except ImportError:
        print("  ❌ Docling no instalado")
    
    try:
        import streamlit
        print("  ✅ Streamlit instalado") 
    except ImportError:
        print("  ❌ Streamlit no instalado")
    
    try:
        import langchain
        print("  ✅ LangChain instalado")
    except ImportError:
        print("  ❌ LangChain no instalado")
    
    # Verificar documentos
    docs_path = Path("data/raw/documents")
    if docs_path.exists():
        doc_files = list(docs_path.glob("*.[pP][dD][fF]")) + list(docs_path.glob("*.[dD][oO][cC][xX]"))
        print(f"\n📄 Documentos encontrados: {len(doc_files)}")
        for doc in doc_files[:5]:  # Mostrar primeros 5
            print(f"  📄 {doc.name}")
        if len(doc_files) > 5:
            print(f"  ... y {len(doc_files) - 5} más")
    
    if not args.check:
        print(f"\n✅ Configuración inicial completada")
        print(f"\n🚀 Próximos pasos:")
        print(f"  1. Edita .env con tu API key de OpenRouter")
        print(f"  2. Coloca documentos en data/raw/documents/")
        print(f"  3. Ejecuta: python3 puddle.py process")
        print(f"  4. Inicia la interfaz: python3 puddle.py web")

def run_clean_command(args):
    """Ejecuta comandos de limpieza."""
    import shutil
    import glob
    from datetime import datetime, timedelta
    
    print("🧹 Limpiando archivos temporales...")
    
    cleaned = []
    
    if args.cache or args.all:
        # Limpiar cache de Python
        cache_dirs = glob.glob("**/__pycache__", recursive=True)
        for cache_dir in cache_dirs:
            shutil.rmtree(cache_dir)
            cleaned.append(f"Cache Python: {cache_dir}")
        
        # Limpiar archivos .pyc
        pyc_files = glob.glob("**/*.pyc", recursive=True)
        for pyc_file in pyc_files:
            Path(pyc_file).unlink()
            cleaned.append(f"Archivo .pyc: {pyc_file}")
    
    if args.logs or args.all:
        # Limpiar logs antiguos (más de 30 días)
        log_path = Path("logs")
        if log_path.exists():
            cutoff_date = datetime.now() - timedelta(days=30)
            for log_file in log_path.glob("*.log"):
                if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_date:
                    log_file.unlink()
                    cleaned.append(f"Log antiguo: {log_file.name}")
    
    if cleaned:
        print("🗑️ Archivos limpiados:")
        for item in cleaned:
            print(f"  ✅ {item}")
    else:
        print("✨ No hay archivos que limpiar")

if __name__ == "__main__":
    print("🤖 Puddle Assistant v1.0")
    print("Sistema RAG Inteligente para Consulta de Documentos")
    print("-" * 50)
    main()