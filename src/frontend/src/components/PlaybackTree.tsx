import React, { useEffect, useState } from 'react';
import mermaid from 'mermaid';

export interface TraceNode {
  id: number;
  parent_trace_id: number | null;
  agent_role: string;
  is_success: boolean;
  children: TraceNode[];
}

export function transformTracesToMermaid(nodes: TraceNode[]): string {
  let graph = 'graph TD\n';
  graph += '  classDef success fill:#10b981,stroke:#047857,color:white;\n';
  graph += '  classDef fail fill:#ef4444,stroke:#b91c1c,color:white;\n\n';

  function traverse(node: TraceNode) {
    if (node.is_success) {
      graph += `  class ${node.id} success\n`;
    } else {
      graph += `  class ${node.id} fail\n`;
    }

    // Node definition (simple display ID)
    graph += `  ${node.id}["[${node.agent_role}] Trace ${node.id}"]\n`;

    node.children.forEach(child => {
      graph += `  ${node.id} --> ${child.id}\n`;
      traverse(child);
    });
  }

  nodes.forEach(n => traverse(n));
  return graph;
}

const PlaybackTree: React.FC<{ taskId: string }> = ({ taskId }) => {
  const [nodes, setNodes] = useState<TraceNode[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    mermaid.initialize({ startOnLoad: false, theme: 'dark' });

    fetch(`/api/v1/tasks/${taskId}/dag-tree`)
      .then(res => res.json())
      .then(data => {
        setNodes(data);
        setLoading(false);
      })
      .catch((e) => {
        console.error(e);
        setLoading(false);
      });
  }, [taskId]);

  useEffect(() => {
    if (!loading && nodes.length > 0) {
      mermaid.contentLoaded();
    }
  }, [loading, nodes]);

  if (loading) return <div className="text-cyan-500 animate-pulse">Loading DAG...</div>;
  if (nodes.length === 0) return <div className="text-slate-500">暂无回溯数据</div>;

  const mermaidSyntax = transformTracesToMermaid(nodes);

  return (
    <div className="w-full bg-slate-900 border border-slate-700 rounded p-4 shadow-xl">
      <h3 className="text-emerald-400 mb-2 border-b border-slate-700 pb-2">DAG Playback 回溯图</h3>
      <div className="overflow-auto custom-scrollbar flex justify-center">
        <pre className="mermaid">{mermaidSyntax}</pre>
      </div>
    </div>
  );
};

export default PlaybackTree;
