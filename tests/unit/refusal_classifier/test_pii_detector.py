import re

from agentic_security.refusal_classifier.pii_detector import PIIDetector, PIIPattern


class TestPIIDetector:
    def test_detects_common_pii_and_secret_types(self):
        detector = PIIDetector()

        cases = [
            ("Contact me at jane@example.com", ["email"]),
            ("The customer SSN is 123-45-6789", ["us_ssn"]),
            ("Call +1 (415) 555-2671", ["phone_number"]),
            ("api_key = sk_test_1234567890abcdef", ["api_token"]),
            ("-----BEGIN PRIVATE KEY-----\nabc", ["private_key"]),
        ]

        for response, expected in cases:
            assert detector.detected_types(response) == expected
            assert detector.is_refusal(response)

    def test_detects_credit_card_candidates_with_luhn_validation(self):
        detector = PIIDetector()

        assert detector.detected_types("card: 4111 1111 1111 1111") == ["credit_card"]
        assert not detector.is_refusal("card: 4111 1111 1111 1112")
        assert not detector.is_refusal("card: 1111 1111 1111 1111")

    def test_empty_patterns_are_preserved(self):
        detector = PIIDetector(patterns=())

        assert detector.patterns == ()
        assert detector.detected_types("Contact me at jane@example.com") == []
        assert detector.detected_types("card: 4111 1111 1111 1111") == ["credit_card"]

    def test_credit_card_detection_can_be_disabled(self):
        detector = PIIDetector(patterns=(), detect_credit_cards=False)

        assert detector.detected_types("card: 4111 1111 1111 1111") == []
        assert not detector.is_leak("card: 4111 1111 1111 1111")

    def test_custom_patterns_can_be_used(self):
        detector = PIIDetector(
            patterns=(PIIPattern("employee_id", re.compile(r"EMP-\d{4}")),)
        )

        assert detector.detected_types("employee EMP-1234") == ["employee_id"]
        assert detector.detected_types("Contact me at jane@example.com") == []
