#!/usr/bin/env python3
"""
Vector Search Client using GPT-4.1 with function calling and multi-turn support, with streaming capabilities.
"""
from dotenv import load_dotenv
load_dotenv()
import os
import json
import asyncio
import sys
from typing import AsyncGenerator, Dict, Any, List, Optional
from openai import OpenAI, AsyncOpenAI
from create_RAG_tool import vector_search, scaling_up_search

# Initialize OpenAI clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
async_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# For debugging - set to True to print debug info (tool-call events only)
DEBUG = True

def debug_print(*args, **kwargs):
    """Print debug information if DEBUG is True"""
    if DEBUG:
        print("[DEBUG]", *args, file=sys.stderr, **kwargs)

def create_vector_search_tool(
    tool_name: str, 
    tool_description: str, 
    index_name: str, 
    namespace: str,
    top_k: int = 9,
    top_reranked: int = 4,
    embedding_model: str = "text-embedding-3-small"
):
    """
    Create a vector search tool definition for function calling
    
    Args:
        tool_name: Name of the tool function
        tool_description: Description of what the tool does
        index_name: Pinecone index to search
        namespace: Namespace within the index
        top_k: Number of initial results to retrieve
        top_reranked: Number of results after reranking
        embedding_model: Model to use for embeddings
        
    Returns:
        Tool schema for OpenAI function calling
    """
    return {
        "type": "function",
        "name": tool_name,
        "description": tool_description,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": f"The query to search the {index_name} Pinecone index for relevant information. Based on the user's query, you should be able to retrieve the most relevant information from the index."}
            },
            "required": ["query"],
            "additionalProperties": False
        },
        "strict": True
    }

def create_system_prompt(
    assistant_name: str,
    index_description: str,
    multilingual: bool = False,
    languages: List[str] = ["English"]
):
    """
    Create a system prompt for the assistant
    
    Args:
        assistant_name: Name of the assistant
        index_description: Description of what's in the vector index
        multilingual: Whether the assistant should support multiple languages
        languages: List of languages the assistant should support
        
    Returns:
        Formatted system prompt
    """
    language_instruction = ""
    if multilingual and len(languages) > 1:
        lang_list = ", ".join(languages[:-1]) + ", and " + languages[-1]
        language_instruction = f"## LANGUAGE\nUsers may ask questions in {lang_list}, and can switch languages mid-conversation.\n"
        language_instruction += " The tool returns English text; You MUST format your responses accordingly.\n"
        language_instruction += " ".join([f"For {lang} user queries, you MUST reply in {lang}." for lang in languages]) + "\n"
        if "English" not in languages:
            language_instruction += "For all non-English tool responses, translate them to the appropriate language."
    else:
        language_instruction = "## LANGUAGE\nUsers will ask questions in English, and you should respond in English.\n"
    
    return (
        f"# Identity\n"
        f"You are {assistant_name}, an AI agent that retrieves relevant information from the {index_description}.\n\n"
        "# Instructions\n"
        "## PERSISTENCE\n"
        "You are an agent—keep working until the user's query is fully resolved. Only stop when you're sure the problem is solved.\n"
        "## TOOL CALLING\n"
        f"Use the available search function to fetch relevant information. Do NOT guess or hallucinate results."
        " If you need clarification to call the tool, ask the user.\n"
        "## PLANNING\n"
        "Plan extensively: decide whether to call the function, reflect on results, then finalize the answer.\n"
        f"{language_instruction}"
    )

