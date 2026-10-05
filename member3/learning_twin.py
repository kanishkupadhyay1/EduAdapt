from typing import Any


def create_learning_twin(
    student_features: dict[str, Any]
) -> dict[str, Any]:

    accuracy = float(student_features["accuracy"])

    if accuracy < 0.50:
        difficulty = "Easy"
    elif accuracy < 0.75:
        difficulty = "Medium"
    else:
        difficulty = "Advanced"

    learning_pace = float(student_features["learning_pace"])

    if learning_pace < 0.02:
        pace = "Slow"
    elif learning_pace < 0.04:
        pace = "Medium"
    else:
        pace = "Fast"

    return {
        "student_id": student_features["student_id"],
        "mastery": round(
            float(student_features["previous_mastery"]),
            2
        ),
        "accuracy": round(accuracy, 2),
        "learning_pace": pace,
        "recommended_difficulty": difficulty
    }