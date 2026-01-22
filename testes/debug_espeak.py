import os
import ctypes
from pathlib import Path

print("🔍 DEBUG ESPEAK-NG (Windows)")
print("-" * 30)

# Caminhos padrão do instalador MSI
caminhos = [
    r"C:\Program Files\eSpeak NG",
    r"C:\Program Files (x86)\eSpeak NG"
]

encontrado = None

for p in caminhos:
    path_obj = Path(p)
    dll_path = path_obj / "libespeak-ng.dll"
    exe_path = path_obj / "espeak-ng.exe"
    
    if dll_path.exists():
        print(f"✅ DLL encontrada em: {dll_path}")
        encontrado = path_obj
        break
    else:
        print(f"❌ Não encontrado em: {p}")

if encontrado:
    print(f"\n📂 Diretório Base: {encontrado}")
    
    # Tenta carregar a DLL para ver se o Windows aceita
    try:
        ctypes.cdll.LoadLibrary(str(encontrado / "libespeak-ng.dll"))
        print("✅ DLL carregada com sucesso pelo Windows!")
    except Exception as e:
        print(f"❌ Erro ao carregar DLL (Pode ser erro de arquitetura x86/x64): {e}")

    # Configuração sugerida
    print("\n--- COPIE ISTO PARA O SEU VOCAL_CORE.PY ---")
    print(f'os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = r"{encontrado / "libespeak-ng.dll"}"')
    print(f'os.environ["PHONEMIZER_ESPEAK_PATH"] = r"{encontrado}"')
else:
    print("\n⚠️ ESPEAK NÃO ENCONTRADO!")
    print("Por favor, reinstale o eSpeak-ng usando o instalador MSI.")