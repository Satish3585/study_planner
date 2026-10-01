import random
from typing import List, Dict, Any
from app.ai.base import BaseAIProvider

# Built-in curriculum repositories for common academic subjects
SUBJECT_QUESTION_BANKS: Dict[str, List[Dict[str, Any]]] = {
    "python": [
        {
            "topic": "Functions & Scope",
            "difficulty": "medium",
            "question": "What will be the output of executing a function that modifies a variable defined in the outer enclosing scope without using the 'nonlocal' keyword?",
            "options": ["UnboundLocalError", "Variable updates globally", "Creates a new local variable", "SyntaxError at runtime"],
            "correct_answer": "Creates a new local variable",
            "explanation": "Assigning to a variable inside a function makes it local to that scope unless declared global or nonlocal."
        },
        {
            "topic": "Exception Handling",
            "difficulty": "medium",
            "question": "Which block is executed regardless of whether an exception occurs or is caught in Python?",
            "options": ["except", "finally", "else", "cleanup"],
            "correct_answer": "finally",
            "explanation": "The 'finally' clause is always executed before leaving the try statement."
        },
        {
            "topic": "OOP & Classes",
            "difficulty": "medium",
            "question": "In Python, which dunder method is invoked when the 'len()' function is called on an object?",
            "options": ["__count__()", "__length__()", "__size__()", "__len__()"],
            "correct_answer": "__len__()",
            "explanation": "Python protocols use '__len__' to return item count."
        },
        {
            "topic": "Data Structures",
            "difficulty": "easy",
            "question": "What is the average time complexity for key lookup in a Python dictionary?",
            "options": ["O(n)", "O(log n)", "O(1)", "O(n log n)"],
            "correct_answer": "O(1)",
            "explanation": "Python dictionaries are implemented as hash tables with O(1) average lookup."
        },
        {
            "topic": "Decorators & Generators",
            "difficulty": "hard",
            "question": "What keyword turns a standard Python function into a generator that yields values lazily?",
            "options": ["generate", "produce", "yield", "return lazy"],
            "correct_answer": "yield",
            "explanation": "The 'yield' statement pauses function execution and emits a value to the caller."
        },
        {
            "topic": "Memory Management",
            "difficulty": "hard",
            "question": "What primary mechanism does CPython use for automatic memory reclamation?",
            "options": ["Mark and Sweep", "Reference Counting with Cyclic GC", "Compacting GC", "Stop-the-world collector"],
            "correct_answer": "Reference Counting with Cyclic GC",
            "explanation": "CPython tracks reference counts and employs a cyclic garbage collector to detect unreachable cycles."
        }
    ],
    "advanced java": [
        {
            "topic": "Inheritance",
            "difficulty": "medium",
            "question": "Which keyword prevents a Java method from being overridden in a subclass?",
            "options": ["static", "abstract", "final", "sealed"],
            "correct_answer": "final",
            "explanation": "Declaring a method 'final' prevents subclasses from altering its implementation."
        },
        {
            "topic": "Collections & Generics",
            "difficulty": "medium",
            "question": "Which Java Collections interface maintains elements in FIFO (First-In, First-Out) order?",
            "options": ["Set", "Queue", "Map", "Stack"],
            "correct_answer": "Queue",
            "explanation": "Queues typically order elements in a FIFO manner."
        },
        {
            "topic": "Concurrency & Multithreading",
            "difficulty": "hard",
            "question": "What guarantee does the 'volatile' keyword provide in the Java Memory Model?",
            "options": ["Atomic compound operations", "Visibility of writes across threads", "Mutual exclusion lock", "Deadlock prevention"],
            "correct_answer": "Visibility of writes across threads",
            "explanation": "'volatile' ensures writes to a variable are immediately visible to other threads."
        },
        {
            "topic": "JVM Internals",
            "difficulty": "hard",
            "question": "In which memory area are Java Class metadata and static methods stored in modern Java (JDK 8+)?",
            "options": ["PermGen", "Metaspace (Native Memory)", "Java Heap", "Thread Stack"],
            "correct_answer": "Metaspace (Native Memory)",
            "explanation": "Metaspace replaced PermGen in Java 8 and resides in native OS memory."
        },
        {
            "topic": "Streams & Lambdas",
            "difficulty": "medium",
            "question": "Which stream operation is an intermediate operation in Java Stream API?",
            "options": ["collect()", "forEach()", "filter()", "count()"],
            "correct_answer": "filter()",
            "explanation": "'filter' returns a new Stream and does not trigger terminal evaluation."
        }
    ],
    "mathematics": [
        {
            "topic": "Linear Algebra",
            "difficulty": "medium",
            "question": "If the determinant of a square matrix A is 0, what does this indicate about matrix A?",
            "options": ["A is invertible", "A is non-singular", "A is singular and has no inverse", "A is symmetric"],
            "correct_answer": "A is singular and has no inverse",
            "explanation": "A determinant of zero means the rows/columns are linearly dependent, so no inverse exists."
        },
        {
            "topic": "Differential Calculus",
            "difficulty": "easy",
            "question": "What is the derivative of f(x) = ln(x) for x > 0?",
            "options": ["1/x", "e^x", "x", "1/(x^2)"],
            "correct_answer": "1/x",
            "explanation": "By fundamental calculus rules, d/dx[ln(x)] = 1/x."
        },
        {
            "topic": "Probability & Statistics",
            "difficulty": "medium",
            "question": "For a standard normal distribution, what are the mean and standard deviation?",
            "options": ["mean = 0, std = 1", "mean = 1, std = 0", "mean = 0, std = 0.5", "mean = 100, std = 15"],
            "correct_answer": "mean = 0, std = 1",
            "explanation": "Standard normal distribution is defined with mean μ = 0 and variance σ² = 1."
        },
        {
            "topic": "Integral Calculus",
            "difficulty": "hard",
            "question": "Which method is the reverse of the product rule for differentiation?",
            "options": ["Integration by Substitution", "Integration by Parts", "Partial Fractions", "Trapezoidal Rule"],
            "correct_answer": "Integration by Parts",
            "explanation": "Integration by parts follows from the product rule: ∫u dv = uv - ∫v du."
        }
    ],
    "economics": [
        {
            "topic": "Microeconomics",
            "difficulty": "easy",
            "question": "What occurs when the price of a good is set above the market equilibrium price?",
            "options": ["Shortage", "Surplus", "Hyperinflation", "Depreciation"],
            "correct_answer": "Surplus",
            "explanation": "At a price above equilibrium, quantity supplied exceeds quantity demanded, creating a surplus."
        },
        {
            "topic": "Macroeconomics",
            "difficulty": "medium",
            "question": "What does GDP stand for?",
            "options": ["Gross Domestic Product", "General Domestic Profit", "Global Development Plan", "Gross Development Price"],
            "correct_answer": "Gross Domestic Product",
            "explanation": "Gross Domestic Product measures total monetary value of finished goods/services."
        },
        {
            "topic": "Fiscal Policy",
            "difficulty": "hard",
            "question": "Which policy is considered expansionary fiscal policy during a recession?",
            "options": ["Increasing interest rates", "Decreasing government spending", "Lowering taxes and increasing government spending", "Selling central bank bonds"],
            "correct_answer": "Lowering taxes and increasing government spending",
            "explanation": "Lower taxes and higher public spending stimulate aggregate demand."
        }
    ]
}

