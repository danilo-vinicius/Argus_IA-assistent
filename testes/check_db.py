import sqlite3

DB_NAME = "jarvis_memory.db"

def ver_recompensas():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # CORREÇÃO: Mudamos 'score' para 'reward_score'
        cursor.execute("SELECT id, brain_id, user_query, reward_score, timestamp FROM recompensas ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        
        print("\n=== 📊 ÚLTIMOS 5 FEEDBACKS REGISTRADOS ===")
        if not rows:
            print("📭 A tabela está vazia. Dê um Like no chat para testar!")
        else:
            for row in rows:
                # row[0]=id, row[1]=brain, row[2]=query, row[3]=score
                print(f"ID: {row[0]} | Cérebro: {row[1]} | Score: {row[3]} | Query: {row[2][:30]}...")
        
        conn.close()
    except Exception as e:
        print(f"Erro ao ler banco: {e}")

if __name__ == "__main__":
    ver_recompensas()