from src.member4.verification import ResponseVerifier


def test_response_verification_passes_with_response_and_context():
    verifier = ResponseVerifier()

    result = verifier.verify(
        generated_response="Pointers store memory addresses.",
        source_context="Pointers are variables that store memory addresses.",
    )

    assert result.verified is True
    assert result.grounded is True
    assert result.issues == []


def test_response_verification_rejects_empty_response():
    verifier = ResponseVerifier()

    result = verifier.verify(
        generated_response="",
        source_context="Pointers are variables that store memory addresses.",
    )

    assert result.verified is False
    assert result.grounded is False
    assert "Generated response is empty." in result.issues


def test_response_verification_detects_empty_source_context():
    verifier = ResponseVerifier()

    result = verifier.verify(
        generated_response="Pointers store memory addresses.",
        source_context="",
    )

    assert result.verified is False
    assert result.grounded is False
    assert "Source context is empty." in result.issues