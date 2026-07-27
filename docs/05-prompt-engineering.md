---
title: Prompt Engineering for Q&A
category: Concepts
id: doc-prompt-engineering
---

# Prompt Engineering for Q&A Tasks

Crafting effective prompts is essential for getting accurate, grounded responses from a language model in a RAG system. The way you present retrieved context and frame the question directly impacts the quality of answers.

## System Prompts

A system prompt defines the model's behavior, role, and constraints. For a Q&A RAG assistant, key elements include:

### Role Definition
Tell the model exactly what it is and what it should do:
"You are a local, offline knowledge assistant that answers questions using only the provided document context."

### Grounding Instructions
Prevent hallucination by explicitly constraining the model:
"ONLY use information from the provided context to answer questions. Do NOT make up or hallucinate information."

### Fallback Behavior
Define what happens when the answer isn't in the context:
"If the answer is NOT found in the provided context, respond with: 'I don't have that information in my knowledge base.'"

### Source Citation
Encourage traceability:
"Always cite the source document when providing an answer."

## User Prompts

The user prompt typically combines retrieved context with the actual question:

```
RETRIEVED CONTEXT:
--- Document: "Safety Procedures" (Relevance: 85.2%) ---
Always wear protective equipment when...

USER QUESTION: What safety equipment is needed?
```

## Best Practices

1. **Be Specific**: Vague instructions lead to vague answers. "Answer concisely in 2-3 sentences" is better than "be brief."

2. **Separate Context from Question**: Clearly delineate where the context ends and the question begins using markers or formatting.

3. **Include Relevance Scores**: Showing relevance percentages helps the model weight sources appropriately.

4. **Limit Context Size**: Providing too much context can confuse the model. Retrieve only the top 2-3 most relevant chunks.

5. **Use Response Templates**: Suggest a structure for the response (summary → details → sources) to get consistent formatting.

6. **Iterate and Test**: Prompt engineering is empirical. Test with various question types and refine based on results.

## Common Pitfalls

- **Over-stuffing context**: Including too many chunks dilutes relevance
- **Missing guardrails**: Without explicit constraints, models may hallucinate
- **Ignoring edge cases**: Empty queries, out-of-scope questions, and adversarial inputs need handling
- **Static prompts**: As your document collection evolves, your prompts may need updating too
