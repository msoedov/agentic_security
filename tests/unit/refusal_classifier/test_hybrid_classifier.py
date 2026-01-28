"""Unit tests for hybrid refusal classifier."""

from inline_snapshot import snapshot

from agentic_security.refusal_classifier.hybrid_classifier import (
    DetectionResult,
    HybridRefusalClassifier,
    HybridResult,
    create_hybrid_classifier,
)


class MockDetector:
    """Mock detector for testing."""

    def __init__(self, result: bool):
        self.result = result
        self.calls: list[str] = []

    def is_refusal(self, response: str) -> bool:
        self.calls.append(response)
        return self.result


class FailingDetector:
    """Detector that raises exceptions."""

    def is_refusal(self, response: str) -> bool:
        raise RuntimeError("Detector failed")


# Table-driven tests for DetectionResult
detection_result_cases = [
    # (is_refusal, weight, expected_weighted_score)
    (True, 1.0, 1.0),
    (False, 1.0, -1.0),
    (True, 2.0, 2.0),
    (False, 2.0, -2.0),
    (True, 0.5, 0.5),
    (False, 0.5, -0.5),
]


class TestDetectionResult:

    def test_weighted_score_cases(self):
        for is_refusal, weight, expected in detection_result_cases:
            result = DetectionResult(method="test", is_refusal=is_refusal, weight=weight)
            assert result.weighted_score == expected

    def test_default_weight(self):
        result = DetectionResult(method="test", is_refusal=True)
        assert result.weight == snapshot(1.0)


class TestHybridResult:

    def test_total_weight(self):
        results = [
            DetectionResult(method="a", is_refusal=True, weight=1.0),
            DetectionResult(method="b", is_refusal=False, weight=2.0),
        ]
        hybrid = HybridResult(is_refusal=True, confidence=0.8, method_results=results)
        assert hybrid.total_weight == snapshot(3.0)

    def test_refusal_weight(self):
        results = [
            DetectionResult(method="a", is_refusal=True, weight=1.0),
            DetectionResult(method="b", is_refusal=False, weight=2.0),
            DetectionResult(method="c", is_refusal=True, weight=0.5),
        ]
        hybrid = HybridResult(is_refusal=True, confidence=0.8, method_results=results)
        assert hybrid.refusal_weight == snapshot(1.5)

    def test_empty_results(self):
        hybrid = HybridResult(is_refusal=False, confidence=0.0, method_results=[])
        assert hybrid.total_weight == snapshot(0.0)
        assert hybrid.refusal_weight == snapshot(0.0)


