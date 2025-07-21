# guardar.py
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib
import re
import shutil
import sys

# Tentar importar dependências
try:
    from langchain_community.document_loaders import PyPDFDirectoryLoader, PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    import chromadb
    from chromadb.utils import embedding_functions
    print("✅ Todas as dependências foram importadas com sucesso!")
except ImportError as e:
    print(f"❌ Erro ao importar dependências: {e}")
    print("Execute: pip install langchain-community chromadb")
    sys.exit(1)

# Tentar importar PyMuPDF (opcional)
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
    print("✅ PyMuPDF disponível para validação robusta de PDFs")
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("⚠️ PyMuPDF não disponível. Execute: pip install PyMuPDF")

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('processamento.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def check_environment():
    """Verifica se o ambiente está configurado corretamente"""
    print("🔍 Verificando ambiente...")
    
    # Verificar Python
    print(f"Python: {sys.version}")
    
    # Verificar diretório atual
    current_dir = Path.cwd()
    print(f"Diretório atual: {current_dir}")
    
    # Verificar se existe diretório data
    data_dir = current_dir / "data"
    if data_dir.exists():
        pdf_files = list(data_dir.glob("*.pdf"))
        print(f"📁 Diretório 'data' encontrado com {len(pdf_files)} arquivos PDF")
        
        # Listar arquivos PDF
        if pdf_files:
            print("📄 Arquivos PDF encontrados:")
            for pdf in pdf_files[:5]:  # Mostrar apenas os primeiros 5
                size_mb = pdf.stat().st_size / (1024 * 1024)
                print(f"  - {pdf.name} ({size_mb:.1f} MB)")
            if len(pdf_files) > 5:
                print(f"  ... e mais {len(pdf_files) - 5} arquivos")
        else:
            print("⚠️ Nenhum arquivo PDF encontrado no diretório 'data'")
    else:
        print("❌ Diretório 'data' não encontrado")
        print("Crie o diretório 'data' e coloque seus arquivos PDF nele")
        return False
    
    return True

def test_pdf_files(data_path: str) -> List[str]:
    """Testa se os arquivos PDF podem ser lidos"""
    print(f"\n🔍 Testando arquivos PDF em: {data_path}")
    
    pdf_files = []
    invalid_files = []
    
    data_dir = Path(data_path)
    
    if not data_dir.exists():
        print(f"❌ Diretório não encontrado: {data_path}")
        return []
    
    # Buscar arquivos PDF
    pdf_paths = list(data_dir.glob("*.pdf"))
    
    if not pdf_paths:
        print(f"❌ Nenhum arquivo PDF encontrado em: {data_path}")
        return []
    
    print(f"📄 Encontrados {len(pdf_paths)} arquivos PDF")
    
    # Testar cada PDF
    for i, pdf_path in enumerate(pdf_paths, 1):
        print(f"\n[{i}/{len(pdf_paths)}] Testando: {pdf_path.name}")
        
        try:
            # Verificar se existe e não está vazio
            if not pdf_path.exists():
                print(f"  ❌ Arquivo não encontrado")
                invalid_files.append(str(pdf_path))
                continue
            
            file_size = pdf_path.stat().st_size
            if file_size == 0:
                print(f"  ❌ Arquivo vazio")
                invalid_files.append(str(pdf_path))
                continue
            
            print(f"  📊 Tamanho: {file_size / (1024*1024):.1f} MB")
            
            # Testar com PyMuPDF se disponível
            if PYMUPDF_AVAILABLE:
                try:
                    doc = fitz.open(str(pdf_path))
                    page_count = doc.page_count
                    
                    if page_count == 0:
                        print(f"  ❌ PDF sem páginas")
                        invalid_files.append(str(pdf_path))
                        doc.close()
                        continue
                    
                    # Tentar ler primeira página
                    first_page = doc[0]
                    text = first_page.get_text()
                    text_length = len(text.strip())
                    
                    doc.close()
                    
                    print(f"  ✅ PDF válido: {page_count} páginas, ~{text_length} caracteres")
                    pdf_files.append(str(pdf_path))
                    
                except Exception as e:
                    print(f"  ⚠️ Erro com PyMuPDF: {e}")
                    
                    # Fallback para PyPDF
                    try:
                        loader = PyPDFLoader(str(pdf_path))
                        docs = loader.load()
                        
                        if docs and any(doc.page_content.strip() for doc in docs):
                            print(f"  ✅ PDF válido (PyPDF): {len(docs)} páginas")
                            pdf_files.append(str(pdf_path))
                        else:
                            print(f"  ❌ PDF sem conteúdo extraível")
                            invalid_files.append(str(pdf_path))
                    except Exception as e2:
                        print(f"  ❌ Erro com PyPDF: {e2}")
                        invalid_files.append(str(pdf_path))
            else:
                # Usar apenas PyPDF
                try:
                    loader = PyPDFLoader(str(pdf_path))
                    docs = loader.load()
                    
                    if docs and any(doc.page_content.strip() for doc in docs):
                        print(f"  ✅ PDF válido: {len(docs)} páginas")
                        pdf_files.append(str(pdf_path))
                    else:
                        print(f"  ❌ PDF sem conteúdo extraível")
                        invalid_files.append(str(pdf_path))
                except Exception as e:
                    print(f"  ❌ Erro ao ler PDF: {e}")
                    invalid_files.append(str(pdf_path))
            
        except Exception as e:
            print(f"  ❌ Erro geral: {e}")
            invalid_files.append(str(pdf_path))
    
    # Resumo final
    print(f"\n📊 RESUMO:")
    print(f"  ✅ PDFs válidos: {len(pdf_files)}")
    print(f"  ❌ PDFs inválidos: {len(invalid_files)}")
    
    if invalid_files:
        print(f"\n❌ Arquivos problemáticos:")
        for file in invalid_files:
            print(f"  - {Path(file).name}")
    
    return pdf_files

def sanitize_collection_name(name: str) -> str:
    """Sanitiza o nome da coleção para ChromaDB"""
    # Remove caracteres não permitidos
    name = re.sub(r'[^a-zA-Z0-9._-]', '_', name)
    
    # Garante que começa e termina com caractere alfanumérico
    name = re.sub(r'^[._-]+', '', name)
    name = re.sub(r'[._-]+$', '', name)
    
    # Limita a 63 caracteres
    if len(name) > 63:
        name = name[:63]
        name = re.sub(r'[._-]+$', '', name)
    
    # Garante pelo menos 3 caracteres
    if len(name) < 3:
        name = name + "001"
    
    return name

class DocumentProcessor:
    """Processador de documentos melhorado"""
    
    def __init__(self, data_path: str, chroma_path: str, collection_name: str = "seade_gecon"):
        self.data_path = Path(data_path)
        self.chroma_path = Path(chroma_path)
        self.collection_name = sanitize_collection_name(collection_name)
        
        print(f"\n🔧 Configurando processador:")
        print(f"  📁 Dados: {self.data_path}")
        print(f"  🗄️ ChromaDB: {self.chroma_path}")
        print(f"  📚 Coleção: {self.collection_name}")
        
        # Criar diretório do ChromaDB
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        
        # Configurar ChromaDB
        self._setup_chromadb()
        
        # Configurar text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            length_function=len,
            is_separator_regex=False
        )
    
    def _setup_chromadb(self):
        """Configura o ChromaDB"""
        try:
            print("🔧 Configurando ChromaDB...")
            self.chroma_client = chromadb.PersistentClient(path=str(self.chroma_path))
            
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            
            print("✅ ChromaDB configurado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao configurar ChromaDB: {e}")
            raise
    
    def process_documents(self, force_update: bool = False):
        """Processa os documentos"""
        print(f"\n🚀 Iniciando processamento de documentos...")
        
        # Validar PDFs
        valid_pdfs = test_pdf_files(str(self.data_path))
        
        if not valid_pdfs:
            print("❌ Nenhum PDF válido encontrado. Processamento interrompido.")
            return False
        
        try:
            # Carregar documentos
            print(f"\n📖 Carregando documentos...")
            loader = PyPDFDirectoryLoader(str(self.data_path))
            documents = loader.load()
            
            if not documents:
                print("❌ Nenhum documento carregado")
                return False
            
            print(f"✅ {len(documents)} documentos carregados")
            
            # Dividir em chunks
            print(f"✂️ Dividindo documentos em chunks...")
            chunks = self.text_splitter.split_documents(documents)
            print(f"✅ {len(chunks)} chunks criados")
            
            # Filtrar chunks válidos
            valid_chunks = [chunk for chunk in chunks if len(chunk.page_content.strip()) > 50]
            print(f"✅ {len(valid_chunks)} chunks válidos")
            
            # Preparar dados
            print(f"🔄 Preparando dados para ChromaDB...")
            documents_list = []
            metadata_list = []
            ids_list = []
            
            for i, chunk in enumerate(valid_chunks):
                doc_id = f"doc_{i}_{hashlib.md5(chunk.page_content.encode()).hexdigest()[:8]}"
                documents_list.append(chunk.page_content)
                metadata_list.append(chunk.metadata)
                ids_list.append(doc_id)
            
            # Inserir no ChromaDB
            print(f"💾 Inserindo no ChromaDB...")
            batch_size = 100
            total_batches = (len(documents_list) + batch_size - 1) // batch_size
            
            for i in range(0, len(documents_list), batch_size):
                batch_docs = documents_list[i:i+batch_size]
                batch_metadata = metadata_list[i:i+batch_size]
                batch_ids = ids_list[i:i+batch_size]
                
                self.collection.upsert(
                    documents=batch_docs,
                    metadatas=batch_metadata,
                    ids=batch_ids
                )
                
                current_batch = (i // batch_size) + 1
                print(f"  📦 Lote {current_batch}/{total_batches} inserido")
            
            # Estatísticas finais
            total_count = self.collection.count()
            print(f"\n✅ Processamento concluído!")
            print(f"📊 Total de documentos na coleção: {total_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro durante o processamento: {e}")
            logger.error(f"Erro no processamento: {e}")
            return False
    
    def test_query(self, query: str = "economia"):
        """Testa uma consulta"""
        print(f"\n🔍 Testando consulta: '{query}'")
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=3
            )
            
            if results and "documents" in results:
                print(f"✅ {len(results['documents'][0])} resultados encontrados")
                
                for i, doc in enumerate(results["documents"][0]):
                    print(f"\n--- Resultado {i+1} ---")
                    print(f"📄 Conteúdo: {doc[:200]}...")
                    
                    if results["metadatas"][0][i]:
                        source = results["metadatas"][0][i].get("source", "N/A")
                        print(f"🔗 Fonte: {Path(source).name}")
            else:
                print("❌ Nenhum resultado encontrado")
                
        except Exception as e:
            print(f"❌ Erro na consulta: {e}")

def main():
    """Função principal"""
    print("🚀 PROCESSADOR DE DOCUMENTOS PDF")
    print("=" * 50)
    
    # Verificar ambiente
    if not check_environment():
        print("\n❌ Ambiente não está configurado corretamente")
        return
    
    # Configurações - CORRIGIDO: Nome da coleção padronizado
    DATA_PATH = "data"
    CHROMA_PATH = "chroma_db"
    COLLECTION_NAME = "seade_gecon"  # <-- MUDANÇA AQUI
    
    try:
        # Criar processador
        processor = DocumentProcessor(
            data_path=DATA_PATH,
            chroma_path=CHROMA_PATH,
            collection_name=COLLECTION_NAME
        )
        
        # Processar documentos
        success = processor.process_documents()
        
        if success:
            # Testar consulta
            processor.test_query("economia")
            
            print(f"\n🎉 Processamento concluído com sucesso!")
            print(f"💡 Agora você pode usar outros scripts para consultar a base de dados.")
        else:
            print(f"\n❌ Falha no processamento")
            
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        logger.error(f"Erro fatal: {e}")

if __name__ == "__main__":
    main()