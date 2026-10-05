import pandas as pd
from typing import Any


def load_assessment_data(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path)


def calculate_student_performance(
    df: pd.DataFrame,
    student_id: str
) -> dict[str, Any]:

    student_data = df[df["student_id"] == student_id]

    total_questions = len(student_data)
    correct_answers = int(student_data["correct"].sum())

    accuracy = (
        correct_answers / total_questions
        if total_questions > 0
        else 0.0
    )

    average_score = (
        float(student_data["score"].mean())
        if total_questions > 0
        else 0.0
    )

    return {
        "student_id": student_id,
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "accuracy": round(accuracy, 3),
        "average_score": round(average_score, 2)
    }