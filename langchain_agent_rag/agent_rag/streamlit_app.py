# streamlit_app.py
import streamlit as st
from dotenv import load_dotenv
from htmlTemplates import css, bot_template, user_template
from agent2 import create_rag_agent
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_userinput(user_question):
    """
    Processa a pergunta do usuário e obtém resposta do agente RAG.
    """
    try:
        # Verificar se o usuário quer sair
        if user_question.lower().strip() in ['sair', 'exit', 'quit', 'fechar']:
            st.write(bot_template.replace(
                "{{MSG}}", "Obrigado por usar o chat! Fechando aplicação..."), unsafe_allow_html=True)
            st.balloons()
            
            # JavaScript para fechar a aba/janela
            st.markdown("""
            <script>
                setTimeout(function() {
                    window.close();
                }, 2000);
            </script>
            """, unsafe_allow_html=True)
            
            # Parar o servidor Streamlit
            import os
            import signal
            import threading
            
            def stop_server():
                import time
                time.sleep(3)  # Espera 3 segundos para mostrar a mensagem
                os.kill(os.getpid(), signal.SIGTERM)
            
            # Executar em thread separada para não bloquear a interface
            thread = threading.Thread(target=stop_server)
            thread.daemon = True
            thread.start()
            
            # Parar a execução do Streamlit
            st.stop()
            return
        
        # Usar o agente RAG para obter resposta
        response = st.session_state.conversation({'question': user_question})
        st.session_state.chat_history = response['chat_history']
        
        # Exibir histórico de conversação
        for i, message in enumerate(st.session_state.chat_history):
            if i % 2 == 0:
                # Mensagem do usuário
                st.write(user_template.replace(
                    "{{MSG}}", message.content), unsafe_allow_html=True)
            else:
                # Mensagem do bot
                st.write(bot_template.replace(
                    "{{MSG}}", message.content), unsafe_allow_html=True)
                
    except Exception as e:
        logger.error(f"Erro ao processar pergunta: {e}")
        st.error(f"Erro ao processar sua pergunta: {str(e)}")

def initialize_agent():
    """
    Inicializa o agente RAG se ainda não foi inicializado.
    """
    if "conversation" not in st.session_state:
        try:
            with st.spinner("Inicializando agente RAG..."):
                st.session_state.conversation = create_rag_agent()
                st.success("✅ Agente RAG inicializado com sucesso!")
        except Exception as e:
            st.error(f"❌ Erro ao inicializar o agente: {str(e)}")
            st.stop()
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

def main():
    """
    Função principal do aplicativo Streamlit.
    """
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Configurar página
    st.set_page_config(
        page_title="Chat com Agente RAG",
        page_icon=":books:",
        layout="wide"
    )
    
    # Aplicar CSS
    st.write(css, unsafe_allow_html=True)
    
    # Inicializar agente
    initialize_agent()
    
    # Interface principal
    st.header("Chat com Agente RAG :books:")
    st.markdown("---")
    
    # Container para o chat
    chat_container = st.container()
    
    # Input do usuário
    with st.form("user_input_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_question = st.text_input(
                "Faça uma pergunta sobre seus documentos:",
                placeholder="Digite sua pergunta aqui... (ou 'sair' para fechar)",
                key="user_input"
            )
        
        with col2:
            submitted = st.form_submit_button(
                "Enviar",
                type="primary",
                use_container_width=True
            )
    
    # Processar pergunta quando enviada
    if submitted and user_question:
        with chat_container:
            handle_userinput(user_question)
    
    # Sidebar com informações e controles
    with st.sidebar:
        st.subheader("🤖 Agente RAG")
        st.write("Este chat utiliza um agente RAG (Retrieval-Augmented Generation) para responder suas perguntas.")
        
        st.markdown("---")
        
        # Informações sobre o agente
        if st.session_state.get("conversation"):
            st.success("✅ Agente ativo")
            
            # Botão para limpar histórico
            if st.button("🗑️ Limpar Histórico"):
                st.session_state.chat_history = []
                if hasattr(st.session_state.conversation, 'memory'):
                    st.session_state.conversation.memory.clear()
                st.rerun()
        else:
            st.error("❌ Agente não inicializado")
        
        st.markdown("---")
        
        # Estatísticas
        st.subheader("📊 Estatísticas")
        if st.session_state.get("chat_history"):
            num_messages = len(st.session_state.chat_history)
            num_questions = num_messages // 2
            st.metric("Perguntas feitas", num_questions)
            st.metric("Total de mensagens", num_messages)
        else:
            st.write("Nenhuma conversa iniciada ainda.")
        
        st.markdown("---")
        
        # Informações técnicas
        with st.expander("ℹ️ Informações Técnicas"):
            st.write("""
            **Modelo**: GPT-4o
            **Tipo**: Agente ReAct
            **Ferramentas**:
            - Consulta RAG
            - Busca específica
            
            **Funcionalidades**:
            - Memória de conversação
            - Busca em documentos
            - Respostas contextualizadas
            
            **Comandos especiais**:
            - Digite 'sair' para fechar a aplicação
            """)

if __name__ == '__main__':
    main()