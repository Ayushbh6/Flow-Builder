import os
import tempfile
from typing import Optional
from sqlalchemy.orm import Session
from llama_cloud_services import LlamaParse
from llama_index.core import SimpleDirectoryReader
import nest_asyncio
import asyncio
from app.db.session import SessionLocal
from app.models.document import Document
from app.core.config import settings
from .knowledge_service import index_document

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

async def process_document(document_id: int):
    """
    Process document and extract text using LlamaParse for PDFs
    """
    # Create new DB session (since we're in a background task)
    db = SessionLocal()
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            print(f"Document with ID {document_id} not found")
            return
        
        # Update document status
        document.status = "processing"
        db.commit()
        
        try:
            # Extract text based on file type
            extracted_text = extract_text_from_file(document.file_path, document.file_type)
            
            # Update document with extracted text
            document.content_text = extracted_text
            document.status = "processed"
            db.commit()
            
            print(f"Successfully processed document {document_id}")
            
            # Start knowledge base indexing if API keys are set
            if settings.OPENAI_API_KEY and settings.PINECONE_API_KEY:
                # Schedule the indexing as a background task
                asyncio.create_task(index_document(document_id, db))
            else:
                print("Skipping knowledge base indexing: API keys not configured")
                
        except Exception as e:
            # Handle processing error
            document.status = "error"
            document.error_message = str(e)
            db.commit()
            print(f"Error processing document {document_id}: {str(e)}")
    
    finally:
        db.close()

def extract_text_from_file(file_path: str, file_type: str) -> str:
    """
    Extract text from a file based on its type
    """
    if file_type == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_type == "docx":
        return extract_text_from_docx(file_path)
    elif file_type == "txt":
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF using LlamaParse via llama-index
    """
    # Check if we have a LlamaParse API key
    if not settings.LLAMA_CLOUD_API_KEY:
        raise ValueError("LLAMA_CLOUD_API_KEY not set. Please provide a valid API key.")
    
    try:
        # Set up the LlamaParse extractor
        parser = LlamaParse(
            api_key=settings.LLAMA_CLOUD_API_KEY,
            result_type="markdown",
            verbose=False
        )
        
        # Use SimpleDirectoryReader with file_extractor
        file_extractor = {".pdf": parser}
        documents = SimpleDirectoryReader(
            input_files=[file_path],
            file_extractor=file_extractor
        ).load_data()
        
        # Combine all document chunks
        extracted_text = "\n\n<!-- Page Break -->\n\n".join([doc.text for doc in documents])
        return extracted_text
    except Exception as e:
        # Log the error
        print(f"Error using LlamaParse: {str(e)}")
        
        # Fallback to PyPDF2 if LlamaParse fails
        import PyPDF2
        
        try:
            text = ""
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n\n<!-- Page Break -->\n\n"
            return text
        except Exception as e2:
            raise Exception(f"Failed to extract text from PDF: {str(e2)}")

def extract_text_from_docx(file_path: str) -> str:
    """
    Extract text from DOCX file
    """
    try:
        import docx
        doc = docx.Document(file_path)
        paragraphs = [paragraph.text for paragraph in doc.paragraphs]
        # Filter out empty paragraphs and join with newlines
        text = "\n".join(p for p in paragraphs if p.strip())
        return text
    except Exception as e:
        raise Exception(f"Failed to extract text from DOCX: {str(e)}")

def extract_text_from_txt(file_path: str) -> str:
    """
    Extract text from TXT file
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except UnicodeDecodeError:
        # Try with a different encoding if UTF-8 fails
        with open(file_path, "r", encoding="latin-1") as file:
            return file.read()
    except Exception as e:
        raise Exception(f"Failed to extract text from TXT: {str(e)}") 