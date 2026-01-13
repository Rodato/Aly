#!/usr/bin/env python3
"""
Test script para verificar detección de GREETING
"""

from agent_orchestrator import AgentOrchestrator

def test_greeting():
    """Prueba rápida de detección de saludo."""
    print("🧪 PROBANDO DETECCIÓN DE SALUDOS")
    print("=" * 60)

    orchestrator = AgentOrchestrator()

    test_greetings = [
        "Hola",
        "Hola!",
        "HOla!",
        "Hello",
        "Hi!",
        "Olá",
        "Buenos días"
    ]

    for greeting in test_greetings:
        print(f"\n📝 Testing: '{greeting}'")
        result = orchestrator.process_query(greeting, debug=True)

        print(f"   🌍 Idioma: {result['language_name']} ({result['language']})")
        print(f"   🎯 Intent: {result['intent']} (confianza: {result['intent_confidence']:.2f})")
        print(f"   🤖 Agente: {result['agent_type']}")
        print(f"   💬 Respuesta preview: {result['answer'][:100]}...")

        # Verificar que se detectó como GREETING
        if result['intent'] == 'GREETING':
            print(f"   ✅ GREETING detectado correctamente")
        else:
            print(f"   ❌ ERROR: Se esperaba GREETING, pero fue {result['intent']}")

    print("\n" + "=" * 60)
    print("✅ Test completado")

if __name__ == "__main__":
    test_greeting()
