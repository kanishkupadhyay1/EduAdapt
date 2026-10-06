from pathlib import Path
import os
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
from xgboost import XGBClassifier

from .features import create_features

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "assessment_data.csv"
MODEL_PATH = BASE_DIR / "models" / "xgboost_model.pkl"

FEATURE_COLUMNS = [
    "accuracy",
    "recent_accuracy",
    "average_score",
    "average_attempts",
    "average_time",
    "previous_mastery",
    "learning_pace"
]


def train_model():

    df = pd.read_csv(DATA_PATH)

    feature_df = create_features(df)

    X = feature_df[FEATURE_COLUMNS]
    y = feature_df["mastery_level"]

    encoder = LabelEncoder()
    y_encoded = encoder.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y_encoded,
        test_size=3,
        random_state=42,
        stratify=y_encoded
    )

    model = XGBClassifier(
        n_estimators=100,
        max_depth=3,
        learning_rate=0.1,
        random_state=42,
        eval_metric="mlogloss"
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    print("XGBoost Accuracy:", round(accuracy, 3))

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            predictions,
            target_names=encoder.classes_,
            zero_division=0
        )
    )

    os.makedirs(MODEL_PATH.parent, exist_ok=True)

    joblib.dump(
        {
            "model": model,
            "encoder": encoder,
            "feature_columns": FEATURE_COLUMNS
        },
        MODEL_PATH
    )

    print("\nModel saved successfully.")


if __name__ == "__main__":
    train_model()