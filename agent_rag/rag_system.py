# rag_system.py
import chromadb
from openai import OpenAI
from dotenv import load_dotenv
import os
from typing import List, Dict, Any
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGSystem:
    """Sistema RAG para consultas."""
    
    def __init__(self, chroma_path: str = "chroma_db", collection_name: str = "Nome_Coleção"):
        """
        Inicializa o sistema RAG.
        
        Args:
            chroma_path: Caminho para o banco de dados ChromaDB
            collection_name: Nome da coleção no ChromaDB
        """
        load_dotenv()
        
        # Validação das variáveis de ambiente
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OPENAI_API_KEY não encontrada nas variáveis de ambiente")
        
        # Configuração dos caminhos
        self.chroma_path = chroma_path
        self.collection_name = collection_name
        
        # Inicialização dos clientes
        self._init_chroma_client()
        self._init_openai_client()
        
        # Prompt do sistema personalizado para o domínio
        self.system_prompt_template = """
Você é um assistente especializado em...(No assunto proposto).
Responda apenas com base nas informações fornecidas abaixo. Não use conhecimento interno 
ou invente informações.

Se não souber a resposta com base nos dados fornecidos, responda: "Não tenho informações 
suficientes para responder essa pergunta com base nos dados disponíveis."

Mantenha suas respostas:
- Precisas e baseadas apenas nos dados fornecidos
- Claras e objetivas
- Em português brasileiro
- Estruturadas quando apropriado

Dados disponíveis:
{documents}
"""
    
    def _init_chroma_client(self) -> None:
        """Inicializa o cliente ChromaDB."""
        try:
            self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)
            self.collection = self.chroma_client.get_or_create_collection(name=self.collection_name)
            logger.info(f"ChromaDB conectado com sucesso. Coleção: {self.collection_name}")
        except Exception as e:
            logger.error(f"Erro ao conectar com ChromaDB: {e}")
            raise
    
    def _init_openai_client(self) -> None:
        """Inicializa o cliente OpenAI."""
        try:
            self.openai_client = OpenAI()
            logger.info("Cliente OpenAI inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente OpenAI: {e}")
            raise
    
    def retrieve_documents(self, query: str, n_results: int = 4) -> List[str]:
        """
        Recupera documentos relevantes da base de conhecimento.
        
        Args:
            query: Consulta do usuário
            n_results: Número de resultados a retornar
            
        Returns:
            Lista de documentos relevantes
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            documents = []
            if results['documents'] and results['documents'][0]:
                documents = results['documents'][0]
                logger.info(f"Recuperados {len(documents)} documentos para a consulta")
            else:
                logger.warning("Nenhum documento encontrado para a consulta")
            
            return documents
            
        except Exception as e:
            logger.error(f"Erro ao recuperar documentos: {e}")
            return []
    
    def generate_response(self, query: str, documents: List[str]) -> str:
        """
        Gera resposta usando o modelo OpenAI.
        
        Args:
            query: Consulta do usuário
            documents: Documentos recuperados
            
        Returns:
            Resposta gerada pelo modelo
        """
        try:
            # Formatação dos documentos para o prompt
            formatted_documents = "\n".join([f"- {doc}" for doc in documents]) if documents else "Nenhum documento encontrado"
            
            system_prompt = self.system_prompt_template.format(documents=formatted_documents)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.1,  # Baixa temperatura para respostas mais determinísticas
                max_tokens=5000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")
            return "Desculpe, ocorreu um erro ao processar sua consulta. Tente novamente."
    
    def query(self, user_query: str, n_results: int = 4) -> Dict[str, Any]:
        """
        Executa uma consulta completa no sistema RAG.
        
        Args:
            user_query: Consulta do usuário
            n_results: Número de documentos a recuperar
            
        Returns:
            Dicionário com a resposta e metadados
        """
        logger.info(f"Processando consulta: {user_query}")
        
        # Recupera documentos relevantes
        documents = self.retrieve_documents(user_query, n_results)
        
        # Gera resposta
        response = self.generate_response(user_query, documents)
        
        return {
            "query": user_query,
            "response": response,
            "retrieved_documents": documents,
            "num_documents": len(documents)
        }
    
    def interactive_session(self) -> None:
        """Inicia uma sessão interativa com o usuário."""
        print("=== Sistema RAG - (Assunto proposto) ===")
        print("Digite 'sair' para encerrar o programa\n")
        
        while True:
            try:
                user_input = input("Qual é a sua dúvida sobre...(Assunto proposto)?\n> ").strip()
                
                if user_input.lower() in ['sair', 'exit', 'quit']:
                    print("Encerrando o sistema. Até logo!")
                    break
                
                if not user_input:
                    print("Por favor, digite uma pergunta válida.\n")
                    continue
                
                # Processa a consulta
                result = self.query(user_input)
                
                # Exibe a resposta
                print(f"\n{'='*50}")
                print("RESPOSTA:")
                print(f"{'='*50}")
                print(result['response'])
                print(f"\n(Baseado em {result['num_documents']} documento(s) recuperado(s))")
                print(f"{'='*50}\n")
                
            except KeyboardInterrupt:
                print("\n\nEncerrando o sistema. Até logo!")
                break
            except Exception as e:
                logger.error(f"Erro durante a sessão interativa: {e}")
                print("Ocorreu um erro. Tente novamente.\n")

def main():
    """Função principal para executar o sistema RAG."""
    try:
        # Inicializa o sistema RAG
        rag_system = RAGSystem()
        
        # Inicia sessão interativa
        rag_system.interactive_session()
        
    except Exception as e:
        logger.error(f"Erro ao inicializar o sistema: {e}")
        print("Erro ao inicializar o sistema. Verifique as configurações e tente novamente.")

if __name__ == "__main__":
    main()