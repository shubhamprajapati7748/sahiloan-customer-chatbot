from pathlib import Path

from sahiloan_chatbot import logger
from sahiloan_chatbot.application.ingest_documents_service.pinecode_ingester import PineconeIngester


def ingest_documents(data_path: str, chunk_size: int = 1000, chunk_overlap: int = 200, pattern: str = "*.md"):
    """
    Convenience function to ingest documents.

    Args:
        data_path: Path to file or directory
        chunk_size: Size of each text chunk
        chunk_overlap: Overlap between chunks
        pattern: File pattern to match (for directories)
    """
    path = Path(data_path)

    ingester = PineconeIngester(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    if path.is_file():
        ingester.ingest_file(path)
    elif path.is_dir():
        ingester.ingest_directory(path, pattern=pattern)
    else:
        logger.error(f"Invalid path: {data_path}")


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ingest.py <path_to_data>")
        sys.exit(1)

    data_path = sys.argv[1]
    ingest_documents(data_path)
