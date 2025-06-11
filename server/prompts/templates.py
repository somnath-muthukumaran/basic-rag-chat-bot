

def generate_rag_prompt(question: str, context_chunks: list) -> str:
    context = "\n\n".join(context_chunks)
    prompt = f"""You are a helpful document assistant. Answer questions based on the provided context accurately and informatively.

CONTEXT:
{context}

QUESTION: {question}

INSTRUCTIONS:
- Answer based primarily on the provided context
- Provide complete, informative answers (2-4 sentences for most questions)
- For "who" questions: Include the person's name, role, and key details from the context
- For "what" questions: Explain the concept, event, or object with relevant details
- For "where/when" questions: Provide specific locations and timeframes when available
- Use direct quotes when they help clarify or support your answer
- If information is missing from the context, state: "The provided documents don't contain information about [specific aspect]"
- Keep responses focused but comprehensive enough to be useful

Answer the question thoroughly using the available context:"""
    return prompt
