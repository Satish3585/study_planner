import { Loader2, GraduationCap } from 'lucide-react'
import type { ReactNode } from 'react'

export const Logo = ({ small }: { small?: boolean }) => (
  <div className="flex items-center gap-2.5">
    <div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-fuchsia-500 shadow-lg shadow-brand-500/30">
      <GraduationCap size={20} />
    </div>
    {!small && <span className="font-bold tracking-tight">AI Study<span className="text-brand-400">Planner</span></span>}
  </div>
)
export const Spinner = ({ className = '' }: { className?: string }) => <Loader2 className={`animate-spin ${className}`} size={18} />
export const FullLoader = () => <div className="grid min-h-screen place-items-center bg-aurora"><Spinner className="text-brand-400" /></div>
export const Alert = ({ kind = 'error', children }: { kind?: 'error' | 'ok' | 'info'; children: ReactNode }) => {
  const c = { error: 'border-rose-500/30 bg-rose-500/10 text-rose-200', ok: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200', info: 'border-sky-500/30 bg-sky-500/10 text-sky-200' }[kind]
  return <div className={`rounded-xl border px-3.5 py-2.5 text-sm ${c}`}>{children}</div>
}
export const Field = ({ label, children, hint }: { label: string; children: ReactNode; hint?: string }) => (
  <label className="block"><span className="label">{label}</span>{children}{hint && <span className="mt-1 block text-[11px] text-slate-500">{hint}</span>}</label>
)
export const Shell = ({ children, right }: { children: ReactNode; right?: ReactNode }) => (
  <div className="min-h-screen bg-aurora">
    <header className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5"><Logo />{right}</header>
    <main className="mx-auto max-w-6xl px-5 pb-16">{children}</main>
  </div>
)
