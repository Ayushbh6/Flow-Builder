# FlowBot Builder MVP

A no-code, flow-based web application that empowers users to create intelligent chatbots trained on their documents. This MVP provides a visual interface for creating a functioning RAG (Retrieval Augmented Generation) chatbot with just a few clicks.

## Features

- **Visual Flow Builder**: Drag-and-drop interface to connect AI components
- **Text Extraction**: Upload and process PDF documents
- **Knowledge Base Creation**: Chunk text and create embeddings
- **Chatbot Configuration**: Configure and test RAG-powered chatbots

## Architecture

- **Backend**: Python FastAPI
- **Frontend**: React with TailwindCSS
- **Database**: SQLite for MVP simplicity

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- OpenAI API key
- Pinecone API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/flowbot-builder.git
cd flowbot-builder
```

2. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Create a `.env` file in the backend directory:
```
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX=your_pinecone_index_name
```

4. Run the backend server:
```bash
uvicorn app.main:app --reload
```

5. Set up the frontend:
```bash
cd ../frontend
npm install
```

6. Create a `.env.local` file in the frontend directory:
```
REACT_APP_API_URL=http://localhost:8000
```

7. Run the frontend:
```bash
npm start
```

8. Open [http://localhost:3000](http://localhost:3000) in your browser to use the application.

## Usage Guide

### Creating a New ChatBot

1. From the dashboard, click "Create New Flow"
2. In the Flow Builder, add the following components:
   - Text Extractor
   - Knowledge Base
   - Chatbot
3. Connect the components in sequence
4. Configure each component:
   - Text Extractor: Upload your PDF document
   - Knowledge Base: Set pinecone parameters for index and namespace
   - Chatbot: Configure model settings
5. Test your chatbot using the chat interface
6. Save your flow for future use

### Component Configuration

#### Text Extractor
- Accepts PDF files
- Configure extraction settings like page range

#### Knowledge Base
- Uses Pinecone for vector storage
- Users can opt to create a new pinecone index and/or namespace or use an existing one
- Uses OpenAI embeddings

#### Chatbot
- Select model (e.g., GPT-4.1)
- Configure temperature, max tokens
- Customize system prompt

## Project Structure

The project is divided into two main parts:
- `backend/`: Python FastAPI server that handles document processing, embeddings, and chat functionality
- `frontend/`: React application for the user interface and flow builder

See `project_structure.md` for detailed structure.

## Limitations

This MVP has the following limitations:
- Supports PDF files only
- Limited deployment options (local only)
- Basic UI with minimal styling

## Next Steps

After the MVP:
- Support for more document types (DOCX, TXT)
- Enhanced flow builder capabilities
- User authentication
- Deployment options (share URL, embed widget)
- Additional vector database options

## License

MIT 