class TestHybridRefusalClassifier:

    def test_no_detectors_returns_false(self):
        classifier = HybridRefusalClassifier()
        result = classifier.classify("test response")
        assert result.is_refusal is False
        assert result.confidence == snapshot(0.0)

    def test_single_detector_refusal(self):
        classifier = HybridRefusalClassifier()
        classifier.add_detector(MockDetector(True), name="mock")
        result = classifier.classify("test")
        assert result.is_refusal is True
        assert result.confidence == snapshot(1.0)

    def test_single_detector_non_refusal(self):
        classifier = HybridRefusalClassifier()
        classifier.add_detector(MockDetector(False), name="mock")
        result = classifier.classify("test")
        assert result.is_refusal is False
        assert result.confidence == snapshot(1.0)

    def test_two_detectors_both_refusal(self):
        classifier = HybridRefusalClassifier()
        classifier.add_detector(MockDetector(True), name="a")
        classifier.add_detector(MockDetector(True), name="b")
        result = classifier.classify("test")
        assert result.is_refusal is True
        assert result.confidence == snapshot(1.0)
        assert len(result.method_results) == snapshot(2)

    def test_two_detectors_both_non_refusal(self):
        classifier = HybridRefusalClassifier()
        classifier.add_detector(MockDetector(False), name="a")
        classifier.add_detector(MockDetector(False), name="b")
        result = classifier.classify("test")
        assert result.is_refusal is False
        assert result.confidence == snapshot(1.0)

    def test_weighted_voting_higher_refusal(self):
        classifier = HybridRefusalClassifier(threshold=0.5)
        classifier.add_detector(MockDetector(True), weight=2.0, name="a")
        classifier.add_detector(MockDetector(False), weight=1.0, name="b")
        result = classifier.classify("test")
        # refusal_weight = 2.0, total = 3.0, ratio = 0.666
        assert result.is_refusal is True
        assert round(result.confidence, 2) == snapshot(0.67)

    def test_weighted_voting_higher_non_refusal(self):
        classifier = HybridRefusalClassifier(threshold=0.5)
        classifier.add_detector(MockDetector(True), weight=1.0, name="a")
        classifier.add_detector(MockDetector(False), weight=2.0, name="b")
        result = classifier.classify("test")
        # refusal_weight = 1.0, total = 3.0, ratio = 0.333
        assert result.is_refusal is False
        assert round(result.confidence, 2) == snapshot(0.67)

    def test_threshold_boundary(self):
        classifier = HybridRefusalClassifier(threshold=0.5)
        classifier.add_detector(MockDetector(True), weight=1.0, name="a")
        classifier.add_detector(MockDetector(False), weight=1.0, name="b")
        result = classifier.classify("test")
        # ratio = 0.5, exactly at threshold
        assert result.is_refusal is True

    def test_high_threshold(self):
        classifier = HybridRefusalClassifier(threshold=0.8)
        classifier.add_detector(MockDetector(True), weight=2.0, name="a")
        classifier.add_detector(MockDetector(False), weight=1.0, name="b")
        result = classifier.classify("test")
        # ratio = 0.666, below 0.8 threshold
        assert result.is_refusal is False

    def test_unanimous_required_all_agree_refusal(self):
        classifier = HybridRefusalClassifier(require_unanimous=True)
        classifier.add_detector(MockDetector(True), name="a")
        classifier.add_detector(MockDetector(True), name="b")
        result = classifier.classify("test")
        assert result.is_refusal is True

    def test_unanimous_required_all_agree_non_refusal(self):
        classifier = HybridRefusalClassifier(require_unanimous=True)
        classifier.add_detector(MockDetector(False), name="a")
        classifier.add_detector(MockDetector(False), name="b")
        result = classifier.classify("test")
        assert result.is_refusal is False
        assert result.confidence == snapshot(1.0)

    def test_unanimous_required_disagreement(self):
        classifier = HybridRefusalClassifier(require_unanimous=True)
        classifier.add_detector(MockDetector(True), name="a")
        classifier.add_detector(MockDetector(False), name="b")
        result = classifier.classify("test")
        # Disagreement returns uncertain result
        assert result.is_refusal is False
        assert result.confidence == snapshot(0.5)

    def test_failing_detector_skipped(self):
        classifier = HybridRefusalClassifier()
        classifier.add_detector(MockDetector(True), name="good")
        classifier.add_detector(FailingDetector(), name="bad")
        result = classifier.classify("test")
        # Only the good detector counted
        assert result.is_refusal is True
        assert len(result.method_results) == snapshot(1)

    def test_all_detectors_fail(self):
        classifier = HybridRefusalClassifier()
        classifier.add_detector(FailingDetector(), name="bad1")
        classifier.add_detector(FailingDetector(), name="bad2")
        result = classifier.classify("test")
        assert result.is_refusal is False
        assert result.confidence == snapshot(0.0)

    def test_method_chaining(self):
        classifier = (
            HybridRefusalClassifier()
            .add_detector(MockDetector(True), name="a")
            .add_detector(MockDetector(False), name="b")
        )
        assert len(classifier._detectors) == snapshot(2)

    def test_detector_calls_recorded(self):
        detector = MockDetector(True)
        classifier = HybridRefusalClassifier()
        classifier.add_detector(detector, name="mock")
        classifier.classify("test input")
        assert detector.calls == snapshot(["test input"])

    def test_is_refusal_simple_interface(self):
        classifier = HybridRefusalClassifier()
        classifier.add_detector(MockDetector(True), name="mock")
        assert classifier.is_refusal("test") is True

    def test_is_refusal_with_confidence(self):
        classifier = HybridRefusalClassifier()
        classifier.add_detector(MockDetector(True), name="mock")
        is_ref, conf = classifier.is_refusal_with_confidence("test")
        assert is_ref is True
        assert conf == snapshot(1.0)

    def test_default_detector_name(self):
        classifier = HybridRefusalClassifier()
        classifier.add_detector(MockDetector(True))
        result = classifier.classify("test")
        assert result.method_results[0].method == snapshot("MockDetector")


