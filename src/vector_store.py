# TF-IDF based vector store with SQLite persistence and inverted index
import sqlite3
import json
import math
import os
from collections import defaultdict
from src.config import CONFIG

def term_frequency(text):
    """
    Compute term frequency map for a given text.
    Returns dict {term: frequency}
    """
    # Clean text: lowercase and remove non-alphanumeric (except spaces)
    cleaned = re_clean(text)
    words = [w for w in cleaned.split() if w]
    
    tf = {}
    for word in words:
        tf[word] = tf.get(word, 0) + 1
        
    total = len(words) or 1
    normalized_tf = {word: count / total for word, count in tf.items()}
    return normalized_tf

def re_clean(text):
    # Quick alphanumeric + space cleanup
    import re
    return re.sub(r'[^\w\s]', '', text.lower())

def cosine_similarity(tf_a, tf_b):
    """
    Compute cosine similarity between two TF dicts.
    """
    dot_product = 0.0
    norm_a = 0.0
    norm_b = 0.0
    
    for term, val_a in tf_a.items():
        norm_a += val_a * val_a
        val_b = tf_b.get(term, 0.0)
        dot_product += val_a * val_b
        
    for val_b in tf_b.values():
        norm_b += val_b * val_b
        
    denominator = math.sqrt(norm_a) * math.sqrt(norm_b)
    return 0.0 if denominator == 0.0 else dot_product / denominator

class VectorStore:
    def __init__(self, db_path=CONFIG["db_file"]):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_schema()
        
        # In-memory caches (lazy-loaded)
        self._row_cache = None
        self._inverted_index = None
        
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _init_schema(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    category TEXT DEFAULT 'General',
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    tf_json TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_doc_id ON documents(doc_id)")
            conn.commit()

    def add_chunk(self, chunk):
        tf = term_frequency(chunk["content"])
        tf_json = json.dumps(tf)
        
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO documents (doc_id, title, category, chunk_index, content, tf_json) VALUES (?, ?, ?, ?, ?, ?)",
                (chunk["docId"], chunk["title"], chunk["category"], chunk["chunkIndex"], chunk["content"], tf_json)
            )
            conn.commit()
            
        # Invalidate cache
        self._row_cache = None
        self._inverted_index = None

    def add_chunks(self, chunks):
        with self._get_conn() as conn:
            for chunk in chunks:
                tf = term_frequency(chunk["content"])
                tf_json = json.dumps(tf)
                conn.execute(
                    "INSERT INTO documents (doc_id, title, category, chunk_index, content, tf_json) VALUES (?, ?, ?, ?, ?, ?)",
                    (chunk["docId"], chunk["title"], chunk["category"], chunk["chunkIndex"], chunk["content"], tf_json)
                )
            conn.commit()
            
        # Invalidate cache
        self._row_cache = None
        self._inverted_index = None

    def _ensure_cache(self):
        if self._row_cache is not None:
            return
            
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM documents")
            rows = cursor.fetchall()
            
        self._row_cache = []
        self._inverted_index = defaultdict(set)
        
        for i, row in enumerate(rows):
            tf_data = json.loads(row["tf_json"])
            row_dict = {
                "id": row["id"],
                "doc_id": row["doc_id"],
                "title": row["title"],
                "category": row["category"],
                "chunk_index": row["chunk_index"],
                "content": row["content"],
                "tf": tf_data
            }
            self._row_cache.append(row_dict)
            for term in tf_data.keys():
                self._inverted_index[term].add(i)

    def search(self, query, top_k=CONFIG["top_k"]):
        query_tf = term_frequency(query)
        self._ensure_cache()
        
        if not self._row_cache:
            return []
            
        # Use inverted index to find candidate chunks
        candidate_indices = set()
        for term in query_tf.keys():
            if term in self._inverted_index:
                candidate_indices.update(self._inverted_index[term])
                
        # Score candidates
        scored = []
        for idx in candidate_indices:
            row = self._row_cache[idx]
            score = cosine_similarity(query_tf, row["tf"])
            if score > 0:
                scored.append({
                    "id": row["id"],
                    "docId": row["doc_id"],
                    "title": row["title"],
                    "category": row["category"],
                    "chunkIndex": row["chunk_index"],
                    "content": row["content"],
                    "score": score
                })
                
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def count(self):
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT COUNT(*) as cnt FROM documents")
            return cursor.fetchone()["cnt"]

    def get_document_ids(self):
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT DISTINCT doc_id, title, category FROM documents")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def clear(self):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM documents")
            conn.commit()
        self._row_cache = None
        self._inverted_index = None