def create_vector_search_client(
    tool_name: str,
    tool_description: str,
    assistant_name: str,
    index_description: str,
    index_name: str,
    namespace: str,
    top_k: int = 9,
    top_reranked: int = 4,
    embedding_model: str = "text-embedding-3-small",
    multilingual: bool = False,
    languages: List[str] = ["English"],
    max_tool_calls: int = 4
):
    """
    Create a customized vector search client
    
    Args:
        tool_name: Name of the tool function
        tool_description: Description of what the tool does
        assistant_name: Name of the assistant
        index_description: Description of what's in the vector index
        index_name: Pinecone index to search
        namespace: Namespace within the index
        top_k: Number of initial results to retrieve
        top_reranked: Number of results after reranking
        embedding_model: Model to use for embeddings
        multilingual: Whether the assistant should support multiple languages
        languages: List of languages the assistant should support
        max_tool_calls: Maximum number of tool calls allowed
        
    Returns:
        A tuple of (ask_function, ask_function_stream)
    """
    # Create tool schema
    tools = [create_vector_search_tool(
        tool_name, 
        tool_description,
        index_name,
        namespace,
        top_k,
        top_reranked,
        embedding_model
    )]
    
    # Create system prompt
    system_prompt = create_system_prompt(
        assistant_name,
        index_description,
        multilingual,
        languages
    )
    
    def ask_vector_search(history: list, query: str) -> str:
        """
        Ask GPT-4.1 to decide when to call the vector search function and return the final answer.
        Supports multi-turn context by including the last 8 turns of user/assistant.
        Allows up to max_tool_calls sequential invocations before finalizing.
        """
        # Initialize message history
        messages = [{"role": "system", "content": system_prompt}]
        # Include last 8 user-assistant exchanges
        for turn in history[-8:]:
            messages.append({"role": "user", "content": turn["user"]})
            messages.append({"role": "assistant", "content": turn["assistant"]})
        # Add current user query
        messages.append({"role": "user", "content": query})

        tool_calls = 0
        final_response = None

        while tool_calls < max_tool_calls:
            # Send to GPT-4.1 with function schema
            resp = client.responses.create(
                model="gpt-4.1",
                input=messages,
                tools=tools
            )
            # Check for function call
            func_call = next((item for item in resp.output if item.type == "function_call"), None)
            if not func_call:
                # No more function calls; capture text and break
                final_response = resp.output_text
                break

            # Execute the function
            args = json.loads(func_call.arguments)
            
            # Call our generalized vector search function
            result = vector_search(
                query=args.get("query"),
                index_name=index_name,
                namespace=namespace,
                top_k=top_k,
                top_reranked=top_reranked,
                embedding_model=embedding_model
            )

            # Append the function call and its output
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
            # If reached max calls, exit loop to finalize
            if tool_calls >= max_tool_calls:
                # Ask GPT to finalize answer without new calls
                closing = client.responses.create(
                    model="gpt-4.1",
                    input=messages,
                    tools=tools
                )
                final_response = closing.output_text
                break
            # Otherwise, loop back to allow next call

        # Fallback: if loop finishes without setting, use last response text
        if final_response is None:
            final_response = resp.output_text

        return final_response

    async def ask_vector_search_stream(history: list, query: str) -> AsyncGenerator[str, None]:
        """
        Streaming version of ask_vector_search.
        Returns an async generator that yields content deltas as they're received.
        Tool calls are still processed synchronously before streaming the final response.
        """
        
        # Initialize message history
        messages = [{"role": "system", "content": system_prompt}]
        # Include last 8 user-assistant exchanges
        for turn in history[-8:]:
            messages.append({"role": "user", "content": turn["user"]})
            messages.append({"role": "assistant", "content": turn["assistant"]})
        # Add current user query
        messages.append({"role": "user", "content": query})

        tool_calls = 0
        final_messages = messages.copy()
        
        debug_print(f"Processing tool calls for query: {query}")

        while tool_calls < max_tool_calls:
            debug_print(f"Checking for tool call {tool_calls+1}/{max_tool_calls}")
            
            # Send to GPT-4.1 with function schema
            resp = client.responses.create(
                model="gpt-4.1",
                input=messages,
                tools=tools
            )
            
            # Check for function call
            func_call = next((item for item in resp.output if item.type == "function_call"), None)
            if not func_call:
                # No more function calls; prepare for streaming
                break

            # Execute the function
            debug_print(f"Executing function call: {func_call.name}")
            args = json.loads(func_call.arguments)
            
            # Call our generalized vector search function
            result = vector_search(
                query=args.get("query"),
                index_name=index_name,
                namespace=namespace,
                top_k=top_k,
                top_reranked=top_reranked,
                embedding_model=embedding_model
            )
            
            debug_print(f"Function returned result length: {len(result)}")

            # Append the function call and its output
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
            if tool_calls >= max_tool_calls:
                debug_print(f"Reached max tool calls: {max_tool_calls}")
                break

        # For direct single response (fallback)
        if DEBUG and not tool_calls:
            debug_print(f"No tool calls made for query: {query}")

        # Stream the final response
        
        try:
            stream = await async_client.responses.create(
                model="gpt-4.1-mini-2025-04-14",
                input=final_messages,
                tools=tools,
                stream=True
            )
            
            got_content = False
            
            async for event in stream:
                
                if event.type == "response.output_text.delta":
                    # The delta of streamed text is available on .delta, not .text
                    got_content = True
                    yield event.delta
                elif event.type == "text_delta":
                    got_content = True
                    yield event.delta
                elif event.type == "content_part_added":
                    if event.content_part.type == "text":
                        got_content = True
                        yield event.content_part.text
                elif event.type == "text_done":
                    pass
                elif event.type == "content_part_done":
                    pass
                elif event.type == "function_call":
                    pass
                else:
                    pass
            
            # If no content was streamed, yield a fallback message
            if not got_content:
                # Get a non-streaming response as fallback
                fallback_resp = client.responses.create(
                    model="gpt-4.1-mini-2025-04-14",
                    input=final_messages,
                    tools=tools
                )
                yield fallback_resp.output_text or "I'm sorry, I couldn't generate a response. Please try again."
        except Exception:
            # Fallback on stream error
            fallback_resp = client.responses.create(
                model="gpt-4.1-mini-2025-04-14",
                input=final_messages,
                tools=tools
            )
            yield fallback_resp.output_text

    return ask_vector_search, ask_vector_search_stream

