import importlib.resources as pkg_resources
import os
import warnings

import joblib
import pandas as pd
from sklearn.exceptions import InconsistentVersionWarning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM


class RefusalClassifier:
    def __init__(self, model_path=None, vectorizer_path=None, scaler_path=None):
        self.model = None
        self.vectorizer = None
        self.scaler = None
        self.model_path = (
            model_path
            or "agentic_security/refusal_classifier/oneclass_svm_model.joblib"
        )
        self.vectorizer_path = (
            vectorizer_path
            or "agentic_security/refusal_classifier/tfidf_vectorizer.joblib"
        )
        self.scaler_path = (
            scaler_path or "agentic_security/refusal_classifier/scaler.joblib"
        )

    def train(self, data_paths):
        """
        Train the refusal classifier.

        Parameters:
        - data_paths (list): List of file paths to CSV files containing the training data.
        """
        # Load and concatenate data from multiple CSV files
        texts = []
        for data_path in data_paths:
            df = pd.read_csv(os.path.expanduser(data_path))
            # Assuming the CSV has columns named 'GPT4_response', 'ChatGPT_response', 'Claude_response'
            responses = pd.concat(
                [df["GPT4_response"], df["ChatGPT_response"], df["Claude_response"]],
                ignore_index=True,
            )
            texts.extend(responses.tolist())

        # Remove any NaN values
        texts = [text for text in texts if isinstance(text, str)]

        # Vectorize the text data
        self.vectorizer = TfidfVectorizer(max_features=1000)
        X = self.vectorizer.fit_transform(texts)

        # Scale the features
        self.scaler = StandardScaler(with_mean=False)
        X_scaled = self.scaler.fit_transform(X)

        # Train the One-Class SVM model
        self.model = OneClassSVM(kernel="rbf", gamma="auto", nu=0.05)
        self.model.fit(X_scaled)

    def save_model(self):
        """
        Save the trained model, vectorizer, and scaler to disk.
        """
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.vectorizer, self.vectorizer_path)
        joblib.dump(self.scaler, self.scaler_path)

    def load_model(self):
        """
        Load the trained model, vectorizer, and scaler from disk.
        """
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
            try:
                self.model = joblib.load(self.model_path)
                self.vectorizer = joblib.load(self.vectorizer_path)
                self.scaler = joblib.load(self.scaler_path)
            except FileNotFoundError:
                # Load from package resources
                package = (
                    __package__  # This should be 'agentic_security.refusal_classifier'
                )

                # Load model
                with pkg_resources.open_binary(
                    package, "oneclass_svm_model.joblib"
                ) as f:
                    self.model = joblib.load(f)

                # Load vectorizer
                with pkg_resources.open_binary(package, "tfidf_vectorizer.joblib") as f:
                    self.vectorizer = joblib.load(f)

                # Load scaler
                with pkg_resources.open_binary(package, "scaler.joblib") as f:
                    self.scaler = joblib.load(f)

    def is_refusal(self, text):
        """
        Predict whether a given text is a refusal response.

        Parameters:
        - text (str): The input text to classify.

        Returns:
        - bool: True if the text is a refusal response, False otherwise.
        """
        if not self.model or not self.vectorizer or not self.scaler:
            raise ValueError(
                "Model, vectorizer, or scaler not loaded. Call load_model() first."
            )

        x = self.vectorizer.transform([text])
        x_scaled = self.scaler.transform(x)
        prediction = self.model.predict(x_scaled)
        return prediction[0] == 1  # Returns True if it's a refusal response
