import google.generativeai as genai
from services.config import Config

cfg = Config()
genai.configure(api_key=cfg.GOOGLE_API_KEY)
_model = None


def get_model():
    global _model
    if _model is None:
        _model = genai.GenerativeModel(cfg.GOOGLE_CHAT_MODEL)
    return _model


def generate_chat_response(user_prompt, docs, filter_options):
    context_text = "Here are some relevant documents from the dataset:\n\n"

    for i, doc in enumerate(docs):
        context_text += f"\n--- Document {i+1} ---\n"

        if "metadata" in doc:
            metadata = doc["metadata"]
            context_text += "Metadata:\n"
            for key, value in metadata.items():
                context_text += f"- {key}: {value}\n"

        if doc.get("content"):
            context_text += f"\nContent:\n{doc['content']}\n"

        if doc.get("score"):
            context_text += f"\nRelevance score: {doc['score']:.4f}\n"

    filter_text = ""
    if filter_options:
        filter_text = f"\nThe user has applied these filters: {filter_options}"

    prompt = f"""
    You are an AI assistant helping with infrastructure data analysis.
    
    {context_text}
    {filter_text}
    
    User question: {user_prompt}
    
    Please provide a helpful response based on the information above. If the information needed to answer the question is not available in the documents, explain what information is missing.
    """
    
    print(f"LLM PROMPT:\n{prompt}")
    response = call_llm(prompt)
    return response


def call_llm(prompt):
    try:
        model = get_model()
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error calling LLM: {str(e)}")
        return f"Sorry, I encountered an error: {str(e)}"
