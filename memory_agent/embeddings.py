"""
embeddings.py
Optional semantic search upgrade using Gemini's free embedding model.
Falls back gracefully if API is unavailable - keyword search in memory_store.py
still works without this file at all.
"""

import json
import numpy as np
from google import genai
import config


def get_client():
    return genai.Client(api_key=config.GEMINI_API_KEY)


def embed_text(text):
    """Returns a vector (list of floats) for a piece of text using Gemini embeddings."""
    client = get_client()
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values


def cosine_similarity(vec_a, vec_b):
    a = np.array(vec_a)
    b = np.array(vec_b)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def search_memories_semantic(query, memories, limit=5):
    """
    memories: list of tuples (id, content, category, created_at, embedding_json)
    Only works for memories that already have an embedding stored.
    Returns top matches sorted by similarity.
    """
    query_vec = embed_text(query)

    scored = []
    for row in memories:
        mem_id, content, category, created_at, embedding_json = row
        if not embedding_json:
            continue
        mem_vec = json.loads(embedding_json)
        score = cosine_similarity(query_vec, mem_vec)
        scored.append((score, row))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [row for _, row in scored[:limit]]
