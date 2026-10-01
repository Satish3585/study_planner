import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { BarChart3, Check, Coffee, Flame, LogOut, Play, RefreshCw, SkipForward, Target, Timer, Trophy } from 'lucide-react'
import { api, errMsg, type Dashboard as D, type Entry, type ProgressAnalytics } from '../api'
import { useAuth } from '../auth'
import { Alert, FullLoader, Shell, Spinner } from '../components/ui'

const badge = (p: string) => p === 'High' ? 'bg-rose-500/20 text-rose-300' : p === 'Medium' ? 'bg-amber-500/20 text-amber-300' : 'bg-sky-500/20 text-sky-300'
const dayLabel = (iso: string) => new Date(iso + 'T00:00').toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' })

export default function Dashboard() {
  const { logout } = useAuth()
  const nav = useNavigate()
  const [dash, setDash] = useState<D | null>(null); const [entries, setEntries] = useState<Entry[]>([])
  const [progress, setProgress] = useState<ProgressAnalytics | null>(null)
  const [day, setDay] = useState(''); const [err, setErr] = useState(''); const [busy, setBusy] = useState<string | 'regen' | null>(null)

  const load = useCallback(async () => {
    try {
      const [d, t, p] = await Promise.all([api.get<D>('/analytics/dashboard'), api.get<Entry[]>('/timetable'), api.get<ProgressAnalytics>('/analytics/progress')])
      setDash(d.data); setEntries(t.data); setProgress(p.data)
      setDay((cur) => cur || t.data.find((e) => e.date >= new Date().toISOString().slice(0, 10))?.date || t.data[0]?.date || '')
    } catch (e) { setErr(errMsg(e)) }
  }, [])
  useEffect(() => { load() }, [load])

  const days = useMemo(() => [...new Set(entries.map((e) => e.date))], [entries])
  const today = entries.filter((e) => e.date === day)
  const studyToday = today.filter((e) => e.activity_type !== 'Break')
  const completedToday = studyToday.filter((e) => e.status === 'Completed').length
  const terminalToday = studyToday.filter((e) => e.status === 'Completed' || e.status === 'Skipped').length
  const skippedPrevious = entries.some((e) => e.status === 'Skipped' && e.date < day)

  const act = async (e: Entry, kind: 'complete' | 'skip') => {
    setBusy(e.id); setErr('')
    try {
      if (kind === 'complete') await api.post(`/timetable/${e.id}/complete`)
      else await api.post(`/timetable/${e.id}/skip`, { reason: 'Busy' })
      await load()
    } catch (e2) { setErr(errMsg(e2)) } finally { setBusy(null) }
  }
  const regen = async () => {
    setBusy('regen'); setErr('')
    try { await api.post('/timetable/regenerate', { days_ahead: 7, preserve_completed: true }); setDay(''); await load() }
    catch (e) { setErr(errMsg(e)) } finally { setBusy(null) }
  }

  if (!dash) return err ? <Shell><Alert>{err}</Alert></Shell> : <FullLoader />
  const stat = [
    { i: Target, l: "Today's progress", v: `${dash.today_progress.completed_sessions}/${dash.today_progress.total_sessions}`, c: 'text-brand-400' },
    { i: Flame, l: 'Study streak', v: `${dash.study_streak_days} day(s)`, c: 'text-orange-400' },
    { i: Timer, l: 'Time studied', v: `${(dash.total_study_minutes / 60).toFixed(1)} h`, c: 'text-emerald-400' },
    { i: Trophy, l: 'Completion rate', v: `${Math.round(dash.completion_rate_percentage)}%`, c: 'text-amber-400' },
  ]

  return (
    <Shell right={<div className="flex gap-2">
      <Link to="/welcome" className="btn-ghost">Subjects & tests</Link>
      <Link to="/schedule" className="btn-ghost">My schedule</Link>
      <button onClick={logout} className="btn-ghost"><LogOut size={16} /></button></div>}>
      <div className="animate-fadeUp py-3">
        <h1 className="text-3xl font-extrabold tracking-tight">Hi {dash.user_name.split(' ')[0]}, here's your plan</h1>
        <p className="mt-1 text-slate-300">{dash.ai_insight}</p>
      </div>
      {studyToday.length > 0 && completedToday > 0 && terminalToday === studyToday.length && <div className="mb-4"><Alert kind="ok">Day complete 🎉 You finished every study block for {dayLabel(day)}. <Link className="ml-2 underline" to={`/retest?date=${day}`}>Take your retest</Link></Alert></div>}
      {skippedPrevious && <div className="mb-4"><Alert kind="info">You have a skipped block from an earlier day. Today's plan prioritises it so nothing important is lost.</Alert></div>}
      {err && <div className="mb-4"><Alert>{err}</Alert></div>}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stat.map((s) => (
          <div key={s.l} className="glass rounded-2xl p-4"><s.i className={s.c} size={20} /><p className="mt-2 text-2xl font-extrabold">{s.v}</p><p className="text-xs text-slate-400">{s.l}</p></div>
        ))}
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-[1fr_320px]">
        <section className="glass rounded-3xl p-5">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap gap-1.5">
              {days.map((d) => <button key={d} onClick={() => setDay(d)} className={`rounded-lg px-3 py-1.5 text-xs font-semibold ${d === day ? 'bg-brand-500' : 'bg-white/5 text-slate-400 hover:bg-white/10'}`}>{dayLabel(d)}</button>)}
            </div>
            <button className="btn-ghost !py-1.5" onClick={regen} disabled={busy === 'regen'}>{busy === 'regen' ? <Spinner /> : <RefreshCw size={14} />} Regenerate</button>
          </div>
          {!today.length && <p className="py-8 text-center text-sm text-slate-400">No sessions for this day.</p>}
          <div className="space-y-2.5">
            {today.map((e) => {
              const brk = e.activity_type === 'Break'; const done = e.status === 'Completed'; const skipped = e.status === 'Skipped'
              return (
                <div key={e.id} onClick={() => !brk && e.status === 'Scheduled' && nav(`/session/${e.id}`)} role={!brk && e.status === 'Scheduled' ? 'button' : undefined} className={`flex items-center gap-4 rounded-2xl border p-3.5 ${brk ? 'border-white/5 bg-white/[0.02]' : 'border-white/10 bg-black/20'} ${done || skipped ? 'opacity-60' : ''} ${!brk && e.status === 'Scheduled' ? 'cursor-pointer hover:border-brand-400/40' : ''}`}>
                  <div className="w-24 shrink-0 text-xs font-mono text-slate-400">{e.start_time}<br />{e.end_time}</div>
                  <div className="min-w-0 flex-1">
                    <p className="flex items-center gap-2 text-sm font-semibold">{brk && <Coffee size={14} className="text-slate-400" />}<span className="truncate">{brk ? e.topic : `${e.subject_name} — ${e.topic}`}</span></p>
                    {!brk && <p className="mt-0.5 line-clamp-1 text-xs text-slate-400">{e.reason}</p>}
                  </div>
                  {!brk && <span className={`rounded-full px-2 py-0.5 text-[11px] ${badge(e.priority)}`}>{e.priority}</span>}
                  {!brk && e.status === 'Scheduled' && (
                    <div className="flex gap-1.5">
                      <Link title="Start study session" to={`/session/${e.id}`} onClick={(ev) => ev.stopPropagation()} className="rounded-lg bg-brand-500/20 p-2 text-brand-200 hover:bg-brand-500/30"><Play size={15} /></Link>
                      <button title="Mark done" disabled={busy === e.id} onClick={(ev) => { ev.stopPropagation(); void act(e, 'complete') }} className="rounded-lg bg-emerald-500/15 p-2 text-emerald-300 hover:bg-emerald-500/25"><Check size={15} /></button>
                      <button title="Skip & rebalance" disabled={busy === e.id} onClick={(ev) => { ev.stopPropagation(); void act(e, 'skip') }} className="rounded-lg bg-white/5 p-2 text-slate-300 hover:bg-white/10"><SkipForward size={15} /></button>
                    </div>
                  )}
                  {done && <span className="text-xs text-emerald-300">Done ✓</span>}
                  {skipped && <span className="text-xs text-slate-400">Skipped</span>}
                </div>
              )
            })}
          </div>
        </section>

        <aside className="space-y-5">
          <div className="glass rounded-3xl p-5">
            <h3 className="mb-3 font-bold text-rose-300">Needs attention</h3>
            <div className="space-y-2">
              {dash.needs_attention_topics.slice(0, 6).map((t, i) => (
                <div key={i} className="flex justify-between text-sm"><span className="truncate pr-2">{t.topic}<span className="text-slate-500"> · {t.subject}</span></span><span className="text-rose-300">{Math.round(t.score)}%</span></div>
              ))}
              {!dash.needs_attention_topics.length && <p className="text-sm text-slate-400">Nothing urgent 🎉</p>}
            </div>
          </div>
          <div className="glass rounded-3xl p-5">
            <h3 className="mb-3 font-bold text-emerald-300">Strong topics</h3>
            <div className="space-y-2">
              {dash.strong_topics.slice(0, 5).map((t, i) => (
                <div key={i} className="flex justify-between text-sm"><span className="truncate pr-2">{t.topic}<span className="text-slate-500"> · {t.subject}</span></span><span className="text-emerald-300">{Math.round(t.score)}%</span></div>
              ))}
              {!dash.strong_topics.length && <p className="text-sm text-slate-400">Complete sessions to build strengths.</p>}
            </div>
          </div>
        </aside>
      </div>
      <div className="mt-5 grid gap-5 lg:grid-cols-[1fr_320px]">
        <section className="glass rounded-3xl p-5">
          <div className="flex items-center justify-between"><h2 className="flex items-center gap-2 font-bold"><BarChart3 size={18} className="text-brand-300" /> Progress over time</h2><Link to="/retest" className="btn-ghost !py-1.5">Weekly retest</Link></div>
          <div className="mt-5 flex h-36 items-end gap-2">
            {(progress?.daily_study_breakdown ?? []).slice(-14).map((d, i, all) => { const value = d.minutes ?? d.completed_minutes ?? d.study_minutes ?? 0; const max = Math.max(1, ...all.map((x) => x.minutes ?? x.completed_minutes ?? x.study_minutes ?? 0)); return <div key={`${d.date ?? d.day ?? i}`} className="flex min-w-0 flex-1 flex-col items-center gap-1"><div className="w-full rounded-t bg-gradient-to-t from-brand-500 to-fuchsia-400" style={{ height: `${Math.max(4, value / max * 100)}%` }} title={`${Math.round(value)} minutes`} /><span className="w-full truncate text-center text-[10px] text-slate-500">{(d.date ?? d.day ?? '').slice(-5)}</span></div> })}
            {!progress?.daily_study_breakdown?.length && <p className="self-center text-sm text-slate-400">Complete a study session to see your trend.</p>}
          </div>
        </section>
        <aside className="glass rounded-3xl p-5"><h2 className="font-bold">Today's summary</h2><p className="mt-3 text-sm text-slate-300">{completedToday} of {studyToday.length} study blocks complete.</p><p className="mt-2 text-sm text-slate-400">Streak: <span className="font-semibold text-orange-300">{dash.study_streak_days} day(s)</span>. {dash.ai_insight}</p><p className="mt-3 text-xs text-slate-500">Why this changed: your plan adapts to completed and skipped sessions, recent topic scores, and available time.</p></aside>
      </div>
    </Shell>
  )
}
