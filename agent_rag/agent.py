# agent.py - Versão Corrigida - Solução para "iteration limit or time limit" e "template not assigned"
import os
import logging
from typing import Dict, Any, List, Tuple

# Carregar variáveis do arquivo .env
from dotenv import load_dotenv
load_dotenv()

# Desabilitar LangSmith (opcional - remove warnings)
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_API_KEY"] = ""

# Imports corretos para a nova API
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from langchain import hub
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage

# Import correto considerando que estamos na pasta rag
try:
    from rag_system import RagSystem
    RAG_AVAILABLE = True
except ImportError as e:
    RAG_AVAILABLE = False
    print(f"⚠️ Aviso: RagSystem não disponível: {e}")

# Configurar logging
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="langsmith")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGAgentReact:
    """
    Agente RAG aprimorado com tratamento robusto de erros e fallback.
    CORREÇÃO: Simplificação do prompt e controle de iterações para evitar loops.
    """
    
    def __init__(self, openai_api_key: str = None):
        """
        Inicializa o agente RAG com configurações aprimoradas e tratamento de erro.
        """
        # Carregar do .env se não fornecida
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        else:
            # Verificar se foi carregada do .env
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY não encontrada. Verifique se:\n"
                    "1. O arquivo .env existe na raiz do projeto\n"
                    "2. Contém: OPENAI_API_KEY=sk-seu-token-aqui\n"
                    "3. O python-dotenv está instalado: pip install python-dotenv"
                )
            print(f"✅ API Key carregada do .env: {api_key[:10]}...")
        
        # Inicialização segura do sistema RAG
        self.rag_available = False
        self.rag_status = "not_initialized"
        
        if RAG_AVAILABLE:
            try:
                self.rag = RagSystem()
                # Verificar se o sistema foi inicializado corretamente
                if hasattr(self.rag, 'is_initialized') and self.rag.is_initialized:
                    self.rag_available = True
                    self.rag_status = "active"
                    print("✅ Sistema RAG inicializado com sucesso")
                else:
                    self.rag_status = "initialization_failed"
                    print("⚠️ Sistema RAG com problemas de inicialização")
            except Exception as e:
                logger.error(f"Erro ao inicializar RAG: {e}")
                self.rag_status = f"error: {str(e)}"
                print(f"❌ Erro na inicialização do RAG: {e}")
        else:
            print("❌ RagSystem não disponível")
        
        # Configuração do LLM com parâmetros otimizados
        self.llm = ChatOpenAI(
            temperature=0.3,  # Reduzido para mais consistência
            model="gpt-4o",
            max_tokens=8000,   # Reduzido para evitar timeouts
            top_p=0.9,
        )
        
        # Adicionar memória para conversação
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            max_token_limit=8000  # Reduzido para melhor performance
        )
        
        # Definir ferramentas simplificadas
        self.tools = self._create_simplified_tools()
        
        # Criar prompt simplificado
        self.prompt = self._create_simplified_prompt()
        
        # Criar agente usando create_react_agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # CORREÇÃO PRINCIPAL: Configurações mais restritivas para evitar loops
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3,        # REDUZIDO de 5 para 3
            max_execution_time=60,   # REDUZIDO de 120 para 60 segundos
            return_intermediate_steps=False,  # Desabilitado para simplicidade
            early_stopping_method="generate"  # Para quando conseguir uma resposta
        )
        
        logger.info(f"Agente RAG inicializado - Status RAG: {self.rag_status}")
    
    def _create_simplified_tools(self) -> List[Tool]:
        """Cria ferramentas simplificadas para evitar loops."""
        tools = []
        
        if self.rag_available:
            # CORREÇÃO: Apenas uma ferramenta principal para evitar confusão do agente
            tools.append(
                Tool(
                    name="consultar_base_conhecimento",
                    func=self._consultar_rag_direto,
                    description="""FERRAMENTA PRINCIPAL: Consulta a base de conhecimento sobre economia de São Paulo.
                    Use esta ferramenta para responder perguntas sobre:
                    - Indústria (automotiva, têxtil, farmacêutica, metalúrgica, etc.)
                    - Economia do Estado de São Paulo
                    - Dados estatísticos e indicadores
                    - Mapa da Indústria Paulista
                    - Balança Comercial
                    - Agropecuária e outros setores
                    
                    Input: A pergunta exata do usuário
                    Output: Resposta completa baseada na base de conhecimento"""
                )
            )
        else:
            tools.append(
                Tool(
                    name="resposta_geral",
                    func=self._resposta_conhecimento_geral,
                    description="""Use esta ferramenta quando o sistema RAG não estiver disponível.
                    Fornece informações gerais sobre economia de São Paulo.
                    
                    Input: Pergunta do usuário
                    Output: Resposta baseada em conhecimento geral"""
                )
            )
        
        return tools
    
    def _create_simplified_prompt(self) -> PromptTemplate:
        """Cria um prompt simplificado que evita loops infinitos."""
        
        # CORREÇÃO: Definir template base primeiro, depois personalizar
        base_template = """Você é um ESPECIALISTA em economia do Estado de São Paulo.

IMPORTANTE: Para saudações simples (olá, oi, bom dia, etc.) responda diretamente SEM usar ferramentas.

Para outras perguntas sobre economia paulista, use as ferramentas disponíveis.

Ferramentas disponíveis:
{tools}

Use o seguinte formato:

Question: {input}
Thought: análise da pergunta
Action: escolha uma ferramenta de [{tool_names}]
Action Input: entrada para a ferramenta
Observation: resultado da ferramenta
Thought: análise final
Final Answer: resposta completa e estruturada

{agent_scratchpad}"""
        
        if self.rag_available:
            # Template específico para quando RAG está disponível
            template = """Você é um ESPECIALISTA em economia do Estado de São Paulo, com foco específico em:
- Indústria Automotiva
- Indústria Têxtil e de Confecções  
- Indústria Farmacêutica
- Máquinas e Equipamentos
- Mapa da Indústria Paulista
- Indústria Metalúrgica
- Agropecuária e Transição Energética
- Balança Comercial Paulista
- Biocombustíveis

INSTRUÇÕES PARA RESPOSTAS DETALHADAS:

1. Use a ferramenta disponível para coletar informações abrangentes
2. Estruture suas respostas com numeração, subtópicos e formatação clara
3. Inclua dados específicos, estatísticas e exemplos sempre que disponível
4. Desenvolva cada ponto com explicações detalhadas
5. Use linguagem técnica apropriada mas acessível

FORMATO OBRIGATÓRIO para Final Answer:
- Use numeração (1., 2., 3., etc.) para pontos principais
- Use subtópicos com **negrito** para destacar aspectos importantes
- Inclua dados quantitativos quando disponível
- Desenvolva cada ponto com pelo menos 2-3 frases explicativas

EXCEÇÕES para respostas diretas (SEM usar ferramentas):
- **Saudações**: "Olá", "Oi", "Bom dia", "Boa tarde", "Boa noite", "Tudo bem?", etc.
- **Confirmações**: "Ok", "Entendi", "Certo", "Sim", "Não"
- **Perguntas sobre funcionamento**: "Como você funciona?", "O que você pode fazer?"
- **Despedidas**: "Tchau", "Até logo", "Obrigado"

Para essas exceções, responda diretamente de forma amigável.

Ferramentas disponíveis:
{tools}

Use o seguinte formato:

Question: {input}
Thought: análise da pergunta e estratégia
Action: escolha uma ferramenta de [{tool_names}]
Action Input: entrada específica para a ferramenta
Observation: resultado da ferramenta
Thought: análise final de todas as informações
Final Answer: resposta DETALHADA, ESTRUTURADA e COMPLETA

{agent_scratchpad}"""
        else:
            # Template para quando RAG não está disponível
            template = """Você é um assistente especializado em economia do Estado de São Paulo.

⚠️ AVISO: Sistema de base de conhecimento não disponível. Respostas baseadas em conhecimento geral.

EXCEÇÕES para respostas diretas (SEM usar ferramentas):
- **Saudações**: "Olá", "Oi", "Bom dia", etc.
- **Confirmações**: "Ok", "Entendi", "Certo"
- **Despedidas**: "Tchau", "Até logo"

Para essas exceções, responda diretamente.

Ferramentas disponíveis:
{tools}

Use o seguinte formato:

Question: {input}
Thought: análise da pergunta
Action: escolha uma ferramenta de [{tool_names}]
Action Input: entrada para a ferramenta
Observation: resultado da ferramenta
Thought: análise final
Final Answer: resposta com base no conhecimento geral disponível

{agent_scratchpad}"""
        
        return PromptTemplate.from_template(template)
    
    def _consultar_rag_direto(self, query: str) -> str:
        """
        CORREÇÃO: Consulta direta e simplificada do RAG.
        """
        try:
            if not self.rag_available:
                return "❌ Sistema RAG não disponível."
            
            logger.info(f"Consulta RAG: {query}")
            
            # Fazer consulta direta sem fallbacks complicados
            resultado = self.rag.query(query)
            
            if 'error' in resultado:
                return f"⚠️ Erro no sistema: {resultado['error']}"
            
            response = resultado.get("response", "")
            
            if not response or len(response) < 50:
                return "⚠️ Resposta muito curta. Sistema pode ter problemas na base de dados."
            
            # Adicionar metadados simples
            num_docs = resultado.get('num_documents', 0)
            if num_docs > 0:
                response += f"\n\n📊 _Baseado em {num_docs} documento(s) da base de conhecimento._"
            
            return response
            
        except Exception as e:
            logger.error(f"Erro na consulta RAG: {e}")
            return f"❌ Erro na consulta: {str(e)}"
    
    def _resposta_conhecimento_geral(self, query: str) -> str:
        """Resposta quando RAG não está disponível."""
        return f"""⚠️ **Sistema de base de conhecimento indisponível**

Pergunta: "{query}"

**Resposta baseada em conhecimento geral:**

São Paulo é o principal centro econômico do Brasil, responsável por cerca de 1/3 do PIB nacional. O estado se destaca em diversos setores:

**Principais Setores:**
- **Indústria Automotiva**: Concentrada no ABC paulista e região de Campinas
- **Indústria Farmacêutica**: Forte presença na região metropolitana
- **Têxtil e Confecções**: Setor tradicional do estado
- **Máquinas e Equipamentos**: Distribuído por várias regiões
- **Agropecuária**: Interior do estado, forte em cana-de-açúcar, café, laranja

**⚠️ IMPORTANTE**: Resposta baseada em conhecimento geral. Para informações precisas, consulte:
- FIESP (Federação das Indústrias do Estado de São Paulo)
- Fundação SEADE
- IBGE

Status do sistema RAG: {self.rag_status}"""
    
    def _is_simple_greeting(self, text: str) -> bool:
        """Verifica se é uma saudação simples que não precisa de ferramentas."""
        greetings = [
            "olá", "oi", "oiê", "ola", "bom dia", "boa tarde", "boa noite",
            "como vai", "tudo bem", "e aí", "salve", "alô", "hello", "hi"
        ]
        text_lower = text.lower().strip()
        return any(greeting in text_lower for greeting in greetings) and len(text_lower) < 20
    
    def consultar(self, pergunta: str) -> str:
        """
        CORREÇÃO PRINCIPAL: Consulta simplificada que evita loops.
        """
        if not pergunta.strip():
            return "Por favor, forneça uma pergunta válida."
        
        try:
            logger.info(f"Processando pergunta: {pergunta}")
            
            # CORREÇÃO: Verificar se é saudação simples
            if self._is_simple_greeting(pergunta):
                return """👋 **Olá! Seja bem-vindo!**

Sou um assistente especializado em economia do Estado de São Paulo. Posso ajudá-lo com informações sobre:

🏭 **Setores Industriais:**
- Indústria Automotiva
- Indústria Têxtil e Confecções
- Indústria Farmacêutica
- Máquinas e Equipamentos
- Indústria Metalúrgica

📊 **Dados Econômicos:**
- Balança Comercial Paulista
- Mapa da Indústria Paulista
- Agropecuária e Transição Energética
- Biocombustíveis

💬 **Como posso ajudar?**
Faça sua pergunta sobre qualquer aspecto da economia paulista!"""
            
            # CORREÇÃO: Input mais simples, sem instruções complexas
            input_simples = pergunta
            
            # Executar com timeout mais restritivo
            resultado = self.agent_executor.invoke(
                {"input": input_simples},
                config={"max_execution_time": 45}  # 45 segundos máximo
            )
            
            resposta = resultado.get("output", "Não foi possível obter uma resposta.")
            
            # CORREÇÃO: Verificar se a resposta é válida
            if "Agent stopped due to iteration limit" in resposta:
                # Fallback direto quando há problema de iteração
                if self.rag_available:
                    logger.warning("Fallback: usando consulta RAG direta")
                    return self._consultar_rag_direto(pergunta)
                else:
                    logger.warning("Fallback: usando conhecimento geral")
                    return self._resposta_conhecimento_geral(pergunta)
            
            return resposta
            
        except Exception as e:
            logger.error(f"Erro ao consultar agente: {e}")
            
            # CORREÇÃO: Fallback robusto em caso de erro
            if self.rag_available:
                try:
                    logger.info("Tentando fallback com RAG direto")
                    return self._consultar_rag_direto(pergunta)
                except:
                    pass
            
            return f"""❌ **Erro no processamento**

Ocorreu um erro ao processar sua pergunta: {str(e)}

**Possíveis soluções:**
1. Tente reformular a pergunta
2. Verifique se é uma pergunta sobre economia de São Paulo
3. Se o problema persistir, reinicie o sistema

Status do RAG: {self.rag_status}"""
    
    def get_system_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o status do sistema."""
        info = {
            "rag_available": self.rag_available,
            "rag_status": self.rag_status,
            "tools_count": len(self.tools),
            "agent_ready": hasattr(self, 'agent_executor'),
            "max_iterations": 3,  # Atualizado
            "max_execution_time": 60  # Atualizado
        }
        
        if self.rag_available and hasattr(self, 'rag'):
            try:
                rag_status = self.rag.get_system_status()
                info.update(rag_status)
            except Exception as e:
                info["rag_error"] = str(e)
        
        return info
    
    def __call__(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        CORREÇÃO: Método para compatibilidade com Streamlit simplificado.
        """
        question = inputs.get("question", "")
        
        if not question:
            return {"chat_history": []}
        
        # Obter resposta do agente
        response = self.consultar(question)
        
        # Adicionar à memória
        self.memory.chat_memory.add_user_message(question)
        self.memory.chat_memory.add_ai_message(response)
        
        # Retornar no formato esperado pelo Streamlit
        return {
            "chat_history": self.memory.chat_memory.messages,
            "output": response  # Adicionar output direto para compatibilidade
        }
    
    def run_interactive(self):
        """Executa o loop interativo."""
        print("=== Agente RAG Corrigido - Sistema de Consulta ===")
        print("Especialista em economia do Estado de São Paulo")
        
        # Mostrar status do sistema
        system_info = self.get_system_info()
        print(f"\n📊 **Status do Sistema:**")
        print(f"RAG disponível: {'✅ Sim' if system_info['rag_available'] else '❌ Não'}")
        print(f"Status: {system_info['rag_status']}")
        print(f"Máx iterações: {system_info['max_iterations']}")
        print(f"Timeout: {system_info['max_execution_time']}s")
        
        print(f"\nDigite 'sair' para encerrar\n")
        
        while True:
            try:
                user_input = input("> ").strip()
                
                if user_input.lower() in ["sair", "exit", "quit"]:
                    print("Encerrando. Até logo!")
                    break
                
                if not user_input:
                    continue
                
                print(f"\n🔍 Processando...")
                resposta = self.consultar(user_input)
                
                print(f"\n{'='*60}")
                print("📊 RESPOSTA:")
                print(f"{'='*60}")
                print(f"{resposta}")
                print(f"{'='*60}\n")
                
            except KeyboardInterrupt:
                print("\nEncerrando. Até logo!")
                break
            except Exception as e:
                logger.error(f"Erro no loop: {e}")
                print(f"Erro: {e}\n")


def create_rag_agent():
    """
    CORREÇÃO: Função para criar o agente RAG corrigido.
    """
    try:
        os.environ["ANONYMIZED_TELEMETRY"] = "False"
        
        print("Inicializando agente RAG corrigido...")
        agent = RAGAgentReact()
        
        system_info = agent.get_system_info()
        if system_info['rag_available']:
            print("✅ Agente RAG completo inicializado!")
        else:
            print(f"⚠️ Agente em modo limitado - Status: {system_info['rag_status']}")
        
        return agent
        
    except Exception as e:
        print(f"❌ Erro ao inicializar: {e}")
        raise


if __name__ == "__main__":
    try:
        os.environ["ANONYMIZED_TELEMETRY"] = "False"
        agent = RAGAgentReact()
        agent.run_interactive()
        
    except ValueError as e:
        print(f"Erro de configuração: {e}")
    except Exception as e:
        print(f"Erro: {e}")
