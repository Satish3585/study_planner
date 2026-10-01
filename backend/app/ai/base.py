from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseAIProvider(ABC):
    @abstractmethod
    async def generate_assessment_questions(
        self, subject: str, course: str, semester: str, count: int = 15, difficulty: str = "adaptive"
    ) -> List[Dict[str, Any]]:
        """Generates list of questions:
        [{
          "question_id": "q1",
          "topic": "...",
          "difficulty": "medium",
          "question": "...",
          "options": ["A", "B", "C", "D"],
          "correct_answer": "B",
          "explanation": "..."
        }]
        """
        pass

    @abstractmethod
    async def analyze_assessment(
        self, subject: str, total_score: int, total_questions: int, topic_stats: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyzes student performance:
        {
          "overall_level": "Intermediate",
          "strengths": [...],
          "moderate_topics": [...],
          "weak_topics": [...],
          "priority_topics": [...],
          "recommendations": [...]
        }
        """
        pass

    @abstractmethod
    async def generate_checkpoint_questions(
        self, subject: str, topic: str, count: int = 3, level: str = "intermediate"
    ) -> List[Dict[str, Any]]:
        """Generates 3-5 quick post-study checkpoint questions."""
        pass

    @abstractmethod
    async def generate_recommendations(
        self, user_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generates actionable grounded study recommendations."""
        pass
