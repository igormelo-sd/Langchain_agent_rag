# streamlit_app.py
import streamlit as st
from dotenv import load_dotenv
from htmlTemplates import load_css, ai_template, human_template
from agent import create_rag_agent
import logging
import os
import signal
import threading
from dataclasses import dataclass
from typing import Literal
import streamlit.components.v1 as components

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Message:
    """Class for keeping track of a chat message."""
    origin: Literal["human", "ai"]
    message: str

def initialize_session_state():
    """
    Inicializa o estado da sessão.
    """
    if "history" not in st.session_state:
        st.session_state.history = []
    if "conversation" not in st.session_state:
        try:
            with st.spinner("Inicializando agente RAG..."):
                st.session_state.conversation = create_rag_agent()
                st.success("✅ Agente RAG inicializado com sucesso!")
        except Exception as e:
            st.error(f"❌ Erro ao inicializar o agente: {str(e)}")
            st.stop()

def extract_message_content(message):
    """
    Extrai o conteúdo de uma mensagem, independente do formato.
    """
    if hasattr(message, 'content'):
        return message.content
    elif hasattr(message, 'message'):
        return message.message
    elif isinstance(message, dict):
        return message.get('content', message.get('message', str(message)))
    else:
        return str(message)

def on_click_callback():
    """
    Callback para processar mensagens do usuário.
    """
    try:
        human_prompt = st.session_state.human_prompt
        
        # Limpar o campo de entrada imediatamente
        st.session_state.human_prompt = ""
        
        if human_prompt.lower().strip() in ['sair', 'exit', 'quit', 'fechar']:
            st.session_state.history.append(
                Message("ai", "Obrigado por usar o chat! Fechando aplicação...")
            )
            st.balloons()
            st.markdown("""
            <script>
                setTimeout(function() {
                    window.close();
                }, 2000);
            </script>
            """, unsafe_allow_html=True)

            def stop_server():
                import time
                time.sleep(3)
                os.kill(os.getpid(), signal.SIGTERM)

            thread = threading.Thread(target=stop_server)
            thread.daemon = True
            thread.start()
            return

        # Adicionar mensagem do usuário
        st.session_state.history.append(
            Message("human", human_prompt)
        )
        
        # Obter resposta do agente
        response = st.session_state.conversation({"question": human_prompt})
        
        # Extrair a resposta do agente de forma mais robusta
        ai_response = ""
        
        # Tentar diferentes formas de extrair a resposta
        if isinstance(response, dict):
            # Tentar chaves comuns
            ai_response = response.get('output', response.get('answer', response.get('result', '')))
            
            # Se não encontrou, tentar no chat_history
            if not ai_response and 'chat_history' in response:
                chat_history = response['chat_history']
                if chat_history and len(chat_history) > 0:
                    last_message = chat_history[-1]
                    ai_response = extract_message_content(last_message)
        else:
            # Se não é dict, tentar extrair conteúdo diretamente
            ai_response = extract_message_content(response)
        
        # Limpar a resposta se ainda contém metadados
        if ai_response and 'additional_kwargs' in ai_response:
            # Parece que ainda está vindo com metadados, vamos processar
            import re
            # Extrair apenas o conteúdo entre aspas após 'content='
            match = re.search(r"content='([^']*)'", ai_response)
            if match:
                ai_response = match.group(1)
            else:
                ai_response = "Desculpe, não consegui processar a resposta adequadamente."
        
        # Fallback se ainda não conseguiu extrair
        if not ai_response or ai_response == "":
            ai_response = "Desculpe, não consegui gerar uma resposta adequada."
        
        # Adicionar resposta do agente
        st.session_state.history.append(
            Message("ai", ai_response)
        )
        
    except Exception as e:
        logger.error(f"Erro ao processar pergunta: {e}")
        st.session_state.history.append(
            Message("ai", f"Erro ao processar sua pergunta: {str(e)}")
        )

