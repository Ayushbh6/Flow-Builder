export interface Flow {
  id: number;
  name: string;
  description?: string;
  flow_data: any;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface FlowList {
  flows: Flow[];
  total: number;
}

export interface Document {
  id: number;
  name: string;
  file_path: string;
  file_size: number;
  content_type: string;
  status: string;
  created_at: string;
  updated_at?: string;
}

export interface KnowledgeBase {
  id: number;
  name: string;
  description?: string;
  index_name: string;
  namespace?: string;
  documents: number[];
  status: string;
  created_at: string;
  updated_at?: string;
}

export interface Chatbot {
  id: number;
  name: string;
  description?: string;
  knowledge_base_id: number;
  model: string;
  temperature: number;
  max_tokens: number;
  system_prompt?: string;
  created_at: string;
  updated_at?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface Conversation {
  id: string;
  messages: ChatMessage[];
  created_at: string;
  updated_at?: string;
} 