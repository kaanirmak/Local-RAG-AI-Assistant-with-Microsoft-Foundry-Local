# Text chunking module with overlapping windows and YAML front-matter support
import re
from src.config import CONFIG

def parse_front_matter(text):
    """
    Parse optional YAML front-matter from markdown content.
    Returns (metadata, content) where metadata is a dict and content is a string.
    """
    fm_regex = r"^---\s*\n([\s\S]*?)\n---\s*\n"
    match = re.match(fm_regex, text)
    
    if not match:
        return {}, text
        
    metadata = {}
    lines = match.group(1).split("\n")
    for line in lines:
        if ":" in line:
            parts = line.split(":", 1)
            key = parts[0].strip()
            value = parts[1].strip()
            metadata[key] = value
            
    return metadata, text[match.end():]

def chunk_text(text, chunk_size=CONFIG["chunk_size"], overlap=CONFIG["chunk_overlap"]):
    """
    Split text into approximately equal-sized chunks with overlap.
    Uses whitespace-based tokenisation.
    """
    clean_text = text.replace("\r\n", "\n").strip()
    if not clean_text:
        return []
        
    words = clean_text.split()
    chunks = []
    
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
            
        start += chunk_size - overlap
        
        # Prevent infinite loop if overlap >= chunk_size
        if chunk_size - overlap <= 0:
            break
            
    return chunks

def process_document(text, filename):
    """
    Process a single document: parse front-matter, chunk, and return structured list.
    """
    metadata, content = parse_front_matter(text)
    
    title = metadata.get("title", filename)
    category = metadata.get("category", "General")
    doc_id = metadata.get("id", filename)
    
    chunks = chunk_text(content)
    
    processed_chunks = []
    for i, chunk in enumerate(chunks):
        processed_chunks.append({
            "docId": doc_id,
            "title": title,
            "category": category,
            "chunkIndex": i,
            "content": chunk
        })
        
    return processed_chunks
