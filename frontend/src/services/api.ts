import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Flow API
export const getFlows = async (skip = 0, limit = 100) => {
  return api.get(`/flows?skip=${skip}&limit=${limit}`);
};

export const getFlow = async (id: number) => {
  return api.get(`/flows/${id}`);
};

export const createFlow = async (flowData: any) => {
  return api.post('/flows', flowData);
};

export const updateFlow = async (id: number, flowData: any) => {
  return api.put(`/flows/${id}`, flowData);
};

export const deleteFlow = async (id: number) => {
  return api.delete(`/flows/${id}`);
};

// Document API
export const uploadDocument = async (file: File, documentName: string) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('name', documentName);
  
  return api.post('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const getDocuments = async () => {
  return api.get('/documents');
};

// Knowledge Base API
export const createKnowledgeBase = async (knowledgeBaseData: any) => {
  return api.post('/knowledge-bases', knowledgeBaseData);
};

export const getKnowledgeBases = async () => {
  return api.get('/knowledge-bases');
};

// Chatbot API
export const createChatbot = async (chatbotData: any) => {
  return api.post('/chatbots', chatbotData);
};

export const getChatbots = async () => {
  return api.get('/chatbots');
};

export const sendChatMessage = async (chatbotId: number, message: string, conversationId?: string) => {
  return api.post(`/chatbots/${chatbotId}/chat`, { message, conversation_id: conversationId });
};

// Flow execution API
export const executeFlow = async (flowId: number, data: any) => {
  return api.post(`/flow-execution/${flowId}/execute`, data);
};

export default api; 