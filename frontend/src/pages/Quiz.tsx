import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { AlertTriangle, ChevronLeft, ChevronRight, Clock, Send } from 'lucide-react'
import { api, errMsg, type Quiz as QuizT } from '../api'
import { useAuth } from '../auth'
import { Alert, FullLoader, Spinner } from '../components/ui'

const MAX_WARNINGS = 3
const fmt = (s: number) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`

export default function Quiz() {
  const { id } = useParams()
  const location = useLocation()
  const retest = location.pathname.startsWith('/retest/')
  const nav = useNavigate()
  const { user } = useAuth()
  const [quiz, setQuiz] = useState<QuizT | null>(null)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [idx, setIdx] = useState(0)
  const [left, setLeft] = useState(0)
  const [warns, setWarns] = useState(0)
  const [away, setAway] = useState(false)
  const [notice, setNotice] = useState('')
  const [err, setErr] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [confirm, setConfirm] = useState(false)
  const endAt = useRef(0)
  const submitted = useRef(false)
  const lastEvt = useRef(0)
  const storeKey = `sp_answers_${id}`

  /* ---- load quiz (server-authoritative timer) ---- */
  useEffect(() => {
    api.get<QuizT>(`/assessment/${id}`).then(({ data }) => {
      if (data.status !== 'in_progress' || data.remaining_seconds <= 0) { nav(`${retest ? '/retest/result' : '/result'}/${id}`, { replace: true }); return }
      endAt.current = Date.now() + data.remaining_seconds * 1000
      setLeft(data.remaining_seconds); setQuiz(data)
      try { setAnswers(JSON.parse(sessionStorage.getItem(storeKey) || '{}')) } catch { /* ignore */ }
    }).catch((e) => setErr(errMsg(e)))
  }, [id, nav, retest, storeKey])

  useEffect(() => { sessionStorage.setItem(storeKey, JSON.stringify(answers)) }, [answers, storeKey])

  /* ---- submit ---- */
  const submit = useCallback(async () => {
    if (submitted.current) return
    submitted.current = true; setSubmitting(true)
    try {
      await api.post(`/assessment/${id}/submit`, {
        answers: Object.entries(answers).map(([question_id, selected_answer]) => ({ question_id, selected_answer })),
      })
      sessionStorage.removeItem(storeKey)
      if (document.fullscreenElement) document.exitFullscreen().catch(() => {})
      nav(`${retest ? '/retest/result' : '/result'}/${id}`, { replace: true })
    } catch (e) { submitted.current = false; setSubmitting(false); setErr(errMsg(e)) }
  }, [answers, id, nav, retest, storeKey])
  const submitRef = useRef(submit); submitRef.current = submit

  /* ---- countdown ---- */
  useEffect(() => {
    if (!quiz) return
    const t = setInterval(() => {
      const s = Math.max(0, Math.round((endAt.current - Date.now()) / 1000))
      setLeft(s)
      if (s <= 0) { clearInterval(t); submitRef.current() }
    }, 500)
    return () => clearInterval(t)
  }, [quiz])

  /* ---- anti-cheat ---- */
  const report = useCallback(async (type: string, details: string) => {
    if (submitted.current) return
    const now = Date.now(); if (now - lastEvt.current < 1500) return // de-duplicate blur + visibilitychange
    lastEvt.current = now
    try {
      const { data } = await api.post(`/assessment/${id}/anti-cheat-event`, { event_type: type, details })
      setWarns(data.warning_count)
      setNotice(`Warning ${data.warning_count}/${MAX_WARNINGS}: ${details}`)
      if (data.warning_count >= MAX_WARNINGS) submitRef.current()
    } catch { /* offline: ignore */ }
  }, [id])

  useEffect(() => {
    if (!quiz) return
    const stop = (e: Event) => e.preventDefault()
    const onKey = (e: KeyboardEvent) => {
      const k = e.key.toLowerCase(); const mod = e.ctrlKey || e.metaKey
      if (k === 'printscreen') { navigator.clipboard?.writeText('').catch(() => {}); e.preventDefault(); report('SCREENSHOT_KEY', 'Screenshot key pressed'); return }
      if (mod && ['c', 'v', 'x', 'a', 'p', 's', 'u', 'f'].includes(k)) { e.preventDefault(); if (k === 'c' || k === 'v' || k === 'x') report('COPY_PASTE_ATTEMPT', 'Copy/paste shortcut blocked'); return }
      if (e.key === 'F12' || (mod && e.shiftKey && ['i', 'j', 'c'].includes(k))) { e.preventDefault(); report('DEVTOOLS_ATTEMPT', 'Developer tools are not allowed'); return }
      if (e.metaKey && e.shiftKey && ['3', '4', '5'].includes(k)) { e.preventDefault(); report('SCREENSHOT_KEY', 'Screenshot shortcut detected') }
    }
    const onVis = () => { if (document.hidden) { setAway(true); report('TAB_SWITCH', 'You switched tabs or minimised the window') } else setAway(false) }
    const onBlur = () => { setAway(true); report('WINDOW_BLUR', 'The test window lost focus') }
    const onFocus = () => setAway(false)
    const onFs = () => { if (!document.fullscreenElement && !submitted.current) report('FULLSCREEN_EXIT', 'You left full-screen mode') }
    const onUnload = (e: BeforeUnloadEvent) => { if (!submitted.current) { e.preventDefault(); e.returnValue = '' } }

    const evts: [string, EventListener][] = [['contextmenu', stop], ['copy', stop], ['cut', stop], ['paste', stop], ['dragstart', stop], ['selectstart', stop], ['beforeprint', stop]]
    evts.forEach(([n, h]) => document.addEventListener(n, h))
    document.addEventListener('keydown', onKey); document.addEventListener('keyup', (e) => { if (e.key === 'PrintScreen') navigator.clipboard?.writeText('').catch(() => {}) })
    document.addEventListener('visibilitychange', onVis); window.addEventListener('blur', onBlur); window.addEventListener('focus', onFocus)
    document.addEventListener('fullscreenchange', onFs); window.addEventListener('beforeunload', onUnload)
    return () => {
      evts.forEach(([n, h]) => document.removeEventListener(n, h))
      document.removeEventListener('keydown', onKey); document.removeEventListener('visibilitychange', onVis)
      window.removeEventListener('blur', onBlur); window.removeEventListener('focus', onFocus)
      document.removeEventListener('fullscreenchange', onFs); window.removeEventListener('beforeunload', onUnload)
    }
  }, [quiz, report])

  const q = quiz?.questions[idx]
  const answered = useMemo(() => Object.keys(answers).length, [answers])
  const watermark = useMemo(() => `${user?.full_name ?? ''} • ID ${user?.id ?? ''} • `.repeat(40), [user])

  if (err && !quiz) return <div className="grid min-h-screen place-items-center bg-aurora p-6"><Alert>{err}</Alert></div>
  if (!quiz || !q) return <FullLoader />
  const low = left <= 300

  return (
    <div className="no-select relative min-h-screen bg-aurora" onCopy={(e) => e.preventDefault()}>
      {/* watermark deters photos of the screen */}
      <div aria-hidden className="pointer-events-none fixed inset-0 z-0 -rotate-12 overflow-hidden text-[13px] font-semibold leading-10 text-white/[0.035]">
        {Array.from({ length: 30 }).map((_, i) => <div key={i} className="whitespace-nowrap">{watermark}</div>)}
      </div>

      <header className="sticky top-0 z-20 border-b border-white/10 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-5 py-3">
          <div><p className="text-xs text-slate-400">Baseline assessment</p><p className="font-bold">{quiz.subject_name}</p></div>
          <div className="flex items-center gap-3">
            <span className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs ${warns ? 'bg-amber-500/15 text-amber-300' : 'bg-white/5 text-slate-400'}`}><AlertTriangle size={14} /> {warns}/{MAX_WARNINGS}</span>
            <span className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-mono text-sm font-bold ${low ? 'animate-pulse bg-rose-500/20 text-rose-300' : 'bg-white/10'}`}><Clock size={14} /> {fmt(left)}</span>
          </div>
        </div>
        <div className="h-1 bg-white/5"><div className="h-full bg-gradient-to-r from-brand-500 to-fuchsia-500 transition-all" style={{ width: `${(answered / quiz.total_questions) * 100}%` }} /></div>
      </header>

      <main className={`relative z-10 mx-auto max-w-4xl px-5 py-6 transition ${away ? 'blur-2xl' : ''}`}>
        {notice && <div className="mb-4"><Alert kind="error">{notice}</Alert></div>}
        {err && <div className="mb-4"><Alert>{err}</Alert></div>}
        <div className="glass rounded-3xl p-6">
          <div className="mb-3 flex items-center gap-2 text-xs text-slate-400">
            <span>Question {idx + 1} of {quiz.total_questions}</span><span>•</span><span>{q.topic}</span>
            <span className="rounded-full bg-white/10 px-2 py-0.5 capitalize">{q.difficulty}</span>
          </div>
          <h2 className="text-lg font-semibold leading-relaxed">{q.question}</h2>
          <div className="mt-5 space-y-2.5">
            {q.options.map((o, i) => {
              const sel = answers[q.question_id] === o
              return (
                <button key={i} onClick={() => setAnswers({ ...answers, [q.question_id]: o })}
                  className={`flex w-full items-start gap-3 rounded-2xl border p-4 text-left text-sm transition ${sel ? 'border-brand-400 bg-brand-500/20' : 'border-white/10 bg-black/20 hover:bg-white/5'}`}>
                  <span className={`grid h-6 w-6 shrink-0 place-items-center rounded-full text-xs font-bold ${sel ? 'bg-brand-500' : 'bg-white/10'}`}>{'ABCD'[i]}</span>
                  <span>{o}</span>
                </button>
              )
            })}
          </div>
          <div className="mt-6 flex items-center justify-between">
            <button className="btn-ghost" disabled={idx === 0} onClick={() => setIdx(idx - 1)}><ChevronLeft size={16} /> Previous</button>
            {idx < quiz.total_questions - 1
              ? <button className="btn-primary" onClick={() => setIdx(idx + 1)}>Next <ChevronRight size={16} /></button>
              : <button className="btn-primary" onClick={() => setConfirm(true)}><Send size={16} /> Finish</button>}
          </div>
        </div>

        <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap gap-1.5">
            {quiz.questions.map((x, i) => (
              <button key={x.question_id} onClick={() => setIdx(i)}
                className={`h-8 w-8 rounded-lg text-xs font-semibold ${i === idx ? 'ring-2 ring-brand-400' : ''} ${answers[x.question_id] ? 'bg-emerald-500/25 text-emerald-200' : 'bg-white/5 text-slate-400'}`}>{i + 1}</button>
            ))}
          </div>
          <button className="btn-ghost" onClick={() => setConfirm(true)}>Submit test</button>
        </div>
      </main>

      {away && (
        <div className="fixed inset-0 z-40 grid place-items-center bg-slate-950/90 p-6 text-center">
          <div><AlertTriangle className="mx-auto text-amber-400" size={40} /><p className="mt-3 text-lg font-bold">Test paused from view</p>
            <p className="text-sm text-slate-400">Return to this window. Leaving again adds a warning.</p>
            {!document.fullscreenElement && <button className="btn-primary mt-4" onClick={() => document.documentElement.requestFullscreen?.().catch(() => {})}>Return to full-screen</button>}
          </div>
        </div>
      )}

      {confirm && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4">
          <div className="glass w-full max-w-sm rounded-3xl bg-slate-900/95 p-6">
            <h3 className="text-lg font-bold">Submit your test?</h3>
            <p className="mt-2 text-sm text-slate-300">You answered {answered} of {quiz.total_questions} questions. Unanswered questions count as wrong.</p>
            <div className="mt-5 flex justify-end gap-2">
              <button className="btn-ghost" onClick={() => setConfirm(false)}>Keep going</button>
              <button className="btn-primary" disabled={submitting} onClick={submit}>{submitting ? <Spinner /> : 'Submit'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
