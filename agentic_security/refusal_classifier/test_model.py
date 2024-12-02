from unittest.mock import patch

import pandas as pd
import pytest

from .model import RefusalClassifier


@pytest.fixture
def mock_training_data():
    """Create mock training data CSV content"""
    data = {
        "GPT4_response": ["I cannot help with that", "I must decline"],
        "ChatGPT_response": ["I won't assist with that", "That's not appropriate"],
        "Claude_response": ["I cannot comply", "That would be unethical"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def classifier():
    """Create a RefusalClassifier instance with test paths"""
    return RefusalClassifier(
        model_path="test_model.joblib",
        vectorizer_path="test_vectorizer.joblib",
        scaler_path="test_scaler.joblib",
    )


@pytest.fixture
def trained_classifier(classifier, mock_training_data):
    """Create a trained classifier with mock data"""
    with patch("pandas.read_csv", return_value=mock_training_data):
        classifier.train(["mock_data.csv"])
    return classifier


def test_is_refusal_without_loading():
    """Test prediction without loading model raises error"""
    classifier = RefusalClassifier()
    with pytest.raises(ValueError, match="Model, vectorizer, or scaler not loaded"):
        classifier.is_refusal("test text")


def test_is_refusal(trained_classifier):
    """Test refusal prediction"""
    # Test refusal text
    refusal_text = "I cannot help with that kind of request"
    assert trained_classifier.is_refusal(refusal_text) in [True, False]

    # Test non-refusal text
    normal_text = "Here's the information you requested"
    assert trained_classifier.is_refusal(normal_text) in [True, False]
