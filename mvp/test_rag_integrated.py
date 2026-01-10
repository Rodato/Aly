#!/usr/bin/env python3
"""
Test RAG Integrado con Detección de Idioma
Prueba específica del MVP Aly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'mongodb', 'scripts'))

from simple_rag_mongo import SimpleMongoRAG

def test_multilingual_rag():
    """Prueba el RAG con diferentes idiomas."""
    
    print("🧪 PRUEBA RAG MULTILINGÜE - MVP ALY")
    print("=" * 60)
    
    try:
        rag = SimpleMongoRAG()
        print("✅ RAG inicializado correctamente")
    except Exception as e:
        print(f"❌ Error inicializando RAG: {e}")
        return
    
    # Casos de prueba multilingües
    test_cases = [
        {
            'query': '¿Cómo involucrar a los niños en actividades de género?',
            'expected_lang': 'es',
            'description': 'Pregunta en español'
        },
        {
            'query': 'How can I engage children in gender activities?',
            'expected_lang': 'en', 
            'description': 'Pregunta en inglés'
        },
        {
            'query': 'Como posso envolver crianças em atividades de gênero?',
            'expected_lang': 'pt',
            'description': 'Pregunta en portugués'
        },
        {
            'query': 'What metodologías do you recommend?',
            'expected_lang': 'en',  # Mixto, debería detectar inglés como dominante
            'description': 'Pregunta mixta (inglés-español)'
        }
    ]
    
    print(f"\n🔬 Ejecutando {len(test_cases)} pruebas...")
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n" + "="*50)
        print(f"📝 PRUEBA {i}: {test['description']}")
        print(f"❓ Pregunta: '{test['query']}'")
        print(f"🎯 Idioma esperado: {test['expected_lang']}")
        
        try:
            # Ejecutar consulta
            result = rag.ask(test['query'], top_k=2)
            
            # Mostrar resultados
            detected_lang = result.get('language_detected', 'unknown')
            lang_name = result.get('language_name', 'Unknown')
            
            # Bandera según idioma
            flag = '🇪🇸' if detected_lang == 'es' else '🇺🇸' if detected_lang == 'en' else '🇧🇷' if detected_lang == 'pt' else '❓'
            
            print(f"🌍 Idioma detectado: {flag} {lang_name} ({detected_lang})")
            
            # Verificar si es correcto
            if detected_lang == test['expected_lang']:
                print("✅ DETECCIÓN CORRECTA")
            else:
                print(f"❌ DETECCIÓN INCORRECTA (esperado: {test['expected_lang']})")
            
            print(f"\n🤖 Respuesta (primeras 150 chars):")
            print(f"   {result['answer'][:150]}...")
            
            if result['sources']:
                print(f"\n📚 Fuentes ({len(result['sources'])}):")
                for j, source in enumerate(result['sources'][:2], 1):
                    print(f"   {j}. {source['document'][:40]}... (sim: {source['similarity']})")
            
        except Exception as e:
            print(f"❌ Error en prueba: {e}")
    
    print(f"\n" + "="*60)
    print("🎉 PRUEBAS COMPLETADAS")
    print("\n💡 El MVP Aly ahora detecta automáticamente el idioma y responde en:")
    print("   🇪🇸 Español")
    print("   🇺🇸 English") 
    print("   🇧🇷 Português")

if __name__ == "__main__":
    test_multilingual_rag()