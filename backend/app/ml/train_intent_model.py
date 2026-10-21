import os
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from app.database import SessionLocal
from app.models import AvaSysIntent, AvaSysIntentTrainingExample




def load_training_data():
    db = SessionLocal()
    try:
        rows = (
            db.query(
                AvaSysIntentTrainingExample.text,
                AvaSysIntent.name
            )
            .join(
                AvaSysIntent,
                AvaSysIntent.id == AvaSysIntentTrainingExample.intent_id
            )
            .filter(
                AvaSysIntent.is_active.is_(True),
                AvaSysIntentTrainingExample.is_active.is_(True)
            )
            .all()
        )

        texts = [row.text for row in rows]
        labels = [row.name for row in rows]

        return texts, labels

    finally:
        db.close()


def train_intent_model():
    texts, labels = load_training_data()

    print("Total training examples:", len(texts))
    print("Unique intents:", sorted(set(labels)))

    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(texts)

    model = LogisticRegression(max_iter=1000)
    model.fit(X, labels)

    print("Intent model trained successfully!")

    artifacts_dir = os.path.join(os.path.dirname(__file__), "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)

    model_path = os.path.join(artifacts_dir, "intent_model.joblib")

    joblib.dump(
        {
            "vectorizer": vectorizer,
            "model": model,
        },
        model_path,
    )

    print("Intent model saved successfully:", model_path)



if __name__ == "__main__":
    train_intent_model()