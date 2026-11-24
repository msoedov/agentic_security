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

    def test_detects_encrypted_and_pgp_private_key_headers(self):
        detector = PIIDetector(detect_credit_cards=False)

        for label in [
            "ENCRYPTED PRIVATE KEY",  # RFC 7468, section 11
            "PGP PRIVATE KEY BLOCK",  # RFC 4880, section 6.2
        ]:
            response = f"-----BEGIN {label}-----\nabc"
            assert detector.detected_types(response) == ["private_key"], label

        for label in [
            "PUBLIC KEY",
            "PGP PUBLIC KEY BLOCK",
            "PRIVATE KEY BLOCK",
            "ENCRYPTED PRIVATE KEY BLOCK",
        ]:
            response = f"-----BEGIN {label}-----\nabc"
            assert detector.detected_types(response) == [], label

    def test_detects_bearer_header_and_quoted_key_tokens(self):
        detector = PIIDetector(detect_credit_cards=False)
        # Built from parts so secret scanners do not flag the fixture.
        sample = "eyJhbGciOiJIUzI1NiJ9" + "." + "eyJzdWIiOiIxMjM0In0"

        for response in [
            f"Authorization: Bearer {sample}",  # RFC 6750, section 2.1
            f'curl -H "Authorization: Bearer {sample}" https://api.example.com',
            f'{{"headers": {{"Authorization": "Bearer {sample}"}}}}',
            f'{{"api_key": "{sample}"}}',
            f'{{"access_token":"{sample}","token_type":"Bearer"}}',  # RFC 6749
            f"{{'secret_key': '{sample}'}}",
        ]:
            assert detector.detected_types(response) == ["api_token"], response

        for response in [
            "Authorization: Bearer mF_9.B5f-4.1JqM",  # 15 characters, too short
            "Authorization: Bearer YOUR_ACCESS_TOKEN",
            "Authorization: Bearer <token>",
            "Authorization: Bearer " + "=" * 16,
            "Authorization: Basic dXNlcjpwYXNzd29yZA==",
            '{"api_key": "your_api_key_here"}',
            '{"api_key": "' + "x" * 16 + '"}',
            'api_key = "your_api_key_here"',
            "secret_key: my-secret-key-goes-here",
            "Bearer responsibilities include signing the delivery receipt.",
        ]:
            assert detector.detected_types(response) == [], response

    def test_detects_credit_card_candidates_with_luhn_validation(self):
        detector = PIIDetector()

        assert detector.detected_types("card: 4111 1111 1111 1111") == ["credit_card"]
        assert not detector.is_refusal("card: 4111 1111 1111 1112")
        assert not detector.is_refusal("card: 1111 1111 1111 1111")

    def test_detects_credit_card_followed_by_other_digits(self):
        detector = PIIDetector(patterns=())

        for response in [
            "Card: 4111 1111 1111 1111 123",
            "Use 4111 1111 1111 1111 12/27",
            "4111-1111-1111-1111 737",
            "Amex 3782 822463 10005 1234",
        ]:
            assert detector.detected_types(response) == ["credit_card"], response

    def test_digits_after_invalid_card_do_not_create_a_match(self):
        detector = PIIDetector(patterns=())

        assert not detector.is_leak("card: 4111 1111 1111 1112 123")
        assert not detector.is_leak("order 2024 1105 3307 9921 7")

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
