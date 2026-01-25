import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# --- LISTA DE PRIORIDADE (ROSTER) ---
# Copiado da sua lista de disponíveis. 
# O sistema tentará um por um até conseguir.
MODEL_ROSTER = [
    "models/gemini-2.5-flash",                  # 1. O mais novo e rápido
    "models/gemini-2.0-flash",                  # 2. Estável anterior
    "models/gemini-2.0-flash-lite-preview-02-05", # 3. Versão leve (cota separada)
    "models/gemini-flash-lite-latest",          # 4. Outra versão leve
    "models/gemini-2.0-flash-exp",              # 5. Experimental (às vezes instável, mas bom)
    "models/gemini-pro-latest"                  # 6. Último recurso (Lento mas funciona)
]

def get_fallback_model(callbacks=[]):
    """
    Gerenciador de Modelos com Sistema de Cascata.
    Tenta invocar os modelos da lista em ordem. Se um falhar (Cota/404), tenta o próximo.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("❌ ERRO CRÍTICO: 'GOOGLE_API_KEY' não encontrada no .env")
        return None

    # Função Wrapper que será chamada pelo app.py
    def gemini_wrapper(prompt, image_data=None):
        last_error = None
        
        # --- LOOP DE TENTATIVAS (CASCATA) ---
        for model_name in MODEL_ROSTER:
            try:
                # print(f"🔄 Tentando conectar no modelo: {model_name}...")
                
                # 1. Configura o modelo da vez
                llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=api_key,
                    temperature=0.7,
                    streaming=True, # Essencial para voz/chat fluir
                    callbacks=callbacks,
                    convert_system_message_to_human=True
                )
                
                # 2. Prepara a mensagem (Texto ou Multimodal)
                if image_data:
                    print(f"📸 Enviando imagem para {model_name}...")
                    message = HumanMessage(
                        content=[
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                            }
                        ]
                    )
                    # Tenta invocar (Aqui é onde o erro acontece se falhar)
                    return llm.invoke([message])
                
                else:
                    # Modo Texto Normal
                    return llm.invoke(prompt)

            except Exception as e:
                # Se deu erro (404, 429, etc), captura e tenta o próximo
                error_str = str(e)
                print(f"⚠️ Falha no {model_name}: {error_str.split(':')[0]}") # Printa só o resumo do erro
                last_error = error_str
                continue # Pula para o próximo modelo da lista
        
        # --- FIM DO LOOP (SE TODOS FALHAREM) ---
        print("❌ TODOS OS MODELOS FALHARAM.")
        
        class FakeResponse:
            content = f"Desculpe, chefe. Todos os sistemas neurais estão fora do ar. Erro final: {last_error}"
        return FakeResponse()

    # Retorna a função wrapper pronta para uso
    return gemini_wrapper