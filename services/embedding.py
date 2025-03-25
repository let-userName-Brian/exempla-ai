import google.generativeai as genai
from typing import List
import time
from services.config import Config

cfg = Config()
_is_configured = False

# throttle to avoid rate limits....bastards
EMBED_THROTTLE_SECONDS = 0.1

def init_google_embeddings(api_key: str, model_name: str):
    global _is_configured
    if not _is_configured:
        genai.configure(api_key=api_key)
        _is_configured = True

def embed_text(text: str) -> List[float]:
    if not _is_configured:
        init_google_embeddings(cfg.GOOGLE_API_KEY, cfg.GOOGLE_EMBED_MODEL)

    max_retries = 3
    backoff = 1.0
    for attempt in range(max_retries):
        try:
            response = genai.embed_content(
                model=cfg.GOOGLE_EMBED_MODEL,
                content=text,
                task_type="retrieval_document"
            )
            embedding = response["embedding"]
            time.sleep(EMBED_THROTTLE_SECONDS)
            return embedding

        except Exception as e:
            error_str = str(e).lower()
            is_rate_limited = ("429" in error_str) or ("rate limit" in error_str)
            if is_rate_limited and attempt < max_retries - 1:
                print(f"Rate-limited or transient error. Retrying in {backoff}s. Error={e}")
                time.sleep(backoff)
                backoff *= 2
            else:
                print(f"Error in embed_text (attempt {attempt+1}/{max_retries}): {e}")
                if attempt >= max_retries - 1:
                    return [0.0]*768

def batch_embed_texts(texts: List[str]) -> List[List[float]]:
    """
    because 0.8.4's embed_content doesn't support multi-doc arrays, we do one doc at a time....
    we can still chunk them or parallelize at a higher level if we want.
    """
    if not texts:
        return []

    if not _is_configured:
        init_google_embeddings(cfg.GOOGLE_API_KEY, cfg.GOOGLE_EMBED_MODEL)

    results = []
    for text in texts:
        vec = embed_text(text)
        results.append(vec)
    return results
