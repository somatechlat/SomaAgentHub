/**
 * ⚠️ WE DO NOT MOCK - Real task graph visualization using D3 and Dagre
 */

import React, { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import dagre from 'dagre'

interface Task {
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  dependencies: string[]
  description: string
}

interface TaskGraphProps {
  tasks: Record<string, Task>
  onTaskClick?: (taskId: string) => void
}

export default function TaskGraph({ tasks, onTaskClick }: TaskGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!svgRef.current || Object.keys(tasks).length === 0) return

    // Clear previous graph
    d3.select(svgRef.current).selectAll('*').remove()

    // Create dagre graph
    const g = new dagre.graphlib.Graph()
    g.setGraph({ rankdir: 'TB', nodesep: 80, ranksep: 100 })
    g.setDefaultEdgeLabel(() => ({}))

    // Add nodes
    Object.entries(tasks).forEach(([taskId, task]) => {
      g.setNode(taskId, {
        label: task.description,
        width: 180,
        height: 80,
        task,
      })
    })

    // Add edges (dependencies)
    Object.entries(tasks).forEach(([taskId, task]) => {
      task.dependencies.forEach((depId) => {
        if (tasks[depId]) {
          g.setEdge(depId, taskId)
        }
      })
    })

    // Calculate layout
    dagre.layout(g)

    // Get graph dimensions
    const graphWidth = (g.graph() as any).width + 100
    const graphHeight = (g.graph() as any).height + 100

    // Create SVG
    const svg = d3
      .select(svgRef.current)
      .attr('width', graphWidth)
      .attr('height', graphHeight)

    // Create container group
    const container = svg.append('g').attr('transform', 'translate(50, 50)')

    // Draw edges
    const edges = container.append('g').attr('class', 'edges')

    g.edges().forEach((e) => {
      const edge = g.edge(e)
      const points = edge.points

      const line = d3
        .line<{ x: number; y: number }>()
        .x((d) => d.x)
        .y((d) => d.y)
        .curve(d3.curveBasis)

      edges
        .append('path')
        .attr('d', line(points))
        .attr('fill', 'none')
        .attr('stroke', '#cbd5e1')
        .attr('stroke-width', 2)
        .attr('marker-end', 'url(#arrowhead)')
    })

    // Add arrowhead marker
    svg
      .append('defs')
      .append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 0 10 10')
      .attr('refX', 9)
      .attr('refY', 5)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M 0 0 L 10 5 L 0 10 z')
      .attr('fill', '#cbd5e1')

    // Draw nodes
    const nodes = container.append('g').attr('class', 'nodes')

    g.nodes().forEach((nodeId) => {
      const node = g.node(nodeId)
      const task = node.task as Task

      // Determine color based on status
      let fillColor = '#f1f5f9' // pending
      let strokeColor = '#cbd5e1'
      let textColor = '#64748b'

      switch (task.status) {
        case 'running':
          fillColor = '#dbeafe'
          strokeColor = '#3b82f6'
          textColor = '#1e40af'
          break
        case 'completed':
          fillColor = '#dcfce7'
          strokeColor = '#22c55e'
          textColor = '#166534'
          break
        case 'failed':
          fillColor = '#fee2e2'
          strokeColor = '#ef4444'
          textColor = '#991b1b'
          break
        case 'cancelled':
          fillColor = '#fef3c7'
          strokeColor = '#f59e0b'
          textColor = '#92400e'
          break
      }

      const nodeGroup = nodes
        .append('g')
        .attr('transform', `translate(${node.x}, ${node.y})`)
        .style('cursor', 'pointer')
        .on('click', () => {
          if (onTaskClick) onTaskClick(nodeId)
        })

      // Node rectangle
      nodeGroup
        .append('rect')
        .attr('x', -node.width / 2)
        .attr('y', -node.height / 2)
        .attr('width', node.width)
        .attr('height', node.height)
        .attr('rx', 8)
        .attr('fill', fillColor)
        .attr('stroke', strokeColor)
        .attr('stroke-width', 2)

      // Task ID
      nodeGroup
        .append('text')
        .attr('text-anchor', 'middle')
        .attr('y', -15)
        .style('font-size', '12px')
        .style('font-weight', '600')
        .style('fill', textColor)
        .text(nodeId)

      // Task description (truncated)
      const description = task.description.substring(0, 25) + '...'
      nodeGroup
        .append('text')
        .attr('text-anchor', 'middle')
        .attr('y', 5)
        .style('font-size', '11px')
        .style('fill', '#6b7280')
        .text(description)

      // Status badge
      nodeGroup
        .append('text')
        .attr('text-anchor', 'middle')
        .attr('y', 25)
        .style('font-size', '10px')
        .style('font-weight', '500')
        .style('fill', textColor)
        .text(task.status.toUpperCase())
    })
  }, [tasks, onTaskClick])

  return (
    <div className="bg-white rounded-lg shadow p-6 overflow-auto">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Task Graph</h3>
      <svg ref={svgRef} className="mx-auto"></svg>
    </div>
  )
}
