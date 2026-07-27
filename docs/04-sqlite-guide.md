---
title: SQLite for Local Data Storage
category: Setup
id: doc-sqlite
---

# SQLite for Local Data Storage

SQLite is the world's most widely deployed database engine. It is a serverless, self-contained SQL database that stores everything in a single file, making it ideal for local AI applications.

## Why SQLite?

- **Zero Configuration**: No server process to install, configure, or manage
- **Single File**: The entire database is stored in one cross-platform file
- **Cross-Platform**: Works on Windows, macOS, Linux, iOS, and Android
- **Reliable**: ACID-compliant with full transaction support
- **Fast**: Optimized for read-heavy workloads common in RAG applications
- **Built into Python**: The `sqlite3` module is part of Python's standard library

## SQLite in RAG Applications

In our RAG system, SQLite serves as the vector store:

### Schema Design
```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT NOT NULL,
    title TEXT NOT NULL,
    category TEXT DEFAULT 'General',
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    tf_json TEXT NOT NULL
);
```

Each row represents a single document chunk with:
- **doc_id**: Links the chunk back to its source document
- **title**: Human-readable document name
- **category**: Document classification
- **chunk_index**: Position within the original document
- **content**: The actual text of the chunk
- **tf_json**: JSON-serialized TF-IDF vector for similarity search

### Node.js Integration

Using the `better-sqlite3` package provides synchronous access to SQLite, which is ideal for RAG applications where database operations are fast and blocking is acceptable:

```javascript
import Database from 'better-sqlite3';
const db = new Database('data/rag.db');
db.pragma('journal_mode = WAL'); // Write-Ahead Logging for better performance
```

### Performance Tips

1. Use WAL (Write-Ahead Logging) mode for concurrent read/write access
2. Create indexes on frequently queried columns
3. Use prepared statements for repeated queries
4. For TF-IDF search, cache all vectors in memory on first access
5. Use transactions for bulk inserts during document ingestion
