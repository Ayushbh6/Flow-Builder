import os
import asyncio
import logging
import tiktoken
from openai import AsyncOpenAI
from openai import OpenAIError
from pinecone import Pinecone, ServerlessSpec
import backoff
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.document import Document
from app.core.config import settings

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Tiktoken Encoding
ENCODING_NAME = "cl100k_base"  # For tiktoken
ENCODING = tiktoken.get_encoding(ENCODING_NAME)

# Concurrency & batch sizes
CHUNK_BATCH_SIZE = 5
# Dynamically derive semaphores from rate limits (reqs/sec)
MAX_CONCURRENT_SUMMARIES = 3
MAX_CONCURRENT_EMBEDS = 3

# Semaphores for concurrency control
summary_concurrency_semaphore = asyncio.Semaphore(MAX_CONCURRENT_SUMMARIES)
embed_concurrency_semaphore = asyncio.Semaphore(MAX_CONCURRENT_EMBEDS)

# Prompts
DOCUMENT_CONTEXT_PROMPT = """
<document>
{doc_content}
</document>
"""

CHUNK_CONTEXT_PROMPT = """
Here is the chunk we want to situate within the whole document:
<chunk>
{chunk_content}
</chunk>

Please give a short, succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk.
Focus on what this specific chunk is about in relation to the entire document.
Answer only with the succinct context and nothing else.
"""

def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string using the global ENCODING."""
    return len(ENCODING.encode(string))

def chunk_markdown(text: str, max_tokens: int = 7000, overlap: int = 300):
    """Chunks markdown text into smaller pieces based on token count using the global ENCODING."""
    tokens = ENCODING.encode(text)
    chunks = []
    start = 0
    total_tokens = len(tokens)
    while start < total_tokens:
        end = min(start + max_tokens, total_tokens)
        chunk_tokens = tokens[start:end]
        chunk_text = ENCODING.decode(chunk_tokens)
        chunks.append(chunk_text)
        if end == total_tokens:
            break
        start = end - overlap # Recalculate start for the next chunk, considering overlap
    return chunks

@backoff.on_exception(backoff.expo,
                     OpenAIError,
                     max_tries=10,
                     max_time=300,
                     jitter=backoff.full_jitter)
async def generate_contextual_summary_async(client, doc_content: str, chunk_content: str) -> str:
    """Generate a summary for a chunk in the context of the full document using OpenAI."""
    async with summary_concurrency_semaphore:
        response = await client.chat.completions.create(
            model=settings.SUMMARY_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert at summarizing text chunks in the context of a larger document."},
                {"role": "user", "content": DOCUMENT_CONTEXT_PROMPT.format(doc_content=doc_content)},
                {"role": "user", "content": CHUNK_CONTEXT_PROMPT.format(chunk_content=chunk_content)}
            ],
            max_tokens=150,
            temperature=0.2
        )
        return response.choices[0].message.content.strip()

@backoff.on_exception(backoff.expo,
                     OpenAIError,
                     max_tries=8,
                     max_time=240,
                     jitter=backoff.full_jitter)
async def get_batch_embeddings_async(client, texts_for_embedding: List[str]) -> List[List[float]]:
    """Get embeddings for a batch of texts using OpenAI API."""
    if not texts_for_embedding:
        return []
    async with embed_concurrency_semaphore:
        response = await client.embeddings.create(
            input=texts_for_embedding,
            model=settings.EMBEDDING_MODEL
        )
        return [data.embedding for data in response.data]

async def prepare_document_chunks(document_id: int, db: Session):
    """
    Process a document from the database:
    1. Chunk the document content
    2. Generate contextual summaries
    3. Create embeddings
    4. Store in Pinecone
    """
    # Get document from database
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        logger.error(f"Document with ID {document_id} not found")
        return
    
    # Check if document has content
    if not document.content_text:
        logger.error(f"Document {document_id} has no content to process")
        return
    
    # Update document status
    document.status = "indexing"
    db.commit()
    
    try:
        # Initialize OpenAI client
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Initialize Pinecone
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        
        # Check if index exists, create if needed
        if settings.PINECONE_INDEX_NAME not in pc.list_indexes():
            logger.info(f"Creating Pinecone index {settings.PINECONE_INDEX_NAME}")
            pc.create_index(
                name=settings.PINECONE_INDEX_NAME,
                dimension=settings.EMBEDDING_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
        
        index = pc.Index(settings.PINECONE_INDEX_NAME)
        
        # Chunk the document
        full_text = document.content_text
        chunks = chunk_markdown(full_text)
        logger.info(f"Document {document_id} split into {len(chunks)} chunks")
        
        # Process chunks in batches to manage memory and concurrency
        for batch_start in range(0, len(chunks), CHUNK_BATCH_SIZE):
            batch = chunks[batch_start:batch_start + CHUNK_BATCH_SIZE]
            
            # Generate contextual summaries for each chunk
            summary_tasks = [
                generate_contextual_summary_async(client, full_text, chunk)
                for chunk in batch
            ]
            summaries = await asyncio.gather(*summary_tasks, return_exceptions=True)
            
            # Filter successful results
            successful_chunks = []
            successful_summaries = []
            
            for idx, result in enumerate(summaries):
                if isinstance(result, Exception):
                    logger.error(f"Chunk {batch_start + idx} of document {document_id} failed: {str(result)}")
                else:
                    successful_chunks.append(batch[idx])
                    successful_summaries.append(result)
            
            if not successful_chunks:
                logger.warning(f"All chunks failed in batch {batch_start}-{batch_start + len(batch) - 1}")
                continue
            
            # Prepare texts for embedding
            texts_for_embedding = [
                f"{chunk}\n\nContextual summary: {summary}"
                for chunk, summary in zip(successful_chunks, successful_summaries)
            ]
            
            # Generate embeddings
            try:
                embeddings = await get_batch_embeddings_async(client, texts_for_embedding)
            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch {batch_start}: {str(e)}")
                continue
            
            # Prepare vectors for Pinecone
            vectors = []
            for idx, (chunk, summary, embedding) in enumerate(
                zip(successful_chunks, successful_summaries, embeddings)
            ):
                vector_id = f"doc_{document_id}_chunk_{batch_start + idx}"
                metadata = {
                    "document_id": document_id,
                    "chunk_id": batch_start + idx,
                    "original_text": chunk[:1000],  # Limit metadata size
                    "contextual_summary": summary,
                    "source_file": document.filename
                }
                vectors.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata
                })
            
            # Upsert to Pinecone
            if vectors:
                try:
                    for i in range(0, len(vectors), 100):  # Pinecone batch limit
                        batch_vectors = vectors[i:i+100]
                        index.upsert(vectors=batch_vectors, namespace=settings.PINECONE_NAMESPACE)
                    logger.info(f"Uploaded {len(vectors)} vectors for document {document_id}")
                except Exception as e:
                    logger.error(f"Failed to upsert vectors to Pinecone: {str(e)}")
        
        # Update document status
        document.status = "indexed"
        db.commit()
        logger.info(f"Document {document_id} successfully indexed")
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        document.status = "error"
        document.error_message = str(e)
        db.commit()

async def index_document(document_id: int, db: Session):
    """
    Entry point to start the document indexing process.
    This should be called as a background task after document processing is complete.
    """
    try:
        # Ensure OpenAI API key is set
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set")
        
        # Ensure Pinecone API key is set
        if not settings.PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY is not set")
        
        await prepare_document_chunks(document_id, db)
    except Exception as e:
        logger.error(f"Failed to index document {document_id}: {str(e)}")
        # Update document status in the current session
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = "error"
            document.error_message = str(e)
            db.commit() 