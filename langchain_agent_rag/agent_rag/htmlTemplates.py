# htmlTemplates.py

css = '''
<style>
.chat-message {
    padding: 1.5rem; 
    border-radius: 0.5rem; 
    margin-bottom: 1rem; 
    display: flex;
    animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.chat-message.user {
    background-color: #2b313e;
    border-left: 4px solid #007bff;
}

.chat-message.bot {
    background-color: #475063;
    border-left: 4px solid #28a745;
}

.chat-message .avatar {
    width: 20%;
    display: flex;
    align-items: flex-start;
    justify-content: center;
}

.chat-message .avatar img {
    max-width: 78px;
    max-height: 78px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid #ffffff20;
    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
}

.chat-message .message {
    width: 80%;
    padding: 0 1.5rem;
    color: #fff;
    line-height: 1.6;
}

.chat-message .message h1,
.chat-message .message h2,
.chat-message .message h3 {
    color: #fff;
    margin-top: 0;
}

.chat-message .message p {
    margin-bottom: 0.5rem;
}

.chat-message .message code {
    background-color: rgba(255,255,255,0.1);
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
}

.chat-message .message pre {
    background-color: rgba(255,255,255,0.1);
    padding: 1rem;
    border-radius: 5px;
    overflow-x: auto;
    margin: 0.5rem 0;
}

.chat-message .message ul,
.chat-message .message ol {
    padding-left: 1.5rem;
}

.chat-message .message li {
    margin-bottom: 0.3rem;
}

.chat-message .message a {
    color: #87ceeb;
    text-decoration: none;
}

.chat-message .message a:hover {
    text-decoration: underline;
}

.chat-message.user .message {
    font-weight: 500;
}

.chat-message.bot .message {
    text-align: justify;
}

/* Responsividade */
@media (max-width: 768px) {
    .chat-message {
        padding: 1rem;
    }
    
    .chat-message .avatar {
        width: 25%;
    }
    
    .chat-message .message {
        width: 75%;
        padding: 0 1rem;
    }
    
    .chat-message .avatar img {
        max-width: 60px;
        max-height: 60px;
    }
}
</style>
'''

bot_template = '''
<div class="chat-message bot">
    <div class="avatar">
        <img src="https://i.ibb.co/cN0nmSj/Screenshot-2023-05-28-at-02-37-21.png" 
             alt="Bot Avatar"
             style="max-height: 78px; max-width: 78px; border-radius: 50%; object-fit: cover;">
    </div>
    <div class="message">{{MSG}}</div>
</div>
'''

user_template = '''
<div class="chat-message user">
    <div class="avatar">
        <img src="https://i.ibb.co/rdZC7LZ/Photo-logo-1.png" 
             alt="User Avatar"
             style="max-height: 78px; max-width: 78px; border-radius: 50%; object-fit: cover;">
    </div>    
    <div class="message">{{MSG}}</div>
</div>
'''

# Template para mensagens de sistema/erro
system_template = '''
<div class="chat-message" style="background-color: #6c757d; border-left: 4px solid #ffc107;">
    <div class="avatar">
        <img src="https://i.ibb.co/x5F1Z4J/system-icon.png" 
             alt="System"
             style="max-height: 78px; max-width: 78px; border-radius: 50%; object-fit: cover;">
    </div>
    <div class="message">{{MSG}}</div>
</div>
'''

# Template para mensagens de loading
loading_template = '''
<div class="chat-message bot">
    <div class="avatar">
        <img src="https://i.ibb.co/cN0nmSj/Screenshot-2023-05-28-at-02-37-21.png" 
             alt="Bot Avatar"
             style="max-height: 78px; max-width: 78px; border-radius: 50%; object-fit: cover;">
    </div>
    <div class="message">
        <div style="display: flex; align-items: center;">
            <div style="margin-right: 10px;">Processando sua pergunta</div>
            <div style="display: flex; gap: 3px;">
                <div style="width: 8px; height: 8px; background-color: #fff; border-radius: 50%; animation: pulse 1.5s infinite;"></div>
                <div style="width: 8px; height: 8px; background-color: #fff; border-radius: 50%; animation: pulse 1.5s infinite 0.5s;"></div>
                <div style="width: 8px; height: 8px; background-color: #fff; border-radius: 50%; animation: pulse 1.5s infinite 1s;"></div>
            </div>
        </div>
        <style>
            @keyframes pulse {
                0%, 100% { opacity: 0.3; }
                50% { opacity: 1; }
            }
        </style>
    </div>
</div>
'''