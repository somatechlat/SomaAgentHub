import React, { useMemo, useState, useEffect } from 'react'

/**
 * SOMAAGENT — PERSONA-DRIVEN UI PROTOTYPE (near-real)
 * ---------------------------------------------------
 * Goals:
 * - Concrete, shippable UI shell for SomaAgent running against SomaBrain.
 * - Persona-first: capabilities & tools filtered by persona, device, and mode.
 * - Makes the RAG pipeline visible: rewrites → multi-retrieve → fusion → rerank → trace.
 * - Two-key approvals and Commit diff view; Evidence pinning; Teach Rule surface.
 * - OS/Container abstraction panel to show how “full toolchains on mobile” are capability-gated but docker-enabled.
 *
 * Notes:
 * - This is a static prototype with simulated events. Wire API calls to SomaBrain later.
 * - No external CSS needed; Tailwind-like utility classes are embedded via inline styles.
 */

// ---------- Tiny design system ----------
const cls = (...xs: (string | false | null | undefined)[]) => xs.filter(Boolean).join(' ')
const Button: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement> & {variant?: 'primary' | 'ghost' | 'danger' | 'success'}> = ({variant = 'primary', className, ...p}) => (
  <button
    {...p}
    className={cls(
      'px-3 py-2 rounded-2xl text-sm font-medium transition-all',
      variant === 'primary' && 'bg-black text-white hover:opacity-90 shadow',
      variant === 'ghost' && 'bg-white/60 hover:bg-white text-black border border-black/10',
      variant === 'danger' && 'bg-red-600 text-white hover:bg-red-700',
      variant === 'success' && 'bg-emerald-600 text-white hover:bg-emerald-700',
      className
    )}
  />
)
const Chip: React.FC<{label:string, active?:boolean, onClick?:()=>void}> = ({label, active, onClick}) => (
  <span onClick={onClick}
        style={{cursor:onClick?'pointer':'default'}}
        className={cls('inline-flex items-center px-2 py-1 rounded-full text-xs mr-2 mb-2 border', active? 'bg-black text-white border-black':'bg-white/70 text-black border-black/10')}>{label}</span>
)
const Card: React.FC<{title?:string, subtitle?:string, right?:React.ReactNode, children?:React.ReactNode, tone?:'default'|'accent'|'warn', className?: string}> = ({title, subtitle, right, children, tone='default', className}) => (
  <div className={cls('rounded-3xl p-4 border backdrop-blur',
    tone==='default' && 'bg-white/70 border-black/10',
    tone==='accent' && 'bg-indigo-50/80 border-indigo-200',
    tone==='warn' && 'bg-amber-50/80 border-amber-200',
    className
  )}>
    {(title || right || subtitle) && (
      <div className='flex items-start justify-between mb-3'>
        <div>
          {title && <div className='text-sm font-semibold'>{title}</div>}
          {subtitle && <div className='text-xs text-black/60'>{subtitle}</div>}
        </div>
        {right}
      </div>
    )}
    <div>{children}</div>
  </div>
)

// ---------- Sample data ----------
const PERSONAS = [
  { id: 'dev', name: 'Developer', emoji: '🧑‍💻', risk: 'medium', summary: 'Builds, tests, and ships code. Prefers traceable evidence.', caps: ['web:read','fs:read','shell:exec','docker:run','git:read','git:write'] },
  { id: 'researcher', name: 'Researcher', emoji: '🔬', risk: 'low', summary: 'Reads, synthesizes, and verifies. Prefers high-precision context.', caps: ['web:read','pdf:parse','graph:walk'] },
  { id: 'educator', name: 'Educator', emoji: '🧑‍🏫', risk: 'low', summary: 'Explains and simplifies. No destructive tools.', caps: ['web:read'] },
  { id: 'ops', name: 'Ops', emoji: '🛡️', risk: 'high', summary: 'Automates environments, migrations, backups. Strong approvals required.', caps: ['docker:run','cloud:api','shell:exec'] },
]
const TOOLS = [
  { name:'browser.extract', label:'Browser — Extract', scope:'web:read', risk:'low'},
  { name:'files.read', label:'Files — Read', scope:'fs:read', risk:'low'},
  { name:'terminal.exec', label:'Terminal — Exec', scope:'shell:exec', risk:'high'},
  { name:'docker.run', label:'Docker — Run', scope:'docker:run', risk:'high'},
  { name:'graph.walk', label:'Graph — Walk', scope:'graph:walk', risk:'low'},
]
const DEVICES = [
  { id:'desktop', name:'Desktop', icon:'💻', notes:'Full UI, full tools subject to policy.' },
  { id:'mobile', name:'Mobile', icon:'📱', notes:'Minimal tools; docker runs via remote sandbox.' },
  { id:'docker', name:'Docker Sandbox', icon:'🐳', notes:'Isolated toolchain; mount policy applies.' },
  { id:'remote', name:'Remote Runner', icon:'🛰️', notes:'Run tools on a remote host; streamed outputs.' },
]

