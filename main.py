from fastapi import FastAPI, Response, status
from routes.embed import router as embed_router
from routes.chat import router as chat_router
import google.generativeai as genai

from services.mongo import get_mongo_client
from services.config import Config
from services.embedding import embed_text
from services.llm import generate_chat_response
from services.vector_store import qdrant

app = FastAPI(title="Exempla AI")

app.include_router(embed_router, prefix="/embed", tags=["embedding"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])


@app.get("/")
def health_check():
    return {"message": "Exempla AI is taking over"}