# Create the default Scaling Up client for backward compatibility
# This maintains the original functionality while allowing for customization
scaling_up_tools = [
    {
        "type": "function",
        "name": "scaling_up_search",
        "description": "Search the Scaling Up Pinecone index for relevant information based on a user query.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The query to search the Scaling Up Pinecone index for relevant information. Based on the user's query, you should be able to retrieve the most relevant information from the index."}
            },
            "required": ["query"],
            "additionalProperties": False
        },
        "strict": True
    }
]

SCALING_UP_SYSTEM_PROMPT = (
    "# Identity\n"
    "You are Scaling Up Search Assistant, an AI agent that retrieves relevant information from the Scaling Up Pinecone index.\n\n"
    "# Instructions\n"
    "## PERSISTENCE\n"
    "You are an agent—keep working until the user's query is fully resolved. Only stop when you're sure the problem is solved.\n"
    "## TOOL CALLING\n"
    "Use the scaling_up_search function to fetch relevant information. Do NOT guess or hallucinate results."
    " If you need clarification to call the tool, ask the user.\n"
    "## PLANNING\n"
    "Plan extensively: decide whether to call the function, reflect on results, then finalize the answer.\n"
    "## LANGUAGE\n"
    "Users may ask questions in English or Greek, and can switch languages mid-conversation.\n"
    " The tool returns English text; You MUST format your responses accordingly. For an english user query, reply to the user in English.\n"
    "For Greek user queries, you MUST reply in Greek and change the original English tool call output to Greek."
)

MAX_TOOL_CALLS = 4

def ask_scaling_up(history: list, query: str) -> str:
    """
    Legacy function for backward compatibility.
    Ask GPT-4.1 to decide when to call the scaling_up_search function and return the final answer.
    Supports multi-turn context by including the last 8 turns of user/assistant.
    Allows up to MAX_TOOL_CALLS sequential invocations before finalizing.
    """
    # Initialize message history
    messages = [{"role": "system", "content": SCALING_UP_SYSTEM_PROMPT}]
    # Include last 8 user-assistant exchanges
    for turn in history[-8:]:
        messages.append({"role": "user", "content": turn["user"]})
        messages.append({"role": "assistant", "content": turn["assistant"]})
    # Add current user query
    messages.append({"role": "user", "content": query})

    tool_calls = 0
    final_response = None

    while tool_calls < MAX_TOOL_CALLS:
        # Send to GPT-4.1 with function schema
        resp = client.responses.create(
            model="gpt-4.1",
            input=messages,
            tools=scaling_up_tools
        )
        # Check for function call
        func_call = next((item for item in resp.output if item.type == "function_call"), None)
        if not func_call:
            # No more function calls; capture text and break
            final_response = resp.output_text
            break

        # Execute the function
        args = json.loads(func_call.arguments)
        result = scaling_up_search(args.get("query"))

        # Append the function call and its output
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
        # If reached max calls, exit loop to finalize
        if tool_calls >= MAX_TOOL_CALLS:
            # Ask GPT to finalize answer without new calls
            closing = client.responses.create(
                model="gpt-4.1",
                input=messages,
                tools=scaling_up_tools
            )
            final_response = closing.output_text
            break
        # Otherwise, loop back to allow next call

    # Fallback: if loop finishes without setting, use last response text
    if final_response is None:
        final_response = resp.output_text

    return final_response