def main():
    """
    Função principal do aplicativo Streamlit.
    """
    load_dotenv()

    st.set_page_config(
        page_title="Chat com Agente RAG",
        page_icon=":books:",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Carregar CSS personalizado
    st.markdown("""
    <style>
    /* Reset e configurações básicas */
    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    
    /* Container principal flexível */
    .chat-container {
        display: flex;
        flex-direction: column;
        height: 100vh;
        overflow: hidden;
    }
    
    /* Header fixo */
    .chat-header {
        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
        color: white;
        padding: 15px 20px;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        flex-shrink: 0;
    }
    
    /* Área de mensagens que ocupa o espaço disponível */
    .messages-area {
        flex: 1;
        overflow-y: auto;
        padding: 20px 20px 140px 20px;
        background: #f8f9fa;
        position: relative;
        display: flex;
        flex-direction: column;
    }
    
    /* Container das mensagens */
    .messages-container {
        flex: 1;
        min-height: 0;
    }
    
    /* Área de entrada fixa na parte inferior */
    .input-area {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 20px;
        border-top: 2px solid #e9ecef;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        flex-shrink: 0;
        z-index: 1000;
    }
    
    @media (max-width: 768px) {
        .input-area {
            padding: 15px;
        }
        
        .messages-area {
            padding: 15px 15px 120px 15px;
        }
        
        .stTextArea textarea {
            font-size: 14px !important;
            min-height: 50px !important;
            max-height: 150px !important;
        }
    }            
    /* Painel lateral para informações */
    .sidebar-info {
        position: fixed;
        top: 80px;
        right: 20px;
        width: 280px;
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 2px 15px rgba(0,0,0,0.1);
        z-index: 1000;
        max-height: calc(100vh - 200px);
        overflow-y: auto;
    }
    
    /* Esconder elementos padrão do Streamlit */
    .stApp > header {
        display: none;
    }
    
    .stApp > .main > div:first-child {
        padding-top: 0;
    }
    
    /* Melhorar aparência dos inputs */
    .stTextArea textarea {
        border-radius: 15px !important;
        border: 2px solid #007bff !important;
        padding: 15px !important;
        font-size: 16px !important;
        resize: none !important;
        min-height: 60px !important;
        max-height: 200px !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        overflow-y: auto !important;
        transition: height 0.2s ease !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #0056b3 !important;
        box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25) !important;
        outline: none !important;
    }
    
    /* Botão de envio */
    .stButton > button {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 15px !important;
        padding: 15px 30px !important;
        font-weight: bold !important;
        font-size: 16px !important;
        transition: all 0.3s !important;
        width: 100% !important;
        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4) !important;
    }
    
    /* Área de estatísticas */
    .stats-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 15px;
        margin-bottom: 20px;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #dee2e6;
        transition: transform 0.2s;
    }
    
    .stat-card:hover {
        transform: translateY(-2px);
    }
    
    .stat-number {
        font-size: 24px;
        font-weight: bold;
        color: #007bff;
    }
    
    .stat-label {
        font-size: 12px;
        color: #6c757d;
        margin-top: 5px;
    }
    
    /* Botões de ação */
    .action-buttons {
        display: flex;
        gap: 10px;
        margin-top: 20px;
    }
    
    .action-button {
        flex: 1;
        padding: 10px;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-size: 14px;
        transition: all 0.2s;
    }
    
    .clear-button {
        background: #dc3545;
        color: white;
    }
    
    .clear-button:hover {
        background: #c82333;
    }
    
    .refresh-button {
        background: #17a2b8;
        color: white;
    }
    
    .refresh-button:hover {
        background: #138496;
    }
    
    /* Responsividade */
    @media (max-width: 1200px) {
        .sidebar-info {
            position: relative;
            top: 0;
            right: 0;
            width: 100%;
            margin-bottom: 20px;
        }
    }
    
    @media (max-width: 768px) {
        .chat-header {
            padding: 10px 15px;
        }
        
        .messages-area {
            padding: 15px;
        }
        
        .input-area {
            padding: 15px;
        }
        
        .sidebar-info {
            padding: 15px;
        }
        
        .stTextArea textarea {
            font-size: 14px !important;
        }
        
        .stButton > button {
            padding: 12px 20px !important;
            font-size: 14px !important;
        }
    }
    
    /* Animações suaves */
    .fade-in {
        animation: fadeIn 0.5s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Status do agente */
    .agent-status {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px;
        background: #e8f5e8;
        border-radius: 8px;
        margin-bottom: 20px;
        border-left: 4px solid #28a745;
    }
    
    .status-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #28a745;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 0.7; }
        50% { opacity: 1; }
    }
    
    /* Melhorias na área de entrada */
    .input-container {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 -5px 20px rgba(0,0,0,0.1);
        border: 2px solid #f8f9fa;
        transition: all 0.3s ease;
    }
    
    .input-container:hover {
        border-color: #007bff;
        box-shadow: 0 -5px 25px rgba(0,123,255,0.15);
    }
    
    /* Indicador de caracteres */
    .char-counter {
        text-align: right;
        font-size: 12px;
        color: #6c757d;
        margin-top: 5px;
    }
    
    /* Scrollbar personalizada */
    .messages-area::-webkit-scrollbar {
        width: 8px;
    }
    
    .messages-area::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    
    .messages-area::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 4px;
    }
    
    .messages-area::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Carregar CSS do chat
    load_css()
    
    # Inicializar estado da sessão
    initialize_session_state()

    # Container principal da aplicação
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Header
    st.markdown('''
    <div class="chat-header">
        <h1 style="margin: 0; font-size: 24px;">🤖 Chat com Agente RAG</h1>
        <p style="margin: 5px 0 0 0; opacity: 0.9;">Converse com inteligência artificial avançada</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Área principal com layout responsivo
    if st.session_state.get("show_sidebar", True):
        col_main, col_sidebar = st.columns([3, 1])
    else:
        col_main = st.container()
        col_sidebar = None
    
    # Área principal de mensagens
    with col_main:
        st.markdown('<div class="messages-area">', unsafe_allow_html=True)
        
        # Container das mensagens
        messages_container = st.container()
        with messages_container:
            if st.session_state.history:
                for chat in st.session_state.history:
                    if chat.origin == 'ai':
                        div = ai_template.replace("{{MSG}}", chat.message)
                    else:
                        div = human_template.replace("{{MSG}}", chat.message)
                    st.markdown(div, unsafe_allow_html=True)
            else:
                st.markdown('''
                <div style="text-align: center; padding: 50px; color: #6c757d;">
                    <h3>🌟 Bem-vindo ao Chat RAG!</h3>
                    <p>Faça sua primeira pergunta para começar a conversa.</p>
                </div>
                ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Área de entrada sempre visível na parte inferior
        st.markdown('<div class="input-area">', unsafe_allow_html=True)
        
        # Formulário de entrada
        with st.form("chat_form", clear_on_submit=True):
            st.markdown('<div class="input-container">', unsafe_allow_html=True)
            
            # Campo de texto que expande automaticamente
            user_input = st.text_area(
                "Digite sua pergunta:",
                placeholder="Digite sua pergunta aqui... (ou 'sair' para fechar)",
                height=60,
                max_chars=2000,
                key="human_prompt",
                label_visibility="collapsed"
            )
            
            # Contador de caracteres
            char_count = len(user_input) if user_input else 0
            st.markdown(f'<div class="char-counter">{char_count}/2000 caracteres</div>', unsafe_allow_html=True)
            
            # Botões de ação
            col_btn1, col_btn2, col_btn3 = st.columns([3, 1, 1])
            
            with col_btn1:
                submit_button = st.form_submit_button(
                    "📤 Enviar Mensagem",
                    type="primary",
                    use_container_width=True,
                    on_click=on_click_callback
                )
            
            with col_btn2:
                if st.form_submit_button("🔄", help="Recarregar", use_container_width=True):
                    st.rerun()
            
            with col_btn3:
                if st.form_submit_button("🗑️", help="Limpar", use_container_width=True):
                    st.session_state.human_prompt = ""
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Painel lateral (se habilitado)
    if col_sidebar:
        with col_sidebar:
            st.markdown('<div class="sidebar-info">', unsafe_allow_html=True)
            
            # Status do agente
            if st.session_state.get("conversation"):
                st.markdown('''
                <div class="agent-status">
                    <div class="status-indicator"></div>
                    <div>
                        <strong>Agente RAG Ativo</strong><br>
                        <small>GPT-4o • ReAct • Online</small>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.error("❌ Agente não inicializado")
            
            # Estatísticas
            st.markdown("### 📊 Estatísticas")
            if st.session_state.get("history"):
                num_messages = len(st.session_state.history)
                num_questions = len([m for m in st.session_state.history if m.origin == 'human'])
                num_responses = len([m for m in st.session_state.history if m.origin == 'ai'])
                
                st.markdown(f'''
                <div class="stats-container">
                    <div class="stat-card">
                        <div class="stat-number">{num_questions}</div>
                        <div class="stat-label">Perguntas</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{num_responses}</div>
                        <div class="stat-label">Respostas</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{num_messages}</div>
                        <div class="stat-label">Total</div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.info("📈 Estatísticas aparecerão após as primeiras mensagens")
            
            # Botões de ação
            st.markdown("### ⚙️ Ações")
            
            if st.button("🗑️ Limpar Histórico", use_container_width=True, type="secondary"):
                st.session_state.history = []
                if hasattr(st.session_state.conversation, 'memory'):
                    st.session_state.conversation.memory.clear()
                st.rerun()
            
            if st.button("👁️ Ocultar Painel", use_container_width=True):
                st.session_state.show_sidebar = False
                st.rerun()
            
            # Informações adicionais
            with st.expander("ℹ️ Informações"):
                st.markdown("""
                **Comandos especiais:**
                - `sair`, `exit`, `quit` - Fechar aplicação
                
                **Recursos:**
                - ✨ Interface responsiva
                - 🔄 Scroll automático
                - 📱 Otimizado para mobile
                - 🎨 Tema moderno
                - 💾 Histórico persistente
                """)
            
            # Configurações
            with st.expander("⚙️ Configurações"):
                auto_scroll = st.checkbox("Scroll automático", value=True)
                show_timestamps = st.checkbox("Mostrar timestamps", value=True)
                compact_mode = st.checkbox("Modo compacto", value=False)
                
                if st.button("💾 Salvar Configurações"):
                    st.session_state.config = {
                        'auto_scroll': auto_scroll,
                        'show_timestamps': show_timestamps,
                        'compact_mode': compact_mode
                    }
                    st.success("Configurações salvas!")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Mostrar botão para exibir painel se estiver oculto
    if not st.session_state.get("show_sidebar", True):
        if st.button("👁️ Mostrar Painel"):
            st.session_state.show_sidebar = True
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

    # JavaScript para funcionalidades avançadas
    components.html("""
    <script>
    // Scroll automático para a última mensagem
    function scrollToBottom() {
        const streamlitDoc = window.parent.document;
        const messagesArea = streamlitDoc.querySelector('.messages-area');
        if (messagesArea) {
            messagesArea.scrollTop = messagesArea.scrollHeight;
        }
    }
    
    // Focar no textarea após envio
    function focusTextArea() {
        const streamlitDoc = window.parent.document;
        const textArea = streamlitDoc.querySelector('textarea');
        if (textArea) {
            textArea.focus();
        }
    }
    
    // Detectar Enter para envio (Shift+Enter para nova linha)
    function setupKeyboardShortcuts() {
        const streamlitDoc = window.parent.document;
        
        streamlitDoc.addEventListener('keydown', function(e) {
            if (e.target.tagName === 'TEXTAREA') {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    const submitBtn = streamlitDoc.querySelector('button[kind="primary"]');
                    if (submitBtn && e.target.value.trim()) {
                        submitBtn.click();
                    }
                }
            }
        });
    }
    
    // Redimensionar textarea automaticamente
    function setupAutoResize() {
        const streamlitDoc = window.parent.document;
        
        function adjustTextarea() {
            const textArea = streamlitDoc.querySelector('textarea');
            if (textArea) {
                // Reset height to auto para calcular o scrollHeight correto
                textArea.style.height = 'auto';
                
                // Calcular nova altura baseada no conteúdo
                const newHeight = Math.min(Math.max(textArea.scrollHeight, 60), 200);
                textArea.style.height = newHeight + 'px';
                
                // Ajustar padding do container de mensagens
                const messagesArea = streamlitDoc.querySelector('.messages-area');
                if (messagesArea) {
                    const inputArea = streamlitDoc.querySelector('.input-area');
                    if (inputArea) {
                        const inputHeight = inputArea.offsetHeight;
                        messagesArea.style.paddingBottom = (inputHeight + 20) + 'px';
                    }
                }
            }
        }
        
        // Observar mudanças no DOM para detectar quando a textarea é criada
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    const textArea = streamlitDoc.querySelector('textarea');
                    if (textArea && !textArea.hasAttribute('data-auto-resize')) {
                        textArea.setAttribute('data-auto-resize', 'true');
                        
                        // Adicionar event listeners
                        textArea.addEventListener('input', adjustTextarea);
                        textArea.addEventListener('paste', function() {
                            setTimeout(adjustTextarea, 10);
                        });
                        
                        // Ajustar altura inicial
                        adjustTextarea();
                    }
                }
            });
        });
        
        observer.observe(streamlitDoc.body, {
            childList: true,
            subtree: true
        });
        
        // Tentar configurar imediatamente se a textarea já existir
        setTimeout(adjustTextarea, 100);
    }
    
    // Configurar notificações
    function setupNotifications() {
        if ("Notification" in window && Notification.permission === "default") {
            Notification.requestPermission();
        }
    }
    
    // Notificar nova mensagem (se não estiver em foco)
    function notifyNewMessage() {
        if (document.hidden && "Notification" in window && Notification.permission === "granted") {
            new Notification("Nova mensagem do Chat RAG", {
                body: "Você recebeu uma nova resposta",
                icon: "🤖"
            });
        }
    }
    
    // Observer para detectar novas mensagens
    const streamlitDoc = window.parent.document;
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                setTimeout(function() {
                    scrollToBottom();
                    focusTextArea();
                    notifyNewMessage();
                }, 100);
            }
        });
    });
    
    // Inicializar funcionalidades
    setTimeout(function() {
        setupKeyboardShortcuts();
        setupAutoResize();
        setupNotifications();
        scrollToBottom();
        focusTextArea();
        
        // Observar mudanças
        observer.observe(streamlitDoc.body, {
            childList: true,
            subtree: true
        });
    }, 1000);
    
    // Scroll inicial
    setTimeout(scrollToBottom, 2000);
    
    // Ajustar height da textarea e padding das mensagens periodicamente
    setInterval(function() {
        const streamlitDoc = window.parent.document;
        const textArea = streamlitDoc.querySelector('textarea');
        const messagesArea = streamlitDoc.querySelector('.messages-area');
        const inputArea = streamlitDoc.querySelector('.input-area');
        
        if (textArea && messagesArea && inputArea) {
            // Ajustar altura da textarea
            if (textArea.scrollHeight > 60) {
                textArea.style.height = Math.min(textArea.scrollHeight, 200) + 'px';
            }
            
            // Ajustar padding das mensagens
            const inputHeight = inputArea.offsetHeight;
            messagesArea.style.paddingBottom = (inputHeight + 20) + 'px';
        }
    }, 500);
    
    // Salvar posição do scroll
    window.addEventListener('beforeunload', function() {
        const streamlitDoc = window.parent.document;
        const messagesArea = streamlitDoc.querySelector('.messages-area');
        if (messagesArea) {
            localStorage.setItem('chatScrollPosition', messagesArea.scrollTop);
        }
    });
    
    // Restaurar posição do scroll
    setTimeout(function() {
        const scrollPosition = localStorage.getItem('chatScrollPosition');
        if (scrollPosition) {
            const streamlitDoc = window.parent.document;
            const messagesArea = streamlitDoc.querySelector('.messages-area');
            if (messagesArea) {
                messagesArea.scrollTop = scrollPosition;
            }
        }
    }, 1500);
    </script>
    """, 
        height=0,
        width=0,
    )

if __name__ == '__main__':
    main()