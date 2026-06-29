import pandas as pd
import joblib
import os

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MAIN_DATA_PATH = os.path.join(BASE_DIR, "data", "scam_messages.csv")
LOCAL_DATA_PATH = os.path.join(BASE_DIR, "data", "local_sri_lankan_scam_dataset.csv")

TYPE_MODEL_PATH = os.path.join(BASE_DIR, "models", "scam_type_model.pkl")
MIN_SAMPLES_PER_CLASS = 2
RARE_CLASS_LABEL = "other"


def _prepare_type_labels(y: pd.Series) -> pd.Series:
    counts = y.value_counts()
    rare = counts[counts < MIN_SAMPLES_PER_CLASS].index
    if len(rare) == 0:
        return y

    collapsed = y.where(~y.isin(rare), other=RARE_CLASS_LABEL)
    print(
        f"\nCollapsed {len(rare)} rare scam type(s) into '{RARE_CLASS_LABEL}': "
        f"{', '.join(sorted(rare))}"
    )
    return collapsed


def load_and_merge_datasets():
    datasets = []

    if os.path.exists(MAIN_DATA_PATH):
        datasets.append(pd.read_csv(MAIN_DATA_PATH))

    if os.path.exists(LOCAL_DATA_PATH):
        datasets.append(pd.read_csv(LOCAL_DATA_PATH, encoding="utf-8-sig"))

    if not datasets:
        raise FileNotFoundError("No dataset files found.")

    df = pd.concat(datasets, ignore_index=True)

    required_columns = ["message", "scam_type"]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    df = df.dropna(subset=["message", "scam_type"])

    df["message"] = df["message"].astype(str)
    df["scam_type"] = df["scam_type"].astype(str).str.lower().str.strip()

    print("\nScam type distribution:")
    print(df["scam_type"].value_counts())

    return df


def train_type_model():
    df = load_and_merge_datasets()

    X = df["message"]
    y = _prepare_type_labels(df["scam_type"])

    split_kwargs = {"test_size": 0.25, "random_state": 42}
    if y.value_counts().min() >= MIN_SAMPLES_PER_CLASS:
        split_kwargs["stratify"] = y

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        **split_kwargs,
    )

    model = Pipeline([
        ("tfidf", TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            min_df=1
        )),
        ("classifier", LogisticRegression(
            max_iter=1000,
            class_weight="balanced"
        ))
    ])

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    print("\nAccuracy:", accuracy_score(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    os.makedirs(os.path.dirname(TYPE_MODEL_PATH), exist_ok=True)
    joblib.dump(model, TYPE_MODEL_PATH)

    print(f"\nScam type model saved to: {TYPE_MODEL_PATH}")


if __name__ == "__main__":
    train_type_model()