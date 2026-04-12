import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import PlaybackTree, { transformTracesToMermaid } from '../src/components/PlaybackTree';
import type { TraceNode } from '../src/components/PlaybackTree';

// Mock fetch
globalThis.fetch = vi.fn() as any;

describe('PlaybackTree DAG Renderer', () => {
  it('函数 transformTracesToMermaid 应当能正确翻译树结构', () => {
    const mockData: TraceNode[] = [
      {
        id: 1, parent_trace_id: null, is_success: true, agent_role: "Gen", 
        children: [
          { id: 2, parent_trace_id: 1, is_success: false, agent_role: "Gen", children: [] },
          { id: 3, parent_trace_id: 1, is_success: true, agent_role: "Eval", children: [] }
        ]
      }
    ];

    const mermaidSyntax = transformTracesToMermaid(mockData);
    
    // Check connections
    expect(mermaidSyntax).toContain('1 --> 2');
    expect(mermaidSyntax).toContain('1 --> 3');
    // Check specific styling coloring based on is_success
    expect(mermaidSyntax).toContain('classDef fail fill:#ef4444');
    expect(mermaidSyntax).toContain('class 2 fail');
  });

  it('如果 API 还没有数据，渲染应当能够优雅降级', async () => {
    (globalThis.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ([]),
    });

    render(<PlaybackTree taskId="1" />);
    
    await waitFor(() => {
      expect(screen.getByText(/暂无回溯数据/i)).toBeInTheDocument();
    });
  });
});
