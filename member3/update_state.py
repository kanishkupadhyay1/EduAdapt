import pandas as pd
from typing import Any

from features import create_features
from learning_twin import create_learning_twin


DATA_PATH = "../data/assessment_data.csv"


def update_student_state(
    student_id: str
) -> dict[str, Any] | None:

    df = pd.read_csv(DATA_PATH)

    feature_df = create_features(df)

    student_data = feature_df[
        feature_df["student_id"] == student_id
    ]

    if student_data.empty:
        return None

    student_features = student_data.iloc[0]

    return create_learning_twin(
        student_features.to_dict()
    )


if __name__ == "__main__":

    state = update_student_state("S001")

    print("\nUpdated Student State:")
    print(state)