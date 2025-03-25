import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Mongo
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB = os.getenv("MONGO_DB", "infra_db")

    # Qdrant
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "infra_vectors")

    # Google
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_EMBED_MODEL = os.getenv("GOOGLE_EMBED_MODEL", "models/embedding-gecko-004")
    GOOGLE_CHAT_MODEL = os.getenv("GOOGLE_CHAT_MODEL", "models/gemini-pro")
