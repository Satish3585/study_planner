import axios from 'axios'

export const api = axios.create({ baseURL: '/api' })

const KEY = 'sp_token'
export const getToken = () => localStorage.getItem(KEY)
export const setToken = (t: string | null) => (t ? localStorage.setItem(KEY, t) : localStorage.removeItem(KEY))

api.interceptors.request.use((cfg) => {
  const t = getToken()
  if (t) cfg.headers.Authorization = `Bearer ${t}`
  return cfg
})
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && getToken()) {
      setToken(null)
      window.location.href = '/'
    }
    return Promise.reject(err)
  },
)

/** Turns any backend/network error into a readable message. */
export function errMsg(e: unknown): string {
  const ax = e as { response?: { data?: { detail?: unknown } }; message?: string }
  const d = ax.response?.data?.detail
  if (typeof d === 'string') return d
  if (d && typeof d === 'object' && 'message' in d) return String((d as { message: unknown }).message)
  if (!ax.response) return 'Cannot reach the server. Is the backend running on port 8000?'
  return ax.message || 'Something went wrong.'
}

export interface User {
  id: string; full_name: string; age: number; class_grade: string; course: string; semester: string
  email: string | null; mobile: string | null; is_verified: boolean
  has_completed_assessment: boolean; has_completed_availability: boolean
}
export interface SubjectStatus {
  subject_id: string; subject_name: string; status: 'pending' | 'in_progress' | 'completed'
  completed_assessment_id: string | null; in_progress_assessment_id: string | null
  percentage: number | null; knowledge_level: string | null
}
export interface Question { question_id: string; topic: string; difficulty: string; question: string; options: string[] }
export interface Quiz {
  assessment_id: string; subject_name: string; title: string; duration_minutes: number
  total_questions: number; status: string; remaining_seconds: number; questions: Question[]
}
export interface StudySession {
  id: string; timetable_entry_id: string | null; subject_id: string | null; subject_name: string | null
  topic: string; objective: string | null; status: string; scheduled_duration_minutes: number
  actual_duration_minutes: number; started_at: string | null; paused_at: string | null
  ended_at: string | null; focus_score: number; interruption_count: number
}
export interface TopicRow {
  topic: string; total: number; correct: number; percentage: number; category: string; priority: string
  previous_percentage?: number | null; difference?: number | null; trend?: string | null
}
export interface Result {
  assessment_id: string; subject_name: string; status: string; score: number; total_questions: number
  percentage: number; knowledge_level: string; anti_cheat_warnings: number; topic_breakdown: TopicRow[]
  strengths: string[]; moderate_topics: string[]; weak_topics: string[]; priority_topics: string[]; recommendations: string[]
  trend?: string | null; feedback?: string[]
}
export interface Entry {
  id: string; date: string; start_time: string; end_time: string; duration_minutes: number; subject_name: string
  topic: string; activity_type: string; priority: string; reason: string | null; status: string
}
export interface Dashboard {
  user_name: string
  today_progress: { total_sessions: number; completed_sessions: number; remaining_sessions: number; percentage: number }
  next_session: Entry | null
  needs_attention_topics: { subject: string; topic: string; score: number }[]
  strong_topics: { subject: string; topic: string; score: number }[]
  latest_assessment_score: number | null; study_streak_days: number; total_study_minutes: number
  completion_rate_percentage: number; average_checkpoint_score: number; ai_insight: string
  latest_assessment_subject?: string | null
}
export interface ProgressAnalytics {
  total_study_time_hours: number; planned_study_time_hours: number; total_completed_sessions: number
  total_planned_sessions: number; session_completion_rate: number; average_checkpoint_accuracy: number
  focus_interruptions_total: number; current_streak_days: number
  subjects_progress: { subject_id: string; subject_name: string; topics_count: number; strong_count: number; moderate_count: number; weak_count: number; average_score: number; completed_study_hours: number }[]
  daily_study_breakdown: { date?: string; day?: string; minutes?: number; completed_minutes?: number; study_minutes?: number }[]
  recommendations: { recommendation_text: string; topic?: string | null; priority: string }[]
}
