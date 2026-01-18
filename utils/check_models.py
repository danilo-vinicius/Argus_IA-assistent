import google.generativeai as genai
import os

# Configure com sua NOVA chave (após revogar a antiga)
GOOGLE_API_KEY = "AIzaSyBy7CMG6pa-DdNzxmAe6nlaslcY2BjOS5s"
genai.configure(api_key=GOOGLE_API_KEY)

print("Listando modelos disponíveis...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Erro ao listar modelos: {e}")