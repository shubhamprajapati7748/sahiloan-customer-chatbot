"""
Pinecone client configuration.
"""

from functools import lru_cache

from pinecone import Pinecone

from sahiloan_chatbot import settings


@lru_cache(maxsize=1)
def get_pinecone_client() -> Pinecone:
    """Get a cached Pinecone client instance."""
    return Pinecone(api_key=settings.PINECONE_API_KEY.get_secret_value())


@lru_cache(maxsize=1)
def get_pinecone_index():
    """Get the Pinecone index instance."""
    pc = get_pinecone_client()
    return pc.Index(settings.PINECONE_INDEX_NAME)
