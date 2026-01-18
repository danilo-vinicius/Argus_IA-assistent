import sqlite3
import pandas as pd
from datetime import datetime

class DataManager:
    def __init__(self, db_name="jarvis_memory.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tarefas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT,
                prioridade TEXT,
                grupo TEXT,
                prazo DATE,
                status TEXT,
                data_criacao TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT,
                conteudo TEXT,
                categoria TEXT
            )
        ''')
        self.conn.commit()

    def add_tarefa(self, descricao, prioridade="Normal", grupo="Geral", prazo=None):
        cursor = self.conn.cursor()
        data_c = datetime.now().strftime("%Y-%m-%d %H:%M")
        if not prazo: prazo = datetime.now().strftime("%Y-%m-%d")
        
        cursor.execute("INSERT INTO tarefas (descricao, prioridade, grupo, prazo, status, data_criacao) VALUES (?, ?, ?, ?, ?, ?)", 
                       (descricao, prioridade, grupo, prazo, "Pendente", data_c))
        self.conn.commit()

    def get_tarefas_pendentes(self):
        return pd.read_sql("SELECT * FROM tarefas WHERE status = 'Pendente' ORDER BY grupo DESC, prazo ASC", self.conn)

    def concluir_tarefa(self, id_tarefa):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE tarefas SET status = 'Concluido' WHERE id = ?", (id_tarefa,))
        self.conn.commit()
    
    # Função de Deletar
    def deletar_tarefa(self, id_tarefa):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tarefas WHERE id = ?", (id_tarefa,))
        self.conn.commit()
        
    # Função para o Chat usar (Tools)
    def atualizar_prazo_tarefa(self, termo_pesquisa, novo_prazo):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE tarefas SET prazo = ? WHERE descricao LIKE ? AND status = 'Pendente'", (novo_prazo, f"%{termo_pesquisa}%"))
        self.conn.commit()
        return f"Tarefas contendo '{termo_pesquisa}' movidas para {novo_prazo}."

    # --- Notas ---
    def add_nota(self, titulo, conteudo, categoria="plaintext"):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO notas (titulo, conteudo, categoria) VALUES (?, ?, ?)", (titulo, conteudo, categoria))
        self.conn.commit()
    
    def get_notas(self):
        return pd.read_sql("SELECT * FROM notas ORDER BY id DESC", self.conn)