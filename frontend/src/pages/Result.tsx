import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { Lightbulb, Target, ThumbsUp, TrendingUp } from 'lucide-react'
import { api, errMsg, type Result as R } from '../api'
import { Alert, FullLoader, Shell } from '../components/ui'

const catStyle = (c: string) => c === 'Strong' ? 'bg-emerald-500/20 text-emerald-300' : c === 'Moderate' ? 'bg-amber-500/20 text-amber-300' : 'bg-rose-500/20 text-rose-300'
const barStyle = (c: string) => c === 'Strong' ? 'bg-emerald-500' : c === 'Moderate' ? 'bg-amber-500' : 'bg-rose-500'

export default function Result() {
  const { id } = useParams(); const nav = useNavigate(); const retest = useLocation().pathname.startsWith('/retest/')
  const [r, setR] = useState<R | null>(null); const [err, setErr] = useState('')
  useEffect(() => { api.get<R>(`/assessment/${id}/result`).then(({ data }) => setR(data)).catch((e) => setErr(errMsg(e))) }, [id])

  if (err) return <Shell><Alert>{err}</Alert></Shell>
  if (!r) return <FullLoader />
  const before = retest ? (() => { try { return JSON.parse(sessionStorage.getItem(`sp_retest_before_${id}`) || 'null') as { percentage?: number; subject_name?: string } | null } catch { return null } })() : null
  const delta = before?.percentage == null ? null : r.percentage - before.percentage
  const ring = `conic-gradient(#8b5cf6 ${r.percentage * 3.6}deg, rgba(255,255,255,.08) 0deg)`

  return (
    <Shell right={<Link to={retest ? '/dashboard' : '/welcome'} className="btn-ghost">← {retest ? 'Dashboard' : 'Subjects'}</Link>}>
      <div className="animate-fadeUp space-y-5 py-4">
        <div className="glass flex flex-wrap items-center gap-6 rounded-3xl p-6">
          <div className="grid h-32 w-32 place-items-center rounded-full" style={{ background: ring }}>
            <div className="grid h-24 w-24 place-items-center rounded-full bg-slate-950 text-center">
              <div><p className="text-2xl font-extrabold">{Math.round(r.percentage)}%</p><p className="text-[10px] text-slate-400">{r.score}/{r.total_questions}</p></div>
            </div>
          </div>
          <div className="flex-1">
            <p className="text-sm text-slate-400">{r.subject_name} · {retest ? 'Weekly retest' : 'Baseline assessment'}</p>
            <h1 className="text-2xl font-extrabold">Your level: <span className="text-brand-400">{r.knowledge_level}</span></h1>
            {r.anti_cheat_warnings > 0 && <p className="mt-1 text-xs text-amber-300">{r.anti_cheat_warnings} focus warning(s) were recorded during this test.</p>}
          </div>
          {retest && <div className="rounded-2xl bg-white/5 px-4 py-3 text-left"><p className="text-xs text-slate-400">Change since last test</p><p className={`text-xl font-bold ${delta !== null && delta >= 0 ? 'text-emerald-300' : 'text-rose-300'}`}>{delta === null ? '—' : `${delta >= 0 ? '+' : ''}${delta.toFixed(1)}%`}</p></div>}
          <button className="btn-primary" onClick={() => nav(retest ? '/dashboard' : '/welcome')}>{retest ? 'Back to dashboard' : 'Next →'}</button>
        </div>
        {retest && <div className="glass rounded-3xl p-6"><h2 className="mb-2 font-bold"><TrendingUp size={18} className="mr-2 inline text-brand-400" />Your trend & feedback</h2><p className="text-sm text-slate-300">{r.trend ? `Trend: ${r.trend}. ` : ''}{delta !== null && delta > 0 ? `Great progress — your score improved by ${delta.toFixed(1)} points.` : delta !== null && delta < 0 ? `Your score dipped by ${Math.abs(delta).toFixed(1)} points.` : 'Your score is holding steady.'}</p>{r.feedback?.length ? <ul className="mt-3 space-y-1 text-sm text-slate-300">{r.feedback.map((line, i) => <li key={i}>• {line}</li>)}</ul> : <p className="mt-1 text-sm text-slate-400">Keep practising consistently and revisit your weaker topics.</p>}</div>}

        <div className="grid gap-5 lg:grid-cols-2">
          <div className="glass rounded-3xl p-6">
            <h2 className="mb-4 flex items-center gap-2 font-bold"><TrendingUp size={18} className="text-brand-400" /> Topic breakdown</h2>
            <div className="space-y-3.5">
              {r.topic_breakdown.map((t) => (
                <div key={t.topic}>
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <span>{t.topic}{retest && t.previous_percentage != null && <span className="ml-2 text-xs text-slate-400">{t.previous_percentage}% → {t.percentage}% {t.difference != null && `(${t.difference >= 0 ? '+' : ''}${t.difference})`}</span>}</span>
                    <span className={`rounded-full px-2 py-0.5 text-[11px] ${catStyle(t.category)}`}>{t.category} · {t.correct}/{t.total}</span>
                  </div>
                  <div className="h-2 rounded-full bg-white/10"><div className={`h-2 rounded-full ${barStyle(t.category)}`} style={{ width: `${t.percentage}%` }} /></div>
                </div>
              ))}
            </div>
          </div>
          <div className="space-y-5">
            <div className="glass rounded-3xl p-6">
              <h2 className="mb-3 flex items-center gap-2 font-bold"><Target size={18} className="text-rose-400" /> Focus first</h2>
              <div className="flex flex-wrap gap-2">
                {(r.priority_topics.length ? r.priority_topics : r.weak_topics).map((t) => <span key={t} className="rounded-full bg-rose-500/15 px-3 py-1 text-xs text-rose-200">{t}</span>)}
                {!r.priority_topics.length && !r.weak_topics.length && <span className="text-sm text-slate-400">No weak topics — nice work!</span>}
              </div>
              <h2 className="mb-3 mt-5 flex items-center gap-2 font-bold"><ThumbsUp size={18} className="text-emerald-400" /> Strengths</h2>
              <div className="flex flex-wrap gap-2">
                {r.strengths.map((t) => <span key={t} className="rounded-full bg-emerald-500/15 px-3 py-1 text-xs text-emerald-200">{t}</span>)}
                {!r.strengths.length && <span className="text-sm text-slate-400">Keep practising — strengths will show up here.</span>}
              </div>
            </div>
            <div className="glass rounded-3xl p-6">
              <h2 className="mb-3 flex items-center gap-2 font-bold"><Lightbulb size={18} className="text-amber-400" /> AI recommendations</h2>
              <ul className="space-y-2 text-sm text-slate-300">{r.recommendations.map((x, i) => <li key={i}>• {x}</li>)}</ul>
            </div>
          </div>
        </div>
      </div>
    </Shell>
  )
}
