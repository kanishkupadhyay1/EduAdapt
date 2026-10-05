import pandas as pd


def create_features(df: pd.DataFrame) -> pd.DataFrame:

    features = []

    for student_id, group in df.groupby("student_id"):

        total_questions = len(group)
        correct_answers = int(group["correct"].sum())

        accuracy = (
            correct_answers / total_questions
            if total_questions > 0
            else 0.0
        )

        average_score = float(group["score"].mean())
        average_attempts = float(group["attempts"].mean())
        average_time = float(group["time_taken"].mean())

        recent_data = group.tail(2)

        recent_accuracy = (
            recent_data["correct"].sum() / len(recent_data)
            if len(recent_data) > 0
            else 0.0
        )

        previous_mastery = accuracy
        learning_pace = 1.0 / (average_time + 1.0)

        mastery_level = str(group["mastery_level"].iloc[0])

        features.append({
            "student_id": str(student_id),
            "accuracy": accuracy,
            "recent_accuracy": recent_accuracy,
            "average_score": average_score,
            "average_attempts": average_attempts,
            "average_time": average_time,
            "previous_mastery": previous_mastery,
            "learning_pace": learning_pace,
            "mastery_level": mastery_level
        })

    return pd.DataFrame(features)