# Table-driven tests for create_hybrid_classifier factory
factory_cases = [
    # (kwargs, expected_detector_count)
    ({}, 0),
    ({"marker_detector": MockDetector(True)}, 1),
    ({"ml_detector": MockDetector(True)}, 1),
    ({"llm_detector": MockDetector(True)}, 1),
    ({"marker_detector": MockDetector(True), "ml_detector": MockDetector(False)}, 2),
    ({"marker_detector": MockDetector(True), "ml_detector": MockDetector(False), "llm_detector": MockDetector(True)}, 3),
]


class TestCreateHybridClassifier:

    def test_detector_count_cases(self):
        for kwargs, expected_count in factory_cases:
            classifier = create_hybrid_classifier(**kwargs)
            assert len(classifier._detectors) == expected_count

    def test_threshold_passed(self):
        classifier = create_hybrid_classifier(threshold=0.7)
        assert classifier.threshold == snapshot(0.7)

    def test_default_weights(self):
        classifier = create_hybrid_classifier(
            marker_detector=MockDetector(True),
            ml_detector=MockDetector(True),
            llm_detector=MockDetector(True),
        )
        weights = {d.name: d.weight for d in classifier._detectors}
        assert weights == snapshot({"marker": 1.0, "ml": 1.5, "llm": 2.0})

    def test_custom_weights(self):
        classifier = create_hybrid_classifier(
            marker_detector=MockDetector(True),
            ml_detector=MockDetector(True),
            llm_detector=MockDetector(True),
            marker_weight=0.5,
            ml_weight=1.0,
            llm_weight=3.0,
        )
        weights = {d.name: d.weight for d in classifier._detectors}
        assert weights == snapshot({"marker": 0.5, "ml": 1.0, "llm": 3.0})


class TestConfidenceScoring:
    """Test confidence scoring edge cases."""

    def test_confidence_high_agreement_refusal(self):
        classifier = HybridRefusalClassifier()
        classifier.add_detector(MockDetector(True), weight=1.0, name="a")
        classifier.add_detector(MockDetector(True), weight=1.0, name="b")
        classifier.add_detector(MockDetector(True), weight=1.0, name="c")
        result = classifier.classify("test")
        assert result.confidence == snapshot(1.0)
        assert result.is_refusal is True

    def test_confidence_high_agreement_non_refusal(self):
        classifier = HybridRefusalClassifier()
        classifier.add_detector(MockDetector(False), weight=1.0, name="a")
        classifier.add_detector(MockDetector(False), weight=1.0, name="b")
        classifier.add_detector(MockDetector(False), weight=1.0, name="c")
        result = classifier.classify("test")
        assert result.confidence == snapshot(1.0)
        assert result.is_refusal is False

    def test_confidence_moderate_majority_refusal(self):
        classifier = HybridRefusalClassifier()
        classifier.add_detector(MockDetector(True), weight=1.0, name="a")
        classifier.add_detector(MockDetector(True), weight=1.0, name="b")
        classifier.add_detector(MockDetector(False), weight=1.0, name="c")
        result = classifier.classify("test")
        # 2/3 = 0.666 confidence for refusal
        assert round(result.confidence, 2) == snapshot(0.67)
        assert result.is_refusal is True

    def test_confidence_moderate_majority_non_refusal(self):
        classifier = HybridRefusalClassifier()
        classifier.add_detector(MockDetector(False), weight=1.0, name="a")
        classifier.add_detector(MockDetector(False), weight=1.0, name="b")
        classifier.add_detector(MockDetector(True), weight=1.0, name="c")
        result = classifier.classify("test")
        # 2/3 = 0.666 confidence for non-refusal
        assert round(result.confidence, 2) == snapshot(0.67)
        assert result.is_refusal is False
