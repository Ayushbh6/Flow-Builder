import React, { useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  NodeTypes,
  Node,
  Panel
} from 'reactflow';
import 'reactflow/dist/style.css';
import { PlusIcon, ExclamationCircleIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import { createFlow } from '../services/api';

// Node components will be defined here
const TextExtractorNode = ({ data }: any) => {
  return (
    <div className="border-2 rounded-md p-4 w-64 bg-white shadow-md border-blue-400">
      <div className="font-semibold text-gray-800">Text Extractor</div>
      <div className="text-sm text-gray-500 mt-1">Extract text from documents</div>
      <div className="mt-2">
        <div className="flex items-center mt-2 text-xs">
          <div className={`w-2 h-2 rounded-full ${data.status === 'configured' ? 'bg-green-500' : 'bg-yellow-500'} mr-2`}></div>
          <span>{data.status === 'configured' ? 'Configured' : 'Not Configured'}</span>
        </div>
      </div>
    </div>
  );
};

const KnowledgeBaseNode = ({ data }: any) => {
  return (
    <div className="border-2 rounded-md p-4 w-64 bg-white shadow-md border-purple-400">
      <div className="font-semibold text-gray-800">Knowledge Base</div>
      <div className="text-sm text-gray-500 mt-1">Create and manage embeddings</div>
      <div className="mt-2">
        <div className="flex items-center mt-2 text-xs">
          <div className={`w-2 h-2 rounded-full ${data.status === 'configured' ? 'bg-green-500' : 'bg-yellow-500'} mr-2`}></div>
          <span>{data.status === 'configured' ? 'Configured' : 'Not Configured'}</span>
        </div>
      </div>
    </div>
  );
};

const ChatbotNode = ({ data }: any) => {
  return (
    <div className="border-2 rounded-md p-4 w-64 bg-white shadow-md border-green-400">
      <div className="font-semibold text-gray-800">Chatbot</div>
      <div className="text-sm text-gray-500 mt-1">Configure and deploy chatbot</div>
      <div className="mt-2">
        <div className="flex items-center mt-2 text-xs">
          <div className={`w-2 h-2 rounded-full ${data.status === 'configured' ? 'bg-green-500' : 'bg-yellow-500'} mr-2`}></div>
          <span>{data.status === 'configured' ? 'Configured' : 'Not Configured'}</span>
        </div>
      </div>
    </div>
  );
};

// Define node types
const nodeTypes: NodeTypes = {
  textExtractor: TextExtractorNode,
  knowledgeBase: KnowledgeBaseNode,
  chatbot: ChatbotNode,
};

const FlowBuilder: React.FC = () => {
  const navigate = useNavigate();
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [flowName, setFlowName] = useState<string>('');
  const [flowDescription, setFlowDescription] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState<boolean>(false);

  const onConnect = useCallback((params: Edge | Connection) => {
    setEdges((eds) => addEdge({ ...params, animated: true }, eds));
  }, [setEdges]);

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);

  const addNode = useCallback((type: string) => {
    const position = { x: 250, y: 100 + nodes.length * 150 };
    const newNode = {
      id: `${type}-${nodes.length + 1}`,
      type: type,
      position,
      data: { 
        label: type.charAt(0).toUpperCase() + type.slice(1), 
        status: 'not_configured'
      },
    };
    setNodes((nds) => nds.concat(newNode));
  }, [nodes, setNodes]);

  const saveFlow = async () => {
    if (!flowName.trim()) {
      setError('Flow name is required');
      return;
    }

    if (nodes.length === 0) {
      setError('Add at least one node to the flow');
      return;
    }

    try {
      setSaving(true);
      const flowData = {
        name: flowName,
        description: flowDescription,
        flow_data: {
          nodes,
          edges,
        },
        is_active: false,
      };

      const response = await createFlow(flowData);
      navigate(`/flows/${response.data.id}`);
    } catch (err: any) {
      setError(err.message || 'Error saving flow');
      console.error('Error saving flow:', err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-120px)]">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-semibold text-gray-900">Flow Builder</h1>
        <div className="flex gap-4">
          <button
            onClick={saveFlow}
            disabled={saving}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? 'Saving...' : 'Save Flow'}
          </button>
        </div>
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

      <div className="grid grid-cols-1 gap-4 md:grid-cols-4 mb-4">
        <div className="col-span-3">
          <div className="bg-white p-4 rounded-md shadow-sm">
            <div className="mb-4">
              <label htmlFor="flowName" className="block text-sm font-medium text-gray-700">
                Flow Name *
              </label>
              <input
                type="text"
                name="flowName"
                id="flowName"
                value={flowName}
                onChange={(e) => setFlowName(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                placeholder="Enter flow name"
              />
            </div>
            <div>
              <label htmlFor="flowDescription" className="block text-sm font-medium text-gray-700">
                Description (optional)
              </label>
              <textarea
                id="flowDescription"
                name="flowDescription"
                rows={2}
                value={flowDescription}
                onChange={(e) => setFlowDescription(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                placeholder="Enter flow description"
              />
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-md shadow-sm">
          <h3 className="font-medium text-gray-700 mb-2">Components</h3>
          <div className="space-y-2">
            <button
              onClick={() => addNode('textExtractor')}
              className="flex items-center w-full px-3 py-2 text-sm text-left text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              Text Extractor
            </button>
            <button
              onClick={() => addNode('knowledgeBase')}
              className="flex items-center w-full px-3 py-2 text-sm text-left text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              Knowledge Base
            </button>
            <button
              onClick={() => addNode('chatbot')}
              className="flex items-center w-full px-3 py-2 text-sm text-left text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              Chatbot
            </button>
          </div>
        </div>
      </div>

      <div className="flex-grow bg-white rounded-md shadow-sm" ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          nodeTypes={nodeTypes}
          fitView
        >
          <Controls />
          <MiniMap />
          <Background color="#aaa" gap={16} />
          <Panel position="bottom-right">
            <div className="bg-white p-2 rounded-md shadow-sm text-sm text-gray-500">
              Drag to connect nodes
            </div>
          </Panel>
        </ReactFlow>
      </div>

      {selectedNode && (
        <div className="mt-4 p-4 bg-white rounded-md shadow-sm">
          <h3 className="font-medium text-gray-700 mb-2">Configure {selectedNode.data.label}</h3>
          <p className="text-sm text-gray-500 mb-4">
            Configure the settings for this component.
          </p>
          <button
            onClick={() => {
              setNodes(nodes.map(node => 
                node.id === selectedNode.id 
                  ? { ...node, data: { ...node.data, status: 'configured' } } 
                  : node
              ));
              setSelectedNode(null);
            }}
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
          >
            <CheckCircleIcon className="h-4 w-4 mr-2" />
            Mark as Configured
          </button>
        </div>
      )}
    </div>
  );
};

export default FlowBuilder; 