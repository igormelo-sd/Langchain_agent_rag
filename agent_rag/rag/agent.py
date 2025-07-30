# agent.py - Versão Corrigida com Tratamento de Erros RAG
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
    Funciona mesmo quando o sistema RAG não está disponível.
    """
    
    def __init__(self, openai_api_key: str = None):
        """
        Inicializa o agente RAG com configurações aprimoradas e tratamento de erro.
        
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
        
        # Configuração aprimorada do LLM para respostas mais detalhadas
        self.llm = ChatOpenAI(
            temperature=0.4,
            model="gpt-4o-mini",
            max_tokens=5000,
            top_p=0.9,
        )
        
        # Adicionar memória para conversação
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            max_token_limit=10000
        )
        
        # Definir ferramentas adaptáveis ao status do RAG
        self.tools = self._create_adaptive_tools()
        
        # Criar prompt adaptável
        self.prompt = self._create_adaptive_prompt()
        
        # Criar agente usando create_react_agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Criar AgentExecutor com configurações aprimoradas
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5 if self.rag_available else 3,  # Menos iterações se RAG não disponível
            max_execution_time=120,
            return_intermediate_steps=True
        )
        
        logger.info(f"Agente RAG inicializado - Status RAG: {self.rag_status}")
    
    def _create_adaptive_tools(self) -> List[Tool]:
        """Cria ferramentas que se adaptam ao status do sistema RAG."""
        tools = []
        
        if self.rag_available:
            # Ferramentas completas quando RAG está disponível
            tools.extend([
                Tool(
                    name="consulta_rag_principal",
                    func=self._consultar_rag_principal,
                    description="""Ferramenta PRINCIPAL para consultar informações sobre economia do Estado de São Paulo.
                    Use esta ferramenta primeiro para qualquer pergunta sobre:
                    - Indústria Automotiva
                    - Indústria Têxtil e de Confecções
                    - Indústria Farmacêutica
                    - Máquinas e Equipamentos
                    - Mapa da Indústria Paulista
                    - Indústria Metalúrgica
                    - Agropecuária e Transição Energética
                    - Balança Comercial Paulista
                    - Biocombustíveis
                    
                    Input: Pergunta completa do usuário
                    Output: Informações detalhadas e estruturadas da base de conhecimento"""
                ),
                Tool(
                    name="busca_dados_complementares",
                    func=self._buscar_dados_complementares,
                    description="""Use esta ferramenta para buscar dados complementares e estatísticas específicas
                    quando precisar enriquecer a resposta com mais detalhes, números ou exemplos concretos.
                    
                    Input: Aspectos específicos que precisam de mais detalhamento
                    Output: Dados complementares, estatísticas e informações adicionais"""
                ),
                Tool(
                    name="verificar_status_sistema",
                    func=self._verificar_status_sistema,
                    description="""Use esta ferramenta para verificar o status do sistema RAG
                    e diagnosticar problemas quando as outras ferramentas falharem.
                    
                    Input: "status" ou "diagnóstico"
                    Output: Status detalhado do sistema"""
                )
            ])
        else:
            # Ferramentas limitadas quando RAG não está disponível
            tools.extend([
                Tool(
                    name="resposta_sem_rag",
                    func=self._resposta_sem_rag,
                    description="""Use esta ferramenta quando o sistema RAG não estiver disponível.
                    Fornece informações gerais sobre economia de São Paulo baseadas no conhecimento do modelo.
                    
                    Input: Pergunta do usuário
                    Output: Resposta baseada em conhecimento geral, com aviso sobre limitações"""
                ),
                Tool(
                    name="diagnostico_sistema",
                    func=self._diagnostico_sistema,
                    description="""Use esta ferramenta para explicar por que o sistema RAG não está funcionando
                    e sugerir soluções.
                    
                    Input: Qualquer texto
                    Output: Diagnóstico do problema e sugestões de solução"""
                )
            ])
        
        return tools
    
    def _create_adaptive_prompt(self) -> PromptTemplate:
        """Cria um prompt que se adapta ao status do sistema RAG."""
        
        if self.rag_available:
            # Prompt completo quando RAG está funcionando
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

