# rag_system.py - Versão Corrigida com Tratamento de Erros Aprimorado
import chromadb
from openai import OpenAI
from dotenv import load_dotenv
import os
from typing import List, Dict, Any, Optional, Tuple
import logging
import csv
from datetime import datetime
import numpy as np

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importação condicional do reranker
try:
    from sentence_transformers import CrossEncoder
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False
    logger.warning("sentence_transformers não disponível. Reranqueamento desabilitado.")

class RagSystem:
    """Sistema RAG aprimorado com reranking, fallback e logging avançado."""
    
    def __init__(self, 
                 chroma_path: str = "chroma_db", 
                 collection_name: str = "seade_gecon",
                 reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
                 enable_reranking: bool = True,
                 enable_logging: bool = True,
                 **kwargs):
        """
        Inicializa o sistema RAG aprimorado.
        """
        load_dotenv()
        
        # Validação das variáveis de ambiente
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OPENAI_API_KEY não encontrada nas variáveis de ambiente")
        
        # Configuração dos caminhos
        self.chroma_path = chroma_path
        self.collection_name = collection_name
        self.enable_reranking = enable_reranking and RERANKER_AVAILABLE
        self.enable_logging = enable_logging
        self.is_initialized = False
        
        # Prompt do sistema definido ANTES das inicializações
        self.system_prompt_template = """
Você é um assistente especializado na economia do setor automotivo de São Paulo.

Use **apenas** os dados fornecidos abaixo para responder à pergunta do usuário. 
**Nunca invente informações. Se não houver dados suficientes, diga isso com clareza.**

Sua resposta deve:
- Ser clara, direta e bem estruturada
- Incluir fatos, números e fontes sempre que possível
- Usar estruturas como listas, seções ou tópicos quando apropriado
- Evitar repetições e redundâncias
- Estar em português formal e técnico
- Indicar claramente quando as informações são limitadas

Se os dados fornecidos forem insuficientes ou irrelevantes para a pergunta, responda:
"Não tenho informações suficientes para responder essa pergunta com base nos dados disponíveis. 
Você poderia reformular ou especificar melhor a pergunta?"

📚 Documentos relevantes encontrados:
{documents}

💡 Confiança dos documentos: {confidence_scores}
"""
        
        # Inicialização segura dos componentes
        try:
            self._init_chroma_client()
            self._init_openai_client()
            
            # Inicialização do reranker
            if self.enable_reranking:
                self._init_reranker(reranker_model)
            
            # Configurar logging de consultas
            if self.enable_logging:
                self._init_logging()
            
            self.is_initialized = True
            
        except Exception as e:
            logger.error(f"Erro na inicialização do RAG System: {e}")
            self.is_initialized = False
        
        status = "ativo" if self.is_initialized else "com problemas"
        rerank_status = "ativo" if self.enable_reranking else "inativo"
        print(f"📝 RAG System inicializado: {status}, reranking: {rerank_status}")
    
    def _init_chroma_client(self) -> None:
        """Inicializa o cliente ChromaDB com tratamento de erro aprimorado."""
        try:
            # Tentar diferentes configurações do ChromaDB
            self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)
            
            # Verificar se a coleção existe
            try:
                self.collection = self.chroma_client.get_collection(name=self.collection_name)
                collection_count = self.collection.count()
                logger.info(f"ChromaDB conectado. Coleção existente: {self.collection_name} ({collection_count} documentos)")
                
                if collection_count == 0:
                    logger.warning("⚠️ Coleção existe mas está vazia!")
                    
            except Exception as collection_error:
                logger.warning(f"Coleção {self.collection_name} não encontrada: {collection_error}")
                # Tentar criar coleção vazia
                try:
                    self.collection = self.chroma_client.create_collection(name=self.collection_name)
                    logger.info(f"Nova coleção criada: {self.collection_name}")
                except Exception as create_error:
                    logger.error(f"Erro ao criar coleção: {create_error}")
                    raise
                
        except Exception as e:
            logger.error(f"Erro crítico ao inicializar ChromaDB: {e}")
            logger.error("Verifique se o ChromaDB está instalado: pip install chromadb")
            raise
    
    def _init_openai_client(self) -> None:
        """Inicializa o cliente OpenAI."""
        try:
            self.openai_client = OpenAI()
            logger.info("Cliente OpenAI inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente OpenAI: {e}")
            raise
    
    def _init_reranker(self, model_name: str) -> None:
        """Inicializa o modelo de reranqueamento com tratamento de erro."""
        if not RERANKER_AVAILABLE:
            logger.warning("Reranker não disponível - sentence_transformers não instalado")
            self.enable_reranking = False
            self.reranker = None
            return
            
        try:
            self.reranker = CrossEncoder(model_name)
            logger.info(f"Reranker inicializado: {model_name}")
        except Exception as e:
            logger.warning(f"Erro ao inicializar reranker: {e}")
            self.enable_reranking = False
            self.reranker = None
    
    def _init_logging(self) -> None:
        """Inicializa sistema de logging de consultas."""
        self.log_file = "logs_rag.csv"
        
        # Criar cabeçalho se arquivo não existir
        if not os.path.exists(self.log_file):
            try:
                with open(self.log_file, "w", encoding="utf-8", newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "timestamp", "query", "response_length", "num_documents", 
                        "confidence_avg", "processing_time_ms", "rerank_enabled"
                    ])
            except Exception as e:
                logger.error(f"Erro ao criar arquivo de log: {e}")
                self.enable_logging = False
    
    def retrieve_documents(self, query: str, n_results: int = 8) -> Tuple[List[str], List[float]]:
        """
        Recupera documentos relevantes da base de conhecimento com tratamento de erro.
        """
        if not self.is_initialized:
            logger.error("Sistema RAG não inicializado corretamente")
            return [], []
            
        try:
            # Verificar se a coleção tem documentos
            collection_count = self.collection.count()
            if collection_count == 0:
                logger.warning("Coleção vazia - nenhum documento para buscar")
                return [], []
            
            results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results, collection_count),
                include=['documents', 'distances']
            )
            
            documents = []
            distances = []
            
            if results and results.get('documents') and results['documents'][0]:
                documents = results['documents'][0]
                distances = results.get('distances', [[]])[0] if results.get('distances') else [0.0] * len(documents)
                logger.info(f"Recuperados {len(documents)} documentos")
            else:
                logger.warning("Nenhum documento encontrado na busca")
            
            return documents, distances
            
        except Exception as e:
            logger.error(f"Erro ao recuperar documentos: {e}")
            return [], []
    
    def rerank_documents(self, query: str, documents: List[str], top_k: int = 4) -> Tuple[List[str], List[float]]:
        """
        Reranqueia documentos usando modelo de cross-encoder com tratamento de erro.
        """
        if not documents:
            return [], []
            
        if not self.enable_reranking or not hasattr(self, 'reranker') or self.reranker is None:
            # Retorna primeiros documentos com scores dummy
            selected_docs = documents[:top_k]
            dummy_scores = [0.5] * len(selected_docs)
            return selected_docs, dummy_scores
        
        try:
            # Criar pares query-document
            pairs = [[query, doc] for doc in documents]
            
            # Calcular scores de relevância
            scores = self.reranker.predict(pairs)
            
            # Converter scores para lista de floats
            if hasattr(scores, 'tolist'):
                scores = scores.tolist()
            elif not isinstance(scores, (list, tuple)):
                scores = [float(scores)]
            
            # Garantir que scores é uma lista de floats
            scores = [float(s) for s in scores]
            
            # Ordenar por relevância (maior score = mais relevante)
            doc_score_pairs = list(zip(documents, scores))
            doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
            
            # Retornar top_k documentos
            ranked_docs = [doc for doc, _ in doc_score_pairs[:top_k]]
            confidence_scores = [float(score) for _, score in doc_score_pairs[:top_k]]
            
            logger.info(f"Reranqueamento concluído. Top score: {max(confidence_scores):.3f}")
            return ranked_docs, confidence_scores
            
        except Exception as e:
            logger.error(f"Erro no reranqueamento: {e}")
            # Fallback: retorna documentos originais
            selected_docs = documents[:top_k]
            fallback_scores = [0.5] * len(selected_docs)
            return selected_docs, fallback_scores
    
    def assess_response_quality(self, query: str, documents: List[str], confidence_scores: List[float]) -> Dict[str, Any]:
        """
        Avalia a qualidade potencial da resposta antes de gerar.
        """
        if not documents:
            return {
                "quality_score": 0.0,
                "has_sufficient_data": False,
                "recommendation": "no_documents"
            }
        
        try:
            # Garantir que confidence_scores não está vazio
            if not confidence_scores:
                confidence_scores = [0.0] * len(documents)
                
            # Garantir que são números válidos
            valid_scores = [float(score) for score in confidence_scores if score is not None]
            if not valid_scores:
                valid_scores = [0.0]
                
            avg_confidence = float(np.mean(valid_scores))
            max_confidence = float(max(valid_scores))
            
        except Exception as e:
            logger.error(f"Erro ao calcular métricas de confiança: {e}")
            avg_confidence = 0.0
            max_confidence = 0.0
        
        # Critérios de qualidade
        has_sufficient_data = len(documents) >= 1 and max_confidence > 0.1
        quality_score = (avg_confidence + max_confidence) / 2
        
        if not has_sufficient_data:
            recommendation = "ask_clarification"
        elif quality_score > 0.7:
            recommendation = "high_confidence"
        elif quality_score > 0.4:
            recommendation = "medium_confidence"
        else:
            recommendation = "low_confidence"
        
        return {
            "quality_score": float(quality_score),
            "has_sufficient_data": bool(has_sufficient_data),
            "recommendation": recommendation,
            "avg_confidence": float(avg_confidence),
            "max_confidence": float(max_confidence)
        }
    
    def generate_response(self, query: str, documents: List[str], confidence_scores: List[float]) -> str:
        """
        Gera resposta usando o modelo OpenAI com contexto aprimorado.
        """
        try:
            # Verificar se o sistema está inicializado
            if not self.is_initialized:
                return "Sistema RAG não está funcionando corretamente. Verifique a configuração do ChromaDB."
            
            # Formatação dos documentos com scores
            if documents:
                # Garantir que confidence_scores tem o mesmo tamanho que documents
                if len(confidence_scores) != len(documents):
                    confidence_scores = [0.5] * len(documents)
                    
                formatted_documents = []
                for i, (doc, score) in enumerate(zip(documents, confidence_scores)):
                    score_safe = float(score) if score is not None else 0.0
                    formatted_documents.append(f"[Doc {i+1} - Relevância: {score_safe:.2f}]\n{doc}")
                documents_text = "\n\n".join(formatted_documents)
                
                confidence_avg = float(np.mean([s for s in confidence_scores if s is not None]))
                confidence_max = float(max([s for s in confidence_scores if s is not None]))
                confidence_text = f"Scores médio: {confidence_avg:.2f}, máximo: {confidence_max:.2f}"
            else:
                documents_text = "⚠️ Nenhum documento relevante encontrado na base de dados. A base pode estar vazia ou inacessível."
                confidence_text = "N/A - Sem documentos recuperados"
            
            # Usar o template já definido no __init__
            system_prompt = self.system_prompt_template.format(
                documents=documents_text,
                confidence_scores=confidence_text
            )
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.4,
                max_tokens=10000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")
            return f"Erro ao processar sua consulta: {str(e)}. Verifique se a API da OpenAI está configurada corretamente."
    
    def search_with_fallback(self, query: str, initial_n_results: int = 8) -> Tuple[List[str], List[float]]:
        """
        Busca com estratégia de fallback com tratamento de erro aprimorado.
        """
        documents = []
        confidence_scores = []
        
        try:
            # Tentativa 1: Busca normal
            documents, distances = self.retrieve_documents(query, initial_n_results)
            
            if documents:
                # Aplicar reranqueamento
                documents, confidence_scores = self.rerank_documents(query, documents, top_k=4)
                
                # Avaliar qualidade
                quality_assessment = self.assess_response_quality(query, documents, confidence_scores)
                
                if quality_assessment["has_sufficient_data"]:
                    return documents, confidence_scores
            
            # Tentativa 2: Busca com termos-chave extraídos
            logger.info("Tentativa de busca com fallback...")
            key_terms = self._extract_key_terms(query)
            if key_terms != query:
                documents_fallback, distances_fallback = self.retrieve_documents(key_terms, initial_n_results)
                if documents_fallback:
                    documents, confidence_scores = self.rerank_documents(key_terms, documents_fallback, top_k=4)
                    return documents, confidence_scores
            
        except Exception as e:
            logger.error(f"Erro na busca com fallback: {e}")
        
        # Garantir que sempre retorna listas válidas
        return documents or [], confidence_scores or []
    
    def _extract_key_terms(self, query: str) -> str:
        """
        Extrai termos-chave da consulta para busca alternativa.
        """
        # Palavras-chave relacionadas ao setor automotivo
        automotive_keywords = [
            "automotivo", "automóvel", "carro", "veículo", "montadora", 
            "mercado", "produção", "vendas", "exportação", "importação",
            "economia", "setor", "indústria", "são paulo", "sp"
        ]
        
        try:
            words = query.lower().split()
            key_words = [word for word in words if len(word) > 3 and word not in ["como", "qual", "onde", "quando", "porque"]]
            
            # Se encontrar palavras do setor automotivo, priorizá-las
            auto_words = [word for word in key_words if any(kw in word for kw in automotive_keywords)]
            if auto_words:
                return " ".join(auto_words)
            
            return " ".join(key_words[:3])  # Primeiras 3 palavras-chave
        except Exception as e:
            logger.error(f"Erro ao extrair termos-chave: {e}")
            return query
    
    def _log_query(self, query: str, response: str, num_docs: int, confidence_avg: float, processing_time_ms: float) -> None:
        """Registra consulta no arquivo de log com tratamento de erro."""
        if not self.enable_logging:
            return
        
        try:
            with open(self.log_file, "a", encoding="utf-8", newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    str(query).replace('\n', ' ').replace('\r', ''),
                    len(str(response)),
                    int(num_docs),
                    f"{float(confidence_avg):.3f}",
                    f"{float(processing_time_ms):.1f}",
                    bool(self.enable_reranking)
                ])
        except Exception as e:
            logger.error(f"Erro ao registrar log: {e}")
    
    def query(self, user_query: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Executa uma consulta completa no sistema RAG aprimorado com tratamento de erro robusto.
        MÉTODO PRINCIPAL COMPATÍVEL COM agent.py
        """
        start_time = datetime.now()
        logger.info(f"Processando consulta: {user_query}")
        
        # Inicializar variáveis padrão
        documents = []
        confidence_scores = []
        error_message = None
        
        try:
            # Verificar se o sistema está inicializado
            if not self.is_initialized:
                error_message = "Sistema RAG não inicializado. Verifique ChromaDB e embeddings."
                raise Exception(error_message)
            
            # Ajustar n_results para busca inicial
            search_n_results = max(n_results * 2, 8)
            
            # Busca com fallback
            documents, confidence_scores = self.search_with_fallback(user_query, search_n_results)
            
            # Garantir que confidence_scores seja uma lista válida
            if not confidence_scores and documents:
                confidence_scores = [0.5] * len(documents)
            elif not confidence_scores:
                confidence_scores = []
            
            # Avaliação da qualidade
            quality_assessment = self.assess_response_quality(user_query, documents, confidence_scores)
            
            # Gerar resposta
            response = self.generate_response(user_query, documents, confidence_scores)
            
        except Exception as e:
            logger.error(f"Erro durante consulta: {e}")
            error_message = str(e)
            
            # Resposta de fallback quando o sistema falha
            if "ChromaDB" in str(e) or "embedding" in str(e).lower():
                response = """⚠️ **Sistema de busca indisponível**

O sistema de busca na base de conhecimento está temporariamente indisponível devido a problemas técnicos com o ChromaDB ou modelos de embedding.

**Possíveis soluções:**
1. Verifique se o ChromaDB está instalado: `pip install chromadb`
2. Verifique se há documentos na base de dados
3. Execute novamente a indexação dos documentos
4. Verifique se os modelos de embedding estão funcionando

Para consultas sobre economia de São Paulo, recomendo reformular a pergunta ou entrar em contato com o administrador do sistema."""
            else:
                response = f"Erro interno do sistema: {error_message}. Tente novamente."
            
            # Valores padrão para erro
            quality_assessment = {
                "quality_score": 0.0, 
                "has_sufficient_data": False,
                "recommendation": "system_error"
            }
        
        # Calcular tempo de processamento
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Logging (mesmo em caso de erro)
        try:
            confidence_avg = float(np.mean(confidence_scores)) if confidence_scores else 0.0
            self._log_query(user_query, response, len(documents), confidence_avg, processing_time)
        except Exception as log_error:
            logger.error(f"Erro no logging: {log_error}")
        
        # Retorno com tipos garantidos
        result = {
            "query": str(user_query),
            "response": str(response),
            "retrieved_documents": list(documents),
            "confidence_scores": [float(score) for score in confidence_scores] if confidence_scores else [],
            "num_documents": int(len(documents)),
            "quality_assessment": quality_assessment,
            "processing_time_ms": float(processing_time),
            "reranking_enabled": bool(self.enable_reranking),
            "system_initialized": bool(self.is_initialized)
        }
        
        if error_message:
            result["error"] = error_message
            
        return result
    
    def get_system_status(self) -> Dict[str, Any]:
        """Retorna o status atual do sistema RAG."""
        status = {
            "initialized": self.is_initialized,
            "chroma_client": hasattr(self, 'chroma_client'),
            "openai_client": hasattr(self, 'openai_client'),
            "collection_exists": False,
            "collection_count": 0,
            "reranking_enabled": self.enable_reranking,
            "logging_enabled": self.enable_logging
        }
        
        try:
            if hasattr(self, 'collection'):
                status["collection_exists"] = True
                status["collection_count"] = self.collection.count()
        except Exception as e:
            status["collection_error"] = str(e)
        
        return status
    
    def interactive_session(self) -> None:
        """Inicia uma sessão interativa aprimorada com diagnóstico."""
        print("=== Sistema RAG Aprimorado ===")
        
        # Mostrar status do sistema
        system_status = self.get_system_status()
        print(f"Status do sistema: {'✅ OK' if system_status['initialized'] else '❌ COM PROBLEMAS'}")
        print(f"ChromaDB: {'✅' if system_status['chroma_client'] else '❌'}")
        print(f"OpenAI: {'✅' if system_status['openai_client'] else '❌'}")
        print(f"Coleção: {'✅' if system_status['collection_exists'] else '❌'}")
        print(f"Documentos: {system_status['collection_count']}")
        print(f"Reranking: {'✅' if system_status['reranking_enabled'] else '❌'}")
        
        if not system_status['initialized']:
            print("\n⚠️ ATENÇÃO: Sistema com problemas técnicos!")
            print("Respostas podem ser limitadas ou imprecisas.")
        
        print("\nDigite 'sair' para encerrar, 'status' para diagnóstico\n")
        
        while True:
            try:
                user_input = input("Qual é a sua dúvida?\n> ").strip()
                
                if user_input.lower() in ['sair', 'exit', 'quit']:
                    print("Encerrando o sistema. Até logo!")
                    break
                
                if user_input.lower() == 'status':
                    status = self.get_system_status()
                    print("\n" + "="*50)
                    print("DIAGNÓSTICO DO SISTEMA:")
                    print("="*50)
                    for key, value in status.items():
                        print(f"{key}: {value}")
                    print("="*50 + "\n")
                    continue
                
                if not user_input:
                    print("Por favor, digite uma pergunta válida.\n")
                    continue
                
                # Processa a consulta
                result = self.query(user_input)
                
                # Exibe a resposta com metadados
                print(f"\n{'='*60}")
                print("RESPOSTA:")
                print(f"{'='*60}")
                print(result['response'])
                
                print(f"\n{'='*60}")
                print("METADADOS:")
                print(f"{'='*60}")
                print(f"📊 Documentos recuperados: {result['num_documents']}")
                print(f"⏱️ Tempo de processamento: {result['processing_time_ms']:.1f}ms")
                print(f"🏗️ Sistema inicializado: {'Sim' if result['system_initialized'] else 'Não'}")
                
                if result['confidence_scores']:
                    avg_conf = np.mean(result['confidence_scores'])
                    max_conf = max(result['confidence_scores'])
                    print(f"🎯 Confiança média: {avg_conf:.2f} | Máxima: {max_conf:.2f}")
                
                quality = result['quality_assessment']
                print(f"✅ Qualidade estimada: {quality['quality_score']:.2f}")
                print(f"🔄 Reranqueamento: {'Ativo' if result['reranking_enabled'] else 'Inativo'}")
                
                if 'error' in result:
                    print(f"⚠️ Erro: {result['error']}")
                
                print(f"{'='*60}\n")
                
            except KeyboardInterrupt:
                print("\n\nEncerrando o sistema. Até logo!")
                break
            except Exception as e:
                logger.error(f"Erro durante a sessão interativa: {e}")
                print("Ocorreu um erro. Tente novamente.\n")

def main():
    """Função principal para executar o sistema RAG aprimorado."""
    try:
        # Inicializa o sistema RAG aprimorado
        rag_system = RagSystem(
            enable_reranking=True,  # Habilita reranqueamento
            enable_logging=True     # Habilita logging detalhado
        )
        
        # Inicia sessão interativa
        rag_system.interactive_session()
        
    except Exception as e:
        logger.error(f"Erro ao inicializar o sistema: {e}")
        print("Erro ao inicializar o sistema. Verificações necessárias:")
        print("1. pip install chromadb sentence-transformers")
        print("2. Verificar se OPENAI_API_KEY está no .env")
        print("3. Verificar se há documentos na base ChromaDB")

if __name__ == "__main__":
    main()