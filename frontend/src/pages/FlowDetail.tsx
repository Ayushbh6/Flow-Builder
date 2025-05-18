import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
} from 'reactflow';
import 'reactflow/dist/style.css';
import { 
  PencilIcon, 
  PlayIcon, 
  TrashIcon, 
  ArrowLeftIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';
import { getFlow, updateFlow, deleteFlow, executeFlow } from '../services/api';
import { Flow as FlowType } from '../types';

// Import the same node components as in FlowBuilder
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

const FlowDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [flow, setFlow] = useState<FlowType | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [executing, setExecuting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [editMode, setEditMode] = useState<boolean>(false);
  const [flowName, setFlowName] = useState<string>('');
  const [flowDescription, setFlowDescription] = useState<string>('');
  const [saving, setSaving] = useState<boolean>(false);

  useEffect(() => {
    const fetchFlow = async () => {
      if (!id) return;
      
      try {
        setLoading(true);
        const response = await getFlow(parseInt(id));
        setFlow(response.data);
        setFlowName(response.data.name);
        setFlowDescription(response.data.description || '');

        // Set nodes and edges from flow data
        if (response.data.flow_data) {
          if (response.data.flow_data.nodes) {
            setNodes(response.data.flow_data.nodes);
          }
          if (response.data.flow_data.edges) {
            setEdges(response.data.flow_data.edges);
          }
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load flow');
        console.error('Flow load error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchFlow();
  }, [id]);

  const onConnect = useCallback((params: Edge | Connection) => {
    setEdges((eds) => addEdge({ ...params, animated: true }, eds));
  }, [setEdges]);

  const onSave = async () => {
    if (!flow || !id) return;
    
    if (!flowName.trim()) {
      setError('Flow name is required');
      return;
    }

    try {
      setSaving(true);
      const updatedFlow = {
        ...flow,
        name: flowName,
        description: flowDescription,
        flow_data: {
          nodes,
          edges,
        },
      };

      await updateFlow(parseInt(id), updatedFlow);
      setFlow(updatedFlow);
      setEditMode(false);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Error saving flow');
      console.error('Error saving flow:', err);
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async () => {
    if (!flow || !id) return;
    
    if (!window.confirm('Are you sure you want to delete this flow?')) {
      return;
    }

    try {
      await deleteFlow(parseInt(id));
      navigate('/flows');
    } catch (err: any) {
      setError(err.message || 'Error deleting flow');
      console.error('Error deleting flow:', err);
    }
  };

  const onExecute = async () => {
    if (!flow || !id) return;
    
    try {
      setExecuting(true);
      await executeFlow(parseInt(id), {});
      // Could navigate to a results page or refresh the flow data
      alert('Flow executed successfully');
    } catch (err: any) {
      setError(err.message || 'Error executing flow');
      console.error('Error executing flow:', err);
    } finally {
      setExecuting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-2 text-gray-500">Loading flow...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-400 p-4 my-4">
        <div className="flex">
          <ExclamationCircleIcon className="h-5 w-5 text-red-400" />
          <div className="ml-3">
            <p className="text-sm text-red-700">
              {error}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!flow) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">Flow not found</p>
        <button
          onClick={() => navigate('/flows')}
          className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-primary-700 bg-primary-100 hover:bg-primary-200"
        >
          <ArrowLeftIcon className="-ml-1 mr-2 h-4 w-4" />
          Back to Flows
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-120px)]">
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center">
          <button
            onClick={() => navigate('/flows')}
            className="mr-4 inline-flex items-center px-3 py-1.5 border border-gray-300 rounded-md text-sm text-gray-700 bg-white hover:bg-gray-50"
          >
            <ArrowLeftIcon className="h-4 w-4 mr-1" />
            Back
          </button>
          
          {editMode ? (
            <div className="flex items-center">
              <input
                type="text"
                value={flowName}
                onChange={(e) => setFlowName(e.target.value)}
                className="text-2xl font-semibold text-gray-900 border-b border-gray-300 focus:outline-none focus:border-primary-500"
                placeholder="Flow Name"
              />
            </div>
          ) : (
            <h1 className="text-2xl font-semibold text-gray-900">{flow.name}</h1>
          )}
        </div>
        
        <div className="flex gap-2">
          {editMode ? (
            <>
              <button
                onClick={() => setEditMode(false)}
                className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={onSave}
                disabled={saving}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setEditMode(true)}
                className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                <PencilIcon className="-ml-1 mr-1 h-4 w-4" />
                Edit
              </button>
              <button
                onClick={onExecute}
                disabled={executing}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
              >
                <PlayIcon className="-ml-1 mr-1 h-4 w-4" />
                {executing ? 'Executing...' : 'Execute Flow'}
              </button>
              <button
                onClick={onDelete}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                <TrashIcon className="-ml-1 mr-1 h-4 w-4" />
                Delete
              </button>
            </>
          )}
        </div>
      </div>

      {editMode && (
        <div className="mb-4 bg-white p-4 rounded-md shadow-sm">
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
      )}

      <div className="flex-grow bg-white rounded-md shadow-sm">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={editMode ? onNodesChange : undefined}
          onEdgesChange={editMode ? onEdgesChange : undefined}
          onConnect={editMode ? onConnect : undefined}
          nodeTypes={nodeTypes}
          fitView
          nodesConnectable={editMode}
          nodesDraggable={editMode}
          elementsSelectable={editMode}
        >
          <Controls />
          <MiniMap />
          <Background color="#aaa" gap={16} />
        </ReactFlow>
      </div>
    </div>
  );
};

export default FlowDetail; 