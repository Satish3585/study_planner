import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Navigate } from 'react-router-dom'
import { BrainCircuit, CalendarClock, ShieldCheck, Sparkles, X, Eye, EyeOff, ArrowLeft } from 'lucide-react'
import { api, errMsg } from '../api'
import { nextRoute, useAuth } from '../auth'
import { Alert, Field, Logo, Spinner } from '../components/ui'

type Mode = 'register' | 'login' | 'otp'
const isEmail = (v: string) => /^[A-Za-z0-9_.+-]+@gmail\.com$/i.test(v.trim())
const isMobile = (v: string) => /^\+?[0-9]{10,15}$/.test(v.replace(/[\s-]/g, ''))

export default function Home() {
  const { user, loading, login } = useAuth()
  const [mode, setMode] = useState<Mode>('register')
  const [identifier, setIdentifier] = useState('')
  const [demoOtp, setDemoOtp] = useState<string | null>(null)
  const card = useRef<HTMLDivElement>(null)

  const go = (m: Mode) => { setMode(m); card.current?.scrollIntoView({ behavior: 'smooth', block: 'center' }) }

  if (!loading && user) return <Navigate to={nextRoute(user)} replace />

  return (
    <div className="min-h-screen bg-aurora">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5">
        <Logo />
        <div className="flex gap-2">
          <button className="btn-ghost" onClick={() => go('login')}>Login</button>
          <button className="btn-primary" onClick={() => go('register')}>Get Started</button>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl items-center gap-10 px-5 pb-16 pt-6 lg:grid-cols-2 lg:pt-14">
        <section className="animate-fadeUp">
          <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-brand-100">
            <Sparkles size={14} className="text-fuchsia-400" /> Powered by AI · Built around your schedule
          </span>
          <h1 className="mt-5 text-4xl font-extrabold leading-tight tracking-tight sm:text-5xl">
            Study smarter with a plan that <span className="bg-gradient-to-r from-brand-400 to-fuchsia-400 bg-clip-text text-transparent">learns you</span>.
          </h1>
          <p className="mt-4 max-w-lg text-slate-300">
            Take a 30-minute AI assessment in your own subjects. We find your weak topics, then build a realistic
            timetable around your college hours, work and free time.
          </p>
          <div className="mt-8 grid gap-3 sm:grid-cols-3">
            {[
              [BrainCircuit, 'AI Assessment', 'Custom quiz for every subject you study'],
              [CalendarClock, 'Smart Timetable', 'Fits college, work & breaks'],
              [ShieldCheck, 'Fair & Secure', 'Timed, proctored-style tests'],
            ].map(([Icon, t, d]) => {
              const I = Icon as typeof BrainCircuit
              return (
                <div key={t as string} className="glass rounded-2xl p-4">
                  <I className="text-brand-400" size={22} />
                  <p className="mt-2 text-sm font-semibold">{t as string}</p>
                  <p className="text-xs text-slate-400">{d as string}</p>
                </div>
              )
            })}
          </div>
        </section>

        <section ref={card} className="animate-fadeUp">
          <div className="glass rounded-3xl p-6 sm:p-7">
            {mode !== 'otp' && (
              <div className="mb-5 grid grid-cols-2 rounded-xl bg-black/30 p-1 text-sm font-semibold">
                {(['register', 'login'] as const).map((m) => (
                  <button key={m} onClick={() => setMode(m)}
                    className={`rounded-lg py-2 transition ${mode === m ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-white'}`}>
                    {m === 'register' ? 'Register' : 'Login'}
                  </button>
                ))}
              </div>
            )}
            {mode === 'register' && <Register onDone={(id, otp) => { setIdentifier(id); setDemoOtp(otp); setMode('otp') }} />}
            {mode === 'login' && (
              <Login onSuccess={login}
                onUnverified={(id, otp) => { setIdentifier(id); setDemoOtp(otp); setMode('otp') }} />
            )}
            {mode === 'otp' && (
              <Otp identifier={identifier} demoOtp={demoOtp} onBack={() => setMode('register')}
                onVerified={(token) => login(token)} />
            )}
          </div>
        </section>
      </main>
    </div>
  )
}

