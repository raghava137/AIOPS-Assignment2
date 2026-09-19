"""Trains the TF-IDF + MultinomialNB spam classifier and saves it with joblib.

Run this once before building the image; model.joblib is copied into the image
so the container does not have to train at startup.
"""

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

SEED = 42
DATA_PATH = "spam_dataset.csv"
MODEL_PATH = "model.joblib"


def main():
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} rows: {df['label'].value_counts().to_dict()}")

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"],
        test_size=0.2, random_state=SEED, stratify=df["label"],
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2))),
        ("nb", MultinomialNB()),
    ])

    pipeline.fit(X_train, y_train)

    preds = pipeline.predict(X_test)
    print(f"\nTest accuracy: {accuracy_score(y_test, preds):.4f}")
    print(classification_report(y_test, preds))

    joblib.dump(pipeline, MODEL_PATH)
    print(f"Saved {MODEL_PATH}")


if __name__ == "__main__":
    main()
