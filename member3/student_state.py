import joblib
import pandas as pd
from typing import Any

from features import create_features
from learning_twin import create_learning_twin


DATA_PATH = "../data/assessment_data.csv"
MODEL_PATH = "../models/xgboost_model.pkl"


def get_student_state(
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

    twin = create_learning_twin(
        student_features.to_dict()
    )

    saved = joblib.load(MODEL_PATH)

    model = saved["model"]
    encoder = saved["encoder"]
    feature_columns = saved["feature_columns"]

    X = student_data[feature_columns]

    prediction = model.predict(X)[0]

    predicted_mastery = encoder.inverse_transform(
        [prediction]
    )[0]

    twin["predicted_mastery_level"] = str(
        predicted_mastery
    )

    return twin


if __name__ == "__main__":

    state = get_student_state("S001")

    print("\nStudent State:")
    print(state)