/* ---------------- Register ---------------- */
function Register({ onDone }: { onDone: (id: string, demoOtp: string | null) => void }) {
  const [f, setF] = useState({ full_name: '', age: '', class_grade: '', course: '', semester: '', contact: '', password: '', confirm: '' })
  const [subjects, setSubjects] = useState<string[]>([])
  const [subInput, setSubInput] = useState('')
  const [show, setShow] = useState(false)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value })

  const addSubject = () => {
    const parts = subInput.split(',').map((s) => s.trim()).filter(Boolean)
    if (!parts.length) return
    setSubjects((prev) => [...prev, ...parts.filter((p) => !prev.some((x) => x.toLowerCase() === p.toLowerCase()))])
    setSubInput('')
  }

  const submit = async (e: FormEvent) => {
    e.preventDefault(); setErr('')
    const contact = f.contact.trim()
    const pending = subInput.trim() ? [...subjects, ...subInput.split(',').map((s) => s.trim()).filter(Boolean)] : subjects
    if (f.full_name.trim().length < 2) return setErr('Please enter your full name.')
    const age = Number(f.age); if (!age || age < 5 || age > 120) return setErr('Please enter a valid age.')
    if (!f.class_grade || !f.course.trim() || !f.semester) return setErr('Please fill class, course and year/semester.')
    if (!pending.length) return setErr('Add at least one subject.')
    if (!isEmail(contact) && !isMobile(contact)) return setErr('Enter a valid Gmail address ending with @gmail.com or a 10–15 digit mobile number.')
    if (f.password.length < 8 || !/[A-Za-z]/.test(f.password) || !/[0-9]/.test(f.password)) return setErr('Password needs 8+ characters with letters and numbers.')
    if (f.password !== f.confirm) return setErr('Passwords do not match.')
    setBusy(true)
    try {
      const email = isEmail(contact)
      const { data } = await api.post('/auth/register', {
        full_name: f.full_name.trim(), age, class_grade: f.class_grade, course: f.course.trim(), semester: f.semester,
        subjects: pending, email: email ? contact.toLowerCase() : null, mobile: email ? null : contact.replace(/[\s-]/g, ''),
        password: f.password, confirm_password: f.confirm,
      })
      onDone(data.identifier, data.demo_otp ?? null)
    } catch (e2) { setErr(errMsg(e2)) } finally { setBusy(false) }
  }

  return (
    <form onSubmit={submit} className="space-y-3.5">
      <h2 className="text-lg font-bold">Create your account</h2>
      <div className="grid gap-3 sm:grid-cols-[1fr_90px]">
        <Field label="Full name"><input className="input" value={f.full_name} onChange={set('full_name')} placeholder="e.g. Satish Yadav" /></Field>
        <Field label="Age"><input className="input" type="number" value={f.age} onChange={set('age')} placeholder="20" /></Field>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Class / Level">
          <select className="input" value={f.class_grade} onChange={set('class_grade')}>
            <option value="">Select…</option>
            {['Class 8', 'Class 9', 'Class 10', 'Class 11', 'Class 12', 'Diploma', 'Undergraduate', 'Postgraduate', 'Other'].map((x) => <option key={x}>{x}</option>)}
          </select>
        </Field>
        <Field label="Year / Semester">
          <select className="input" value={f.semester} onChange={set('semester')}>
            <option value="">Select…</option>
            <optgroup label="Year">{[1, 2, 3, 4].map((n) => <option key={'y' + n}>Year {n}</option>)}</optgroup>
            <optgroup label="Semester">{[1, 2, 3, 4, 5, 6, 7, 8].map((n) => <option key={'s' + n}>Semester {n}</option>)}</optgroup>
          </select>
        </Field>
      </div>
      <Field label="Course"><input className="input" list="courses" value={f.course} onChange={set('course')} placeholder="BCA, B.Com, B.Sc, B.Tech, PUC Science…" />
        <datalist id="courses">{['BCA', 'MCA', 'B.Com', 'B.Sc', 'B.Tech', 'B.E', 'BBA', 'MBA', 'PUC Science', 'PUC Commerce'].map((c) => <option key={c} value={c} />)}</datalist>
      </Field>
      <Field label="Subjects" hint="Type a subject and press Enter or comma. You can change these later.">
        <div className="input flex flex-wrap items-center gap-1.5 !py-2">
          {subjects.map((s) => (
            <span key={s} className="inline-flex items-center gap-1 rounded-full bg-brand-500/20 px-2.5 py-1 text-xs text-brand-100">
              {s}<button type="button" onClick={() => setSubjects(subjects.filter((x) => x !== s))}><X size={12} /></button>
            </span>
          ))}
          <input className="min-w-[8rem] flex-1 bg-transparent text-sm outline-none placeholder:text-slate-500" value={subInput}
            placeholder={subjects.length ? 'Add another…' : 'Python, DBMS, Maths…'}
            onChange={(e) => setSubInput(e.target.value)} onBlur={addSubject}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ',') { e.preventDefault(); addSubject() } }} />
        </div>
      </Field>
      <Field label="Email or mobile number" hint="Use a Gmail address ending with @gmail.com, or a mobile number.">
        <input className="input" value={f.contact} onChange={set('contact')} placeholder="you@example.com or 9876543210" />
      </Field>
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Password">
          <div className="relative">
            <input className="input pr-10" type={show ? 'text' : 'password'} value={f.password} onChange={set('password')} placeholder="8+ chars, letters & numbers" />
            <button type="button" className="absolute right-3 top-2.5 text-slate-400" onClick={() => setShow(!show)}>{show ? <EyeOff size={16} /> : <Eye size={16} />}</button>
          </div>
        </Field>
        <Field label="Confirm password"><input className="input" type={show ? 'text' : 'password'} value={f.confirm} onChange={set('confirm')} /></Field>
      </div>
      {err && <Alert>{err}</Alert>}
      <button className="btn-primary w-full" disabled={busy}>{busy ? <Spinner /> : 'Register & send OTP'}</button>
    </form>
  )
}