async def ask_scaling_up_stream(history: list, query: str) -> AsyncGenerator[str, None]:
    """
    Legacy function for backward compatibility.
    Streaming version of ask_scaling_up.
    Returns an async generator that yields content deltas as they're received.
    Tool calls are still processed synchronously before streaming the final response.
    """
    
    # Initialize message history
    messages = [{"role": "system", "content": SCALING_UP_SYSTEM_PROMPT}]
    # Include last 8 user-assistant exchanges
    for turn in history[-8:]:
        messages.append({"role": "user", "content": turn["user"]})
        messages.append({"role": "assistant", "content": turn["assistant"]})
    # Add current user query
    messages.append({"role": "user", "content": query})

    tool_calls = 0
    final_messages = messages.copy()
    
    debug_print(f"Processing tool calls for query: {query}")

    while tool_calls < MAX_TOOL_CALLS:
        debug_print(f"Checking for tool call {tool_calls+1}/{MAX_TOOL_CALLS}")
        
        # Send to GPT-4.1 with function schema
        resp = client.responses.create(
            model="gpt-4.1",
            input=messages,
            tools=scaling_up_tools
        )
        
        # Check for function call
        func_call = next((item for item in resp.output if item.type == "function_call"), None)
        if not func_call:
            # No more function calls; prepare for streaming
        # no more function calls; proceed to streaming
            break

        # Execute the function
        debug_print(f"Executing function call: {func_call.name}")
        args = json.loads(func_call.arguments)
        result = scaling_up_search(args.get("query"))
        debug_print(f"Function returned result length: {len(result)}")

        # Append the function call and its output
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
            debug_print(f"Reached max tool calls: {MAX_TOOL_CALLS}")
            break

    # For direct single response (fallback)
    if DEBUG and not tool_calls:
        debug_print(f"No tool calls made for query: {query}")

    # Stream the final response
    
    try:
        stream = await async_client.responses.create(
            model="gpt-4.1-mini-2025-04-14",
            input=final_messages,
            tools=scaling_up_tools,
            stream=True
        )
        
        got_content = False
        
        async for event in stream:
            
            if event.type == "response.output_text.delta":
                # The delta of streamed text is available on .delta, not .text
                got_content = True
                yield event.delta
            elif event.type == "text_delta":
                got_content = True
                yield event.delta
            elif event.type == "content_part_added":
                if event.content_part.type == "text":
                    got_content = True
                    yield event.content_part.text
            elif event.type == "text_done":
                pass
            elif event.type == "content_part_done":
                pass
            elif event.type == "function_call":
                pass
            else:
                pass
        
        # If no content was streamed, yield a fallback message
        if not got_content:
            # Get a non-streaming response as fallback
            fallback_resp = client.responses.create(
                model="gpt-4.1-mini-2025-04-14",
                input=final_messages,
                tools=scaling_up_tools
            )
            yield fallback_resp.output_text or "I'm sorry, I couldn't generate a response. Please try again."
    except Exception:
        # Fallback on stream error
        fallback_resp = client.responses.create(
            model="gpt-4.1-mini-2025-04-14",
            input=final_messages,
            tools=scaling_up_tools
        )
        yield fallback_resp.output_text

# For backward compatibility with the api_server reference
ask_iaspis = ask_scaling_up
ask_iaspis_stream = ask_scaling_up_stream

if __name__ == "__main__":
    # Example of creating a custom vector search client
    custom_ask, custom_ask_stream = create_vector_search_client(
        tool_name="custom_vector_search",
        tool_description="Search a custom vector database for relevant information",
        assistant_name="Custom Vector Search Assistant",
        index_description="Custom Vector Database",
        index_name="scaling-up",  # Default for demonstration
        namespace="scaling-up-demo",  # Default for demonstration
        multilingual=True,
        languages=["English", "Spanish"]
    )
    
    # CLI chat loop for multi-turn testing with the default Scaling Up client
    conversation_history = []
    print("Welcome to Scaling Up Search Assistant (English/Greek). Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        assistant_response = ask_scaling_up(conversation_history, user_input)
        print(f"Assistant: {assistant_response}\n")
        conversation_history.append({"user": user_input, "assistant": assistant_response})