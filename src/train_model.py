import pandas as pd
import joblib
import os

from sklearn.model_selection import cross_val_score, train_test_split, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MAIN_DATA_PATH = os.path.join(BASE_DIR, "data", "scam_messages.csv")
LOCAL_DATA_PATH = os.path.join(BASE_DIR, "data", "local_sri_lankan_scam_dataset.csv")

MODEL_PATH = os.path.join(BASE_DIR, "models", "scam_detector_model.pkl")


def load_and_merge_datasets():
    datasets = []

    if os.path.exists(MAIN_DATA_PATH):
        main_df = pd.read_csv(MAIN_DATA_PATH)
        datasets.append(main_df)
        print(f"Loaded main dataset: {MAIN_DATA_PATH}")
        print(f"Main dataset rows: {len(main_df)}")

    if os.path.exists(LOCAL_DATA_PATH):
        local_df = pd.read_csv(LOCAL_DATA_PATH)
        datasets.append(local_df)
        print(f"Loaded local dataset: {LOCAL_DATA_PATH}")
        print(f"Local dataset rows: {len(local_df)}")

    if not datasets:
        raise FileNotFoundError("No dataset files found in the data folder.")

    df = pd.concat(datasets, ignore_index=True)

    required_columns = ["message", "label"]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    df = df.dropna(subset=["message", "label"])

    df["message"] = df["message"].astype(str).str.strip()
    df["label"] = df["label"].astype(str).str.lower().str.strip()

    valid_labels = ["safe", "suspicious", "scam"]
    df = df[df["label"].isin(valid_labels)]

    # Prefer the latest label when the exact same message appears more than once.
    df = df.drop_duplicates(subset=["message"], keep="last")

    print("\nFinal merged dataset rows:", len(df))
    print("\nLabel distribution:")
    print(df["label"].value_counts())

    return df


def build_model():
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
        )),
        ("classifier", LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            C=0.8,
        ))
    ])


def train_model():
    df = load_and_merge_datasets()

    X = df["message"]
    y = df["label"]

    model = build_model()

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X, y, cv=cv, scoring="f1_macro")
    print("\n5-fold cross-validation F1 (macro):", round(cv_scores.mean(), 3))
    print("Fold scores:", [round(score, 3) for score in cv_scores])

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    print("\nHold-out accuracy:", accuracy_score(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print(f"\nModel saved successfully to: {MODEL_PATH}")


if __name__ == "__main__":
    train_model()
