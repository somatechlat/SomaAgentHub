import { HealthData } from '../../api/dashboard'

interface Props {
  data: HealthData
}

export function HealthPanel({ data }: Props) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="text-sm font-semibold text-slate-700">Environment</div>
      <div className="mt-1 text-xs text-slate-500">Tenant: {data.tenant} · Mode: {data.deployment_mode}</div>
      <div className="mt-3 grid gap-2 text-sm">
        {Object.entries(data.services).map(([service, status]) => (
          <div key={service} className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 px-3 py-2">
            <span className="font-medium capitalize">{service}</span>
            <span className="text-xs text-slate-500">{typeof status === 'string' ? status : JSON.stringify(status)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
