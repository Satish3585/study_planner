# AI Personalized Study Planner

Register (OTP) → Login → Welcome + subject check → 30-min AI quiz per subject (anti-cheat) → AI analysis → your schedule → AI timetable → dashboard.

**Stack:** React + TypeScript + Tailwind (Vite) · FastAPI · MongoDB Atlas (Motor) · Gemini API for AI.

## Run (Windows PowerShell)

```powershell
# Terminal 1 - backend
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env        # then edit .env (see below)
uvicorn app.main:app --reload --port 8000

# Terminal 2 - frontend
cd frontend
npm install
npm run dev                         # http://localhost:5173  (proxies /api -> :8000)
```
API docs: http://127.0.0.1:8000/docs

## Configure `backend/.env`

| Goal | Setting |
|---|---|
| Real AI quiz for ANY subject (required for real use) | `AI_PROVIDER=gemini`, `GEMINI_API_KEY=<key from aistudio.google.com>`, `GEMINI_MODEL=gemini-2.5-flash` |
| Email OTP | `OTP_DEMO_MODE=false`, `SMTP_HOST=smtp.gmail.com`, `SMTP_USER`, `SMTP_PASSWORD` (Gmail App Password), `SMTP_FROM` |
| SMS OTP (India) | `SMS_PROVIDER=fast2sms`, `FAST2SMS_API_KEY` |
| Development | `OTP_DEMO_MODE=true` -> OTP is printed in the backend console and shown on the OTP screen |

With `AI_PROVIDER=mock` the app works offline, but questions for subjects outside the built-in bank are generic filler.
If Gemini fails (bad key / quota) the backend silently falls back to mock - check the backend log.

## Before production
- Set a long random `JWT_SECRET_KEY`; set `OTP_DEMO_MODE=false`.
- Use a least-privilege MongoDB Atlas database user and add rate limiting on `/auth/*`.
- Browsers cannot block OS-level screenshots or a phone camera. The test deters and records (fullscreen, tab/blur detection, blocked copy/paste/print/PrintScreen, watermark, 3 warnings = auto-submit). For high-stakes exams use a proctoring tool.
