# agent.py
import os
import logging
from typing import Dict, Any, List

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
from rag_system import RAGSystem

# Configurar logging
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="langsmith")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGAgentReact:
    """
    Agente RAG usando create_react_agent e AgentExecutor.
    Substitui a API deprecada initialize_agent.
    """
    
    def __init__(self, openai_api_key: str = None):
        """
        Inicializa o agente RAG com a nova API.
        
        Args:
            openai_api_key: Chave da API da OpenAI. Se None, será obtida do arquivo .env
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
        
        # Inicializar componentes
        self.rag = RAGSystem()
        self.llm = ChatOpenAI(
            temperature=0, 
            model="gpt-4o",
            max_tokens=10000
        )
        
        # Adicionar memória para conversação
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Definir ferramentas
        self.tools = self._create_tools()
        
        # Criar prompt
        self.prompt = self._create_prompt()
        
        # Criar agente usando create_react_agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Criar AgentExecutor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
            early_stopping_method="generate"
        )
        
        logger.info("Agente RAG com create_react_agent inicializado com sucesso")
    
    def _create_tools(self) -> List[Tool]:
        """Cria as ferramentas disponíveis para o agente."""
        return [
            Tool(
                name="consulta_rag",
                func=self._consultar_rag,
                description="""Use esta ferramenta para consultar informações sobre... (Assuntos Diversos) 
                """
            ),
            Tool(
                name="busca_especifica",
                func=self._busca_especifica,
                description="""Use esta ferramenta para fazer buscas mais específicas na base de conhecimento
                quando a consulta geral não retornar informações suficientes.
                
                Input: Termos específicos ou palavras-chave para busca
                Output: Informações mais detalhadas sobre o tema específico"""
            )
        ]
    
    def _create_prompt(self) -> PromptTemplate:
        """Cria o prompt para o agente ReAct."""
        try:
            # Tentar usar o prompt padrão do LangChain Hub
            prompt = hub.pull("hwchase17/react")
            logger.info("Prompt carregado do LangChain Hub")
            return prompt
        except Exception as e:
            logger.warning(f"Não foi possível carregar prompt do hub: {e}")
            # Criar prompt customizado
            template = """Você é um assistente especializado em diversos assuntos.

Você tem acesso às seguintes ferramentas:
{tools}

Use o seguinte formato:

Question: a pergunta de entrada que você deve responder  
Thought: você deve sempre pensar sobre o que fazer  
Action: a ação a ser tomada, deve ser uma das [{tool_names}]  
Action Input: a entrada para a ação  
Observation: o resultado da ação  
... (este Thought/Action/Action Input/Observation pode se repetir N vezes)  
Thought: Agora eu sei a resposta final  
Final Answer: a resposta final para a pergunta original

Diretrizes importantes:
- Sempre use as ferramentas disponíveis para buscar informações  
- Baseie suas respostas nos dados encontrados  
- Se não encontrar informações específicas, deixe isso claro  
- Seja preciso e cite dados quando disponíveis  
- Mantenha o foco em temas econômicos e industriais relevantes  

Comece!

