import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Check, Clock3, Pause, Play, X } from 'lucide-react'
import { api, errMsg, type Entry, type StudySession as Session } from '../api'
import { Alert, FullLoader, Shell, Spinner } from '../components/ui'

const format = (seconds: number) => `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`

export default function StudySession() {
  const { entryId } = useParams(); const nav = useNavigate()
  const [entry, setEntry] = useState<Entry | null>(null); const [session, setSession] = useState<Session | null>(null)
  const [left, setLeft] = useState(0); const [confirm, setConfirm] = useState(false); const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false); const endAt = useRef(0); const finished = useRef(false)

  useEffect(() => {
    if (!entryId) return
    Promise.all([api.get<Entry[]>('/timetable'), api.post<Session>('/study-sessions/start', { timetable_entry_id: entryId })])
      .then(([entries, started]) => { const e = entries.data.find((x) => x.id === entryId) ?? null; setEntry(e); setSession(started.data); const seconds = started.data.scheduled_duration_minutes * 60; setLeft(seconds); endAt.current = Date.now() + seconds * 1000 })
      .catch((e) => setErr(errMsg(e)))
  }, [entryId])

  const action = useCallback(async (kind: 'pause' | 'resume' | 'finish') => {
    if (!session) return
    setBusy(true); setErr('')
    try {
      const { data } = await api.post<Session>(`/study-sessions/${session.id}/${kind}`)
      setSession(data)
      if (kind === 'resume') endAt.current = Date.now() + Math.max(0, (data.scheduled_duration_minutes - data.actual_duration_minutes) * 60 * 1000)
      if (kind === 'finish') { finished.current = true; nav('/dashboard', { replace: true }) }
    } catch (e) { setErr(errMsg(e)) } finally { setBusy(false) }
  }, [nav, session])

  useEffect(() => {
    if (!session || session.status === 'paused' || session.status === 'completed') return
    const timer = window.setInterval(() => {
      const seconds = Math.max(0, Math.ceil((endAt.current - Date.now()) / 1000)); setLeft(seconds)
      if (seconds === 0) void action('finish')
    }, 500)
    return () => window.clearInterval(timer)
  }, [action, session])

  useEffect(() => {
    const leave = (e: BeforeUnloadEvent) => { if (!finished.current && session?.status !== 'completed') { e.preventDefault(); e.returnValue = '' } }
    window.addEventListener('beforeunload', leave); return () => window.removeEventListener('beforeunload', leave)
  }, [session])

  if (err && !session) return <Shell><Alert>{err}</Alert></Shell>
  if (!session) return <FullLoader />
  const paused = session.status.toLowerCase() === 'paused'
  return <Shell right={<button className="btn-ghost" onClick={() => setConfirm(true)}><X size={16} /> Leave</button>}>
    <div className="mx-auto max-w-2xl py-8">
      {err && <div className="mb-4"><Alert>{err}</Alert></div>}
      <div className="glass rounded-3xl p-6 text-center sm:p-10">
        <p className="text-sm text-brand-300">{entry?.subject_name ?? session.subject_name ?? 'Study session'}</p>
        <h1 className="mt-2 text-3xl font-extrabold">{entry?.topic ?? session.topic}</h1>
        <p className="mt-2 text-sm text-slate-400">{entry?.reason ?? session.objective ?? 'Stay focused and make steady progress.'}</p>
        <div className={`mx-auto my-10 grid h-52 w-52 place-items-center rounded-full border-8 ${paused ? 'border-amber-400/40' : 'border-brand-400/50'}`}>
          <div><Clock3 className="mx-auto mb-2 text-brand-300" size={24} /><p className="font-mono text-5xl font-bold">{format(left)}</p><p className="mt-2 text-xs text-slate-400">{paused ? 'Paused' : 'remaining'}</p></div>
        </div>
        <div className="flex justify-center gap-3">
          <button className="btn-ghost" disabled={busy} onClick={() => void action(paused ? 'resume' : 'pause')}>{busy ? <Spinner /> : paused ? <Play size={17} /> : <Pause size={17} />} {paused ? 'Resume' : 'Pause'}</button>
          <button className="btn-primary" disabled={busy} onClick={() => void action('finish')}><Check size={17} /> Finish session</button>
        </div>
        <p className="mt-5 text-xs text-slate-500">You can finish early; your partial progress will be saved.</p>
      </div>
    </div>
    {confirm && <div className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4"><div className="glass max-w-sm rounded-3xl bg-slate-900 p-6"><h2 className="text-lg font-bold">Mark as partially done?</h2><p className="mt-2 text-sm text-slate-300">Leaving now will save the actual minutes studied and mark this session complete as partial.</p><div className="mt-5 flex justify-end gap-2"><button className="btn-ghost" onClick={() => setConfirm(false)}>Keep studying</button><button className="btn-primary" onClick={() => { setConfirm(false); void action('finish') }}>Finish partially</button></div></div></div>}
  </Shell>
}