/* ---------------- Login ---------------- */
function Login({ onSuccess, onUnverified }: { onSuccess: (t: string) => Promise<unknown>; onUnverified: (id: string, otp: string | null) => void }) {
  const [id, setId] = useState(''); const [pw, setPw] = useState('')
  const [show, setShow] = useState(false); const [err, setErr] = useState(''); const [busy, setBusy] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault(); setErr('')
    if (!id.trim() || !pw) return setErr('Enter your email / mobile number and password.')
    setBusy(true)
    try {
      const { data } = await api.post('/auth/login', { identifier: id.trim(), password: pw })
      await onSuccess(data.access_token)
    } catch (e2) {
      const ax = e2 as { response?: { status?: number; data?: { detail?: { demo_otp?: string } } } }
      if (ax.response?.status === 403) onUnverified(id.trim().toLowerCase(), ax.response.data?.detail?.demo_otp ?? null)
      else setErr(errMsg(e2))
    } finally { setBusy(false) }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <h2 className="text-lg font-bold">Welcome back</h2>
      <Field label="Email ID / Mobile number"><input className="input" value={id} onChange={(e) => setId(e.target.value)} placeholder="you@example.com or 9876543210" autoComplete="username" /></Field>
      <Field label="Password">
        <div className="relative">
          <input className="input pr-10" type={show ? 'text' : 'password'} value={pw} onChange={(e) => setPw(e.target.value)} autoComplete="current-password" />
          <button type="button" className="absolute right-3 top-2.5 text-slate-400" onClick={() => setShow(!show)}>{show ? <EyeOff size={16} /> : <Eye size={16} />}</button>
        </div>
      </Field>
      {err && <Alert>{err}</Alert>}
      <button className="btn-primary w-full" disabled={busy}>{busy ? <Spinner /> : 'Login'}</button>
    </form>
  )
}

/* ---------------- OTP ---------------- */
function Otp({ identifier, demoOtp, onBack, onVerified }: { identifier: string; demoOtp: string | null; onBack: () => void; onVerified: (t: string) => Promise<unknown> }) {
  const [code, setCode] = useState(''); const [err, setErr] = useState(''); const [busy, setBusy] = useState(false)
  const [demo, setDemo] = useState(demoOtp); const [wait, setWait] = useState(60); const [info, setInfo] = useState('')

  useEffect(() => { if (wait <= 0) return; const t = setTimeout(() => setWait(wait - 1), 1000); return () => clearTimeout(t) }, [wait])

  const verify = async (e: FormEvent) => {
    e.preventDefault(); setErr('')
    if (code.length !== 6) return setErr('Enter the 6-digit code.')
    setBusy(true)
    try { const { data } = await api.post('/auth/verify-otp', { identifier, otp: code }); await onVerified(data.access_token) }
    catch (e2) { setErr(errMsg(e2)) } finally { setBusy(false) }
  }
  const resend = async () => {
    setErr(''); setInfo('')
    try { const { data } = await api.post('/auth/send-otp', { identifier }); setDemo(data.demo_otp ?? null); setWait(60); setInfo('A new code has been sent.') }
    catch (e2) { setErr(errMsg(e2)) }
  }

  return (
    <form onSubmit={verify} className="space-y-4">
      <button type="button" onClick={onBack} className="flex items-center gap-1 text-xs text-slate-400 hover:text-white"><ArrowLeft size={14} /> Back</button>
      <div>
        <h2 className="text-lg font-bold">Verify your account</h2>
        <p className="text-sm text-slate-400">Enter the 6-digit code sent to <span className="text-slate-200">{identifier}</span></p>
      </div>
      {demo && <Alert kind="info">Demo mode: your OTP is <b className="tracking-widest">{demo}</b> <button type="button" className="ml-2 underline" onClick={() => setCode(demo)}>autofill</button></Alert>}
      <input className="input text-center text-2xl font-bold tracking-[0.6em]" inputMode="numeric" maxLength={6} value={code} autoFocus
        onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))} placeholder="••••••" />
      {err && <Alert>{err}</Alert>}
      {info && <Alert kind="ok">{info}</Alert>}
      <button className="btn-primary w-full" disabled={busy}>{busy ? <Spinner /> : 'Verify & continue'}</button>
      <p className="text-center text-xs text-slate-400">
        {wait > 0 ? `Resend code in ${wait}s` : <button type="button" className="text-brand-400 underline" onClick={resend}>Resend code</button>}
      </p>
    </form>
  )
}