INSTRUÇÕES IMPORTANTES PARA RESPOSTAS DETALHADAS:

1. **SEMPRE use múltiplas ferramentas** para coletar informações abrangentes
2. **Estruture suas respostas** com numeração, subtópicos e formatação clara
3. **Inclua dados específicos, estatísticas e exemplos** sempre que disponível
4. **Desenvolva cada ponto** com explicações detalhadas, não apenas liste
5. **Conecte informações** entre diferentes aspectos do tema
6. **Use linguagem técnica apropriada** mas acessível

Se as ferramentas RAG falharem, use a ferramenta de verificação de status para diagnosticar o problema.

Ferramentas disponíveis:
{tools}

Use o seguinte formato de raciocínio:

Question: a pergunta de entrada que você deve responder
Thought: análise da pergunta e estratégia para buscar informações abrangentes
Action: a ação a ser tomada, deve ser uma das [{tool_names}]
Action Input: a entrada específica para a ação
Observation: o resultado da ação
... (repita Thought/Action/Action Input/Observation quantas vezes necessário)
Thought: análise completa de todas as informações coletadas
Final Answer: resposta DETALHADA, ESTRUTURADA e COMPLETA

Pergunta: {input}
Raciocínio: {agent_scratchpad}"""
        else:
            # Prompt limitado quando RAG não está disponível
            template = """Você é um assistente especializado em economia do Estado de São Paulo.

⚠️ **IMPORTANTE**: O sistema de busca na base de conhecimento está indisponível.
Suas respostas serão baseadas em conhecimento geral e podem estar limitadas.

INSTRUÇÕES:
1. **Sempre informe** que o sistema RAG está indisponível
2. **Forneça o máximo de informação** baseada em conhecimento geral
3. **Sugira verificação** de fontes oficiais quando apropriado
4. **Use a ferramenta de diagnóstico** se o usuário quiser entender o problema

Ferramentas disponíveis:
{tools}

Use o seguinte formato de raciocínio:

Question: a pergunta de entrada que você deve responder
Thought: análise da pergunta considerando limitações do sistema
Action: a ação a ser tomada, deve ser uma das [{tool_names}]
Action Input: a entrada específica para a ação
Observation: o resultado da ação
Thought: análise das informações coletadas
Final Answer: resposta com aviso sobre limitações do sistema

