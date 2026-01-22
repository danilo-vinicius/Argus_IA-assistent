from vocal_core import VocalCore
import time

print("Iniciando teste de voz...")
vocal = VocalCore()

# Simula um stream de texto
texto = "Olá Danilo. O sistema de voz Kokoro está operacional. Testando voz masculina."
for palavra in texto.split():
    vocal.speak_stream([palavra + " "], brain_name="The Architect")
    time.sleep(0.1)

print("Teste finalizado.")