Question: {input}  
Thought: {agent_scratchpad}"""

            
            return PromptTemplate.from_template(template)
    
    def _consultar_rag(self, query: str) -> str:
        """Consulta o sistema RAG."""
        try:
            logger.info(f"Consultando RAG: {query}")
            resultado = self.rag.query(query)
            response = resultado.get("response", "Nenhuma informação específica encontrada.")
            logger.info(f"RAG response length: {len(response)}")
            return response
        except Exception as e:
            logger.error(f"Erro ao consultar RAG: {e}")
            return f"Erro ao consultar a base de conhecimento: {str(e)}"
    
    def _busca_especifica(self, termos: str) -> str:
        """Faz uma busca mais específica na base de conhecimento."""
        try:
            logger.info(f"Busca específica: {termos}")
            # Reformular a consulta para busca mais específica
            query_especifica = f"Informações específicas sobre {termos} no ...(No local desejado)"
            resultado = self.rag.query(query_especifica)
            return resultado.get("response", "Nenhuma informação específica encontrada para estes termos.")
        except Exception as e:
            logger.error(f"Erro na busca específica: {e}")
            return f"Erro na busca específica: {str(e)}"
    
    def consultar(self, pergunta: str) -> str:
        """
        Consulta o agente com uma pergunta.
        
        Args:
            pergunta: Pergunta sobre diversos assuntos
            
        Returns:
            Resposta do agente
        """
        if not pergunta.strip():
            return "Por favor, forneça uma pergunta válida."
        
        try:
            logger.info(f"Processando pergunta: {pergunta}")
            resultado = self.agent_executor.invoke({"input": pergunta})
            return resultado.get("output", "Não foi possível obter uma resposta.")
        except Exception as e:
            logger.error(f"Erro ao consultar agente: {e}")
            return f"Erro ao processar a consulta: {str(e)}"
    
    def __call__(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Método para compatibilidade com Streamlit.
        Permite usar o agente como se fosse uma chain do LangChain.
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
            "chat_history": self.memory.chat_memory.messages
        }
    
    def run_interactive(self):
        """Executa o loop interativo."""
        print("=== Agente ReAct - (Assunto desejado) ===")
        print("O agente usa create_react_agent e AgentExecutor")
        print("Digite 'sair' para encerrar.\n")
        
        while True:
            try:
                user_input = input("Digite sua pergunta:\n> ").strip()
                
                if user_input.lower() in ["sair", "exit", "quit"]:
                    print("Encerrando o agente. Até logo!")
                    break
                
                if not user_input:
                    print("Por favor, digite uma pergunta.\n")
                    continue
                
                print("\nProcessando sua pergunta...")
                resposta = self.consultar(user_input)
                print(f"\n{'='*50}\nRESPOSTA:\n{'='*50}\n{resposta}\n{'='*50}\n")
                
            except KeyboardInterrupt:
                print("\nEncerrando o agente. Até logo!")
                break
            except Exception as e:
                logger.error(f"Erro no loop interativo: {e}")
                print(f"Erro inesperado: {e}\n")


def create_rag_agent():
    """
    Função para criar o agente RAG.
    Esta função é chamada pelo streamlit.py
    """
    try:
        # Desabilitar telemetria do ChromaDB (opcional)
        os.environ["ANONYMIZED_TELEMETRY"] = "False"
        
        print("Inicializando agente RAG...")
        agent = RAGAgentReact()
        print("✅ Agente RAG inicializado com sucesso!")
        return agent
        
    except Exception as e:
        print(f"❌ Erro ao inicializar o agente: {e}")
        raise


# Exemplo de uso comparativo
if __name__ == "__main__":
    try:
        # Desabilitar telemetria do ChromaDB (opcional)
        os.environ["ANONYMIZED_TELEMETRY"] = "False"
        
        print("Inicializando agente com create_react_agent...")
        
        # Opção 1: Usando variável de ambiente
        agent = RAGAgentReact()
        
        # Opção 2: Passando a chave diretamente (descomente se necessário)
        # agent = RAGAgentReact(openai_api_key="sk-seu-token-aqui")
        
        # Executar loop interativo
        agent.run_interactive()
        
    except ValueError as e:
        print(f"Erro de configuração: {e}")
        print("\nOpções para configurar a API key:")
        print("1. Variável de ambiente: set OPENAI_API_KEY=sk-seu-token-aqui")
        print("2. Arquivo .env: OPENAI_API_KEY=sk-seu-token-aqui")
        print("3. Parâmetro direto: RAGAgentReact(openai_api_key='sk-seu-token-aqui')")
    except Exception as e:
        print(f"Erro ao inicializar o agente: {e}")
        print("Verifique se a chave da OpenAI está configurada corretamente.")
        print("Certifique-se de ter instalado: pip install langchain-openai langchainhub")