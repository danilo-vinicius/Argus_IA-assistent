import sqlite3
import datetime
import json

DB_NAME = "jarvis_memory.db"

class DataManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Tabela 1: Recompensas (O "Dopamina" do Sistema)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS recompensas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brain_id TEXT,
                timestamp DATETIME,
                user_query TEXT,
                bot_response TEXT,
                reward_score INTEGER,
                feedback_notes TEXT
            )
        ''')

        # Tabela 2: Curiosidade Ativa (Backlog de Estudos)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pontos_curiosidade (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tema TEXT,
                origem_contexto TEXT,
                status_pesquisa TEXT DEFAULT 'Pendente', -- Pendente, Em Analise, Aprendido
                insight_gerado TEXT,
                data_descoberta DATETIME
            )
        ''')

        # Tabela 3: Configuração Dinâmica dos Cérebros (Meta-Cognição)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS config_cerebros (
                brain_id TEXT PRIMARY KEY,
                system_prompt TEXT,
                temperatura REAL,
                ultima_atualizacao DATETIME
            )
        ''')
        
        # Tabelas Legadas (Mantidas para compatibilidade)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico_comandos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comando TEXT,
                data_hora DATETIME
            )
        ''')
        self.conn.commit()

    # --- MÉTODOS DE APRENDIZADO POR REFORÇO ---

    def registrar_recompensa(self, brain_id, query, response, score, notes=""):
        """Registra feedback positivo (+1) ou negativo (-1)"""
        self.cursor.execute('''
            INSERT INTO recompensas (brain_id, timestamp, user_query, bot_response, reward_score, feedback_notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (brain_id, datetime.datetime.now(), query, response, score, notes))
        self.conn.commit()

    def adicionar_curiosidade(self, tema, contexto):
        """Registra algo que o Argus não sabe e precisa pesquisar depois"""
        self.cursor.execute('''
            INSERT INTO pontos_curiosidade (tema, origem_contexto, data_descoberta)
            VALUES (?, ?, ?)
        ''', (tema, contexto, datetime.datetime.now()))
        self.conn.commit()

    def get_curiosidades_pendentes(self):
        """Busca o que precisa ser estudado"""
        self.cursor.execute("SELECT * FROM pontos_curiosidade WHERE status_pesquisa = 'Pendente'")
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()