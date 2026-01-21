from vocal_core import VocalCore
import time

print("\n--- INICIANDO TESTE DE VOZ ---")
vc = VocalCore()

texto = "Olá Argus. Testando o sistema de fonetização no Windows."
print(f"Enviando texto: {texto}")

# Tenta gerar
vc._generate_and_queue(texto, "pm_alex")

# Dá tempo para tocar
time.sleep(5)
print("--- TESTE FINALIZADO ---")