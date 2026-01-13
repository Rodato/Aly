#!/usr/bin/env python3
"""
Welcome Messages - Multi-language
Mensajes de bienvenida automáticos según idioma detectado
"""

WELCOME_MESSAGES = {
    'en': """Hello!
Welcome, I'm Aly! 🤖💬

I'm here to assist you with implementing or learning about Equimundo's programs. Feel free to ask me anything related to these topics! 🌟

To get started, simply type your question below.

If you don't want to chat any more, type /exit. Let's make facilitating and implementing programs a joyful journey together! 🚀👨‍👩‍👧‍👦""",

    'es': """¡Hola!
¡Bienvenido/a, soy Aly! 🤖💬

Estoy aquí para ayudarte a implementar o aprender sobre los programas de Equimundo. ¡No dudes en preguntarme cualquier cosa relacionada con estos temas! 🌟

Para comenzar, simplemente escribe tu pregunta a continuación.

Si no quieres conversar más, escribe /salir. ¡Hagamos de la facilitación e implementación de programas un viaje alegre juntos! 🚀👨‍👩‍👧‍👦""",

    'pt': """Olá!
Bem-vindo/a, sou Aly! 🤖💬

Estou aqui para ajudá-lo a implementar ou aprender sobre os programas da Equimundo. Sinta-se à vontade para me perguntar qualquer coisa relacionada a esses tópicos! 🌟

Para começar, basta digitar sua pergunta abaixo.

Se você não quiser conversar mais, digite /sair. Vamos fazer da facilitação e implementação de programas uma jornada alegre juntos! 🚀👨‍👩‍👧‍👦"""
}

def get_welcome_message(language_code: str) -> str:
    """
    Obtiene el mensaje de bienvenida según el idioma detectado.

    Args:
        language_code: Código de idioma ('en', 'es', 'pt')

    Returns:
        Mensaje de bienvenida en el idioma correspondiente
    """
    return WELCOME_MESSAGES.get(language_code, WELCOME_MESSAGES['en'])
