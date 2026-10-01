import json
import logging
import re
from typing import List, Dict, Any, Optional
import httpx
from app.config import settings
from app.ai.base import BaseAIProvider
from app.ai.mock_provider import MockAIProvider
from app.ai.prompts import get_assessment_prompt, get_analysis_prompt, get_checkpoint_prompt

logger = logging.getLogger(__name__)

class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL or "gemini-2.5-flash"
        self.mock_fallback = MockAIProvider()

    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Extracts JSON even if wrapped in markdown codeblocks or surrounded by text."""
        try:
            # 1. Direct parse
            return json.loads(text.strip())
        except Exception:
            pass

        # 2. Check markdown blocks: ```json ... ```
        pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except Exception:
                pass

        # 3. Find outermost braces { ... }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                pass

        return None

    async def _call_gemini(self, prompt: str) -> Optional[str]:
        if not self.api_key:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "response_mime_type": "application/json"
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                else:
                    logger.warning(f"Gemini API returned status {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")

        return None

    async def generate_assessment_questions(
        self, subject: str, course: str, semester: str, count: int = 15, difficulty: str = "adaptive"
    ) -> List[Dict[str, Any]]:
        prompt = get_assessment_prompt(subject, course, semester, count, difficulty)
        raw_text = await self._call_gemini(prompt)

        if raw_text:
            parsed = self._extract_json_from_text(raw_text)
            if parsed and "questions" in parsed and isinstance(parsed["questions"], list) and len(parsed["questions"]) > 0:
                # Normalize questions
                questions = []
                for idx, q in enumerate(parsed["questions"][:count]):
                    questions.append({
                        "question_id": f"q{idx+1}",
                        "topic": q.get("topic", f"{subject} Concepts"),
                        "difficulty": q.get("difficulty", "medium"),
                        "question": q.get("question", "Question text?"),
                        "options": q.get("options", ["A", "B", "C", "D"]),
                        "correct_answer": q.get("correct_answer", "A"),
                        "explanation": q.get("explanation", "Standard concept explanation.")
                    })
                return questions

        logger.info(f"Using mock fallback for assessment generation: {subject}")
        return await self.mock_fallback.generate_assessment_questions(subject, course, semester, count, difficulty)

    async def analyze_assessment(
        self, subject: str, total_score: int, total_questions: int, topic_stats: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        prompt = get_analysis_prompt(subject, total_score, total_questions, topic_stats)
        raw_text = await self._call_gemini(prompt)

        if raw_text:
            parsed = self._extract_json_from_text(raw_text)
            if parsed and "overall_level" in parsed:
                return {
                    "overall_level": parsed.get("overall_level", "Intermediate"),
                    "strengths": parsed.get("strengths", []),
                    "moderate_topics": parsed.get("moderate_topics", []),
                    "weak_topics": parsed.get("weak_topics", []),
                    "priority_topics": parsed.get("priority_topics", []),
                    "feedback": parsed.get("feedback", []),
                    "recommendations": parsed.get("recommendations", [])
                }

        logger.info(f"Using mock fallback for assessment analysis: {subject}")
        return await self.mock_fallback.analyze_assessment(subject, total_score, total_questions, topic_stats)

    async def generate_checkpoint_questions(
        self, subject: str, topic: str, count: int = 3, level: str = "intermediate"
    ) -> List[Dict[str, Any]]:
        prompt = get_checkpoint_prompt(subject, topic, count, level)
        raw_text = await self._call_gemini(prompt)

        if raw_text:
            parsed = self._extract_json_from_text(raw_text)
            if parsed and "questions" in parsed and isinstance(parsed["questions"], list) and len(parsed["questions"]) > 0:
                questions = []
                for idx, q in enumerate(parsed["questions"][:count]):
                    questions.append({
                        "question_id": f"cp_{idx+1}",
                        "topic": topic,
                        "question": q.get("question", f"Checkpoint query on {topic}?"),
                        "options": q.get("options", ["A", "B", "C", "D"]),
                        "correct_answer": q.get("correct_answer", "A"),
                        "explanation": q.get("explanation", "Conceptual rationale.")
                    })
                return questions

        logger.info(f"Using mock fallback for checkpoint questions: {subject} - {topic}")
        return await self.mock_fallback.generate_checkpoint_questions(subject, topic, count, level)

    async def generate_recommendations(
        self, user_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        return await self.mock_fallback.generate_recommendations(user_data)