def generate_dynamic_questions_for_arbitrary_subject(subject: str, count: int) -> List[Dict[str, Any]]:
    """Synthesizes high-caliber conceptual questions for ANY subject."""
    clean_sub = subject.strip().title()
    core_topics = [
        f"Foundations of {clean_sub}",
        f"Core Principles & Models",
        f"Applied Methodologies in {clean_sub}",
        f"Analytical Problem Solving",
        f"Advanced Frameworks & Systems",
        f"Contemporary Applications"
    ]
    
    questions = []
    for i in range(count):
        topic = core_topics[i % len(core_topics)]
        idx = i + 1
        diff = "easy" if i < count // 3 else ("hard" if i > (count * 2) // 3 else "medium")
        
        q_text = f"In the study of {clean_sub} ({topic}), which statement correctly characterizes key theoretical principles?"
        opt_correct = f"Systematic validation through verified principles of {clean_sub}"
        opt_b = f"Arbitrary heuristics without reference to {topic}"
        opt_c = f"Restricting empirical analysis strictly to static non-adaptive cases"
        opt_d = f"Ignoring foundational assumptions in applied environments"
        
        options = [opt_correct, opt_b, opt_c, opt_d]
        random.shuffle(options)
        
        questions.append({
            "question_id": f"q{idx}",
            "topic": topic,
            "difficulty": diff,
            "question": q_text,
            "options": options,
            "correct_answer": opt_correct,
            "explanation": f"Understanding {topic} in {clean_sub} relies on systematic verification of foundational principles."
        })
    return questions

