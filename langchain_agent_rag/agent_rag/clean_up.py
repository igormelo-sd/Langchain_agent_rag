#!/usr/bin/env python3
"""
Script para limpar coleções antigas do ChromaDB
"""

import chromadb
from pathlib import Path

def cleanup_collections():
    """Remove todas as coleções antigas"""
    
    chroma_path = "chroma_db"
    
    try:
        # Conectar ao ChromaDB
        client = chromadb.PersistentClient(path=chroma_path)
        
        # Listar coleções existentes
        collections = client.list_collections()
        print(f"🔍 Encontradas {len(collections)} coleções:")
        
        for collection in collections:
            print(f"  - {collection.name} (ID: {collection.id})")
        
        # Deletar todas as coleções
        for collection in collections:
            client.delete_collection(collection.name)
            print(f"🗑️ Coleção '{collection.name}' deletada")
        
        print("\n✅ Limpeza concluída!")
        print("💡 Agora execute o guardar.py novamente para criar a coleção correta")
        
    except Exception as e:
        print(f"❌ Erro durante limpeza: {e}")

if __name__ == "__main__":
    cleanup_collections()