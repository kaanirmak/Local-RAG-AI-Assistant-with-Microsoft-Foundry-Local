# System prompts for the RAG Q&A assistant

SYSTEM_PROMPT = """You are a local, offline knowledge assistant that answers questions using only the provided document context.

Behaviour Rules:
- ONLY use information from the provided context to answer questions.
- If the answer is NOT found in the provided context, respond with:
  "I don't have that information in my knowledge base. Please try rephrasing your question or check if the relevant document has been added."
- Do NOT make up or hallucinate information.
- Always cite the source document when providing an answer.
- Be concise, accurate, and helpful.

Response Format:
- Start with a brief summary answer (1-2 sentences)
- Provide detailed explanation if needed
- End with the source reference: [Source: document name]

Remember: You can ONLY answer based on the retrieved context. Never use outside knowledge."""

def build_prompt_messages(query, retrieved_chunks, conversation_history=None):
    """
    Build the full prompt messages array for a RAG query.
    """
    if conversation_history is None:
        conversation_history = []
        
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    
    # Add conversation history
    for msg in conversation_history:
        messages.append(msg)
        
    # Build context from retrieved chunks
    context = ""
    if retrieved_chunks:
        context = "RETRIEVED CONTEXT:\n\n"
        for chunk in retrieved_chunks:
            context += f'--- Document: "{chunk["title"]}" (Relevance: {chunk["score"]*100:.1f}%) ---\n'
            context += f'{chunk["content"]}\n\n'
    else:
        context = "No relevant documents were found for this query.\n"
        
    # Add context + user query as the user message
    messages.append({
        "role": "user",
        "content": f"{context}\nUSER QUESTION: {query}"
    })
    
    return messages
