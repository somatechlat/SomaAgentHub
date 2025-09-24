import './styles.css'
import { useEffect, useState } from 'react'
import { fetchBenchmarkScores, fetchHealth, BenchmarkScore, HealthData } from './api/dashboard'
import { HealthPanel } from './components/dashboard/HealthPanel'
import { BenchmarkTable } from './components/dashboard/BenchmarkTable'
import { MarketplaceBuilder } from './components/marketplace/MarketplaceBuilder'

export function App() {
  const [health, setHealth] = useState<HealthData | null>(null)
  const [scores, setScores] = useState<BenchmarkScore[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchHealth().then(setHealth).catch((err) => setError(err.message))
    fetchBenchmarkScores().then(setScores).catch((err) => setError(err.message))
  }, [])

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto max-w-6xl py-12 px-6 space-y-6">
        <header>
          <h1 className="text-3xl font-semibold">SomaGent Agent One Sight</h1>
          <p className="mt-3 text-slate-600">Live health, benchmark, and observability for SomaStack.</p>
        </header>
        {error && <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
        <div className="grid gap-4 md:grid-cols-2">
          {health && <HealthPanel data={health} />}
          <BenchmarkTable scores={scores} />
        </div>
        <MarketplaceBuilder />
      </div>
    </div>
  )
}
