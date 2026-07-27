# Document ingestion script — reads docs/ folder, chunks, and indexes into SQLite
import os
import sys
from src.vector_store import VectorStore
from src.chunker import process_document
from src.config import CONFIG

def read_pdf(file_path):
    """
    Extract text content from a PDF file using PyMuPDF.
    Returns the full text as a string.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("⚠️  PyMuPDF not installed. Run: pip install PyMuPDF")
        return None

    text_parts = []
    with fitz.open(file_path) as doc:
        for page_num, page in enumerate(doc):
            page_text = page.get_text("text")
            if page_text.strip():
                text_parts.append(page_text)

    return "\n\n".join(text_parts)

def ingest():
    docs_path = CONFIG["docs_dir"]
    
    if not os.path.exists(docs_path):
        print(f"❌ Documents directory not found: {docs_path}")
        print("   Create a 'docs/' folder and add .md, .txt, or .pdf files.")
        sys.exit(1)
        
    files = [f for f in os.listdir(docs_path) if f.lower().endswith(('.md', '.txt', '.pdf'))]
    
    if not files:
        print("❌ No .md, .txt, or .pdf files found in docs/ folder.")
        sys.exit(1)
        
    print("🔄 Starting document ingestion...\n")
    print(f"📂 Found {len(files)} document(s) in {docs_path}/\n")
    
    # Initialize vector store and clear existing data
    store = VectorStore(CONFIG["db_file"])
    store.clear()
    
    total_chunks = 0
    
    for file in files:
        file_path = os.path.join(docs_path, file)
        ext = os.path.splitext(file.lower())[1]

        if ext == ".pdf":
            content = read_pdf(file_path)
            if content is None:
                print(f"  ⚠️  {file} → skipped (PyMuPDF not available)")
                continue
            if not content.strip():
                print(f"  ⚠️  {file} → skipped (no extractable text)")
                continue
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
        chunks = process_document(content, file)
        store.add_chunks(chunks)
        total_chunks += len(chunks)
        
        print(f"  ✅ {file} → {len(chunks)} chunk(s)")
        
    print(f"\n📊 Total: {total_chunks} chunks from {len(files)} document(s)")
    print(f"💾 Saved to: {CONFIG['db_file']}")
    print("\n✨ Ingestion complete! Run 'python src/server.py' to launch the assistant.\n")

if __name__ == "__main__":
    ingest()
