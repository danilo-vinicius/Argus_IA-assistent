import os
import shutil
from pathlib import Path
import datetime

# --- CONFIGURAÇÃO DE DIRETÓRIOS ---
# Pega a pasta do usuário dinamicamente (C:\Users\Danilo)
USER_HOME = str(Path.home())
DOWNLOADS_DIR = os.path.join(USER_HOME, "Downloads")
DOCUMENTS_DIR = os.path.join(USER_HOME, "Documents")
PICTURES_DIR = os.path.join(USER_HOME, "Pictures")

# --- REGRAS DE ORGANIZAÇÃO (O "Cérebro" do Organizador) ---
FILE_MAPPING = {
    "Argus_Docs": [".pdf", ".docx", ".txt", ".md", ".pptx"],
    "Argus_Data": [".csv", ".xlsx", ".json", ".sql", ".parquet"],
    "Argus_Images": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    "Argus_Installers": [".exe", ".msi", ".zip", ".rar"],
    "Argus_Code": [".py", ".js", ".html", ".css", ".ipynb"]
}

def organizar_downloads():
    """
    Varre a pasta Downloads e move arquivos para pastas categorizadas
    dentro de Documentos e Imagens.
    """
    log_movimentos = []
    
    if not os.path.exists(DOWNLOADS_DIR):
        return "Erro: Pasta Downloads não encontrada."

    arquivos = [f for f in os.listdir(DOWNLOADS_DIR) if os.path.isfile(os.path.join(DOWNLOADS_DIR, f))]
    
    if not arquivos:
        return "A pasta Downloads já está limpa, Sr. Danilo."

    for arquivo in arquivos:
        nome, extensao = os.path.splitext(arquivo)
        extensao = extensao.lower()
        
        # Ignora arquivos temporários
        if extensao in [".tmp", ".crdownload", ".ini"]:
            continue

        destino_final = None

        # 1. Decide para onde vai
        for pasta, extensoes in FILE_MAPPING.items():
            if extensao in extensoes:
                # Se for Imagem, vai para Pictures, se não, Documents
                base_path = PICTURES_DIR if pasta == "Argus_Images" else DOCUMENTS_DIR
                destino_final = os.path.join(base_path, pasta)
                break
        
        # Se não achou categoria, joga em "Argus_Outros"
        if not destino_final:
            destino_final = os.path.join(DOCUMENTS_DIR, "Argus_Outros")

        # 2. Cria a pasta se não existir
        if not os.path.exists(destino_final):
            os.makedirs(destino_final)

        # 3. Move o arquivo
        try:
            origem = os.path.join(DOWNLOADS_DIR, arquivo)
            destino = os.path.join(destino_final, arquivo)
            
            # Se já existe um arquivo com esse nome, renomeia com timestamp
            if os.path.exists(destino):
                timestamp = datetime.datetime.now().strftime("%H%M%S")
                destino = os.path.join(destino_final, f"{nome}_{timestamp}{extensao}")

            shutil.move(origem, destino)
            log_movimentos.append(f"Moved: {arquivo} -> {os.path.basename(destino_final)}")
        except Exception as e:
            log_movimentos.append(f"Erro em {arquivo}: {str(e)}")

    qtd = len(log_movimentos)
    if qtd == 0:
        return "Nenhum arquivo elegível para organização."
        
    return f"Limpeza concluída. {qtd} arquivos organizados em pastas 'Argus'."