class MockAIProvider(BaseAIProvider):
    async def generate_assessment_questions(
        self, subject: str, course: str, semester: str, count: int = 15, difficulty: str = "adaptive"
    ) -> List[Dict[str, Any]]:
        sub_key = subject.strip().lower()
        
        # Check matching subject bank
        matched_bank = None
        for key in SUBJECT_QUESTION_BANKS:
            if key in sub_key or sub_key in key:
                matched_bank = SUBJECT_QUESTION_BANKS[key]
                break
                
        if matched_bank:
            # Duplicate and adapt to reach desired count
            pool = list(matched_bank)
            questions = []
            for i in range(count):
                base_q = pool[i % len(pool)].copy()
                base_q["question_id"] = f"q{i+1}"
                # shuffle options
                opts = list(base_q["options"])
                base_q["options"] = opts
                questions.append(base_q)
            return questions
        
        # Generate arbitrary subject questions
        return generate_dynamic_questions_for_arbitrary_subject(subject, count)

    async def analyze_assessment(
        self, subject: str, total_score: int, total_questions: int, topic_stats: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        pct = (total_score / max(1, total_questions)) * 100.0
        
        strengths = []
        moderate = []
        weak = []
        
        for item in topic_stats:
            top_pct = item.get("percentage", 0.0)
            topic_name = item.get("topic", "Topic")
            if top_pct >= 75.0:
                strengths.append(topic_name)
            elif top_pct >= 45.0:
                moderate.append(topic_name)
            else:
                weak.append(topic_name)
                
        if not weak and not moderate and not strengths:
            weak.append(f"Foundations of {subject}")
            moderate.append(f"Core Principles of {subject}")
            
        priority = list(weak) + list(moderate)
        
        if pct >= 80:
            level = "Advanced"
        elif pct >= 50:
            level = "Intermediate"
        else:
            level = "Beginner"
            
        recommendations = [
            f"Dedicate 60% of your initial study blocks to weak topics: {', '.join(weak[:2]) or 'fundamental concepts'}.",
            f"Solidify moderate topics with active recall and practice problems before progressing to new modules.",
            f"Maintain your strong topics ({', '.join(strengths[:2]) or 'basics'}) through spaced weekly revisions."
        ]
        
        return {
            "overall_level": level,
            "strengths": strengths,
            "moderate_topics": moderate,
            "weak_topics": weak,
            "priority_topics": priority,
            "feedback": [
                f"You scored {round(pct)}% overall across the assessed topics.",
                f"Use active recall on {', '.join(weak[:2]) or 'the topics you just reviewed'}.",
                "Keep the next study block short and consistent to reinforce this progress.",
            ],
            "recommendations": recommendations
        }

    async def generate_checkpoint_questions(
        self, subject: str, topic: str, count: int = 3, level: str = "intermediate"
    ) -> List[Dict[str, Any]]:
        questions = []
        for i in range(count):
            idx = i + 1
            opt_a = f"Correctly implements the core rule of {topic}"
            opt_b = f"Bypasses standard verification in {subject}"
            opt_c = f"Applies unrelated conventions without context"
            opt_d = f"Causes unpredictable runtime side effects"
            
            options = [opt_a, opt_b, opt_c, opt_d]
            random.shuffle(options)
            
            questions.append({
                "question_id": f"cp_{idx}",
                "topic": topic,
                "question": f"When applying {topic} in practice, which approach adheres to standard principles?",
                "options": options,
                "correct_answer": opt_a,
                "explanation": f"In {subject}, mastering {topic} requires adhering to verified structural methodologies."
            })
        return questions

    async def generate_recommendations(
        self, user_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        weak_topics = user_data.get("weak_topics", [])
        avg_score = user_data.get("average_score", 65.0)
        
        recs = []
        if weak_topics:
            recs.append({
                "category": "Topic Priority",
                "topic": weak_topics[0],
                "priority": "High",
                "recommendation_text": f"Your performance in {weak_topics[0]} needs immediate focus. We have prioritized 45-minute deep work blocks for it."
            })
        recs.append({
            "category": "Study Rhythm",
            "topic": "Balance",
            "priority": "Medium",
            "recommendation_text": "Maintain your 9-8-7 balance by protecting your sleep window. Take full advantage of the 10-minute breaks between blocks."
        })
        if avg_score < 70:
            recs.append({
                "category": "Active Recall",
                "topic": "Retention",
                "priority": "High",
                "recommendation_text": "Review checkpoint explanations after every study session to convert short-term memory into long-term mastery."
            })
        return recs
