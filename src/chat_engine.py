# RAG pipeline orchestration — retrieval + generation
import json
import logging
from src.config import CONFIG
from src.prompts import build_prompt_messages

logger = logging.getLogger("chat_engine")

class ChatEngine:
    def __init__(self, vector_store, model_client=None, model_id=None):
        self.vector_store = vector_store
        self.model_client = model_client
        self.model_id = model_id or CONFIG["model"]
        self.conversation_history = []

    def chat(self, query):
        """
        Process a user query through the RAG pipeline.
        Yields dictionaries representing RAG pipeline events (token, sources, done).
        """
        # Step 1: Retrieve relevant chunks
        retrieved_chunks = self.vector_store.search(query, CONFIG["top_k"])

        # Step 2: Build prompt messages
        messages = build_prompt_messages(
            query,
            retrieved_chunks,
            self.conversation_history[-CONFIG["max_conversation_history"]:]
        )

        # Step 3: Generate response via Foundry Local
        full_response = ""

        try:
            if self.model_client is not None:
                # Use standard openai client stream
                response = self.model_client.chat.completions.create(
                    model=self.model_id,
                    messages=messages,
                    stream=True
                )
                for chunk in response:
                    content = chunk.choices[0].delta.content or ""
                    if content:
                        full_response += content
                        yield {
                            "type": "token",
                            "content": content
                        }
            else:
                # Fallback response if no model client is initialized
                full_response = (
                    "⚠️ **Fallback Mode**: Foundry Local model is not initialized or running. "
                    "The retrieval pipeline works successfully — relevant document chunks were found. "
                    "Ensure you install Microsoft Foundry Local and restart the server to get full AI answers."
                )
                yield {
                    "type": "token",
                    "content": full_response
                }
        except Exception as e:
            logger.error(f"Model inference error: {e}", exc_info=True)
            full_response = "An error occurred while generating the response. Please try again."
            yield {
                "type": "token",
                "content": full_response
            }

        # Step 4: Update conversation history
        self.conversation_history.append({"role": "user", "content": query})
        self.conversation_history.append({"role": "assistant", "content": full_response})

        # Trim history
        max_len = CONFIG["max_conversation_history"] * 2
        if len(self.conversation_history) > max_len:
            self.conversation_history = self.conversation_history[-max_len:]

        # Step 5: Yield sources
        sources_list = []
        for chunk in retrieved_chunks:
            sources_list.append({
                "title": chunk["title"],
                "docId": chunk["docId"],
                "score": chunk["score"],
                "preview": chunk["content"][:150] + "..."
            })

        yield {
            "type": "sources",
            "sources": sources_list
        }

        yield {"type": "done"}

    def clear_history(self):
        self.conversation_history = []
