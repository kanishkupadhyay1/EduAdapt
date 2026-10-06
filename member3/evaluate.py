from pathlib import Path
import joblib
import pandas as pd

from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from .features import create_features

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "assessment_data.csv"
MODEL_PATH = BASE_DIR / "models" / "xgboost_model.pkl"


def evaluate_model():

    df = pd.read_csv(DATA_PATH)

    feature_df = create_features(df)

    saved = joblib.load(MODEL_PATH)

    model = saved["model"]
    encoder = saved["encoder"]
    feature_columns = saved["feature_columns"]

    X = feature_df[feature_columns]

    y = encoder.transform(
        feature_df["mastery_level"]
    )

    _, X_test, _, y_test = train_test_split(
        X,
        y,
        test_size=3,
        random_state=42,
        stratify=y
    )

    predictions = model.predict(X_test)

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    print("Evaluation Accuracy:", round(accuracy, 3))

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            predictions,
            target_names=encoder.classes_,
            zero_division=0
        )
    )


if __name__ == "__main__":
    evaluate_model()