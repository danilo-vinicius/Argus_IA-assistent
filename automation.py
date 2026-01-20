import os
import ctypes
import AppOpener
import datetime

# Função nova que faltava!
def bloquear_windows():
    """Bloqueia a estação de trabalho do Windows imediatamente."""
    print("🔒 Executando Bloqueio de Segurança...")
    ctypes.windll.user32.LockWorkStation()
    return "Estação de Trabalho Bloqueada."

def abrir_app_windows(nome_app):
    """Abre um aplicativo usando o AppOpener"""
    print(f"📂 Tentando abrir: {nome_app}")
    try:
        # Tenta abrir (match_closest=True ajuda a achar 'chrome' se digitar 'google')
        AppOpener.open(nome_app, match_closest=True)
        return f"Aplicativo '{nome_app}' iniciado."
    except Exception as e:
        return f"Falha ao abrir {nome_app}: {str(e)}"

def executar_rotina_matinal():
    """Abre o kit básico de trabalho"""
    print("☕ Iniciando Rotina Matinal...")
    
    apps_para_abrir = ["outlook", "teams", "chrome"]
    resultados = []
    
    for app in apps_para_abrir:
        res = abrir_app_windows(app)
        resultados.append(res)
        
    return " | ".join(resultados)