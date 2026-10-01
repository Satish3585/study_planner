import type { ReactElement } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth'
import { FullLoader } from './components/ui'
import Home from './pages/Home'
import Welcome from './pages/Welcome'
import Quiz from './pages/Quiz'
import Result from './pages/Result'
import Schedule from './pages/Schedule'
import Dashboard from './pages/Dashboard'
import StudySession from './pages/StudySession'
import RetestStart from './pages/RetestStart'

function Private({ children }: { children: ReactElement }) {
  const { user, loading } = useAuth()
  if (loading) return <FullLoader />
  return user ? children : <Navigate to="/" replace />
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/welcome" element={<Private><Welcome /></Private>} />
          <Route path="/quiz/:id" element={<Private><Quiz /></Private>} />
          <Route path="/retest" element={<Private><RetestStart /></Private>} />
          <Route path="/retest/quiz/:id" element={<Private><Quiz /></Private>} />
          <Route path="/result/:id" element={<Private><Result /></Private>} />
          <Route path="/retest/result/:id" element={<Private><Result /></Private>} />
          <Route path="/session/:entryId" element={<Private><StudySession /></Private>} />
          <Route path="/schedule" element={<Private><Schedule /></Private>} />
          <Route path="/dashboard" element={<Private><Dashboard /></Private>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
