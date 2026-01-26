"""
Document ingestion service for Pinecone.
Handles reading MD files, chunking, and upserting to Pinecone.
"""
import os
from pathlib import Path
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from sahiloan_chatbot.infrastructure.db import get_pinecone_index
from sahiloan_chatbot.config import settings
from sahiloan_chatbot import logger
import hashlib


class DocumentIngester:
    """Simple document ingester for markdown files."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        batch_size: int = 100
    ):
        """
        Initialize the document ingester.
        
        Args:
            chunk_size: Size of each text chunk in characters
            chunk_overlap: Overlap between chunks in characters
            batch_size: Number of vectors to upsert at once
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.batch_size = batch_size
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Initialize embeddings (dimensions must match Pinecone index)
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            dimensions=1024,
            api_key=settings.OPENAI_API_KEY.get_secret_value()
        )
        
        # Get Pinecone index
        self.index = get_pinecone_index()
        
        logger.info(f"DocumentIngester initialized | chunk_size: {chunk_size} | overlap: {chunk_overlap}")
    
    def read_markdown_file(self, file_path: Path) -> str:
        """Read a markdown file and return its content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return ""
    
    def chunk_text(self, text: str, metadata: Dict) -> List[Dict]:
        """
        Chunk text and prepare metadata.
        
        Args:
            text: Text to chunk
            metadata: Base metadata for the document
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        chunks = self.text_splitter.split_text(text)
        
        chunk_data = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk)
            }
            chunk_data.append({
                "text": chunk,
                "metadata": chunk_metadata
            })
        
        return chunk_data
    
    def chunk_faq_by_questions(self, text: str, metadata: Dict) -> List[Dict]:
        """
        Chunk FAQ text by question markers (###).
        Each chunk contains one complete Q&A pair.
        
        Args:
            text: FAQ markdown text
            metadata: Base metadata for the document
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        # Split on ### markers
        sections = text.split('###')
        
        chunk_data = []
        chunk_index = 0
        
        for section in sections:
            section = section.strip()
            if not section:  # Skip empty sections
                continue
            
            # Add back the ### marker for consistency
            chunk_text = f"### {section}"
            
            chunk_metadata = {
                **metadata,
                "chunk_index": chunk_index,
                "chunk_size": len(chunk_text),
                "chunking_strategy": "faq_question"
            }
            
            chunk_data.append({
                "text": chunk_text,
                "metadata": chunk_metadata
            })
            
            chunk_index += 1
        
        # Update total_chunks for all chunks
        for chunk in chunk_data:
            chunk["metadata"]["total_chunks"] = len(chunk_data)
        
        return chunk_data
    
    def generate_chunk_id(self, file_path: str, chunk_index: int) -> str:
        """Generate a unique ID for a chunk."""
        content = f"{file_path}_{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def upsert_chunks(self, chunks: List[Dict]):
        """
        Upsert chunks to Pinecone.
        
        Args:
            chunks: List of chunks with text and metadata
        """
        if not chunks:
            logger.warning("No chunks to upsert")
            return
        
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        
        # Prepare vectors for upsert
        vectors = []
        for chunk in chunks:
            # Generate embedding
            embedding = self.embeddings.embed_query(chunk["text"])
            
            # Generate unique ID
            chunk_id = self.generate_chunk_id(
                chunk["metadata"]["source"],
                chunk["metadata"]["chunk_index"]
            )
            
            vectors.append({
                "id": chunk_id,
                "values": embedding,
                "metadata": {
                    **chunk["metadata"],
                    "text": chunk["text"]  # Store text in metadata for retrieval
                }
            })
        
        # Upsert in batches
        logger.info(f"Upserting {len(vectors)} vectors to Pinecone...")
        for i in range(0, len(vectors), self.batch_size):
            batch = vectors[i:i + self.batch_size]
            self.index.upsert(vectors=batch)
            logger.info(f"Upserted batch {i//self.batch_size + 1}/{(len(vectors)-1)//self.batch_size + 1}")
        
        logger.info(f"Successfully upserted {len(vectors)} vectors")
    
    def ingest_file(self, file_path: Path):
        """
        Ingest a single markdown file.
        
        Args:
            file_path: Path to the markdown file
        """
        logger.info(f"Ingesting file: {file_path}")
        
        # Read file
        content = self.read_markdown_file(file_path)
        if not content:
            logger.warning(f"Skipping empty file: {file_path}")
            return
        
        # Prepare metadata
        metadata = {
            "source": str(file_path),
            "filename": file_path.name,
            "file_type": "markdown"
        }
        
        # Check if this is a FAQ file (contains ### markers and 'faq' in filename)
        is_faq = content.count('###') > 2 and 'faq' in file_path.name.lower()
        
        if is_faq:
            # Use FAQ-specific chunking (one Q&A per chunk)
            chunks = self.chunk_faq_by_questions(content, metadata)
            logger.info(f"Created {len(chunks)} FAQ question chunks from {file_path}")
        else:
            # Use default text chunking
            chunks = self.chunk_text(content, metadata)
            logger.info(f"Created {len(chunks)} text chunks from {file_path}")
        
        # Upsert to Pinecone
        self.upsert_chunks(chunks)
        
        logger.info(f"Successfully ingested {file_path}")
    
    def ingest_directory(self, directory_path: Path, pattern: str = "*.md"):
        """
        Ingest all markdown files from a directory.
        
        Args:
            directory_path: Path to the directory
            pattern: File pattern to match (default: *.md)
        """
        logger.info(f"Ingesting directory: {directory_path}")
        
        # Find all markdown files
        md_files = list(directory_path.glob(pattern))
        
        if not md_files:
            logger.warning(f"No files found matching pattern '{pattern}' in {directory_path}")
            return
        
        logger.info(f"Found {len(md_files)} markdown files")
        
        # Ingest each file
        for file_path in md_files:
            try:
                self.ingest_file(file_path)
            except Exception as e:
                logger.error(f"Error ingesting {file_path}: {e}")
                continue
        
        logger.info(f"Completed ingestion of {len(md_files)} files")


def ingest_documents(
    data_path: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    pattern: str = "*.md"
):
    """
    Convenience function to ingest documents.
    
    Args:
        data_path: Path to file or directory
        chunk_size: Size of each text chunk
        chunk_overlap: Overlap between chunks
        pattern: File pattern to match (for directories)
    """
    path = Path(data_path)
    
    ingester = DocumentIngester(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
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
