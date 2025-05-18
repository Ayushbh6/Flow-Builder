# FlowBot Builder MVP

A no-code, flow-based web application that empowers users to create intelligent chatbots trained on their documents. This MVP provides a visual interface for creating a functioning RAG (Retrieval Augmented Generation) chatbot with just a few clicks.

## Features

- **Visual Flow Builder**: Drag-and-drop interface to connect AI components
- **Text Extraction**: Upload and process PDF documents
- **Knowledge Base Creation**: Chunk text and create embeddings
- **Chatbot Configuration**: Configure and test RAG-powered chatbots

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- OpenAI API key
- Pinecone API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/flowbot-builder.git
cd flowbot-builder
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env.local` file in the root directory:
```
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX=your_pinecone_index_name
```

4. Run the development server:
```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser to use the application.

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
   - Knowledge Base: Set chunking parameters
   - Chatbot: Configure model settings
5. Test your chatbot using the chat interface
6. Save your flow for future use

### Component Configuration

#### Text Extractor
- Accepts PDF files
- Configure extraction settings like page range

#### Knowledge Base
- Set chunk size and overlap
- Uses Pinecone for vector storage
- Uses OpenAI embeddings

#### Chatbot
- Select model (e.g., GPT-3.5-turbo)
- Configure temperature, max tokens
- Customize system prompt

## Project Structure

The project follows a standard Next.js application structure with React components for the UI and API routes for backend functionality. See `project_structure.md` for details.

## Development Plan

See `mvp_plan.md` for the detailed development plan and implementation timeline.

## Dependencies

Major dependencies include:
- Next.js for the application framework
- React Flow for the visual builder
- Langchain.js for RAG implementation
- PDF.js for PDF processing

For a complete list, see `dependencies.md`.

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