/**
 * ⚠️ WE DO NOT MOCK - Real API client for MAO service
 */

import axios from 'axios'

const API_BASE = '/api'

export interface Task {
  task_id?: string
  capsule_id: string
  persona_id: string
  description: string
  dependencies: string[]
  timeout_seconds?: number
  retry_attempts?: number
  metadata?: Record<string, any>
}

export interface CreateProjectRequest {
  project_name: string
  tasks: Task[]
  execution_mode?: 'sequential' | 'parallel' | 'dag'
  workspace_config?: Record<string, any>
  git_repo_url?: string
  artifact_storage?: string
  notify_webhooks?: string[]
  max_parallel_tasks?: number
}

export interface Project {
  project_id: string
  project_name: string
  workflow_id: string
  run_id: string
  status: string
  created_at: string
}

export interface ProjectStatus {
  project_id: string
  workflow_id: string
  current_status: string
  workspace_id: string | null
  completed_tasks: number
  total_tasks: number
  task_results: Record<string, any>
}

// API client
const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const maoApi = {
  // Create new project
  createProject: async (data: CreateProjectRequest): Promise<Project> => {
    const response = await client.post('/projects', data)
    return response.data
  },

  // Get project status
  getProjectStatus: async (projectId: string): Promise<ProjectStatus> => {
    const response = await client.get(`/projects/${projectId}`)
    return response.data
  },

  // Get project result
  getProjectResult: async (projectId: string): Promise<any> => {
    const response = await client.get(`/projects/${projectId}/result`)
    return response.data
  },

  // Cancel project
  cancelProject: async (projectId: string): Promise<void> => {
    await client.post(`/projects/${projectId}/cancel`)
  },

  // List projects
  listProjects: async (limit: number = 10): Promise<{ projects: any[] }> => {
    const response = await client.get('/projects', { params: { limit } })
    return response.data
  },

  // WebSocket connection for real-time updates
  connectWebSocket: (
    projectId: string,
    onMessage: (data: any) => void,
    onError?: (error: any) => void
  ): WebSocket => {
    const ws = new WebSocket(`ws://localhost:8007/v1/projects/${projectId}/stream`)

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      onMessage(data)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      if (onError) onError(error)
    }

    return ws
  },
}