Pergunta: {input}
Raciocínio: {agent_scratchpad}"""
        
        return PromptTemplate.from_template(template)
    
    def _consultar_rag_principal(self, query: str) -> str:
        """Consulta principal do sistema RAG com tratamento robusto de erros."""
        try:
            if not self.rag_available:
                return "❌ Sistema RAG não disponível. Use a ferramenta de diagnóstico para mais detalhes."
            
            logger.info(f"Consulta RAG principal: {query}")
            
            # Fazer consulta principal
            resultado = self.rag.query(query)
            
            # Verificar se houve erro no resultado
            if 'error' in resultado:
                logger.error(f"Erro no RAG: {resultado['error']}")
                return f"⚠️ Erro no sistema RAG: {resultado['error']}\n\nResposta parcial: {resultado.get('response', 'Não foi possível obter resposta.')}"
            
            response = resultado.get("response", "")
            
            # Verificar qualidade da resposta
            if not response or len(response) < 50:
                return "⚠️ Sistema RAG retornou resposta muito curta ou vazia. Pode haver problemas na base de dados."
            
            # Verificar se obteve informações suficientes
            if len(response) < 200:
                query_expandida = f"Informações detalhadas e completas sobre {query} no Estado de São Paulo"
                resultado_expandido = self.rag.query(query_expandida)
                response_expandida = resultado_expandido.get("response", "")
                if len(response_expandida) > len(response):
                    response = response_expandida
            
            # Adicionar metadados úteis
            num_docs = resultado.get('num_documents', 0)
            if num_docs > 0:
                response += f"\n\n📊 _Informações baseadas em {num_docs} documento(s) da base de conhecimento._"
            else:
                response += "\n\n⚠️ _Nenhum documento específico encontrado na base de dados._"
            
            logger.info(f"RAG principal - tamanho da resposta: {len(response)}")
            return response
            
        except Exception as e:
            logger.error(f"Erro na consulta RAG principal: {e}")
            return f"❌ Erro crítico na consulta RAG: {str(e)}\n\nVerifique se o ChromaDB está funcionando corretamente."
    
    def _buscar_dados_complementares(self, aspecto: str) -> str:
        """Busca dados complementares com tratamento de erro."""
        try:
            if not self.rag_available:
                return "❌ Sistema RAG não disponível para busca complementar."
            
            logger.info(f"Buscando dados complementares: {aspecto}")
            
            # Consultas específicas para dados complementares
            queries_complementares = [
                f"dados estatísticos {aspecto} São Paulo",
                f"números e indicadores {aspecto}",
                f"exemplos práticos {aspecto} indústria paulista"
            ]
            
            respostas_complementares = []
            for query in queries_complementares:
                try:
                    resultado = self.rag.query(query)
                    if 'error' not in resultado:
                        response = resultado.get("response", "")
                        if response and len(response) > 50:
                            respostas_complementares.append(response)
                except Exception as query_error:
                    logger.warning(f"Erro em consulta complementar: {query_error}")
                    continue
            
            # Combinar as melhores respostas
            if respostas_complementares:
                resposta_final = " | ".join(respostas_complementares[:2])
                logger.info(f"Dados complementares encontrados: {len(resposta_final)} caracteres")
                return resposta_final
            else:
                return "⚠️ Dados complementares específicos não encontrados ou sistema com problemas."
                
        except Exception as e:
            logger.error(f"Erro ao buscar dados complementares: {e}")
            return f"❌ Erro na busca de dados complementares: {str(e)}"
    
    def _verificar_status_sistema(self, input_text: str) -> str:
        """Verifica o status do sistema RAG e fornece diagnóstico."""
        try:
            if not self.rag_available:
                return f"""❌ **Sistema RAG Indisponível**

Status atual: {self.rag_status}

**Possíveis causas:**
1. ChromaDB não instalado ou com problemas
2. Base de dados vazia ou corrompida
3. Modelos de embedding não funcionando
4. Problemas de configuração

**Soluções sugeridas:**
1. Verificar instalação: `pip install chromadb sentence-transformers`
2. Verificar se há documentos na base
3. Reinicializar o sistema
4. Verificar logs de erro detalhados"""
            
            # Obter status detalhado do sistema RAG
            status = self.rag.get_system_status()
            
            status_text = "✅ **Sistema RAG Ativo**\n\n"
            status_text += f"**Detalhes do Sistema:**\n"
            status_text += f"- Inicializado: {'✅' if status['initialized'] else '❌'}\n"
            status_text += f"- ChromaDB: {'✅' if status['chroma_client'] else '❌'}\n"
            status_text += f"- OpenAI: {'✅' if status['openai_client'] else '❌'}\n"
            status_text += f"- Coleção existe: {'✅' if status['collection_exists'] else '❌'}\n"
            status_text += f"- Documentos na base: {status['collection_count']}\n"
            status_text += f"- Reranking: {'✅' if status['reranking_enabled'] else '❌'}\n"
            status_text += f"- Logging: {'✅' if status['logging_enabled'] else '❌'}\n"
            
            if 'collection_error' in status:
                status_text += f"\n⚠️ **Erro na coleção:** {status['collection_error']}"
            
            return status_text
            
        except Exception as e:
            return f"❌ Erro ao verificar status: {str(e)}"
    
    def _resposta_sem_rag(self, query: str) -> str:
        """Fornece resposta baseada em conhecimento geral quando RAG não está disponível."""
        logger.info(f"Respondendo sem RAG: {query}")
        
        return f"""⚠️ **Sistema de base de conhecimento indisponível**

Sua pergunta: "{query}"

**Resposta baseada em conhecimento geral:**

São Paulo é o principal centro econômico do Brasil, com destaque especial na indústria automotiva. O estado concentra grande parte da produção nacional de veículos, com plantas das principais montadoras como Volkswagen, General Motors, Ford, Toyota, Honda, entre outras.

