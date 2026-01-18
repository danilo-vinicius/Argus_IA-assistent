import os
from langchain_google_genai import ChatGoogleGenerativeAI
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable

# --- LISTA DE PRIORIDADE (ROSTER) ---
# Ordenado do Melhor/Mais Rápido -> Para o Backup/Antigo
# Baseado na sua lista de modelos disponíveis
MODEL_ROSTER = [
    "gemini-2.5-flash",          # Principal (Mais inteligente e rápido)
    "gemini-2.5-flash-lite",     # Backup Imediato (Mesma arquitetura, mais leve)
    "gemini-2.0-flash",          # Versão anterior (Muito estável)
    "gemini-2.0-flash-lite",     # Backup da versão anterior
    "gemma-3-27b-it"             # Modelo Open Source (Costuma ter cota separada)
]

# Modelos específicos para tarefas simples (Economia de cota)
ADMIN_MODEL = "gemini-2.5-flash-lite" 

def get_fallback_model(callbacks, temperature=0.3):
    """
    Retorna uma função que, quando chamada, tenta invocar os modelos em sequência
    até um funcionar.
    """
    
    def invoker(messages):
        erros_log = []
        
        for model_name in MODEL_ROSTER:
            try:
                print(f"🔄 Tentando conectar no modelo: {model_name}...")
                
                llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    temperature=temperature,
                    streaming=True,
                    callbacks=callbacks,
                    google_api_key=os.getenv("GOOGLE_API_KEY")
                )
                
                # Tenta gerar a resposta
                result = llm.invoke(messages)
                
                # Se chegou aqui, funcionou!
                print(f"✅ Sucesso com: {model_name}")
                return result
                
            except ResourceExhausted:
                print(f"⚠️ Cota estourada no {model_name} (429). Tentando próximo...")
                erros_log.append(f"{model_name}: 429")
                continue # Pula para o próximo loop
            except Exception as e:
                print(f"❌ Erro genérico no {model_name}: {e}")
                erros_log.append(f"{model_name}: {str(e)}")
                continue
        
        # Se saiu do loop, nenhum funcionou
        raise Exception(f"Todos os modelos falharam. Logs: {', '.join(erros_log)}")

    return invoker