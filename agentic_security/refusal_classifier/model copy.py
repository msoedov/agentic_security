import pandas as pd
from os import path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
import joblib

# **Training and Saving**

# Load your data
df = pd.read_csv(path.expanduser("~/Downloads/data_en.csv"))
texts = pd.concat(
    [df["GPT4_response"], df["ChatGPT_response"], df["Claude_response"]],
    ignore_index=True,
)

# Preprocess and vectorize
vectorizer = TfidfVectorizer(max_features=1000)
X = vectorizer.fit_transform(texts)

scaler = StandardScaler(with_mean=False)
X_scaled = scaler.fit_transform(X)
model = OneClassSVM(kernel="rbf", gamma="auto", nu=0.05).fit(X_scaled)

# Save the model and vectorizer to disk
joblib.dump(model, "oneclass_svm_model.joblib")
joblib.dump(vectorizer, "tfidf_vectorizer.joblib")

# **Loading and Predicting**

# Load the model and vectorizer from disk
model = joblib.load("oneclass_svm_model.joblib")
vectorizer = joblib.load("tfidf_vectorizer.joblib")


def is_refusal(text):
    x = vectorizer.transform([text])
    x_scaled = scaler.transform(x)
    prediction = model.predict(x_scaled)
    return prediction[0] == 1  # Returns True if it's a refusal response
