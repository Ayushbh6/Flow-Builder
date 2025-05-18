import os
from llama_cloud_services import LlamaParse
from llama_index.core import SimpleDirectoryReader
import nest_asyncio
from dotenv import load_dotenv

load_dotenv()

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

LLAMA_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")


# Input and output directories
PDF_DIR = "/Users/aparajitbhattacharya/Library/CloudStorage/OneDrive-Personal/MyDocuments/AI/IASPIS_AND_SCALING_UP"
MD_DIR = os.path.join(PDF_DIR, "md")

# Create MD_DIR if it doesn't exist
os.makedirs(MD_DIR, exist_ok=True)

# Set up the LlamaParse extractor
parser = LlamaParse(
    api_key=LLAMA_API_KEY,
    result_type="markdown",
    verbose=False  # Set to True for more detailed logs
)

# List all PDF files in the directory
pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf')]

print(f"Found {len(pdf_files)} PDF files to process")

# Process each PDF file
for pdf_file in pdf_files:
    pdf_path = os.path.join(PDF_DIR, pdf_file)
    md_file = os.path.splitext(pdf_file)[0] + ".md"
    md_path = os.path.join(MD_DIR, md_file)
    
    print(f"Processing: {pdf_file} -> {md_file}")
    
    try:
        # Use SimpleDirectoryReader with specific_files parameter
        file_extractor = {".pdf": parser}
        documents = SimpleDirectoryReader(
            input_files=[pdf_path],
            file_extractor=file_extractor
        ).load_data()
        
        print(f"Successfully parsed {pdf_file} into {len(documents)} document chunks")
        
        # Combine all document chunks into a single markdown file
        with open(md_path, 'w', encoding='utf-8') as md_file:
            for i, doc in enumerate(documents):
                # Add page separator between documents
                if i > 0:
                    md_file.write("\n\n<!-- Page Break -->\n\n")
                
                # Write the document content
                md_file.write(doc.text)
        
        print(f"Created markdown file: {md_path}")
        
    except Exception as e:
        print(f"Failed to process {pdf_file} with error: {e}")

print("Processing complete!")