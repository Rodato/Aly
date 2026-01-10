#!/usr/bin/env python3
"""
RAG Console - Puddle Assistant
Sistema RAG interactivo para uso en consola
"""

from simple_rag_mongo import SimpleMongoRAG

def main():
    """Consola interactiva RAG."""
    try:
        print("🚀 Inicializando RAG MongoDB...")
        rag = SimpleMongoRAG()
        
        # Mostrar estadísticas
        stats = rag.get_stats()
        print(f"✅ Conectado: {stats.get('total_chunks', 0)} chunks, {stats.get('documents', 0)} documentos")
        
        if stats.get('documents_detail'):
            print("\n📋 Documentos disponibles:")
            for doc in stats['documents_detail'][:5]:  # Mostrar solo primeros 5
                print(f"  📄 {doc['_id']}: {doc['count']} chunks")
        
        print("\n" + "="*70)
        print("🤖 RAG PUDDLE ASSISTANT - MVP ALY")
        print("🌍 Detección automática de idioma: Español | English | Português")
        print("💡 El idioma se detecta con tu PRIMER mensaje y se mantiene toda la sesión")
        print("Pregunta sobre educación de género y desarrollo infantil")
        print("Ejemplos: '¿Cómo involucrar a los niños?' | 'How to engage children?' | 'Como envolver crianças?'")
        print("Escribe 'salir' para terminar")
        print("="*70)
        
        first_message = True
        while True:
            try:
                query = input("\n🔍 Tu pregunta: ").strip()
                
                if query.lower() in ['salir', 'exit', 'quit', '']:
                    print("\n👋 ¡Hasta luego!")
                    break
                
                print("\n⏳ Buscando información relevante...")
                result = rag.ask(query, top_k=3, is_first_message=first_message)
                
                # Mostrar información de idioma si es primer mensaje
                if first_message and 'session_info' in result:
                    session = result['session_info']
                    lang_flag = '🇪🇸' if session['language'] == 'es' else '🇺🇸' if session['language'] == 'en' else '🇧🇷'
                    print(f"\n🌍 Idioma detectado para toda la sesión: {lang_flag} {session['config']['name']}")
                    if session.get('greeting'):
                        print(f"👋 {session['greeting']}")
                    print("-" * 50)
                    first_message = False
                elif 'language_detected' in result:
                    # Mostrar idioma actual (ya fijado)
                    lang_flag = '🇪🇸' if result['language_detected'] == 'es' else '🇺🇸' if result['language_detected'] == 'en' else '🇧🇷'
                    lang_name = result.get('language_name', result['language_detected'])
                    print(f"\n🌍 Idioma de sesión: {lang_flag} {lang_name}")
                
                # Mostrar respuesta (formato conversacional natural)
                print(f"\n{result['answer']}")
                
                # TODO: Descomentar si se necesitan fuentes en el futuro
                # if result['sources']:
                #     print(f"\n📚 **Fuentes consultadas:**")
                #     for i, source in enumerate(result['sources'], 1):
                #         print(f"  {i}. **{source['document']}**")
                #         print(f"     📝 Sección: {source['section']}")
                #         print(f"     🎯 Similitud: {source['similarity']}")
                
                print("\n" + "-"*50)
                
            except KeyboardInterrupt:
                print("\n\n👋 ¡Hasta luego!")
                break
            except EOFError:
                print("\n\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                print(f"❌ Error procesando pregunta: {e}")
                continue
                
    except Exception as e:
        print(f"❌ Error inicializando RAG: {e}")
        print("Verifica que MongoDB esté configurado correctamente en .env")

if __name__ == "__main__":
    main()