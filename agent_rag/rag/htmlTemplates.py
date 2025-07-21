# htmlTemplates.py
import streamlit as st

def load_css():
    """
    Carrega o CSS customizado para o chat.
    """
    css = """
    <style>
    /* Container principal do chat */
    .chat-messages-container {
        max-height: 70vh;
        overflow-y: auto;
        padding: 10px;
        background: #ffffff;
        border-radius: 10px;
        box-shadow: inset 0 2px 5px rgba(0,0,0,0.1);
    }
    
    /* Linhas do chat */
    .chat-row {
        display: flex;
        margin: 10px 0;
        width: 100%;
        animation: slideIn 0.4s ease-out;
    }
    
    .row-reverse {
        flex-direction: row-reverse;
    }
    
    /* Bolhas de chat */
    .chat-bubble {
        font-family: "Source Sans Pro", sans-serif, "Segoe UI", "Roboto", sans-serif;
        border: 1px solid transparent;
        padding: 12px 16px;
        margin: 0px 10px;
        max-width: 85%;
        word-wrap: break-word;
        line-height: 1.5;
        font-size: 14px;
        position: relative;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    
    /* Bolha da IA */
    .ai-bubble {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 18px 18px 18px 4px;
        color: #2c3e50;
        border-left: 4px solid #007bff;
    }
    
    /* Bolha do usuário */
    .human-bubble {
        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
        color: white;
        border-radius: 18px 18px 4px 18px;
        border-right: 4px solid #004085;
    }
    
    /* Ícones do chat */
    .chat-icon {
        border-radius: 50%;
        margin: 5px;
        flex-shrink: 0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        border: 2px solid #fff;
    }
    
    /* Estilos para conteúdo das mensagens */
    .chat-bubble p {
        margin: 0;
        padding: 5px 0;
    }
    
    .chat-bubble h1,
    .chat-bubble h2,
    .chat-bubble h3 {
        margin: 12px 0 8px 0;
        font-weight: 600;
        color: inherit;
    }
    
    .ai-bubble h1,
    .ai-bubble h2,
    .ai-bubble h3 {
        color: #2c3e50;
    }
    
    /* Código inline */
    .chat-bubble code {
        background-color: rgba(0,0,0,0.1);
        padding: 3px 6px;
        border-radius: 4px;
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 0.9em;
        border: 1px solid rgba(0,0,0,0.1);
    }
    
    .human-bubble code {
        background-color: rgba(255,255,255,0.2);
        color: #f8f9fa;
        border-color: rgba(255,255,255,0.2);
    }
    
    /* Blocos de código */
    .chat-bubble pre {
        background-color: rgba(0,0,0,0.05);
        padding: 12px;
        border-radius: 6px;
        overflow-x: auto;
        margin: 12px 0;
        border: 1px solid rgba(0,0,0,0.1);
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 0.9em;
    }
    
    .human-bubble pre {
        background-color: rgba(255,255,255,0.15);
        border-color: rgba(255,255,255,0.2);
        color: #f8f9fa;
    }
    
    /* Listas */
    .chat-bubble ul,
    .chat-bubble ol {
        padding-left: 20px;
        margin: 10px 0;
    }
    
    .chat-bubble li {
        margin-bottom: 5px;
        line-height: 1.4;
    }
    
    /* Links */
    .chat-bubble a {
        color: #007bff;
        text-decoration: none;
        font-weight: 500;
        transition: color 0.2s;
    }
    
    .chat-bubble a:hover {
        color: #0056b3;
        text-decoration: underline;
    }
    
    .human-bubble a {
        color: #87ceeb;
    }
    
    .human-bubble a:hover {
        color: #b0e0e6;
    }
    
    /* Animações */
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% { 
            opacity: 0.4; 
            transform: scale(0.95);
        }
        50% { 
            opacity: 1; 
            transform: scale(1);
        }
    }
    
    /* Indicadores de status */
    .status-indicator {
        position: absolute;
        top: -5px;
        right: -5px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #28a745;
        border: 2px solid #fff;
        animation: pulse 2s infinite;
    }
    
    /* Timestamps */
    .timestamp {
        font-size: 0.7em;
        opacity: 0.7;
        margin-top: 5px;
        text-align: right;
    }
    
    .human-bubble .timestamp {
        color: rgba(255,255,255,0.8);
    }
    
    .ai-bubble .timestamp {
        color: #6c757d;
    }
    
    /* Scrollbar personalizada */
    .chat-messages-container::-webkit-scrollbar {
        width: 8px;
    }
    
    .chat-messages-container::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    .chat-messages-container::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 10px;
        transition: background 0.2s;
    }
    
    .chat-messages-container::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }
    
    /* Responsividade */
    @media (max-width: 768px) {
        .chat-bubble {
            max-width: 90%;
            padding: 10px 14px;
            font-size: 13px;
        }
        
        .chat-icon {
            width: 28px;
            height: 28px;
        }
        
        .chat-row {
            margin: 8px 0;
        }
    }
    
    @media (max-width: 480px) {
        .chat-bubble {
            max-width: 95%;
            padding: 8px 12px;
            font-size: 12px;
        }
        
        .chat-icon {
            width: 24px;
            height: 24px;
        }
        
        .chat-row {
            margin: 6px 0;
        }
    }
    
    /* Estados especiais */
    .chat-bubble.typing {
        animation: typing 1.5s infinite;
    }
    
    @keyframes typing {
        0%, 100% { opacity: 0.7; }
        50% { opacity: 1; }
    }
    
    /* Melhorias visuais */
    .chat-bubble::before {
        content: '';
        position: absolute;
        width: 0;
        height: 0;
    }
    
    .ai-bubble::before {
        left: -8px;
        top: 15px;
        border-top: 8px solid transparent;
        border-bottom: 8px solid transparent;
        border-right: 8px solid #f8f9fa;
    }
    
    .human-bubble::before {
        right: -8px;
        top: 15px;
        border-top: 8px solid transparent;
        border-bottom: 8px solid transparent;
        border-left: 8px solid #007bff;
    }
    
    /* Efeitos hover */
    .chat-bubble:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        transition: all 0.2s ease;
    }
    
    /* Destaque para mensagens recentes */
    .chat-row:last-child .chat-bubble {
        animation: slideIn 0.4s ease-out, highlight 2s ease-out;
    }
    
    @keyframes highlight {
        0% { background-color: rgba(255, 255, 0, 0.3); }
        100% { background-color: transparent; }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Templates atualizados com melhor estrutura
ai_template = '''
<div class="chat-row">
    <img class="chat-icon" src="https://img.icons8.com/fluency/48/000000/robot-2.png" width="36" height="36" alt="AI">
    <div class="chat-bubble ai-bubble">
        {{MSG}}
        <div class="timestamp">Agente RAG</div>
    </div>
</div>
'''

human_template = '''
<div class="chat-row row-reverse">
    <img class="chat-icon" src="https://img.icons8.com/fluency/48/000000/user-male-circle.png" width="36" height="36" alt="Usuário">
    <div class="chat-bubble human-bubble">
        {{MSG}}
        <div class="timestamp">Você</div>
    </div>
</div>
'''

# Template para mensagens de sistema
system_template = '''
<div class="chat-row">
    <img class="chat-icon" src="https://img.icons8.com/fluency/48/000000/info.png" width="36" height="36" alt="Sistema">
    <div class="chat-bubble" style="background: linear-gradient(135deg, #17a2b8 0%, #138496 100%); color: white; border-radius: 18px; border-left: 4px solid #0c5460;">
        {{MSG}}
        <div class="timestamp" style="color: rgba(255,255,255,0.8);">Sistema</div>
    </div>
</div>
'''

# Template para mensagens de erro
error_template = '''
<div class="chat-row">
    <img class="chat-icon" src="https://img.icons8.com/fluency/48/000000/error.png" width="36" height="36" alt="Erro">
    <div class="chat-bubble" style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; border-radius: 18px; border-left: 4px solid #a71e2a;">
        {{MSG}}
        <div class="timestamp" style="color: rgba(255,255,255,0.8);">Erro</div>
    </div>
</div>
'''

# Template para indicador de carregamento
loading_template = '''
<div class="chat-row">
    <img class="chat-icon" src="https://img.icons8.com/fluency/48/000000/robot-2.png" width="36" height="36" alt="Carregando">
    <div class="chat-bubble ai-bubble typing">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span>Processando sua pergunta</span>
            <div style="display: flex; gap: 3px;">
                <div style="width: 8px; height: 8px; background-color: #007bff; border-radius: 50%; animation: pulse 1.5s infinite;"></div>
                <div style="width: 8px; height: 8px; background-color: #007bff; border-radius: 50%; animation: pulse 1.5s infinite 0.5s;"></div>
                <div style="width: 8px; height: 8px; background-color: #007bff; border-radius: 50%; animation: pulse 1.5s infinite 1s;"></div>
            </div>
        </div>
        <div class="timestamp">Agente RAG</div>
    </div>
</div>
'''

# Template para mensagens de sucesso
success_template = '''
<div class="chat-row">
    <img class="chat-icon" src="https://img.icons8.com/fluency/48/000000/checkmark.png" width="36" height="36" alt="Sucesso">
    <div class="chat-bubble" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; border-radius: 18px; border-left: 4px solid #1e7e34;">
        {{MSG}}
        <div class="timestamp" style="color: rgba(255,255,255,0.8);">Sucesso</div>
    </div>
</div>
'''

# Função auxiliar para escapar HTML
def escape_html(text):
    """
    Escapa caracteres especiais HTML preservando quebras de linha.
    """
    import html
    return html.escape(text).replace("\n", "<br>")

# Função auxiliar para processar markdown simples
def simple_markdown(text):
    """
    Processa markdown básico em HTML.
    """
    import re
    
    # Negrito
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Itálico
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    
    # Código inline
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" target="_blank">\1</a>', text)
    
    # Quebras de linha
    text = text.replace('\n', '<br>')
    
    return text

# Função auxiliar para criar mensagens formatadas
def create_message(message_type, content, timestamp=None):
    """
    Cria uma mensagem formatada com base no tipo.
    
    Args:
        message_type (str): Tipo da mensagem ('ai', 'human', 'system', 'error', 'loading', 'success')
        content (str): Conteúdo da mensagem
        timestamp (str, optional): Timestamp personalizado
    
    Returns:
        str: HTML formatado da mensagem
    """
    # Processar markdown e escapar HTML
    processed_content = simple_markdown(escape_html(content))
    
    templates = {
        'ai': ai_template,
        'human': human_template,
        'system': system_template,
        'error': error_template,
        'loading': loading_template,
        'success': success_template
    }
    
    template = templates.get(message_type, ai_template)
    
    # Adicionar timestamp se fornecido
    if timestamp and message_type in ['ai', 'human']:
        if message_type == 'ai':
            processed_content += f'<div class="timestamp">{timestamp}</div>'
        else:
            processed_content += f'<div class="timestamp">{timestamp}</div>'
    
    return template.replace("{{MSG}}", processed_content)

# Função para renderizar múltiplas mensagens
def render_messages(messages):
    """
    Renderiza uma lista de mensagens.
    
    Args:
        messages (list): Lista de objetos Message
    
    Returns:
        str: HTML formatado de todas as mensagens
    """
    html_messages = []
    
    for message in messages:
        if hasattr(message, 'origin') and hasattr(message, 'message'):
            html_messages.append(create_message(message.origin, message.message))
        else:
            # Fallback para mensagens em formato diferente
            html_messages.append(create_message('system', str(message)))
    
    return "\n".join(html_messages)

# Função para criar container de mensagens
def create_chat_container(messages, container_height="70vh"):
    """
    Cria um container completo para as mensagens do chat.
    
    Args:
        messages (list): Lista de mensagens
        container_height (str): Altura do container
    
    Returns:
        str: HTML completo do container
    """
    messages_html = render_messages(messages)
    
    return f"""
    <div class="chat-messages-container" style="max-height: {container_height};">
        {messages_html}
    </div>
    """

# Função para adicionar efeitos especiais
def add_message_effects(message_html, effects=None):
    """
    Adiciona efeitos especiais a uma mensagem.
    
    Args:
        message_html (str): HTML da mensagem
        effects (list): Lista de efeitos a aplicar
    
    Returns:
        str: HTML com efeitos aplicados
    """
    if not effects:
        return message_html
    
    # Efeitos disponíveis
    effect_classes = {
        'highlight': 'highlight-message',
        'typing': 'typing',
        'pulse': 'pulse-effect',
        'shake': 'shake-effect'
    }
    
    for effect in effects:
        if effect in effect_classes:
            message_html = message_html.replace(
                'class="chat-bubble',
                f'class="chat-bubble {effect_classes[effect]}'
            )
    
    return message_html

# Função para validar e limpar conteúdo
def sanitize_content(content):
    """
    Sanitiza o conteúdo da mensagem para prevenir XSS.
    
    Args:
        content (str): Conteúdo a ser sanitizado
    
    Returns:
        str: Conteúdo sanitizado
    """
    import html
    import re
    
    # Escapar HTML básico
    content = html.escape(content)
    
    # Permitir apenas tags seguras
    safe_tags = ['b', 'i', 'em', 'strong', 'code', 'pre', 'br', 'p', 'ul', 'ol', 'li', 'a']
    
    # Remover scripts
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remover eventos JavaScript
    content = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)
    
    return content

# Função para formatar código
def format_code_blocks(content):
    """
    Formata blocos de código com syntax highlighting básico.
    
    Args:
        content (str): Conteúdo com blocos de código
    
    Returns:
        str: Conteúdo com código formatado
    """
    import re
    
    # Detectar blocos de código
    def format_code_block(match):
        code = match.group(1)
        language = match.group(2) if match.group(2) else 'text'
        
        return f'''
        <div class="code-block">
            <div class="code-header">
                <span class="language-tag">{language}</span>
                <button class="copy-button" onclick="copyCode(this)">📋 Copiar</button>
            </div>
            <pre><code class="language-{language}">{code}</code></pre>
        </div>
        '''
    
    # Substituir blocos de código
    content = re.sub(r'```(\w+)?\n(.*?)\n```', format_code_block, content, flags=re.DOTALL)
    
    return content

# Função para criar mensagem com status
def create_status_message(status, message, details=None):
    """
    Cria uma mensagem de status especial.
    
    Args:
        status (str): Status ('success', 'error', 'warning', 'info')
        message (str): Mensagem principal
        details (str, optional): Detalhes adicionais
    
    Returns:
        str: HTML da mensagem de status
    """
    status_colors = {
        'success': '#28a745',
        'error': '#dc3545',
        'warning': '#ffc107',
        'info': '#17a2b8'
    }
    
    status_icons = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️'
    }
    
    color = status_colors.get(status, '#6c757d')
    icon = status_icons.get(status, '📝')
    
    html = f'''
    <div class="chat-row">
        <div class="chat-bubble" style="background: {color}; color: white; border-radius: 18px; width: 100%; max-width: 100%;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.2em;">{icon}</span>
                <div>
                    <div style="font-weight: bold;">{escape_html(message)}</div>
                    {f'<div style="font-size: 0.9em; opacity: 0.9; margin-top: 5px;">{escape_html(details)}</div>' if details else ''}
                </div>
            </div>
        </div>
    </div>
    '''
    
    return html