import os
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from app.database import SessionLocal
from app.models import AvaSysIntent, AvaSysIntentTrainingExample