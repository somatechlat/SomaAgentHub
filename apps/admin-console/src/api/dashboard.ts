export interface HealthData {
  tenant: string
  deployment_mode: string
  services: Record<string, unknown>
}

export async function fetchHealth(): Promise<HealthData> {
  const res = await fetch('/v1/dashboard/health', {
    headers: {
      'X-Tenant-ID': 'demo',
      'X-Client-Type': 'web',
      'X-Deployment-Mode': 'developer-light'
    }
  })
  if (!res.ok) {
    throw new Error('Failed to load dashboard health')
  }
  return res.json()
}

export interface BenchmarkScore {
  provider: string
  model: string
  role: string
  score: number
  latency_ms: number
}

export async function fetchBenchmarkScores(): Promise<BenchmarkScore[]> {
  const res = await fetch('/benchmark/v1/scores')
  if (!res.ok) {
    throw new Error('Failed to load benchmark scores')
  }
  const data = await res.json()
  return data.scores ?? []
}
