"""Question Service for EduAdapt.

Coordinates Practice and Assessment question sessions, authoritative backend evaluation,
Learning Twin updates, question history persistence, and roadmap progression.
Enforces |P|=5, |A|=10, P ∩ A = ∅.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from eduadapt.services.question_bank import (
    PRACTICE_BANK,
    ASSESSMENT_BANK,
    get_practice_questions,
    get_assessment_questions,
    normalize_topic_name,
    verify_topic_zero_intersection,
)

HISTORY_FILE = Path(__file__).resolve().parent.parent.parent.parent / "data" / "question_history.json"

PPS_CURRICULUM_SEQUENCE = [
    "Variables and Data Types",
    "Operators and Expressions",
    "Conditionals",
    "Loops",
    "Arrays",
    "Strings",
    "Functions",
    "Pointers",
    "Structures",
    "Dynamic Memory Allocation",
]


class QuestionService:
    """Manages question retrieval, evaluation, history, and roadmap transitions."""

    def __init__(self, history_path: Optional[Path] = None) -> None:
        self.history_file = history_path or HISTORY_FILE
        self._ensure_history_file()

    def _ensure_history_file(self) -> None:
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            if not self.history_file.exists():
                self.history_file.write_text("{}", encoding="utf-8")
        except Exception:
            pass

    def _load_history(self) -> Dict[str, Any]:
        try:
            if self.history_file.exists():
                text = self.history_file.read_text(encoding="utf-8")
                return json.loads(text) if text.strip() else {}
        except Exception:
            pass
        return {}

    def _save_history(self, history: Dict[str, Any]) -> None:
        try:
            self.history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")
        except Exception:
            pass

    def get_next_topic(self, current_topic: str) -> str:
        """Return the next topic in the PPS curriculum progression sequence."""
        norm_topic = normalize_topic_name(current_topic)
        try:
            idx = PPS_CURRICULUM_SEQUENCE.index(norm_topic)
            if idx + 1 < len(PPS_CURRICULUM_SEQUENCE):
                return PPS_CURRICULUM_SEQUENCE[idx + 1]
            return PPS_CURRICULUM_SEQUENCE[0]
        except ValueError:
            return "Variables and Data Types"

    def get_practice_session(self, student_id: str, topic: str) -> Dict[str, Any]:
        """Generate a practice session with exactly 5 questions (|P| = 5)."""
        questions = get_practice_questions(topic, count=5)
        return {
            "student_id": student_id,
            "topic": topic,
            "total_questions": len(questions),
            "questions": questions,
            "type": "practice_mcq",
        }

    def evaluate_practice_submission(
        self,
        student_id: str,
        topic: str,
        answers: Dict[Any, str],
        time_taken_seconds: int = 25,
    ) -> Dict[str, Any]:
        """Authoritative backend evaluation for a 5-question Practice session."""
        questions = get_practice_questions(topic, count=5)
        correct_count = 0
        detailed_results = []
        weak_concepts = []

        for idx, q in enumerate(questions):
            # Answers map index or question_id to selected option letter (e.g. 'A', 'B')
            student_choice = (
                answers.get(str(idx))
                or answers.get(idx)
                or answers.get(q["id"])
                or ""
            )
            student_choice = str(student_choice).strip().upper()
            if student_choice and ")" in student_choice:
                student_choice = student_choice.split(")")[0].strip()

            correct_choice = str(q.get("correct_option", "B")).strip().upper()
            is_match = (student_choice == correct_choice)

            if is_match:
                correct_count += 1
            else:
                concept = q.get("concept", topic)
                if concept not in weak_concepts:
                    weak_concepts.append(concept)

            detailed_results.append({
                "question_id": q["id"],
                "question": q["question"],
                "student_answer": student_choice or "Not Answered",
                "correct_answer": correct_choice,
                "is_correct": is_match,
                "explanation": q.get("explanation", ""),
                "concept": q.get("concept", topic),
            })

        total = len(questions) or 5
        score = int(round((correct_count / total) * 100))
        accuracy = round(correct_count / total, 2)
        is_passing = (score >= 60)

        # Record practice attempt in history
        history = self._load_history()
        s_hist = history.setdefault(student_id, {}).setdefault("practice", [])
        s_hist.append({
            "timestamp": datetime.utcnow().isoformat(),
            "topic": topic,
            "score": score,
            "accuracy": accuracy,
            "correct_count": correct_count,
            "total_questions": total,
            "time_taken_seconds": time_taken_seconds,
            "weak_concepts": weak_concepts,
        })
        self._save_history(history)

        feedback = (
            f"Great job! You answered {correct_count} of {total} practice questions correctly ({score}%). "
            f"You are well prepared to take the formal assessment."
            if is_passing else
            f"You scored {score}% ({correct_count}/{total} correct). Focus on revising: {', '.join(weak_concepts) or topic}."
        )

        return {
            "student_id": student_id,
            "topic": topic,
            "score": score,
            "accuracy": accuracy,
            "correct_count": correct_count,
            "total_questions": total,
            "is_correct": is_passing,
            "results": detailed_results,
            "weak_concepts": weak_concepts,
            "feedback": feedback,
            "time_taken_seconds": time_taken_seconds,
            "recommended_next": "tests" if is_passing else "learn",
        }

    def get_assessment_session(self, student_id: str, topic: str) -> Dict[str, Any]:
        """Generate a formal assessment session with exactly 10 questions (|A| = 10).
        Enforces zero intersection: P ∩ A = ∅.
        """
        questions = get_assessment_questions(topic, count=10)
        return {
            "student_id": student_id,
            "topic": topic,
            "total_questions": len(questions),
            "questions": questions,
            "type": "formal_assessment",
        }

    def evaluate_assessment_submission(
        self,
        student_id: str,
        topic: str,
        answers: Dict[Any, str],
        time_taken_seconds: int = 120,
    ) -> Dict[str, Any]:
        """Authoritative backend evaluation for a 10-question Formal Assessment."""
        questions = get_assessment_questions(topic, count=10)
        correct_count = 0
        detailed_results = []
        weak_concepts = []

        for idx, q in enumerate(questions):
            student_choice = (
                answers.get(str(idx))
                or answers.get(idx)
                or answers.get(q["id"])
                or ""
            )
            student_choice = str(student_choice).strip().upper()
            if student_choice and ")" in student_choice:
                student_choice = student_choice.split(")")[0].strip()

            correct_choice = str(q.get("correct_option", "B")).strip().upper()
            is_match = (student_choice == correct_choice)

            if is_match:
                correct_count += 1
            else:
                concept = q.get("concept", topic)
                if concept not in weak_concepts:
                    weak_concepts.append(concept)

            detailed_results.append({
                "question_id": q["id"],
                "question": q["question"],
                "student_answer": student_choice or "Not Answered",
                "correct_answer": correct_choice,
                "is_correct": is_match,
                "explanation": q.get("explanation", ""),
                "concept": q.get("concept", topic),
            })

        total = len(questions) or 10
        score = int(round((correct_count / total) * 100))
        accuracy = round(correct_count / total, 2)
        mastery_achieved = (score >= 60)
        next_topic = self.get_next_topic(topic) if mastery_achieved else topic

        # Record in history
        history = self._load_history()
        asmt_hist = history.setdefault(student_id, {}).setdefault("assessments", [])
        asmt_hist.append({
            "timestamp": datetime.utcnow().isoformat(),
            "topic": topic,
            "score": score,
            "accuracy": accuracy,
            "correct_count": correct_count,
            "total_questions": total,
            "mastery_achieved": mastery_achieved,
            "time_taken_seconds": time_taken_seconds,
            "weak_concepts": weak_concepts,
            "next_topic": next_topic,
        })

        completed_topics = history.setdefault(student_id, {}).setdefault("completed_topics", [])
        if mastery_achieved and topic not in completed_topics:
            completed_topics.append(topic)

        self._save_history(history)

        feedback = (
            f"Congratulations! You scored {score}% ({correct_count}/{total}) and achieved satisfactory mastery in {topic}. "
            f"Your roadmap has updated to next recommended topic: {next_topic}."
            if mastery_achieved else
            f"You scored {score}% ({correct_count}/{total} correct). Satisfactory mastery requires 60%. "
            f"Review weak concepts ({', '.join(weak_concepts) or topic}) and practice further before retrying."
        )

        return {
            "student_id": student_id,
            "topic": topic,
            "score": score,
            "accuracy": accuracy,
            "correct_count": correct_count,
            "total_questions": total,
            "is_correct": mastery_achieved,
            "mastery_achieved": mastery_achieved,
            "completed_topic": topic if mastery_achieved else None,
            "next_topic": next_topic,
            "results": detailed_results,
            "weak_concepts": weak_concepts,
            "feedback": feedback,
            "time_taken_seconds": time_taken_seconds,
            "recommended_next": "learn" if mastery_achieved else "practice",
        }

    def get_student_roadmap(self, student_id: str) -> Dict[str, Any]:
        """Return the completed topics, current active topic, and upcoming topics for student."""
        history = self._load_history()
        completed = history.get(student_id, {}).get("completed_topics", [])

        current = PPS_CURRICULUM_SEQUENCE[0]
        for t in PPS_CURRICULUM_SEQUENCE:
            if t not in completed:
                current = t
                break

        upcoming = [t for t in PPS_CURRICULUM_SEQUENCE if t not in completed and t != current]

        return {
            "student_id": student_id,
            "completed_topics": completed,
            "current_topic": current,
            "upcoming_topics": upcoming,
            "progress_percent": int(round((len(completed) / len(PPS_CURRICULUM_SEQUENCE)) * 100)),
        }
