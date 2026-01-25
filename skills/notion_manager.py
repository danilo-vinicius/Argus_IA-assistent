import os
import notion_client
from notion_client import Client
from datetime import datetime

# (Removi o print de versão que estava dando erro)

class NotionManager:
    def __init__(self):
        # --- CARREGA CREDENCIAIS ---
        self.work_key = os.getenv("NOTION_WORK_KEY")
        self.work_db = os.getenv("NOTION_WORK_DB_ID")
        
        self.play_key = os.getenv("NOTION_PLAY_KEY")
        self.play_db = os.getenv("NOTION_ARGUS_DB_ID")

        # --- INICIALIZA OS DOIS CLIENTES ---
        # 1. Leitor Oficial (Work)
        if self.work_key:
            self.client_work = Client(auth=self.work_key)
            print("💼 [NOTION] Cliente de Trabalho: ONLINE")
        else:
            self.client_work = None
            print("⚠️ [NOTION] Chave de Trabalho não encontrada.")

        # 2. Escritor Criativo (Playground)
        if self.play_key:
            self.client_play = Client(auth=self.play_key)
            print("🧪 [NOTION] Cliente Playground: ONLINE")
        else:
            self.client_play = None
            print("⚠️ [NOTION] Chave Playground não encontrada.")

    # ==========================================================
    # 🔍 LEITURA (GET) - BANCO OFICIAL
    # ==========================================================
    def get_pending_tasks(self):
        """Lê tarefas pendentes no banco do trabalho."""
        if not self.client_work: return []
        
        print(f"📡 Lendo tarefas do banco: {self.work_db}...")
        
        try:
            response = self.client_work.databases.query(
                database_id=self.work_db,
                filter={
                    "property": "Status",
                    "status": {
                        "equals": "Não iniciado"
                    }
                }
            )
            
            tasks = []
            for page in response["results"]:
                props = page["properties"]
                
                # 1. Pega o Título
                title = "Sem Título"
                if "Nome do projeto" in props and props["Nome do projeto"]["title"]:
                    title = props["Nome do projeto"]["title"][0]["text"]["content"]
                
                # 2. Pega o Status
                status_name = "N/A"
                if "Status" in props and props["Status"]["status"]:
                    status_name = props["Status"]["status"]["name"]

                # 3. Pega a Prioridade
                prio = "Normal"
                if "Prioridade" in props and props["Prioridade"]["select"]:
                    prio = props["Prioridade"]["select"]["name"]

                tasks.append({
                    "id": page["id"], 
                    "title": title,
                    "status": status_name,
                    "priority": prio
                })
            
            return tasks

        except Exception as e:
            print(f"❌ Erro ao ler Notion Trabalho: {e}")
            return []

    # ==========================================================
    # 🔍 VERIFICAÇÃO (CHECK) - EVITAR DUPLICIDADE
    # ==========================================================
    def check_existing_plan(self, task_title):
        """Verifica se já existe um plano criado para essa tarefa no Playground."""
        if not self.client_play: return False
        
        # O padrão de nome que usamos é "Plano: [Nome da Tarefa]"
        plan_title = f"Plano: {task_title}"
        
        try:
            response = self.client_play.databases.query(
                database_id=self.play_db,
                filter={
                    "property": "Name",
                    "title": {
                        "equals": plan_title
                    }
                }
            )
            # Se a lista de resultados não for vazia, significa que já existe
            exists = len(response["results"]) > 0
            if exists:
                print(f"⚠️ [NOTION] Plano duplicado encontrado: {plan_title}")
            return exists
            
        except Exception as e:
            print(f"⚠️ Erro ao checar duplicidade: {e}")
            return False

    # ==========================================================
    # ✍️ ESCRITA (POST) - ARGUS PLAYGROUND (COM CHUNKING)
    # ==========================================================
    def create_insight(self, title, content, tags=None):
        """
        Cria uma página de 'Sugestão Técnica'.
        Fatia o conteúdo em blocos de 2000 caracteres para evitar erro de limite da API.
        """
        if not self.client_play: return None
        
        print(f"💡 [NOTION] Publicando Insight: {title}...")
        
        try:
            # 1. Cria o bloco do Título
            children_blocks = [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "Análise Técnica"}}]}
                }
            ]

            # 2. FATIADOR DE TEXTO (Chunking)
            # O Notion aceita no máx 2000 chars por bloco. Vamos dividir o content.
            chunk_size = 2000
            chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]

            for chunk in chunks:
                children_blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": chunk}}]}
                })

            # 3. Cria a página no banco de dados
            new_page = self.client_play.pages.create(
                parent={"database_id": self.play_db},
                properties={
                    "Name": {"title": [{"text": {"content": title}}]},
                    "Tipo": {"select": {"name": "Insight"}},
                    "Data": {"date": {"start": datetime.now().isoformat()}}
                },
                children=children_blocks
            )
            return new_page["url"]

        except Exception as e:
            print(f"❌ Erro ao postar Insight: {e}")
            return None

    def create_daily_log(self, summary):
        """Cria o Diário de Bordo Automático (Daily Log)"""
        if not self.client_play: return None
        
        date_str = datetime.now().strftime("%d/%m/%Y")
        title = f"Diário de Bordo - {date_str}"
        
        try:
            self.client_play.pages.create(
                parent={"database_id": self.play_db},
                properties={
                    "Name": {"title": [{"text": {"content": title}}]},
                    "Tipo": {"select": {"name": "Daily Log"}}
                },
                children=[
                    {
                        "object": "block",
                        "type": "callout",
                        "callout": {
                            "rich_text": [{"text": {"content": summary}}],
                            "icon": {"emoji": "⚓"}
                        }
                    }
                ]
            )
            print(f"📖 [NOTION] Diário de Bordo criado: {title}")
        except Exception as e:
            print(f"❌ Erro ao criar Daily Log: {e}")

# ==========================================
# ÁREA DE TESTES
# ==========================================
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    nm = NotionManager()
    
    print("\n--- 📋 TAREFAS PENDENTES (Leitura Real) ---")
    tarefas = nm.get_pending_tasks()
    
    if tarefas:
        for t in tarefas:
            print(f"🔹 [{t['priority']}] {t['title']} (Status: {t['status']})")
    else:
        print("⚠️ Nenhuma tarefa encontrada com status 'Not started'.")