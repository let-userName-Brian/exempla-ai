from fastapi import APIRouter, Body
from services.embedding import embed_text
from services.vector_store import search_vectors
from services.llm import generate_chat_response
from typing import Dict

router = APIRouter()


@router.post("/")
def chat_with_dataset(
    dataset_id: int = Body(...),
    user_prompt: str = Body(...),
    filter_options: Dict = Body({}),
    top_k: int = Body(5),
):
    """
    1. Embed user prompt.
    2. Search top_k docs in Qdrant filtered by dataset_id.
    3. Call Google LLM with context + filter_options + user prompt.
    4. Return LLM response (which might suggest filters or more Qs).
    """

    query_vector = embed_text(user_prompt)
    docs = search_vectors(query_vector, dataset_id=dataset_id, top_k=top_k)

    # Log what we got from the vector store
    print(f"Retrieved {len(docs)} documents from vector store")
    for i, doc in enumerate(docs):
        print(f"Document {i+1} - Score: {doc.get('score')}")
        print(f"  Content length: {len(doc.get('content', ''))}")
        print(f"  Metadata keys: {list(doc.get('metadata', {}).keys())}")


    # docs is a list of nearest matches with metadata
    response_text = generate_chat_response(user_prompt, docs, filter_options)
    return {"response": response_text}
