import json
import os
import sys

# Cérebro de Emergência (Caso o JSON quebre)
DEFAULT_BRAIN = {
    "default": {
        "name": "Argus (Safe Mode)",
        "color": "#ff0000",
        "voice": "pm_alex",
        "instruction": "Ocorreu um erro ao ler o arquivo de personalidades. Verifique a sintaxe do JSON."
    }
}

def load_personas():
    # --- CORREÇÃO DE CAMINHO ---
    # Pega o diretório onde ESTE arquivo (personas.py) está: .../brain/
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Junta com o nome do arquivo JSON
    file_path = os.path.join(base_dir, 'personas.json')
    
    # Debug (opcional, pra você ver onde ele tá buscando)
    print(f"🔍 Buscando personas em: {file_path}")

    # 1. Verifica se arquivo existe
    if not os.path.exists(file_path):
        print("⚠️ [AVISO] 'personas.json' não encontrado. Usando modo de segurança.")
        return DEFAULT_BRAIN

    try:
        # 2. Tenta ler com UTF-8
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # 3. Validação básica (Se estiver vazio)
            if not data:
                print("⚠️ [AVISO] O JSON está vazio.")
                return DEFAULT_BRAIN
                
            # SE TUDO DEU CERTO, RETORNA OS DADOS:
            return data

    except json.JSONDecodeError as e:
        # Aqui pegamos o erro de vírgula/aspas do seu amigo
        print("\n" + "="*60)
        print("❌ ERRO CRÍTICO NO ARQUIVO 'personas.json'")
        print(f"   O Argus não conseguiu ler suas configurações.")
        print(f"   Erro de Sintaxe na linha {e.lineno}: {e.msg}")
        print("   -> Dica: Verifique vírgulas faltando ou sobrando.")
        print("="*60 + "\n")
        return DEFAULT_BRAIN
        
    except Exception as e:
        print(f"❌ Erro genérico ao carregar personas: {e}")
        return DEFAULT_BRAIN

# Carrega na inicialização (Isso vai pra RAM e fica lá)
BRAINS = load_personas()

def get_active_brain():
    # Retorna o primeiro cérebro disponível
    keys = list(BRAINS.keys())
    if keys:
        return BRAINS[keys[0]]
    return BRAINS.get("default") # Fallback final