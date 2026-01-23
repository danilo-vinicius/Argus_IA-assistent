import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# 📋 ROSTER DE MODELOS GRATUITOS (OPENROUTER)
# ==============================================================================
# Ordem de prioridade: Tenta o primeiro, se falhar, tenta o próximo.
# Todos abaixo possuem tier "free" no OpenRouter.

MODEL_ROSTER = [
    # 1. Gemini 1.5 Flash 8B (Versão leve, cota separada da versão Pro/Exp)
    "nvidia/nemotron-3-nano-30b-a3b:free", 
    
    # 2. Mistral Nemo (Muito estável e rápido)
    "liquid/lfm-2.5-1.2b-thinking:free",
    
    # 3. Qwen 2.5 7B (Modelo chinês excelente para código e lógica)
    "qwen/qwen-2.5-7b-instruct:free",
    
    # 4. Microsoft Phi-3 (Modelo pequeno da Microsoft, quase sempre livre)
    "microsoft/phi-3-medium-128k-instruct:free",
    
    # 5. Liquid LFM (Modelo novo, pouca gente usa, então está livre)
    "liquid/lfm-40b:free"
]

# Modelos que ACEITAM IMAGEM (Vision Capable)
# Se o usuário mandar print, só podemos usar estes.
VISION_MODELS = [
    "google/gemini-2.0-flash-lite-preview-02-05:free",
    "google/gemini-2.0-flash-exp:free"
]

def get_fallback_model(callbacks=None, temperature=0.7):
    """
    Retorna uma função executora que gerencia a conexão com o OpenRouter
    e faz o fallback automático entre modelos em caso de erro.
    """
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ ERRO: OPENROUTER_API_KEY não encontrada no .env")
        return None

    def generate_response(prompt_input, image_data=None):
        """
        Executa a geração de texto ou análise de imagem.
        """
        
        # 1. Monta a mensagem
        message_content = [{"type": "text", "text": prompt_input}]
        
        # Se tiver imagem, adiciona ao payload
        if image_data:
            message_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_data}"}
            })
            # Filtra apenas modelos que enxergam
            current_roster = [m for m in MODEL_ROSTER if m in VISION_MODELS]
            print("👁️ Modo Visão Ativado: Filtrando modelos multimodais...")
        else:
            # Texto puro: usa todos
            current_roster = MODEL_ROSTER

        # 2. Loop de Tentativas (Fallback)
        last_error = None
        
        for model_name in current_roster:
            try:
                print(f"🔄 Conectando OpenRouter: {model_name}...")
                
                llm = ChatOpenAI(
                    model=model_name,
                    openai_api_key=api_key,
                    openai_api_base="https://openrouter.ai/api/v1",
                    temperature=temperature,
                    streaming=True,
                    callbacks=callbacks,
                    # Headers exigidos pelo OpenRouter para ranking
                    default_headers={
                        "HTTP-Referer": os.getenv("YOUR_SITE_URL", "http://localhost:5000"),
                        "X-Title": os.getenv("YOUR_APP_NAME", "Argus Local")
                    }
                )
                
                messages = [HumanMessage(content=message_content)]
                response = llm.invoke(messages)
                
                print(f"✅ Sucesso com: {model_name}")
                return response

            except Exception as e:
                error_msg = str(e)
                print(f"⚠️ Falha no {model_name}: {error_msg}")
                last_error = error_msg
                # Continua para o próximo modelo da lista
                continue
        
        # Se saiu do loop, tudo falhou
        return f"Desculpe, chefe. Todos os satélites de IA estão fora do ar. Erro final: {last_error}"

    return generate_response