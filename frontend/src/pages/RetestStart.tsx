import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSearchParams } from 'react-router-dom'
import { RotateCcw } from 'lucide-react'
import { api, errMsg, type SubjectStatus } from '../api'
import { Alert, FullLoader, Shell, Spinner } from '../components/ui'

export default function RetestStart() {
  const nav = useNavigate(); const [params] = useSearchParams(); const day = params.get('date')
  const [subjects, setSubjects] = useState<SubjectStatus[] | null>(null); const [err, setErr] = useState(''); const [busy, setBusy] = useState('')
  const [dailyAssessment, setDailyAssessment] = useState<string | null>(null)
  const [weeklyDue, setWeeklyDue] = useState<boolean | null>(null)
  useEffect(() => {
    if (!day) return
    api.post<{ assessment_id: string }>(`/retest/start?date=${encodeURIComponent(day)}`)
      .then(({ data }) => { setDailyAssessment(data.assessment_id); nav(`/retest/quiz/${data.assessment_id}`, { replace: true }) })
      .catch((e) => setErr(errMsg(e)))
  }, [day, nav])
  useEffect(() => {
    if (day) return
    api.get<{ state: string }>('/retest/weekly/state')
      .then(({ data }) => setWeeklyDue(data.state === 'available'))
      .catch((e) => setErr(errMsg(e)))
  }, [day])
  useEffect(() => { api.get<SubjectStatus[]>('/assessment/summary').then(({ data }) => setSubjects(data.filter((s) => s.status === 'completed'))).catch((e) => setErr(errMsg(e))) }, [])
  const start = async (s: SubjectStatus) => {
    setBusy(s.subject_id)
    try {
      const { data } = await api.post<{ assessment_id: string }>('/assessment/retest/start', {
        subject_id: s.subject_id, source_assessment_id: s.completed_assessment_id, duration_minutes: 20, question_count: 3,
      })
      sessionStorage.setItem(`sp_retest_before_${data.assessment_id}`, JSON.stringify(s))
      nav(`/retest/quiz/${data.assessment_id}`)
    } catch (e) { setErr(errMsg(e)) } finally { setBusy('') }
  }
  const startWeekly = async () => {
    setBusy('weekly')
    try {
      const { data } = await api.post<{ assessment_id: string }>('/retest/weekly/start')
      nav(`/retest/quiz/${data.assessment_id}`)
    } catch (e) { setErr(errMsg(e)) } finally { setBusy('') }
  }
  if (day && !dailyAssessment && !err) return <FullLoader />
  if (!subjects) return err ? <Shell><Alert>{err}</Alert></Shell> : <FullLoader />
  return (
    <Shell>
      <div className="py-6"><h1 className="text-3xl font-extrabold">{day ? 'Daily retest' : 'Weekly retest'}</h1><p className="mt-2 text-slate-300">{day ? `Review topics completed on ${day}.` : 'After seven days, review every subject with extra questions for weaker topics.'}</p></div>
      {err && <Alert>{err}</Alert>}
      {!day && weeklyDue === true && <div className="mb-4"><Alert kind="ok">Your weekly retest is due. <button className="ml-2 underline" disabled={!!busy} onClick={() => void startWeekly()}>Start all-subject retest</button></Alert></div>}
      {!day && weeklyDue === false && <div className="mb-4"><Alert kind="info">Your next weekly retest will be offered after seven days of progress.</Alert></div>}
      <div className="mt-5 space-y-3">
        {subjects.map((s) => (
          <div key={s.subject_id} className="glass flex items-center justify-between rounded-2xl p-4">
            <div><p className="font-semibold">{s.subject_name}</p><p className="text-xs text-slate-400">Previous score: {s.percentage ?? 0}% · {s.knowledge_level}</p></div>
            <button className="btn-primary" disabled={!!busy} onClick={() => void start(s)}>{busy === s.subject_id ? <Spinner /> : <RotateCcw size={16} />} Start retest</button>
          </div>
        ))}
        {!subjects.length && <p className="mt-5 text-sm text-slate-400">Complete a baseline assessment first.</p>}
      </div>
    </Shell>
  )
}
