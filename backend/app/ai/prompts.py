import json
from typing import List, Dict, Any

def get_assessment_prompt(subject: str, course: str, semester: str, count: int, difficulty: str) -> str:
    return f"""You are an expert academic evaluator.
Generate {count} high-quality, conceptual multiple-choice questions (MCQs) for a baseline diagnostic assessment.

Subject: {subject}
Academic Program / Course: {course}
Semester / Year: {semester}
Target Difficulty: {difficulty}

Requirements:
1. Cover key fundamental, intermediate, and advanced topics within {subject}.
2. Each question must have exactly 4 plausible options (labeled A, B, C, D or given as 4 text choices).
3. Specify the exact topic for each question.
4. Specify the difficulty: 'easy', 'medium', or 'hard'.
5. Provide the correct answer (e.g., 'A', 'B', 'C', or 'D', or the exact option text).
6. Provide a concise, clear explanation.

Return ONLY a valid JSON object matching this schema, without markdown formatting or code fences:
{{
  "questions": [
    {{
      "question_id": "q1",
      "topic": "Topic Name",
      "difficulty": "medium",
      "question": "Question text here?",
      "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
      "correct_answer": "Option 2",
      "explanation": "Explanation why this is correct."
    }}
  ]
}}
"""

def get_analysis_prompt(subject: str, total_score: int, total_questions: int, topic_stats: List[Dict[str, Any]]) -> str:
    stats_str = json.dumps(topic_stats, indent=2)
    return f"""You are an educational diagnostics AI. Analyze this student's baseline assessment performance in '{subject}'.

Overall Score: {total_score} / {total_questions} ({round((total_score/max(1, total_questions))*100, 1)}%)

Topic Performance Breakdown:
{stats_str}

Analyze their strengths, moderate topics, and weak areas. Group them objectively and provide constructive recommendations.

Return ONLY a valid JSON object with no markdown fences:
{{
  "overall_level": "Beginner | Intermediate | Advanced",
  "strengths": ["topic1", "topic2"],
  "moderate_topics": ["topic3"],
  "weak_topics": ["topic4"],
  "priority_topics": ["topic4", "topic3"],
  "feedback": [
    "One concise observation about the result.",
    "One actionable next step.",
    "One encouraging closing line."
  ],
  "recommendations": [
    "Actionable recommendation grounded in their weak topics.",
    "Revision strategy recommendation."
  ]
}}
"""

def get_checkpoint_prompt(subject: str, topic: str, count: int, level: str) -> str:
    return f"""You are an expert tutor. The student just finished an intensive study session on '{topic}' in the subject '{subject}'.
Generate {count} quick verification checkpoint questions at '{level}' level to test their conceptual retention and application.

Requirements:
- 4 multiple choice options per question.
- Clear correct answer and explanation.

Return ONLY a valid JSON object with no markdown fences:
{{
  "questions": [
    {{
      "question_id": "cp1",
      "topic": "{topic}",
      "question": "Question text?",
      "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
      "correct_answer": "Option 1",
      "explanation": "Why Option 1 is correct."
    }}
  ]
}}
"""
