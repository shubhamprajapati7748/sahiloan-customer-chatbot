"""Document ingestion service."""

from .ingest_documents import ingest_documents
from .pinecode_ingester import PineconeIngester

__all__ = ["PineconeIngester", "ingest_documents"]
