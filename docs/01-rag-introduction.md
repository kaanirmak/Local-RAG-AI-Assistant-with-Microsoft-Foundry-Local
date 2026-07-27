---
title: Introduction to RAG
category: Concepts
id: doc-rag-intro
---

# What is Retrieval-Augmented Generation (RAG)?

Retrieval-Augmented Generation (RAG) is an AI design pattern that enhances a language model's responses by grounding them in your own data. Instead of relying solely on the model's pre-trained knowledge, RAG retrieves relevant information from a document collection and injects it into the prompt.

## How RAG Works

The RAG process follows three key steps:

1. **Retrieve**: When a user asks a question, the system searches a knowledge base (vector store) for the most relevant document chunks. This uses semantic similarity or keyword matching to find passages that are likely to contain the answer.

2. **Augment**: The retrieved chunks are added to the model's prompt as context. This gives the model access to specific, up-to-date information that it may not have seen during training.

3. **Generate**: The language model generates a response based on both the user's question and the retrieved context. Because the model has access to relevant source material, its answers are more accurate and grounded.

## Benefits of RAG

- **Reduced Hallucination**: By grounding responses in actual documents, RAG significantly reduces the chance of the model making up information.
- **Source Attribution**: RAG enables citing specific documents or passages that informed the answer.
- **Up-to-date Information**: Unlike static model training, RAG can incorporate newly added documents immediately.
- **Domain Specificity**: RAG allows a general-purpose model to answer domain-specific questions accurately.
- **Privacy**: When combined with local inference (like Foundry Local), all data stays on-device.

## RAG vs. Fine-Tuning

While fine-tuning permanently modifies a model's weights, RAG dynamically provides context at query time. RAG is often preferred because it requires no expensive retraining, works with any base model, and allows easy updates to the knowledge base.
