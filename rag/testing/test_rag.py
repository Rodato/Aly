#!/usr/bin/env python3
"""
Test RAG MongoDB - Prueba simple del sistema RAG
"""

from simple_rag_mongo import SimpleMongoRAG

def test_rag():
    """Prueba el sistema RAG con preguntas específicas."""
    
    try:
        rag = SimpleMongoRAG()
        
        # Mostrar estadísticas
        stats = rag.get_stats()
        print("📊 Base de datos MongoDB:")
        print(f"  📝 Total chunks: {stats.get('total_chunks', 0)}")
        print(f"  📄 Documentos: {stats.get('documents', 0)}")
        
        # Preguntas de prueba
        test_questions = [
            "¿Qué estrategias se recomiendan para involucrar a los niños en la educación?",
            "¿Cómo pueden los padres apoyar la educación de sus hijos?",
            "¿Qué actividades se sugieren para el club de niños?",
            "¿Cuáles son las barreras que enfrentan los niños en la educación?"
        ]
        
        print("\n" + "="*70)
        print("🧪 PRUEBAS DEL SISTEMA RAG")
        print("="*70)
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n🔍 PREGUNTA {i}: {question}")
            print("-" * 60)
            
            result = rag.ask(question, top_k=3)
            
            print("🤖 RESPUESTA:")
            print(result['answer'])
            
            if result['sources']:
                print(f"\n📚 FUENTES CONSULTADAS:")
                for j, source in enumerate(result['sources'], 1):
                    print(f"  {j}. {source['document']}")
                    print(f"     Sección: {source['section']}")
                    print(f"     Similitud: {source['similarity']}")
            
            print("\n" + "="*70)
        
        print("\n✅ Pruebas completadas exitosamente!")
        
    except Exception as e:
        print(f"❌ Error en las pruebas: {e}")

if __name__ == "__main__":
    test_rag()