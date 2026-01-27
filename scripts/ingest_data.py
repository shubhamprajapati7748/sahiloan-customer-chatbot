import sys

from sahiloan_chatbot import logger
from sahiloan_chatbot.application.ingest_documents_service import ingest_documents


def main():
    """Main entry point for document ingestion."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    data_path = sys.argv[1]

    # Optional: custom chunk size and overlap from command line
    chunk_size = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    chunk_overlap = int(sys.argv[3]) if len(sys.argv) > 3 else 200

    logger.info(f"Starting document ingestion from: {data_path}")
    logger.info(f"Chunk size: {chunk_size}, Overlap: {chunk_overlap}")

    try:
        ingest_documents(data_path=data_path, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        logger.info("Document ingestion completed successfully!")
    except Exception as e:
        logger.exception(f"Error during ingestion: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
