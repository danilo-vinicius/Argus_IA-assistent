import webbrowser
import os
import time
import platform

# --- CONFIGURAÇÃO DAS URLS ---
URLS = {
    "notion": "https://www.notion.so",
    "gemini": "https://gemini.google.com",
    "notebooklm": "https://notebooklm.google.com",
    "brasfort_email": "https://outlook.office.com/mail/" # Ou outlook web se preferir
}

# --- FUNÇÕES DE ROTINA ---

def abrir_navegador(urls):
    """Abre uma lista de sites no navegador padrão"""
    # Registra o Chrome se necessário (Windows geralmente acha o padrão sozinho)
    for url in urls:
        webbrowser.open(url)
        time.sleep(0.5) # Pausa rápida para não travar o browser

def abrir_app_windows(nome_executavel):
    """Tenta abrir um app do Windows pelo comando executar"""
    try:
        os.startfile(nome_executavel)
        return True
    except Exception as e:
        print(f"Erro ao abrir {nome_executavel}: {e}")
        return False

def executar_rotina_matinal():
    """
    Executa a sequência:
    1. Outlook
    2. Ferramentas de IA (Gemini, NotebookLM)
    3. Gestão (Notion)
    """
    relatorio = []
    
    # 1. Tenta abrir Outlook Desktop
    # Se você usa o Outlook web, comente a linha abaixo e adicione na lista de URLs
    if abrir_app_windows("outlook"):
        relatorio.append("Outlook (Desktop)")
    else:
        # Fallback para Web se não tiver o app instalado/configurado no PATH
        webbrowser.open(URLS["brasfort_email"])
        relatorio.append("Outlook (Web)")

    # 2. Abre as ferramentas Web
    ferramentas = [URLS["gemini"], URLS["notebooklm"], URLS["notion"]]
    abrir_navegador(ferramentas)
    relatorio.append("Gemini, NotebookLM & Notion")
    
    return f"Rotina executada. Apps iniciados: {', '.join(relatorio)}."

def executar_modo_foco():
    """Exemplo: Fecha distrações e abre música (Futuro)"""
    # Aqui poderíamos usar scripts para fechar abas, mas vamos começar simples
    return "Modo foco ainda em construção."