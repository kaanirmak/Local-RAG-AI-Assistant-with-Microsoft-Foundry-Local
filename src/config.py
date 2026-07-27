# Configuration constants for the Python Local RAG Assistant
import os

CONFIG = {
    # Server
    "port": int(os.environ.get("PORT", 3000)),
    "host": "127.0.0.1",

    # Model
    "model": "phi-3.5-mini",
    "app_name": "local-rag-assistant",

    # Chunking
    "chunk_size": 200,       # approximate tokens/words per chunk
    "chunk_overlap": 25,     # overlap tokens/words between chunks

    # Retrieval
    "top_k": 3,              # number of chunks to retrieve per query

    # Paths
    "docs_dir": "docs",
    "data_dir": "data",
    "db_file": "data/rag.db",

    # Chat
    "max_conversation_history": 10, # max messages to keep in context
}
