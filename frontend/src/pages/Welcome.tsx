import { useCallback, useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { CheckCircle2, Clock, LogOut, Play, Plus, RotateCcw, ShieldAlert, Trash2, X } from 'lucide-react'
import { api, errMsg, type SubjectStatus } from '../api'
import { useAuth } from '../auth'
import { Alert, FullLoader, Shell, Spinner } from '../components/ui'

export default function Welcome() {
  const { user, logout, refresh } = useAuth()
  const nav = useNavigate()
  const [subs, setSubs] = useState<SubjectStatus[] | null>(null)
  const [input, setInput] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const [rules, setRules] = useState<SubjectStatus | null>(null)

  const load = useCallback(async () => {
    try { const { data } = await api.get<SubjectStatus[]>('/assessment/summary'); setSubs(data) }
    catch (e) { setErr(errMsg(e)) }
  }, [])
  useEffect(() => { load(); refresh() }, [load, refresh])

  const saveSubjects = async (names: string[]) => {
    setErr(''); setBusy(true)
    try { await api.post('/subjects/confirm', { subjects: names }); await load() }
    catch (e) { setErr(errMsg(e)) } finally { setBusy(false) }
  }
  const add = () => {
    const parts = input.split(',').map((s) => s.trim()).filter(Boolean)
    if (!parts.length || !subs) return
    const names = [...subs.map((s) => s.subject_name)]
    parts.forEach((p) => { if (!names.some((n) => n.toLowerCase() === p.toLowerCase())) names.push(p) })
    setInput(''); saveSubjects(names)
  }
  const remove = (name: string) => {
    if (!subs || subs.length <= 1) return setErr('Keep at least one subject.')
    saveSubjects(subs.filter((s) => s.subject_name !== name).map((s) => s.subject_name))
  }

  const start = async (s: SubjectStatus) => {
    setBusy(true); setErr('')
    try {
      // Fullscreen must be requested inside the click handler (user gesture)
      try { await document.documentElement.requestFullscreen?.() } catch { /* not fatal */ }
      const { data } = await api.post('/assessment/start', { subject_id: s.subject_id, duration_minutes: 30 })
      nav(`/quiz/${data.assessment_id}`)
    } catch (e) { setErr(errMsg(e)); setRules(null) } finally { setBusy(false) }
  }

  if (!subs) return <FullLoader />
  const done = subs.filter((s) => s.status === 'completed').length

  return (
    <Shell right={<button onClick={logout} className="btn-ghost"><LogOut size={16} /> Logout</button>}>
      <div className="animate-fadeUp py-6">
        <p className="text-sm text-brand-400">Hello, {user?.full_name?.split(' ')[0]} 👋</p>
        <h1 className="mt-1 text-3xl font-extrabold tracking-tight sm:text-4xl">Welcome to AI Personalized Study Planner</h1>
        <p className="mt-2 max-w-2xl text-slate-300">
          Before we plan your study time, we need to know where you stand. Confirm your subjects below (add any you missed
          at registration), then take a 30-minute AI assessment for each one.
        </p>
      </div>

      {err && <div className="mb-4"><Alert>{err}</Alert></div>}

      <div className="glass rounded-3xl p-5 sm:p-6">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-bold">Your subjects <span className="text-slate-400">({done}/{subs.length} assessed)</span></h2>
          <div className="flex gap-2">
            <input className="input !w-56" placeholder="Add subject(s), comma separated" value={input}
              onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && add()} />
            <button className="btn-ghost" onClick={add} disabled={busy}><Plus size={16} /> Add</button>
          </div>
        </div>

        <div className="space-y-3">
          {subs.map((s) => (
            <div key={s.subject_id} className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/10 bg-black/20 p-4">
              <div>
                <p className="font-semibold">{s.subject_name}</p>
                <p className="mt-0.5 text-xs text-slate-400">
                  {s.status === 'completed' && <span className="text-emerald-400">✓ Assessed · {s.percentage}% · {s.knowledge_level}</span>}
                  {s.status === 'in_progress' && <span className="text-amber-400">Test in progress — resume it</span>}
                  {s.status === 'pending' && 'Not assessed yet'}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {s.status === 'completed' && <>
                  <Link to={`/result/${s.completed_assessment_id}`} className="btn-ghost"><CheckCircle2 size={16} /> Result</Link>
                  <button className="btn-ghost" onClick={() => setRules(s)}><RotateCcw size={16} /> Retake</button>
                </>}
                {s.status === 'in_progress' && <button className="btn-primary" onClick={() => nav(`/quiz/${s.in_progress_assessment_id}`)}><Play size={16} /> Resume</button>}
                {s.status === 'pending' && <button className="btn-primary" onClick={() => setRules(s)}><Play size={16} /> Start test</button>}
                <button className="rounded-lg p-2 text-slate-400 hover:bg-rose-500/10 hover:text-rose-300" title="Remove subject" onClick={() => remove(s.subject_name)}><Trash2 size={16} /></button>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-white/10 pt-5">
          <p className="text-sm text-slate-400">
            {done === subs.length ? 'All subjects assessed — great! Now tell us about your schedule.' :
              done > 0 ? 'Tip: assess every subject for the most accurate plan.' : 'Complete at least one assessment to continue.'}
          </p>
          <button className="btn-primary" disabled={done === 0} onClick={() => nav('/schedule')}>Continue to my schedule →</button>
        </div>
      </div>

      {rules && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="glass w-full max-w-lg rounded-3xl bg-slate-900/90 p-6">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2"><ShieldAlert className="text-amber-400" /><h3 className="text-lg font-bold">{rules.subject_name} — Test rules</h3></div>
              <button onClick={() => setRules(null)}><X size={18} /></button>
            </div>
            <ul className="mt-4 space-y-2 text-sm text-slate-300">
              <li className="flex gap-2"><Clock size={16} className="mt-0.5 shrink-0 text-brand-400" /> 30 minutes, 15 AI-generated questions. The timer runs on the server and cannot be paused.</li>
              <li>• The test opens in <b>full-screen</b>. Leaving full-screen, switching tabs/windows, or losing focus is recorded as a warning.</li>
              <li>• Copy, paste, right-click, text selection, printing and screenshot keys are blocked.</li>
              <li>• <b>3 warnings</b> and the test is submitted automatically.</li>
              <li>• Be honest — this test only exists to build a study plan that fits <i>you</i>.</li>
            </ul>
            <div className="mt-6 flex justify-end gap-2">
              <button className="btn-ghost" onClick={() => setRules(null)}>Cancel</button>
              <button className="btn-primary" disabled={busy} onClick={() => start(rules)}>{busy ? <Spinner /> : 'I agree — start test'}</button>
            </div>
          </div>
        </div>
      )}
    </Shell>
  )
}
