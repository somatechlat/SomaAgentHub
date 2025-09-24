import { FormEvent, useState } from 'react'

const initialForm = {
  id: '',
  name: '',
  version: '1.0.0',
  summary: '',
  persona: '',
  tools: '',
  policy: ''
}

export function MarketplaceBuilder() {
  const [form, setForm] = useState(initialForm)
  const [message, setMessage] = useState<string | null>(null)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    try {
      const payload = {
        id: form.id,
        name: form.name,
        version: form.version,
        summary: form.summary,
        persona: form.persona,
        tools: form.tools.split(',').map((t) => t.trim()).filter(Boolean),
        policy: form.policy
      }
      const res = await fetch('/v1/marketplace/capsules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (!res.ok) {
        throw new Error(await res.text())
      }
      setMessage('Capsule saved!')
      setForm(initialForm)
    } catch (err) {
      setMessage((err as Error).message)
    }
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-700">Marketplace Builder</h2>
      <p className="mt-2 text-sm text-slate-600">Draft a Task Capsule template and submit it to the settings service.</p>
      {message && <div className="mt-3 rounded-xl border border-slate-200 bg-slate-100 p-2 text-xs text-slate-700">{message}</div>}
      <form className="mt-4 grid gap-3" onSubmit={handleSubmit}>
        <input className="rounded-xl border border-slate-200 px-3 py-2 text-sm" placeholder="Capsule ID" name="id" value={form.id} onChange={handleChange} required />
        <input className="rounded-xl border border-slate-200 px-3 py-2 text-sm" placeholder="Name" name="name" value={form.name} onChange={handleChange} required />
        <input className="rounded-xl border border-slate-200 px-3 py-2 text-sm" placeholder="Version" name="version" value={form.version} onChange={handleChange} />
        <textarea className="rounded-xl border border-slate-200 px-3 py-2 text-sm" placeholder="Summary" name="summary" value={form.summary} onChange={handleChange} rows={2} />
        <input className="rounded-xl border border-slate-200 px-3 py-2 text-sm" placeholder="Persona mold" name="persona" value={form.persona} onChange={handleChange} />
        <input className="rounded-xl border border-slate-200 px-3 py-2 text-sm" placeholder="Tools (comma separated)" name="tools" value={form.tools} onChange={handleChange} />
        <textarea className="rounded-xl border border-slate-200 px-3 py-2 text-sm" placeholder="Policy / guardrails" name="policy" value={form.policy} onChange={handleChange} rows={2} />
        <button className="inline-flex items-center justify-center rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white">Save Capsule</button>
      </form>
    </section>
  )
}
