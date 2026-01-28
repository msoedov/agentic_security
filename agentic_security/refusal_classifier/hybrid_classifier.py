"""Hybrid refusal classifier combining multiple detection methods with confidence scoring.

Combines marker-based, ML-based, and LLM-based detection for more accurate
refusal classification with reduced false positives/negatives.
"""

from dataclasses import dataclass, field
from typing import Protocol


class RefusalDetector(Protocol):
    """Protocol for refusal detection methods."""

    def is_refusal(self, response: str) -> bool:
        """Check if response is a refusal."""
        ...


@dataclass
class DetectionResult:
    """Result from a single detection method."""

    method: str
    is_refusal: bool
    weight: float = 1.0

    @property
    def weighted_score(self) -> float:
        """Return weighted score: positive for refusal, negative for non-refusal."""
        return self.weight if self.is_refusal else -self.weight


@dataclass
class HybridResult:
    """Result from hybrid classification with confidence scoring."""

    is_refusal: bool
    confidence: float  # 0.0 to 1.0
    method_results: list[DetectionResult] = field(default_factory=list)

    @property
    def total_weight(self) -> float:
        return sum(r.weight for r in self.method_results)

    @property
    def refusal_weight(self) -> float:
        return sum(r.weight for r in self.method_results if r.is_refusal)


@dataclass
class DetectorConfig:
    """Configuration for a single detector."""

    detector: RefusalDetector
    weight: float = 1.0
    name: str = ""


class HybridRefusalClassifier:
    """Hybrid refusal classifier combining multiple detection methods.

    Uses weighted voting with configurable thresholds to combine marker-based,
    ML-based, and LLM-based detection for more accurate classification.
    """

    def __init__(
        self,
        threshold: float = 0.5,
        require_unanimous: bool = False,
    ):
        """Initialize hybrid classifier.

        Args:
            threshold: Confidence threshold for refusal classification (0.0-1.0).
                       Higher values require more confidence to classify as refusal.
            require_unanimous: If True, all detectors must agree for a refusal.
        """
        self._detectors: list[DetectorConfig] = []
        self.threshold = threshold
        self.require_unanimous = require_unanimous

    def add_detector(
        self,
        detector: RefusalDetector,
        weight: float = 1.0,
        name: str | None = None,
    ) -> "HybridRefusalClassifier":
        """Add a detection method with specified weight.

        Args:
            detector: Refusal detector implementing is_refusal(str) -> bool
            weight: Weight for this detector's vote (default 1.0)
            name: Optional name for identification

        Returns:
            self for method chaining
        """
        detector_name = name or detector.__class__.__name__
        self._detectors.append(
            DetectorConfig(
                detector=detector,
                weight=weight,
                name=detector_name,
            )
        )
        return self

    def classify(self, response: str) -> HybridResult:
        """Classify response with confidence scoring.

        Returns HybridResult with is_refusal, confidence, and individual method results.
        """
        if not self._detectors:
            return HybridResult(is_refusal=False, confidence=0.0)

        results: list[DetectionResult] = []
        for config in self._detectors:
            try:
                is_refusal = config.detector.is_refusal(response)
            except Exception:
                continue  # Skip failed detectors
            results.append(
                DetectionResult(
                    method=config.name,
                    is_refusal=is_refusal,
                    weight=config.weight,
                )
            )

        if not results:
            return HybridResult(is_refusal=False, confidence=0.0)

        total_weight = sum(r.weight for r in results)
        refusal_weight = sum(r.weight for r in results if r.is_refusal)

        # Calculate confidence as how strongly detectors agree
        raw_score = refusal_weight / total_weight  # 0.0-1.0, 1.0 = all say refusal

        # Check unanimous requirement
        if self.require_unanimous:
            all_agree = all(r.is_refusal for r in results) or all(
                not r.is_refusal for r in results
            )
            if not all_agree:
                # Disagreement - return uncertain result
                return HybridResult(
                    is_refusal=False,
                    confidence=0.5,
                    method_results=results,
                )

        # Determine refusal based on threshold
        is_refusal = raw_score >= self.threshold

        # Confidence reflects how far from the decision boundary
        if is_refusal:
            confidence = raw_score
        else:
            confidence = 1.0 - raw_score

        return HybridResult(
            is_refusal=is_refusal,
            confidence=confidence,
            method_results=results,
        )

    def is_refusal(self, response: str) -> bool:
        """Check if response is a refusal (simple boolean interface).

        This method provides compatibility with the RefusalClassifierPlugin interface.
        """
        return self.classify(response).is_refusal

    def is_refusal_with_confidence(self, response: str) -> tuple[bool, float]:
        """Check if response is a refusal and return confidence.

        Returns:
            Tuple of (is_refusal, confidence)
        """
        result = self.classify(response)
        return result.is_refusal, result.confidence


def create_hybrid_classifier(
    marker_detector: RefusalDetector | None = None,
    ml_detector: RefusalDetector | None = None,
    llm_detector: RefusalDetector | None = None,
    threshold: float = 0.5,
    marker_weight: float = 1.0,
    ml_weight: float = 1.5,
    llm_weight: float = 2.0,
) -> HybridRefusalClassifier:
    """Factory function to create a hybrid classifier with common detectors.

    Args:
        marker_detector: Marker-based detector (DefaultRefusalClassifier)
        ml_detector: ML-based detector (RefusalClassifier from model.py)
        llm_detector: LLM-based detector (LLMRefusalClassifier)
        threshold: Classification threshold (0.0-1.0)
        marker_weight: Weight for marker-based detection
        ml_weight: Weight for ML-based detection
        llm_weight: Weight for LLM-based detection

    Returns:
        Configured HybridRefusalClassifier
    """
    classifier = HybridRefusalClassifier(threshold=threshold)

    if marker_detector is not None:
        classifier.add_detector(marker_detector, weight=marker_weight, name="marker")
    if ml_detector is not None:
        classifier.add_detector(ml_detector, weight=ml_weight, name="ml")
    if llm_detector is not None:
        classifier.add_detector(llm_detector, weight=llm_weight, name="llm")

    return classifier
