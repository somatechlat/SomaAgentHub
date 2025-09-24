import { BenchmarkScore } from '../../api/dashboard'

interface Props {
  scores: BenchmarkScore[]
}

export function BenchmarkTable({ scores }: Props) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="text-sm font-semibold text-slate-700">SLM Benchmark Scores</div>
      <table className="mt-3 w-full table-auto text-sm">
        <thead className="text-left text-xs uppercase text-slate-500">
          <tr>
            <th className="py-2">Provider</th>
            <th className="py-2">Model</th>
            <th className="py-2">Role</th>
            <th className="py-2">Score</th>
            <th className="py-2">Latency (ms)</th>
          </tr>
        </thead>
        <tbody>
          {scores.map((row, idx) => (
            <tr key={`${row.provider}-${row.model}-${idx}`} className="border-t border-slate-100">
              <td className="py-2 font-medium text-slate-700">{row.provider}</td>
              <td className="py-2 text-slate-600">{row.model}</td>
              <td className="py-2 text-slate-600">{row.role}</td>
              <td className="py-2 text-slate-600">{row.score.toFixed(2)}</td>
              <td className="py-2 text-slate-600">{row.latency_ms.toFixed(1)}</td>
            </tr>
          ))}
          {scores.length === 0 && (
            <tr>
              <td colSpan={5} className="py-4 text-center text-xs text-slate-500">No benchmark data yet.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