// ---------- Main component ----------
export default function SomaAgentPrototype(){
  const [tenant, setTenant] = useState('acme')
  const [personaId, setPersonaId] = useState('dev')
  const persona = useMemo(()=> PERSONAS.find(p=>p.id===personaId)!, [personaId])
  const [device, setDevice] = useState('desktop')
  const [mode, setMode] = useState<'dev'|'testing'|'training'>('dev')
  const [goal, setGoal] = useState('Create a secure S3 backup policy with lifecycle rules and cost estimate.')
  const [approvals, setApprovals] = useState({policy:false, human:false})
  const [step, setStep] = useState<'plan'|'evidence'|'pot'|'verify'|'commit'|'learn'>('plan')
  const [events, setEvents] = useState<{ts:number, kind:string, data:any}[]>([])
  const [trace, setTrace] = useState<any[]>([])
  const [contexts, setContexts] = useState<any[]>([])
  const [rules, setRules] = useState<{id:string, if:string, then:string, severity:'warn'|'block'}[]>([])
  const [budget, setBudget] = useState({tokens: 200000, cost: 10, time: 120}) // visual only

  // Tool filtering by persona + device
  const allowedTools = useMemo(()=>{
    return TOOLS.filter(t=> persona.caps.includes(t.scope))
                .filter(t=> device==='mobile' ? t.risk==='low' : true)
  }, [persona, device])

  // Simulate a run
  const run = async ()=>{
    setEvents(e=>[...e, {ts:Date.now(), kind:'state', data:{state:'planning'}}])
    setStep('evidence')
    setTimeout(()=>{
      // RAG trace (simulated)
      const t = [
        {stage:'mqe', samples:['S3 backup retention policy','S3 lifecycle transition rules','Backup cost optimization S3']},
        {stage:'hyde', ok:true, len:132},
        {stage:'retriever', mode:'keyword', k:20},
        {stage:'retriever', mode:'hrr', k:20},
        {stage:'graph_neighbors', seed:11, added:6},
        {stage:'fusion', method:'rrf', candidates:27},
        {stage:'rerank', model:'bge', before:27, after:8},
      ]
      setTrace(t)
      const ctx = [
        {id:'doc:aws-policy', title:'AWS S3 Backup & Lifecycle (official)', score:0.86, rrf:0.31, rerank:0.91},
        {id:'post:cost-optim', title:'Cost optimization for cold storage', score:0.79, rrf:0.29, rerank:0.84},
        {id:'kb:acl', title:'ACL vs Bucket Policy implications', score:0.72, rrf:0.25, rerank:0.78},
      ]
      setContexts(ctx)
      setEvents(e=>[...e, {ts:Date.now(), kind:'evidence', data:{count:ctx.length}}])
      setStep('pot')
      setTimeout(()=>{
        setEvents(e=>[...e, {ts:Date.now(), kind:'pot', data:{claims:3}}])
        setStep('verify')
      }, 800)
    }, 800)
  }

  const approve = (kind:'policy'|'human')=>{
    setApprovals(a=>({ ...a, [kind]: true }))
    setEvents(e=>[...e, {ts:Date.now(), kind:'approve', data:{kind}}])
  }

  useEffect(()=>{
    if(step==='verify' && approvals.policy && approvals.human){
      setStep('commit')
      setEvents(e=>[...e, {ts:Date.now(), kind:'state', data:{state:'awaiting_commit'}}])
      setTimeout(()=>{
        setEvents(e=>[...e, {ts:Date.now(), kind:'commit', data:{diff:'POST /remember intent, plan, evidence, verification'}}])
        setStep('learn')
        setTimeout(()=>{
          setEvents(e=>[...e, {ts:Date.now(), kind:'state', data:{state:'done'}}])
        }, 700)
      }, 800)
    }
  }, [approvals, step])

  const pinEvidence = (c:any)=>{
    setEvents(e=>[...e, {ts:Date.now(), kind:'remember', data:{type:'evidence', id:c.id}}])
  }

  const teachRule = ()=>{
    const id = 'rule_'+Math.random().toString(36).slice(2)
    const r = { id, if:'query contains "policy"', then:'boost documents tagged:policy by 1.2x', severity:'warn' as const }
    setRules(rs=>[r, ...rs])
    setEvents(e=>[...e, {ts:Date.now(), kind:'rule', data:r}])
  }

  // ---------- Render ----------
  return (
    <div style={styles.page}>
      <Header tenant={tenant} setTenant={setTenant} mode={mode} setMode={setMode} />
      <div style={styles.layout}>
        {/* Left rail */}
        <div style={styles.leftRail}>
          <Card title="Persona" subtitle="Who am I right now?" right={<span>{persona.emoji}</span>}>
            <div className="flex gap-2 flex-wrap">
              {PERSONAS.map(p=> (
                <Button key={p.id} variant={p.id===personaId?'primary':'ghost'} onClick={()=>setPersonaId(p.id)}>{p.emoji} {p.name}</Button>
              ))}
            </div>
            <div className="mt-3 text-xs text-black/70">{persona.summary}</div>
            <div className="mt-3">
              <div className="text-xs font-semibold mb-1">Capabilities</div>
              <div>{persona.caps.map(c=><Chip key={c} label={c} />)}</div>
            </div>
          </Card>

          <Card title="Device" subtitle="Where am I running?">
            <div className="grid gap-2">
              {DEVICES.map(d=> (
                <Button key={d.id} variant={d.id===device?'primary':'ghost'} onClick={()=>setDevice(d.id)}>{d.icon} {d.name}</Button>
              ))}
            </div>
            <div className="mt-2 text-[11px] text-black/60">{DEVICES.find(d=>d.id===device)?.notes}</div>
          </Card>

          <Card title="Execution Context" subtitle="OS / Container Abstraction">
            <div className="text-xs text-black/70 mb-2">Choose where heavy tools run; mobile offloads to Docker/remote.</div>
            <div className="grid grid-cols-2 gap-2">
              <Chip label="Local OS" active={device==='desktop'} onClick={()=>setDevice('desktop')} />
              <Chip label="Docker Sandbox" active={device==='docker'} onClick={()=>setDevice('docker')} />
              <Chip label="Remote Runner" active={device==='remote'} onClick={()=>setDevice('remote')} />
              <Chip label="Secure Mounts" />
            </div>
            <div className="mt-2 text-[11px] text-black/60">Policy gates decide mounts, network, and secrets exposure.</div>
          </Card>

          <Card title="Intent" subtitle="What should we achieve?" className="mt-3">
            <textarea value={goal} onChange={e=>setGoal(e.target.value)} rows={6} className="w-full text-sm p-2 rounded-xl border border-black/10"/>
            <div className="flex gap-2 mt-3">
              <Button onClick={run}>Run Plan</Button>
              <Button variant="ghost" onClick={teachRule}>Teach Rule</Button>
            </div>
          </Card>
        </div>

        {/* Center */}
        <div style={styles.center}>
          <div className="grid gap-3">
            <Stepper step={step} />
            {step==='plan' && (
              <Card title="Plan" subtitle="Auto-generated from intent" tone="accent">
                <ol className="list-decimal ml-4 text-sm">
                  <li>Gather evidence from AWS docs and prior policies.</li>
                  <li>Build PoT with claims on retention, lifecycle, cost.</li>
                  <li>Verify groundedness and numeric thresholds.</li>
                  <li>Request approvals; commit minimal artifacts.</li>
                </ol>
              </Card>
            )}
            {(step==='evidence' || contexts.length>0) && (
              <Card title="Evidence" subtitle="Pinned contexts from RAG">
                <div className="grid gap-2">
                  {contexts.map(c=> (
                    <div key={c.id} className="flex items-start justify-between p-2 rounded-xl border border-black/10 bg-white/60">
                      <div>
                        <div className="text-sm font-medium">{c.title}</div>
                        <div className="text-xs text-black/60">score {c.score.toFixed(2)} · rrf {c.rrf.toFixed(2)} · rerank {c.rerank.toFixed(2)}</div>
                      </div>
                      <Button variant="ghost" onClick={()=>pinEvidence(c)}>Pin as Evidence</Button>
                    </div>
                  ))}
                  {contexts.length===0 && <div className="text-xs text-black/60">No contexts yet. Click “Run Plan”.</div>}
                </div>
              </Card>
            )}
            {step!=='plan' && (
              <Card title="Proof-of-Thought" subtitle="Claims linked to evidence">
                <div className="text-sm">Claim: “Retention must be ≥ 90 days; transition to Glacier after 30 days; versioning required.”
                  <div className="text-xs text-black/60 mt-1">Supports: AWS S3 Policy Docs, Cost Guide</div>
                </div>
              </Card>
            )}
            {step!=='plan' && (
              <Card title="Verification" subtitle="Groundedness · Numeric thresholds">
                <div className="text-sm">Self-consistency: <span className="text-emerald-700 font-semibold">PASS</span> · Groundedness: <span className="text-emerald-700 font-semibold">PASS</span></div>
                <div className="text-xs text-black/60">Checks reflect current contexts and rules.</div>
              </Card>
            )}
            {(step==='commit' || step==='learn' || (approvals.policy && approvals.human)) && (
              <Card title="Commit (dry-run)" subtitle="Minimal, reversible changes">
                <div className="bg-black/90 text-white rounded-xl p-3 text-xs overflow-auto">
{`diff --git a/memory b/memory
+ remember(intent)
+ remember(plan)
+ link(intent -> plan)
`}
                </div>
              </Card>
            )}
          </div>
        </div>

        {/* Right rail */}
        <div style={styles.rightRail}>
          <Card title="RAG Trace" subtitle="How we built context">
            <div className="text-xs">
              {trace.map((t,i)=> (
                <div key={i} className="flex items-start gap-2 py-1">
                  <span className="text-black/50">●</span>
                  <div>
                    <div className="font-medium">{t.stage}</div>
                    {t.samples && <div className="text-black/60">{t.samples.slice(0,2).join(' · ')}</div>}
                    {t.mode && <div className="text-black/60">retriever: {t.mode}</div>}
                    {t.method && <div className="text-black/60">fusion: {t.method}</div>}
                    {t.model && <div className="text-black/60">rerank: {t.model}</div>}
                  </div>
                </div>
              ))}
              {trace.length===0 && <div className="text-black/60">No trace yet.</div>}
            </div>
          </Card>

          <Card title="Approvals" subtitle="Two-key gate" right={<span className="text-xs text-black/60">policy + human</span>}>
            <div className="flex gap-2">
              <Button variant={approvals.policy?'success':'ghost'} onClick={()=>approve('policy')}>{approvals.policy?'✓':'◻'} Policy</Button>
              <Button variant={approvals.human?'success':'ghost'} onClick={()=>approve('human')}>{approvals.human?'✓':'◻'} Human</Button>
            </div>
          </Card>

          <Card title="Rules (Teach)" subtitle="Bias future retrieval">
            <div className="text-xs mb-2 text-black/60">Rules are stored in SomaBrain and applied during /rag retrieval.</div>
            <div className="grid gap-2">
              {rules.map(r=> (
                <div key={r.id} className="p-2 rounded-xl border border-black/10 bg-white/60">
                  <div className="text-xs font-medium">IF: {r.if}</div>
                  <div className="text-xs">THEN: {r.then}</div>
                  <div className="text-[10px] text-black/50">severity: {r.severity}</div>
                </div>
              ))}
              {rules.length===0 && <div className="text-xs text-black/60">No rules yet. Click “Teach Rule”.</div>}
            </div>
          </Card>

          <Card title="Events" subtitle="Live stream">
            <div className="h-44 overflow-auto border border-black/10 rounded-xl p-2 bg-white/60 text-[11px]">
              {events.slice().reverse().map((ev,i)=> (
                <div key={i} className="mb-1"><span className="text-black/50">{new Date(ev.ts).toLocaleTimeString()} — </span><span className="font-medium">{ev.kind}</span> <span className="text-black/60">{JSON.stringify(ev.data)}</span></div>
              ))}
              {events.length===0 && <div className="text-black/60">No events yet.</div>}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}

// ---------- Header ----------
const Header: React.FC<{tenant:string, setTenant:(x:string)=>void, mode:'dev'|'testing'|'training', setMode:(m:any)=>void}> = ({tenant,setTenant,mode,setMode}) => {
  return (
    <div style={styles.header}>
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-xl bg-black text-white grid place-items-center font-bold">Σ</div>
        <div>
          <div className="font-semibold">SomaAgent</div>
          <div className="text-xs text-black/60">Persona-driven agent UI</div>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <select value={tenant} onChange={e=>setTenant(e.target.value)} className="text-sm border border-black/10 rounded-xl px-2 py-1 bg-white/70">
          <option value="acme">Tenant: acme</option>
          <option value="lab">Tenant: lab</option>
          <option value="school">Tenant: school</option>
        </select>
        <select value={mode} onChange={e=>setMode(e.target.value as any)} className="text-sm border border-black/10 rounded-xl px-2 py-1 bg-white/70">
          <option value="dev">Mode: Dev</option>
          <option value="testing">Mode: Testing</option>
          <option value="training">Mode: Training</option>
        </select>
      </div>
    </div>
  )
}

// ---------- Styles ----------
const styles: Record<string, React.CSSProperties> = {
  page: {
    fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial',
    minHeight: '100vh',
    background: 'radial-gradient(1200px 600px at -10% -20%, #c7d2fe66 0%, transparent 70%), radial-gradient(900px 500px at 110% 0%, #fbcfe866 0%, transparent 70%), linear-gradient(180deg, #f8fafc, #ffffff)'
  },
  header: {
    display: 'flex', alignItems:'center', justifyContent:'space-between',
    padding: '16px 20px', position:'sticky', top:0, zIndex:20,
    borderBottom: '1px solid rgba(0,0,0,0.06)', backdropFilter:'blur(8px)', background:'rgba(255,255,255,0.7)'
  },
  layout: {
    display:'grid', gridTemplateColumns:'360px 1fr 360px', gap: 16, padding: 16,
    maxWidth: 1400, margin: '0 auto'
  },
  leftRail: { display:'grid', gap:12 },
  center: { display:'grid', gap:12 },
  rightRail: { display:'grid', gap:12 }
}

// ---------- Stepper ----------
const Stepper: React.FC<{step: 'plan'|'evidence'|'pot'|'verify'|'commit'|'learn'}> = ({step}) => {
  const steps = [
    {id:'plan', label:'Plan'},
    {id:'evidence', label:'Evidence'},
    {id:'pot', label:'PoT'},
    {id:'verify', label:'Verify'},
    {id:'commit', label:'Commit'},
    {id:'learn', label:'Learn'},
  ] as const
  return (
    <div className="flex items-center justify-between bg-white/70 border border-black/10 rounded-3xl px-3 py-2">
      {steps.map((s, idx)=>{
        const active = s.id===step
        const done = steps.findIndex(x=>x.id===step) > idx
        return (
          <div key={s.id} className="flex items-center gap-2">
            <div className={cls('w-6 h-6 rounded-full grid place-items-center text-xs border', active? 'bg-black text-white border-black': done? 'bg-emerald-600 text-white border-emerald-700':'bg-white text-black border-black/10')}>{done?'✓':idx+1}
            </div>
            <div className={cls('text-sm', active?'font-semibold':'text-black/60')}>{s.label}</div>
          </div>
        )
      })}
    </div>
  )
}
