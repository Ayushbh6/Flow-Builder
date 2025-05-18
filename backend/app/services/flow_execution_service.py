import logging
from typing import Dict, Any, List, Set, Tuple, Optional
import json
from sqlalchemy.orm import Session

from app.models.flow import Flow
from app.services.chatbot_service import ChatbotService

# Configure logging
logger = logging.getLogger(__name__)

class FlowExecutionService:
    """
    Service for executing flows.
    This handles running a flow with input data and validating the flow configuration.
    """
    
    def __init__(self, chatbot_service=None):
        """
        Initialize the flow execution service
        
        Args:
            chatbot_service: Optional chatbot service for dependency injection (useful for testing)
        """
        self.chatbot_service = chatbot_service or ChatbotService()
        
    def validate_connections(self, flow_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate that all node connections in the flow are valid
        
        Args:
            flow_data: The flow configuration data
            
        Returns:
            A tuple of (is_valid, error_message)
        """
        # Check required fields
        if "nodes" not in flow_data or "edges" not in flow_data:
            return False, "Flow configuration must include 'nodes' and 'edges'"
        
        nodes = flow_data["nodes"]
        edges = flow_data["edges"]
        
        # Build node lookup
        node_lookup = {}
        for node in nodes:
            if "id" not in node:
                return False, f"Node missing 'id': {node}"
            node_lookup[node["id"]] = node
        
        # Check that all edges connect existing nodes
        for edge in edges:
            if "source" not in edge or "target" not in edge:
                return False, f"Edge missing 'source' or 'target': {edge}"
                
            if edge["source"] not in node_lookup:
                return False, f"Edge source '{edge['source']}' does not exist"
                
            if edge["target"] not in node_lookup:
                return False, f"Edge target '{edge['target']}' does not exist"
        
        # Validate node types and connections
        for node in nodes:
            node_type = node.get("type")
            
            # Check that required node types have appropriate connections
            if node_type == "input":
                # Input nodes should have outgoing edges
                if not any(edge["source"] == node["id"] for edge in edges):
                    return False, f"Input node '{node['id']}' has no outgoing connections"
            
            elif node_type == "output":
                # Output nodes should have incoming edges
                if not any(edge["target"] == node["id"] for edge in edges):
                    return False, f"Output node '{node['id']}' has no incoming connections"
        
        # Check for cycles in the graph
        if self._has_cycles(nodes, edges):
            return False, "Flow contains cycles, which are not allowed"
        
        return True, ""
    
    def _has_cycles(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> bool:
        """
        Check if the flow graph contains cycles
        
        Args:
            nodes: List of nodes in the flow
            edges: List of edges in the flow
            
        Returns:
            True if cycles are detected, False otherwise
        """
        # Build adjacency list
        adjacency = {}
        for node in nodes:
            adjacency[node["id"]] = []
            
        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            adjacency[source].append(target)
        
        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def dfs_cycle(node_id):
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in adjacency[node_id]:
                if neighbor not in visited:
                    if dfs_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node in nodes:
            if node["id"] not in visited:
                if dfs_cycle(node["id"]):
                    return True
        
        return False
    
    async def execute_flow(self, flow_id: int, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Execute a flow with the given input data
        
        Args:
            flow_id: The ID of the flow to execute
            input_data: The input data for the flow
            db: Database session
            
        Returns:
            The output data from the flow execution
        """
        # Get the flow
        flow = db.query(Flow).filter(Flow.id == flow_id, Flow.is_active == True).first()
        if not flow:
            raise ValueError(f"Flow with ID {flow_id} not found or not active")
        
        # Validate connections
        is_valid, error = self.validate_connections(flow.flow_data)
        if not is_valid:
            raise ValueError(f"Invalid flow configuration: {error}")
        
        # Extract flow data
        nodes = flow.flow_data["nodes"]
        edges = flow.flow_data["edges"]
        
        # Build node lookup
        node_lookup = {}
        for node in nodes:
            node_lookup[node["id"]] = node
        
        # Build edge lists
        outgoing_edges = {}
        incoming_edges = {}
        
        for node in nodes:
            outgoing_edges[node["id"]] = []
            incoming_edges[node["id"]] = []
        
        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            outgoing_edges[source].append(edge)
            incoming_edges[target].append(edge)
        
        # Find input nodes
        input_nodes = [node for node in nodes if node.get("type") == "input"]
        
        # Initialize node values (output of each node)
        node_values = {}
        
        # Set initial values from input data
        for input_node in input_nodes:
            input_key = input_node.get("data", {}).get("input_key", "default_input")
            node_values[input_node["id"]] = input_data.get(input_key, "")
        
        # Process nodes in topological order
        # Note: We know the graph is acyclic because we validated it
        processed = set()
        
        # Keep processing until all nodes are processed
        while len(processed) < len(nodes):
            for node in nodes:
                if node["id"] in processed:
                    continue
                
                # Check if all incoming nodes are processed
                if all(edge["source"] in processed for edge in incoming_edges[node["id"]]):
                    # Process this node
                    node_type = node.get("type")
                    
                    if node_type == "input":
                        # Already set the value
                        pass
                    
                    elif node_type == "output":
                        # Get the input value from incoming edge
                        if incoming_edges[node["id"]]:
                            source_node_id = incoming_edges[node["id"]][0]["source"]
                            node_values[node["id"]] = node_values[source_node_id]
                    
                    elif node_type == "chatbot":
                        # Process through chatbot
                        try:
                            # Get input from incoming edge
                            if incoming_edges[node["id"]]:
                                source_node_id = incoming_edges[node["id"]][0]["source"]
                                input_text = node_values[source_node_id]
                                
                                # Use chatbot service to process
                                response = self.chatbot_service.chat([], input_text)
                                node_values[node["id"]] = response
                            else:
                                node_values[node["id"]] = "No input provided to chatbot node"
                        except Exception as e:
                            logger.error(f"Error processing chatbot node: {str(e)}")
                            node_values[node["id"]] = f"Error: {str(e)}"
                    
                    elif node_type == "transform":
                        # Simple transform node (just passes through for now)
                        if incoming_edges[node["id"]]:
                            source_node_id = incoming_edges[node["id"]][0]["source"]
                            node_values[node["id"]] = node_values[source_node_id]
                    
                    else:
                        # Unknown node type
                        logger.warning(f"Unknown node type: {node_type}")
                        node_values[node["id"]] = f"Unsupported node type: {node_type}"
                    
                    processed.add(node["id"])
        
        # Collect outputs
        output_data = {}
        output_nodes = [node for node in nodes if node.get("type") == "output"]
        
        for output_node in output_nodes:
            output_key = output_node.get("data", {}).get("output_key", "default_output")
            output_data[output_key] = node_values.get(output_node["id"], "")
        
        return output_data 