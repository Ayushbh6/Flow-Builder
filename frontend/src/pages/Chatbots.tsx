import React, { useState, useEffect, useRef } from 'react';
import { getChatbots, getKnowledgeBases, sendChatMessage, createChatbot } from '../services/api';
import { Chatbot, KnowledgeBase, ChatMessage } from '../types';
import { 
  ChatBubbleLeftRightIcon,
  PaperAirplaneIcon,
  PlusIcon,
  XMarkIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline';

const Chatbots: React.FC = () => {
  const [chatbots, setChatbots] = useState<Chatbot[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedChatbot, setSelectedChatbot] = useState<Chatbot | null>(null);
  const [showChatInterface, setShowChatInterface] = useState<boolean>(false);
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [conversation, setConversation] = useState<ChatMessage[]>([]);
  const [userMessage, setUserMessage] = useState<string>('');
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [sendingMessage, setSendingMessage] = useState<boolean>(false);
  
  // Form state for creating a new chatbot
  const [newChatbotName, setNewChatbotName] = useState<string>('');
  const [newChatbotDescription, setNewChatbotDescription] = useState<string>('');
  const [selectedKnowledgeBaseId, setSelectedKnowledgeBaseId] = useState<number | null>(null);
  const [modelName, setModelName] = useState<string>('gpt-4.1-mini');
  const [temperature, setTemperature] = useState<number>(0.7);
  const [maxTokens, setMaxTokens] = useState<number>(1000);
  const [systemPrompt, setSystemPrompt] = useState<string>(
    'You are a helpful assistant. Answer questions based on the provided knowledge base.'
  );
  const [creatingChatbot, setCreatingChatbot] = useState<boolean>(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    // Scroll to bottom of chat messages
    scrollToBottom();
  }, [conversation]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [chatbotsRes, knowledgeBasesRes] = await Promise.all([
        getChatbots(),
        getKnowledgeBases(),
      ]);
      
      setChatbots(chatbotsRes.data || []);
      setKnowledgeBases(knowledgeBasesRes.data || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load chatbots');
      console.error('Chatbots fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSelectChatbot = (chatbot: Chatbot) => {
    setSelectedChatbot(chatbot);
    setShowChatInterface(true);
    // Reset conversation when selecting a new chatbot
    setConversation([]);
    setConversationId(undefined);
  };

  const handleSendMessage = async () => {
    if (!userMessage.trim() || !selectedChatbot) return;

    const newUserMessage: ChatMessage = {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    };

    // Add user message to conversation immediately
    setConversation([...conversation, newUserMessage]);
    setUserMessage('');
    setSendingMessage(true);

    try {
      const response = await sendChatMessage(
        selectedChatbot.id,
        userMessage,
        conversationId
      );
      
      // Get conversation ID if this is the first message
      if (!conversationId && response.data.conversation_id) {
        setConversationId(response.data.conversation_id);
      }

      // Add assistant's response to conversation
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.data.message,
        timestamp: new Date().toISOString(),
      };
      
      setConversation(prev => [...prev, assistantMessage]);
    } catch (err: any) {
      setError(err.message || 'Error sending message');
      console.error('Message send error:', err);
      
      // Add error message to conversation
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request.',
        timestamp: new Date().toISOString(),
      };
      
      setConversation(prev => [...prev, errorMessage]);
    } finally {
      setSendingMessage(false);
    }
  };

  const handleCreateChatbot = async () => {
    if (!newChatbotName.trim() || !selectedKnowledgeBaseId) {
      setError('Chatbot name and knowledge base are required');
      return;
    }

    try {
      setCreatingChatbot(true);
      
      const chatbotData = {
        name: newChatbotName,
        description: newChatbotDescription,
        knowledge_base_id: selectedKnowledgeBaseId,
        model: modelName,
        temperature: temperature,
        max_tokens: maxTokens,
        system_prompt: systemPrompt,
      };

      await createChatbot(chatbotData);
      
      // Reset form and close modal
      setNewChatbotName('');
      setNewChatbotDescription('');
      setSelectedKnowledgeBaseId(null);
      setModelName('gpt-4.1-mini');
      setTemperature(0.7);
      setMaxTokens(1000);
      setSystemPrompt('You are a helpful assistant. Answer questions based on the provided knowledge base.');
      setShowCreateModal(false);
      
      // Refresh chatbot list
      fetchData();
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Error creating chatbot');
      console.error('Chatbot creation error:', err);
    } finally {
      setCreatingChatbot(false);
    }
  };

  if (loading && !chatbots.length) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-2 text-gray-500">Loading chatbots...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Chatbots</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <PlusIcon className="-ml-1 mr-2 h-5 w-5" />
          Create Chatbot
        </button>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <ExclamationCircleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <p className="text-sm text-red-700">
                {error}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {chatbots.length > 0 ? (
          chatbots.map((chatbot) => (
            <div
              key={chatbot.id}
              className="bg-white overflow-hidden shadow rounded-lg divide-y divide-gray-200"
            >
              <div className="px-4 py-5 sm:px-6">
                <div className="flex justify-between">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">{chatbot.name}</h3>
                </div>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">
                  {chatbot.description || 'No description'}
                </p>
              </div>
              <div className="px-4 py-4 sm:px-6">
                <div className="grid grid-cols-1 gap-2">
                  <div className="text-sm text-gray-500">
                    <span className="font-medium text-gray-700">Model:</span> {chatbot.model}
                  </div>
                  <div className="text-sm text-gray-500">
                    <span className="font-medium text-gray-700">Temperature:</span> {chatbot.temperature}
                  </div>
                  <div className="text-sm text-gray-500">
                    <span className="font-medium text-gray-700">Max Tokens:</span> {chatbot.max_tokens}
                  </div>
                </div>
                <div className="mt-4 flex space-x-3">
                  <button
                    onClick={() => handleSelectChatbot(chatbot)}
                    className="flex-1 inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                  >
                    <ChatBubbleLeftRightIcon className="-ml-1 mr-2 h-5 w-5" />
                    Test Chat
                  </button>
                  <button
                    className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                  >
                    <Cog6ToothIcon className="h-5 w-5" aria-hidden="true" />
                  </button>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="col-span-3 bg-white overflow-hidden shadow rounded-lg">
            <div className="px-4 py-16 sm:px-6 text-center">
              <ChatBubbleLeftRightIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-base font-medium text-gray-900">No chatbots yet</h3>
              <p className="mt-1 text-sm text-gray-500">Get started by creating your first chatbot.</p>
              <div className="mt-6">
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  <PlusIcon className="-ml-1 mr-2 h-5 w-5" />
                  Create Chatbot
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Chat Interface */}
      {showChatInterface && selectedChatbot && (
        <div className="fixed inset-0 overflow-hidden z-10" aria-labelledby="chat-panel">
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true"></div>
            <div className="fixed inset-y-0 right-0 max-w-full flex">
              <div className="relative w-screen max-w-md">
                <div className="h-full flex flex-col py-6 bg-white shadow-xl overflow-y-scroll">
                  <div className="px-4 sm:px-6">
                    <div className="flex items-start justify-between">
                      <h2 className="text-lg font-medium text-gray-900" id="chat-panel">
                        Chat with {selectedChatbot.name}
                      </h2>
                      <div className="ml-3 h-7 flex items-center">
                        <button
                          onClick={() => setShowChatInterface(false)}
                          className="bg-white rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                        >
                          <span className="sr-only">Close panel</span>
                          <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                        </button>
                      </div>
                    </div>
                  </div>
                  <div className="mt-6 relative flex-1 px-4 sm:px-6">
                    <div className="absolute inset-0 px-4 sm:px-6">
                      <div className="h-full flex flex-col justify-between">
                        {/* Chat messages */}
                        <div className="overflow-y-auto mb-4">
                          {conversation.length > 0 ? (
                            <div className="space-y-4">
                              {conversation.map((message, index) => (
                                <div
                                  key={index}
                                  className={`flex ${
                                    message.role === 'user' ? 'justify-end' : 'justify-start'
                                  }`}
                                >
                                  <div
                                    className={`max-w-xs sm:max-w-md px-4 py-2 rounded-lg ${
                                      message.role === 'user'
                                        ? 'bg-primary-600 text-white'
                                        : 'bg-gray-100 text-gray-900'
                                    }`}
                                  >
                                    <p className="text-sm">{message.content}</p>
                                  </div>
                                </div>
                              ))}
                              <div ref={messagesEndRef} />
                            </div>
                          ) : (
                            <div className="h-full flex flex-col items-center justify-center text-center">
                              <ChatBubbleLeftRightIcon className="h-12 w-12 text-gray-300" />
                              <h3 className="mt-2 text-sm font-medium text-gray-900">No messages</h3>
                              <p className="mt-1 text-sm text-gray-500">Ask a question to start the conversation</p>
                            </div>
                          )}
                        </div>

                        {/* Input area */}
                        <div className="pt-4 border-t border-gray-200">
                          <div className="flex rounded-md shadow-sm">
                            <input
                              type="text"
                              name="message"
                              id="message"
                              value={userMessage}
                              onChange={(e) => setUserMessage(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                  e.preventDefault();
                                  handleSendMessage();
                                }
                              }}
                              disabled={sendingMessage}
                              className="focus:ring-primary-500 focus:border-primary-500 flex-1 block w-full rounded-md sm:text-sm border-gray-300"
                              placeholder="Type your message..."
                            />
                            <button
                              type="button"
                              onClick={handleSendMessage}
                              disabled={!userMessage.trim() || sendingMessage}
                              className="ml-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              {sendingMessage ? (
                                <ArrowPathIcon className="h-5 w-5 animate-spin" />
                              ) : (
                                <PaperAirplaneIcon className="h-5 w-5" />
                              )}
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Chatbot Modal */}
      {showCreateModal && (
        <div className="fixed z-10 inset-0 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true"></div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                      Create New Chatbot
                    </h3>
                    <div className="mt-6 space-y-6">
                      <div>
                        <label htmlFor="chatbotName" className="block text-sm font-medium text-gray-700">
                          Chatbot Name *
                        </label>
                        <input
                          type="text"
                          name="chatbotName"
                          id="chatbotName"
                          value={newChatbotName}
                          onChange={(e) => setNewChatbotName(e.target.value)}
                          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                          placeholder="Enter chatbot name"
                          required
                        />
                      </div>

                      <div>
                        <label htmlFor="chatbotDescription" className="block text-sm font-medium text-gray-700">
                          Description (optional)
                        </label>
                        <textarea
                          id="chatbotDescription"
                          name="chatbotDescription"
                          rows={2}
                          value={newChatbotDescription}
                          onChange={(e) => setNewChatbotDescription(e.target.value)}
                          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                          placeholder="Enter description"
                        />
                      </div>

                      <div>
                        <label htmlFor="knowledgeBase" className="block text-sm font-medium text-gray-700">
                          Knowledge Base *
                        </label>
                        <select
                          id="knowledgeBase"
                          name="knowledgeBase"
                          value={selectedKnowledgeBaseId || ''}
                          onChange={(e) => setSelectedKnowledgeBaseId(parseInt(e.target.value))}
                          className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                          required
                        >
                          <option value="">Select a knowledge base</option>
                          {knowledgeBases.map((kb) => (
                            <option key={kb.id} value={kb.id}>
                              {kb.name}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label htmlFor="model" className="block text-sm font-medium text-gray-700">
                          Model
                        </label>
                        <select
                          id="model"
                          name="model"
                          value={modelName}
                          onChange={(e) => setModelName(e.target.value)}
                          className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                        >
                          <option value="gpt-4.1-mini">GPT-4.1-mini</option>
                          <option value="gpt-4.1">GPT-4.1</option>
                          <option value="gpt-4.1-turbo">GPT-4.1-turbo</option>
                        </select>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label htmlFor="temperature" className="block text-sm font-medium text-gray-700">
                            Temperature: {temperature}
                          </label>
                          <input
                            type="range"
                            id="temperature"
                            name="temperature"
                            min="0"
                            max="1"
                            step="0.1"
                            value={temperature}
                            onChange={(e) => setTemperature(parseFloat(e.target.value))}
                            className="mt-1 block w-full"
                          />
                        </div>

                        <div>
                          <label htmlFor="maxTokens" className="block text-sm font-medium text-gray-700">
                            Max Tokens
                          </label>
                          <input
                            type="number"
                            id="maxTokens"
                            name="maxTokens"
                            min="100"
                            max="8000"
                            value={maxTokens}
                            onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                          />
                        </div>
                      </div>

                      <div>
                        <label htmlFor="systemPrompt" className="block text-sm font-medium text-gray-700">
                          System Prompt
                        </label>
                        <textarea
                          id="systemPrompt"
                          name="systemPrompt"
                          rows={3}
                          value={systemPrompt}
                          onChange={(e) => setSystemPrompt(e.target.value)}
                          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  onClick={handleCreateChatbot}
                  disabled={creatingChatbot}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
                >
                  {creatingChatbot ? 'Creating...' : 'Create Chatbot'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Chatbots; 