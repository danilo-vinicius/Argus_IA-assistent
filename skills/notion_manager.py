import os
from notion_client import Client
from datetime import datetime

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
    # 🔍 LEITURA (GET) - BANCO OFICIAL (Corrigido PT-BR)
    # ==========================================================
    def get_pending_tasks(self):
        """Lê tarefas pendentes no banco do trabalho."""
        if not self.client_work: return []
        
        print(f"📡 Lendo tarefas do banco: {self.work_db}...")
        
        try:
            # --- MUDANÇA AQUI: De 'Not started' para 'Não iniciado' ---
            response = self.client_work.databases.query(
                database_id=self.work_db,
                filter={
                    "property": "Status",
                    "status": {
                        "equals": "Não iniciado" # <--- Agora bate com o print!
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
    # ✍️ ESCRITA (POST) - ARGUS PLAYGROUND
    # ==========================================================
    def create_insight(self, title, content, tags=None):
        """
        Cria uma página de 'Sugestão Técnica' no seu banco pessoal.
        Usado pelo Architect/Strategist.
        """
        if not self.client_play: return None
        
        print(f"💡 [NOTION] Publicando Insight: {title}...")
        
        try:
            # Monta os blocos de texto da página
            children_blocks = [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "Análise Técnica"}}]}
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": content}}]}
                }
            ]

            # Cria a página no banco de dados
            new_page = self.client_play.pages.create(
                parent={"database_id": self.play_db},
                properties={
                    "Name": {"title": [{"text": {"content": title}}]},
                    "Tipo": {"select": {"name": "Insight"}}, # <--- Cria uma tag automática
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
# ÁREA DE TESTES (DEBUG DE INTROSPECÇÃO)
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
        print("DICA: Se tiver tarefas a fazer, tente mudar o filtro no código para 'Não iniciado' ou 'To-do'.")