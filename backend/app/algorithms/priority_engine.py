from typing import List, Dict, Any

class PriorityEngine:
    """Computes academic priority weights and proportional study allocations.
    Default guideline: 60% Weak / Needs Attention, 30% Moderate, 10% Strong / Revision.
    Adapts gracefully when topic distributions vary.
    """
    @staticmethod
    def calculate_topic_weights(topic_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Given a list of topic dicts with 'topic', 'score_percentage', 'category',
        assigns 'priority' (High, Medium, Low) and 'weight' (e.g. 3.0, 1.5, 0.5).
        """
        results = []
        for t in topic_records:
            pct = t.get("score_percentage", 50.0)
            if pct < 50.0:
                cat = "Needs Attention"
                prio = "High"
                weight = 3.0
            elif pct < 75.0:
                cat = "Moderate"
                prio = "Medium"
                weight = 1.5
            else:
                cat = "Strong"
                prio = "Low"
                weight = 0.5
            
            results.append({
                **t,
                "category": cat,
                "priority": prio,
                "weight": weight
            })
        return results

    @staticmethod
    def calculate_study_distribution(
        topics: List[Dict[str, Any]], total_available_minutes: int
    ) -> List[Dict[str, Any]]:
        """Distributes available study minutes proportionally across topics
        guided by the 60/30/10 framework.
        """
        if not topics or total_available_minutes <= 0:
            return []

        # Group by category
        weak = [t for t in topics if t.get("category") == "Needs Attention"]
        moderate = [t for t in topics if t.get("category") == "Moderate"]
        strong = [t for t in topics if t.get("category") == "Strong"]

        # Proportional budget
        weak_budget = total_available_minutes * 0.60 if weak else 0
        mod_budget = total_available_minutes * 0.30 if moderate else 0
        strong_budget = total_available_minutes * 0.10 if strong else 0

        # Remaining redistributed if category is empty
        unallocated = total_available_minutes - (weak_budget + mod_budget + strong_budget)
        active_cats = (1 if weak else 0) + (1 if moderate else 0) + (1 if strong else 0)
        if active_cats > 0 and unallocated > 0:
            bonus = unallocated / active_cats
            if weak: weak_budget += bonus
            if moderate: mod_budget += bonus
            if strong: strong_budget += bonus

        allocated_topics = []
        for t in weak:
            mins = int(round(weak_budget / len(weak)))
            allocated_topics.append({**t, "allocated_minutes": max(15, mins)})

        for t in moderate:
            mins = int(round(mod_budget / len(moderate)))
            allocated_topics.append({**t, "allocated_minutes": max(15, mins)})

        for t in strong:
            mins = int(round(strong_budget / len(strong)))
            allocated_topics.append({**t, "allocated_minutes": max(15, mins)})

        return allocated_topics
