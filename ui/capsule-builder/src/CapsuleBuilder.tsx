/*
 * ⚠️ WE DO NOT MOCK - Capsule Builder visual UI (React + TypeScript).
 * 
 * Drag-and-drop interface for building task capsules:
 * - Visual workflow designer
 * - Tool selector palette
 * - Parameter configuration
 * - Real-time validation
 * - Capsule preview and testing
 */

import React, { useState, useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Background,
  Controls,
  MiniMap,
  Connection,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow.css';

// Tool categories from tool ecosystem
const TOOL_CATEGORIES = [
  { id: 'project', name: 'Project Management', tools: ['Plane', 'Jira', 'GitHub Projects'] },
  { id: 'code', name: 'Code & Repos', tools: ['GitHub', 'GitLab'] },
  { id: 'docs', name: 'Documentation', tools: ['Notion', 'Confluence'] },
  { id: 'comm', name: 'Communication', tools: ['Slack', 'Discord'] },
  { id: 'infra', name: 'Infrastructure', tools: ['Terraform', 'AWS', 'Kubernetes'] },
  { id: 'design', name: 'Design', tools: ['Penpot', 'Figma'] },
];

interface CapsuleNode extends Node {
  data: {
    label: string;
    tool: string;
    action: string;
    parameters: Record<string, any>;
    outputs: string[];
  };
}

const CapsuleBuilder: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState<CapsuleNode>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<CapsuleNode | null>(null);
  const [capsuleName, setCapsuleName] = useState('');
  const [capsuleDescription, setCapsuleDescription] = useState('');

  // Add node to canvas
  const addToolNode = useCallback((tool: string, action: string) => {
    const newNode: CapsuleNode = {
      id: `node-${Date.now()}`,
      type: 'default',
      position: { x: Math.random() * 400, y: Math.random() * 400 },
      data: {
        label: `${tool}: ${action}`,
        tool,
        action,
        parameters: {},
        outputs: [],
      },
    };
    
    setNodes((nds) => [...nds, newNode]);
  }, [setNodes]);

  // Connect nodes
  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  // Select node for editing
  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node as CapsuleNode);
  }, []);

  // Update node parameters
  const updateNodeParameter = useCallback((paramName: string, value: any) => {
    if (!selectedNode) return;

    setNodes((nds) =>
      nds.map((node) =>
        node.id === selectedNode.id
          ? {
              ...node,
              data: {
                ...node.data,
                parameters: {
                  ...node.data.parameters,
                  [paramName]: value,
                },
              },
            }
          : node
      )
    );
  }, [selectedNode, setNodes]);

  // Save capsule
  const saveCapsule = async () => {
    const capsule = {
      name: capsuleName,
      description: capsuleDescription,
      nodes: nodes.map((node) => ({
        id: node.id,
        tool: node.data.tool,
        action: node.data.action,
        parameters: node.data.parameters,
        outputs: node.data.outputs,
      })),
      edges: edges.map((edge) => ({
        from: edge.source,
        to: edge.target,
      })),
    };

    const response = await fetch('/api/capsules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(capsule),
    });

    if (response.ok) {
      alert('Capsule saved successfully!');
    }
  };

  // Test capsule
  const testCapsule = async () => {
    const response = await fetch('/api/capsules/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nodes, edges }),
    });

    const result = await response.json();
    console.log('Test result:', result);
  };

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      {/* Left Panel - Tool Palette */}
      <div style={{ width: '300px', borderRight: '1px solid #ccc', padding: '20px', overflowY: 'auto' }}>
        <h2>Capsule Builder</h2>
        
        <div style={{ marginBottom: '20px' }}>
          <input
            type="text"
            placeholder="Capsule Name"
            value={capsuleName}
            onChange={(e) => setCapsuleName(e.target.value)}
            style={{ width: '100%', padding: '8px', marginBottom: '10px' }}
          />
          <textarea
            placeholder="Description"
            value={capsuleDescription}
            onChange={(e) => setCapsuleDescription(e.target.value)}
            style={{ width: '100%', padding: '8px', height: '60px' }}
          />
        </div>

        <h3>Tool Palette</h3>
        {TOOL_CATEGORIES.map((category) => (
          <details key={category.id} style={{ marginBottom: '10px' }}>
            <summary style={{ fontWeight: 'bold', cursor: 'pointer' }}>{category.name}</summary>
            <ul style={{ paddingLeft: '20px' }}>
              {category.tools.map((tool) => (
                <li key={tool} style={{ marginBottom: '5px' }}>
                  <button
                    onClick={() => addToolNode(tool, 'default_action')}
                    style={{
                      padding: '5px 10px',
                      cursor: 'pointer',
                      border: '1px solid #007bff',
                      background: '#007bff',
                      color: 'white',
                      borderRadius: '4px',
                    }}
                  >
                    Add {tool}
                  </button>
                </li>
              ))}
            </ul>
          </details>
        ))}

        <div style={{ marginTop: '20px' }}>
          <button
            onClick={saveCapsule}
            style={{
              width: '100%',
              padding: '10px',
              background: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              marginBottom: '10px',
            }}
          >
            💾 Save Capsule
          </button>
          <button
            onClick={testCapsule}
            style={{
              width: '100%',
              padding: '10px',
              background: '#ffc107',
              color: 'black',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            🧪 Test Capsule
          </button>
        </div>
      </div>

      {/* Center - Canvas */}
      <div style={{ flex: 1 }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          fitView
        >
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </div>

      {/* Right Panel - Node Editor */}
      {selectedNode && (
        <div style={{ width: '300px', borderLeft: '1px solid #ccc', padding: '20px', overflowY: 'auto' }}>
          <h3>Node Configuration</h3>
          <p><strong>Tool:</strong> {selectedNode.data.tool}</p>
          <p><strong>Action:</strong> {selectedNode.data.action}</p>

          <h4>Parameters</h4>
          <div>
            <input
              type="text"
              placeholder="Parameter name"
              onBlur={(e) => {
                if (e.target.value) {
                  updateNodeParameter(e.target.value, '');
                }
              }}
              style={{ width: '100%', padding: '8px', marginBottom: '10px' }}
            />
          </div>

          {Object.entries(selectedNode.data.parameters).map(([key, value]) => (
            <div key={key} style={{ marginBottom: '10px' }}>
              <label>{key}</label>
              <input
                type="text"
                value={value as string}
                onChange={(e) => updateNodeParameter(key, e.target.value)}
                style={{ width: '100%', padding: '8px' }}
              />
            </div>
          ))}

          <h4>Outputs</h4>
          <ul>
            {selectedNode.data.outputs.map((output, idx) => (
              <li key={idx}>{output}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default CapsuleBuilder;
