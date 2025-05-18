import os
import json
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from openai import OpenAI, AsyncOpenAI
from pinecone import Pinecone

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Default values
DEFAULT_TOP_K = 9  # Number of chunks to retrieve
DEFAULT_TOP_RERANKED = 4  # Number of chunks to keep after reranking
MAX_TOOL_CALLS = 4  # Maximum number of sequential tool calls

class ChatbotService:
    """
    Service for handling chatbot functionality with RAG (Retrieval Augmented Generation)
    """
    
    def __init__(self):
        """Initialize the chatbot service with API clients"""
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.async_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate an embedding for the given text using OpenAI's embedding model"""
        response = self.client.embeddings.create(
            input=text,
            model=settings.EMBEDDING_MODEL
        )
        return response.data[0].embedding
    
    def vector_search(
        self, 
        query: str, 
        top_k: int = DEFAULT_TOP_K,
        top_reranked: int = DEFAULT_TOP_RERANKED
    ) -> str:
        """
        Search for relevant chunks in Pinecone based on the query
        Returns formatted string with top results
        """
        try:
            # Get embedding for the query
            query_embedding = self.get_embedding(query)
            
            # Connect to Pinecone index
            index = self.pc.Index(settings.PINECONE_INDEX_NAME)
            
            # Query the index
            query_response = index.query(
                namespace=settings.PINECONE_NAMESPACE,
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                include_values=False
            )
            
            # Prepare documents for reranking
            documents = []
            doc_mapping = {}
            
            for i, match in enumerate(query_response.matches):
                chunk_id = match.id
                metadata = match.metadata or {}
                
                # Extract content for reranking (prefer contextual summary)
                contextual_summary = metadata.get("contextual_summary", "")
                doc_text = contextual_summary if contextual_summary else metadata.get("original_text", "")
                
                documents.append(doc_text)
                doc_mapping[doc_text] = match
            
            # Apply reranking if documents were found
            if documents:
                reranked_results = self.pc.inference.rerank(
                    model="cohere-rerank-3.5",
                    query=query,
                    documents=documents,
                    top_n=top_reranked,
                    return_documents=True
                )
                
                # Format results from reranked matches
                results = []
                for i, reranked in enumerate(reranked_results.data):
                    # Get the original match using the mapping
                    original_match = doc_mapping[reranked.document.text]
                    
                    # Extract metadata
                    chunk_id = original_match.id
                    score = reranked.score
                    metadata = original_match.metadata or {}
                    
                    source_file = metadata.get("source_file", "")
                    original_text = metadata.get("original_text", "")
                    contextual_summary = metadata.get("contextual_summary", "")
                    document_id = metadata.get("document_id", "")
                    
                    # Format the chunk for LLM context
                    chunk_text = f"{i+1}\n\n"
                    chunk_text += f"ID: {chunk_id}\n"
                    chunk_text += f"Document: {source_file} (ID: {document_id})\n"
                    chunk_text += f"Contextual summary: {contextual_summary}\n"
                    chunk_text += f"Content: {original_text[:1000]}...\n"  # Truncate long content
                    
                    results.append(chunk_text)
                
                # Combine all chunks
                return "\n".join(results)
            else:
                return "No relevant information found in the knowledge base."
                
        except Exception as e:
            logger.error(f"Error in vector search: {str(e)}")
            return f"Error performing search: {str(e)}"
    
    def create_rag_tools(self):
        """Create tool definition for RAG search function calling"""
        return [{
            "type": "function",
            "name": "retrieve_knowledge",
            "description": f"Search the knowledge base for relevant information based on a user query. This tool retrieves the most relevant information from the {settings.PINECONE_INDEX_NAME} index.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string", 
                        "description": "The search query to find relevant information in the knowledge base."
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            },
            "strict": True
        }]
    
    def create_system_prompt(self, assistant_name: str = "FlowBot Assistant"):
        """Create system prompt for the chatbot"""
        return (
            f"# Identity\n"
            f"You are {assistant_name}, an AI assistant that retrieves relevant information from the knowledge base.\n\n"
            "# Instructions\n"
            "## PERSISTENCE\n"
            "You are an agent—keep working until the user's query is fully resolved. Only stop when you're sure the problem is solved.\n"
            "## TOOL CALLING\n"
            "Use the retrieve_knowledge function to fetch relevant information from the knowledge base. Do NOT guess or hallucinate results."
            " If you need clarification to call the tool, ask the user.\n"
            "## PLANNING\n"
            "Plan extensively: decide whether to call the function, reflect on results, then finalize the answer.\n"
            "## LANGUAGE\n"
            "Users will ask questions in English, and you should respond in English.\n"
        )
    
    async def process_chat(
        self, 
        history: List[Dict[str, str]], 
        query: str
    ) -> AsyncGenerator[str, None]:
        """
        Process a chat message with RAG, using streaming response
        
        Args:
            history: List of conversation history (user/assistant messages)
            query: Current user query
            
        Returns:
            Async generator that yields content chunks as they're received
        """
        # Initialize message history with system prompt
        messages = [{"role": "system", "content": self.create_system_prompt()}]
        
        # Include the last 8 exchanges (if available)
        for turn in history[-8:]:
            messages.append({"role": "user", "content": turn["user"]})
            messages.append({"role": "assistant", "content": turn["assistant"]})
        
        # Add current user query
        messages.append({"role": "user", "content": query})
        
        # Get tools for RAG function calling
        tools = self.create_rag_tools()
        
        # Process tool calls first (non-streaming)
        tool_calls = 0
        final_messages = messages.copy()
        
        while tool_calls < MAX_TOOL_CALLS:
            # Send to LLM with function schema
            response = self.client.responses.create(
                model=settings.COMPLETION_MODEL,
                input=messages,
                tools=tools
            )
            
            # Check for function call
            func_call = next((item for item in response.output if item.type == "function_call"), None)
            if not func_call:
                # No more function calls needed
                break
            
            # Execute the function
            logger.info(f"Executing knowledge retrieval: {func_call.arguments}")
            args = json.loads(func_call.arguments)
            
            # Call vector search
            result = self.vector_search(args.get("query"))
            
            # Append function call and result to messages
            function_call_msg = {
                "type": "function_call",
                "name": func_call.name,
                "call_id": func_call.call_id,
                "arguments": func_call.arguments
            }
            function_output_msg = {
                "type": "function_call_output",
                "call_id": func_call.call_id,
                "output": result
            }
            
            messages.append(function_call_msg)
            messages.append(function_output_msg)
            final_messages.append(function_call_msg)
            final_messages.append(function_output_msg)
            
            tool_calls += 1
            if tool_calls >= MAX_TOOL_CALLS:
                break
        
        # Stream the final response
        try:
            stream = await self.async_client.responses.create(
                model=settings.COMPLETION_MODEL,
                input=final_messages,
                tools=tools,
                stream=True
            )
            
            content_received = False
            
            async for event in stream:
                if event.type == "response.output_text.delta":
                    content_received = True
                    yield event.delta
                elif event.type == "text_delta":
                    content_received = True
                    yield event.delta
                elif event.type == "content_part_added":
                    if event.content_part.type == "text":
                        content_received = True
                        yield event.content_part.text
            
            # If no content was streamed, return a fallback message
            if not content_received:
                fallback_resp = self.client.responses.create(
                    model=settings.COMPLETION_MODEL,
                    input=final_messages,
                    tools=tools
                )
                yield fallback_resp.output_text or "I'm sorry, I couldn't generate a response. Please try again."
        
        except Exception as e:
            logger.error(f"Error in streaming response: {str(e)}")
            yield f"I'm sorry, an error occurred while processing your request: {str(e)}"
    
    def chat(self, history: List[Dict[str, str]], query: str) -> str:
        """
        Non-streaming version of the chat function
        
        Args:
            history: List of conversation history (user/assistant messages)
            query: Current user query
            
        Returns:
            Complete response as a string
        """
        # Initialize message history with system prompt
        messages = [{"role": "system", "content": self.create_system_prompt()}]
        
        # Include the last 8 exchanges (if available)
        for turn in history[-8:]:
            messages.append({"role": "user", "content": turn["user"]})
            messages.append({"role": "assistant", "content": turn["assistant"]})
        
        # Add current user query
        messages.append({"role": "user", "content": query})
        
        # Get tools for RAG function calling
        tools = self.create_rag_tools()
        
        # Process tool calls
        tool_calls = 0
        final_response = None
        
        while tool_calls < MAX_TOOL_CALLS:
            # Send to LLM with function schema
            response = self.client.responses.create(
                model=settings.COMPLETION_MODEL,
                input=messages,
                tools=tools
            )
            
            # Check for function call
            func_call = next((item for item in response.output if item.type == "function_call"), None)
            if not func_call:
                # No more function calls; capture text and break
                final_response = response.output_text
                break
            
            # Execute the function
            args = json.loads(func_call.arguments)
            result = self.vector_search(args.get("query"))
            
            # Append function call and output
            messages.append({
                "type": "function_call",
                "name": func_call.name,
                "call_id": func_call.call_id,
                "arguments": func_call.arguments
            })
            messages.append({
                "type": "function_call_output",
                "call_id": func_call.call_id,
                "output": result
            })
            
            tool_calls += 1
            if tool_calls >= MAX_TOOL_CALLS:
                # Ask LLM to finalize answer without new calls
                closing = self.client.responses.create(
                    model=settings.COMPLETION_MODEL,
                    input=messages,
                    tools=tools
                )
                final_response = closing.output_text
                break
        
        # Fallback if needed
        if final_response is None:
            final_response = response.output_text
        
        return final_response 