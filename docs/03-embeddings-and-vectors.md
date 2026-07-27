---
title: Embeddings and Vector Search
category: Concepts
id: doc-embeddings
---

# Understanding Embeddings and Vector Search

Text embeddings are numerical vector representations of text that capture semantic meaning. They are fundamental to how RAG systems retrieve relevant documents.

## What Are Embeddings?

An embedding is a list of numbers (a vector) that represents the meaning of a piece of text. When two pieces of text have similar meanings, their embeddings will be close together in the vector space.

For example:
- "The cat sat on the mat" and "A kitten rested on the rug" would have similar embeddings
- "The cat sat on the mat" and "Stock prices rose today" would have very different embeddings

## How Vector Search Works

1. **Indexing Phase**: Each document chunk is converted into an embedding vector and stored in a database
2. **Query Phase**: The user's question is also converted into an embedding vector
3. **Similarity Computation**: The system computes the similarity between the query vector and all stored vectors
4. **Ranking**: Results are ranked by similarity score, and the top-K most similar chunks are returned

## Similarity Metrics

### Cosine Similarity
The most common metric for text embeddings. It measures the cosine of the angle between two vectors:
- Score of 1.0 = identical direction (very similar)
- Score of 0.0 = perpendicular (unrelated)
- Score of -1.0 = opposite direction (opposite meaning)

### TF-IDF (Term Frequency–Inverse Document Frequency)
A simpler, keyword-based approach that:
- Counts how often each word appears in a document (Term Frequency)
- Weighs words by how rare they are across all documents (Inverse Document Frequency)
- Common words like "the" get low weights; distinctive words get high weights

TF-IDF is computationally cheap, fully offline, and works well for domain-specific document collections where keyword overlap is reliable.

## Choosing Between Embedding Models and TF-IDF

| Feature | Neural Embeddings | TF-IDF |
|---------|------------------|--------|
| Semantic understanding | High | Low |
| Speed | Slower (model inference) | Very fast (math only) |
| Offline capability | Requires embedding model | Fully offline |
| Domain specificity | Good for general queries | Good for keyword-rich domains |
| Transparency | Black box | Inspectable vocabulary |

For small-to-medium document collections with domain-specific vocabulary, TF-IDF is often sufficient and keeps the architecture simple.
