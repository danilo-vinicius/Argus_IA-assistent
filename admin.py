import streamlit as st
import os
import shutil
from database import DataManager
import pandas as pd
from trainer import treinar_cerebro # Importa nossa função de treino

# Configuração da Página
st.set_page_config(page_title="Jarvis Admin", page_icon="⚙️", layout="wide")

st.title("⚙️ Jarvis Admin Console")

# Conexão com Banco de Dados
db = DataManager()

# Abas do Painel
tab1, tab2, tab3 = st.tabs(["🧠 Gestão de Conhecimento", "📊 Banco de Tarefas", "📝 Notas & Snippets"])

# --- ABA 1: CÉREBROS (RAG) ---
with tab1:
    st.header("Treinamento Neural")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Upload de Arquivos")
        # Seletor de Cérebro
        brain_option = st.selectbox(
            "Para qual cérebro enviar?",
            ["ds_analytics", "iqm_diretoria", "brasfort_global"]
        )
        
        # Upload
        uploaded_files = st.file_uploader("Arraste PDFs ou TXTs", accept_multiple_files=True)
        
        if st.button("Processar e Treinar"):
            if uploaded_files:
                # 1. Salva arquivos na pasta correta
                target_dir = os.path.join("knowledge_base", brain_option)
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                
                saved_count = 0
                for file in uploaded_files:
                    file_path = os.path.join(target_dir, file.name)
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())
                    saved_count += 1
                
                st.success(f"{saved_count} arquivos salvos em {brain_option}.")
                
                # 2. Chama o Treinador
                with st.spinner('O Jarvis está lendo e vetorizando...'):
                    treinar_cerebro(brain_option)
                
                st.balloons()
                st.success("Cérebro Atualizado com Sucesso!")
            else:
                st.warning("Selecione arquivos primeiro.")

    with col2:
        st.subheader("Arquivos na Memória")
        # Lista o que já tem na pasta
        target_dir = os.path.join("knowledge_base", brain_option)
        if os.path.exists(target_dir):
            files = os.listdir(target_dir)
            if files:
                st.table(files)
            else:
                st.info("Nenhum arquivo nesta base de conhecimento.")
        else:
            st.info("Diretório ainda não criado.")

# --- ABA 2: TAREFAS (CRUD) ---
with tab2:
    st.header("Gestão de Protocolos")
    
    # Carrega dados
    df_tarefas = db.get_tarefas_pendentes()
    
    # Editor de Dados (Visual)
    if not df_tarefas.empty:
        edited_df = st.data_editor(
            df_tarefas, 
            num_rows="dynamic",
            column_config={
                "status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Pendente", "Concluido"],
                    required=True,
                ),
                "prioridade": st.column_config.SelectboxColumn(
                    "Prioridade",
                    options=["Alta", "Normal", "Baixa"],
                    required=True,
                )
            }
        )
        
        # Botão para salvar alterações (Lógica simplificada)
        # Em um app real, iterariamos sobre as mudanças para dar UPDATE no SQL
        st.info("A edição direta no SQL via Streamlit requer lógica de update linha a linha. (Implementação futura)")
    else:
        st.info("Nenhuma tarefa pendente.")

# --- ABA 3: SNIPPETS ---
with tab3:
    st.header("Visualizador de Snippets")
    df_notas = db.get_notas()
    st.dataframe(df_notas, hide_index=True)

# Rodapé
st.markdown("---")
st.caption("Jarvis System v2.0 - Local Instance Running on RX 580")