**Setores importantes em SP:**
- **Indústria Automotiva**: Região do ABC, Campinas, São José dos Campos
- **Indústria Farmacêutica**: Concentrada na região metropolitana
- **Têxtil e Confecções**: Tradicional setor paulista
- **Máquinas e Equipamentos**: Distribuído por várias regiões
- **Metalurgia**: Forte presença no interior

**⚠️ IMPORTANTE**: Esta resposta é baseada em conhecimento geral e pode estar desatualizada. Para informações precisas e atualizadas, recomendo:
1. Consultar dados oficiais da FIESP
2. Verificar relatórios da Fundação SEADE
3. Acessar dados do IBGE sobre indústria paulista

**Status do sistema**: {self.rag_status}"""
    
    def _diagnostico_sistema(self, input_text: str) -> str:
        """Fornece diagnóstico detalhado do problema no sistema."""
        return f"""🔧 **Diagnóstico do Sistema RAG**

**Status atual**: Sistema RAG indisponível
**Causa**: {self.rag_status}

**Verificações necessárias:**

1. **Dependências Python:**
   ```bash
   pip install chromadb sentence-transformers python-dotenv langchain-openai
   ```

2. **Variáveis de ambiente:**
   - Verificar se existe arquivo .env
   - Confirmar OPENAI_API_KEY configurada

3. **Base de dados ChromaDB:**
   - Verificar se existe pasta chroma_db/
   - Confirmar se há documentos indexados
   - Testar acesso à coleção

4. **Modelos de embedding:**
   - Verificar download automático dos modelos
   - Confirmar funcionamento do sentence-transformers

**Próximos passos:**
1. Verificar logs detalhados no terminal
2. Testar inicialização manual do RagSystem
3. Verificar se todos os arquivos estão no lugar correto
4. Considerar reindexação dos documentos

