import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Sparkles, Trash2 } from 'lucide-react'
import { api, errMsg } from '../api'
import { useAuth } from '../auth'
import { Alert, Field, Shell, Spinner } from '../components/ui'

interface Commitment { title: string; start: string; end: string }
const DEFAULT = {
  wake_time: '06:30', sleep_time: '23:00', college_start: '09:00', college_end: '16:00',
  morning_travel_minutes: 30, evening_travel_minutes: 30, available_study_hours: 3,
  preferred_study_time: 'evening', session_duration_minutes: 45, break_duration_minutes: 10,
}

export default function Schedule() {
  const nav = useNavigate(); const { refresh } = useAuth()
  const [f, setF] = useState(DEFAULT)
  const [commitments, setCommitments] = useState<Commitment[]>([])
  const [err, setErr] = useState(''); const [busy, setBusy] = useState(false); const [ready, setReady] = useState(false)

  useEffect(() => {
    api.get('/availability').then(({ data }) => {
      setF({ ...DEFAULT, ...Object.fromEntries(Object.keys(DEFAULT).map((k) => [k, data[k] ?? (DEFAULT as Record<string, unknown>)[k]])) })
      setCommitments(data.commitments ?? [])
    }).catch(() => {}).finally(() => setReady(true))
  }, [])

  const set = (k: keyof typeof DEFAULT) => (e: { target: { value: string } }) =>
    setF({ ...f, [k]: typeof DEFAULT[k] === 'number' ? Number(e.target.value) : e.target.value })

  const submit = async (e: FormEvent) => {
    e.preventDefault(); setErr('')
    if (f.college_end <= f.college_start) return setErr('College end time must be after the start time.')
    if (commitments.some((c) => !c.title.trim() || c.end <= c.start)) return setErr('Check your work/other commitments: each needs a name and an end time after the start time.')
    setBusy(true)
    try {
      await api.put('/availability', { ...f, commitments })
      await api.post('/planning/generate?days_ahead=7')
      await refresh(); nav('/dashboard')
    } catch (e2) { setErr(errMsg(e2)) } finally { setBusy(false) }
  }

  const upd = (i: number, k: keyof Commitment, v: string) => setCommitments(commitments.map((c, j) => (j === i ? { ...c, [k]: v } : c)))

  return (
    <Shell>
      <div className="animate-fadeUp py-4">
        <h1 className="text-3xl font-extrabold tracking-tight">Tell us about your day</h1>
        <p className="mt-1 max-w-2xl text-slate-300">The AI will place study sessions only in your free time — never over college, work, meals or sleep.</p>
      </div>
      {!ready ? <Spinner /> : (
        <form onSubmit={submit} className="glass space-y-6 rounded-3xl p-6">
          <section>
            <h2 className="mb-3 font-bold">🎓 College hours</h2>
            <div className="grid gap-3 sm:grid-cols-4">
              <Field label="College starts"><input className="input" type="time" value={f.college_start} onChange={set('college_start')} /></Field>
              <Field label="College ends"><input className="input" type="time" value={f.college_end} onChange={set('college_end')} /></Field>
              <Field label="Travel to college (min)"><input className="input" type="number" min={0} max={180} value={f.morning_travel_minutes} onChange={set('morning_travel_minutes')} /></Field>
              <Field label="Travel back (min)"><input className="input" type="number" min={0} max={180} value={f.evening_travel_minutes} onChange={set('evening_travel_minutes')} /></Field>
            </div>
          </section>
          <section>
            <h2 className="mb-3 font-bold">😴 Sleep</h2>
            <div className="grid gap-3 sm:grid-cols-4">
              <Field label="Wake up"><input className="input" type="time" value={f.wake_time} onChange={set('wake_time')} /></Field>
              <Field label="Go to sleep"><input className="input" type="time" value={f.sleep_time} onChange={set('sleep_time')} /></Field>
            </div>
          </section>
          <section>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-bold">💼 Work & other commitments</h2>
              <button type="button" className="btn-ghost !py-1.5" onClick={() => setCommitments([...commitments, { title: '', start: '18:00', end: '19:00' }])}><Plus size={14} /> Add</button>
            </div>
            {!commitments.length && <p className="text-sm text-slate-400">Part-time job, tuition, sports, family time… add anything you can't move.</p>}
            <div className="space-y-2">
              {commitments.map((c, i) => (
                <div key={i} className="grid items-end gap-2 sm:grid-cols-[1fr_130px_130px_40px]">
                  <Field label="What"><input className="input" value={c.title} onChange={(e) => upd(i, 'title', e.target.value)} placeholder="Part-time job" /></Field>
                  <Field label="From"><input className="input" type="time" value={c.start} onChange={(e) => upd(i, 'start', e.target.value)} /></Field>
                  <Field label="To"><input className="input" type="time" value={c.end} onChange={(e) => upd(i, 'end', e.target.value)} /></Field>
                  <button type="button" className="mb-1 rounded-lg p-2 text-slate-400 hover:text-rose-300" onClick={() => setCommitments(commitments.filter((_, j) => j !== i))}><Trash2 size={16} /></button>
                </div>
              ))}
            </div>
          </section>
          <section>
            <h2 className="mb-3 font-bold">📚 Study time</h2>
            <div className="grid gap-3 sm:grid-cols-4">
              <Field label={`Total study time / day: ${f.available_study_hours} h`}>
                <input type="range" min={0.5} max={10} step={0.5} className="w-full accent-brand-500" value={f.available_study_hours} onChange={set('available_study_hours')} />
              </Field>
              <Field label="Best time to study">
                <select className="input" value={f.preferred_study_time} onChange={set('preferred_study_time')}>
                  <option value="morning">Morning</option><option value="afternoon">Afternoon</option><option value="evening">Evening</option><option value="night">Night</option>
                </select>
              </Field>
              <Field label="Session length">
                <select className="input" value={f.session_duration_minutes} onChange={set('session_duration_minutes')}>{[25, 45, 60, 90].map((m) => <option key={m} value={m}>{m} min</option>)}</select>
              </Field>
              <Field label="Break length">
                <select className="input" value={f.break_duration_minutes} onChange={set('break_duration_minutes')}>{[5, 10, 15].map((m) => <option key={m} value={m}>{m} min</option>)}</select>
              </Field>
            </div>
          </section>
          {err && <Alert>{err}</Alert>}
          <div className="flex justify-end"><button className="btn-primary" disabled={busy}>{busy ? <><Spinner /> Building your plan…</> : <><Sparkles size={16} /> Generate my timetable</>}</button></div>
        </form>
      )}
    </Shell>
  )
}