**Modo atual**: Funcionando apenas com conhecimento geral do modelo."""
    
    def consultar(self, pergunta: str) -> str:
        """
        Consulta o agente com uma pergunta, adaptando-se ao status do RAG.
        
        Args:
            pergunta: Pergunta sobre economia do Estado de São Paulo
            
        Returns:
            Resposta detalhada e estruturada do agente
        """
        if not pergunta.strip():
            return "Por favor, forneça uma pergunta válida sobre economia do Estado de São Paulo."
        
        try:
            logger.info(f"Processando pergunta: {pergunta}")
            
            # Preparar input com contexto sobre status do sistema
            if self.rag_available:
                input_aprimorado = f"""
                PERGUNTA: {pergunta}
                
                IMPORTANTE: Forneça uma resposta COMPLETA e DETALHADA seguindo estas diretrizes:
                1. Use múltiplas ferramentas para coletar informações abrangentes
                2. Estruture a resposta com numeração e subtópicos
                3. Inclua dados específicos e exemplos quando disponível
                4. Desenvolva cada ponto com explicações detalhadas
                5. Conecte diferentes aspectos do tema
                """
            else:
                input_aprimorado = f"""
                PERGUNTA: {pergunta}
                
                CONTEXTO: Sistema RAG indisponível (Status: {self.rag_status})
                Forneça a melhor resposta possível com as ferramentas disponíveis.
                """
            
            resultado = self.agent_executor.invoke({"input": input_aprimorado})
            resposta = resultado.get("output", "Não foi possível obter uma resposta.")
            
            # Adicionar aviso sobre status do sistema se necessário
            if not self.rag_available and "⚠️" not in resposta:
                resposta = f"⚠️ **Sistema de base de conhecimento indisponível**\n\n{resposta}\n\n_Resposta baseada em conhecimento geral. Para informações precisas, verifique o sistema RAG._"
            
            return resposta
            
        except Exception as e:
            logger.error(f"Erro ao consultar agente: {e}")
            return f"Erro ao processar a consulta: {str(e)}\n\nStatus do sistema RAG: {self.rag_status}"
    
    def get_system_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o status do sistema."""
        info = {
            "rag_available": self.rag_available,
            "rag_status": self.rag_status,
            "tools_count": len(self.tools),
            "agent_ready": hasattr(self, 'agent_executor')
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
        """Executa o loop interativo com informações sobre o status do sistema."""
        print("=== Agente RAG Adaptativo - Sistema de Consulta ===")
        print("Especialista em economia do Estado de São Paulo")
        
        # Mostrar status do sistema
        system_info = self.get_system_info()
        print(f"\n📊 **Status do Sistema:**")
        print(f"RAG disponível: {'✅ Sim' if system_info['rag_available'] else '❌ Não'}")
        print(f"Status: {system_info['rag_status']}")
        print(f"Ferramentas ativas: {system_info['tools_count']}")
        
        if not system_info['rag_available']:
            print(f"\n⚠️ **MODO LIMITADO**: Sistema funcionando apenas com conhecimento geral")
            print(f"Para funcionalidade completa, resolva os problemas do RAG")
        
        print(f"\nDigite 'sair' para encerrar, 'status' para diagnóstico\n")
        
        while True:
            try:
                user_input = input("Digite sua pergunta sobre economia de São Paulo:\n> ").strip()
                
                if user_input.lower() in ["sair", "exit", "quit"]:
                    print("Encerrando o agente. Até logo!")
                    break
                
                if user_input.lower() == "status":
                    info = self.get_system_info()
                    print("\n" + "="*60)
                    print("INFORMAÇÕES DO SISTEMA:")
                    print("="*60)
                    for key, value in info.items():
                        print(f"{key}: {value}")
                    print("="*60 + "\n")
                    continue
                
                if not user_input:
                    print("Por favor, digite uma pergunta.\n")
                    continue
                
                print(f"\n🔍 Analisando sua pergunta...")
                if self.rag_available:
                    print("⚙️ Usando sistema RAG completo...")
                else:
                    print("⚠️ Usando modo limitado (sem base de conhecimento)...")
                
                resposta = self.consultar(user_input)
                
                print(f"\n{'='*80}")
                print("📊 RESPOSTA:")
                print(f"{'='*80}")
                print(f"{resposta}")
                print(f"{'='*80}\n")
                
            except KeyboardInterrupt:
                print("\nEncerrando o agente. Até logo!")
                break
            except Exception as e:
                logger.error(f"Erro no loop interativo: {e}")
                print(f"Erro inesperado: {e}\n")


def create_rag_agent():
    """
    Função para criar o agente RAG aprimorado com tratamento de erro.
    Esta função é chamada pelo streamlit.py
    """
    try:
        # Desabilitar telemetria do ChromaDB (opcional)
        os.environ["ANONYMIZED_TELEMETRY"] = "False"
        
        print("Inicializando agente RAG adaptativo...")
        agent = RAGAgentReact()
        
        # Verificar status do sistema
        system_info = agent.get_system_info()
        if system_info['rag_available']:
            print("✅ Agente RAG completo inicializado com sucesso!")
        else:
            print(f"⚠️ Agente inicializado em modo limitado - RAG Status: {system_info['rag_status']}")
        
        return agent
        
    except Exception as e:
        print(f"❌ Erro ao inicializar agente: {e}")
        raise


# Exemplo de uso
if __name__ == "__main__":
    try:
        # Desabilitar telemetria do ChromaDB (opcional)
        os.environ["ANONYMIZED_TELEMETRY"] = "False"
        
        print("Inicializando agente RAG adaptativo...")
        
        # Criar agente adaptativo
        agent = RAGAgentReact()
        
        # Executar loop interativo
        agent.run_interactive()
        
    except ValueError as e:
        print(f"Erro de configuração: {e}")
        print("\nOpções para configurar a API key:")
        print("1. Variável de ambiente: set OPENAI_API_KEY=sk-seu-token-aqui")
        print("2. Arquivo .env: OPENAI_API_KEY=sk-seu-token-aqui")
        print("3. Parâmetro direto: RAGAgentReact(openai_api_key='sk-seu-token-aqui')")
    except Exception as e:
        print(f"Erro ao inicializar agente: {e}")
        print("Verifique se as dependências estão instaladas e a chave da OpenAI está configurada.")