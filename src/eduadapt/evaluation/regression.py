"""Targeted regression detector for the known while-loop termination explanation error.

Context:
In Scenario 4 of previous inference, Mistral 7B produced the following flawed explanation:
"The loop continues until `i` is greater than `n+1`, which ensures that every natural number up to `n` is included in the sum calculation."

Under ISO C, for `while (i <= n)`:
- The loop terminates as soon as `i` reaches `n + 1`, because `(n + 1) <= n` evaluates to false.
- The loop NEVER "continues until i is greater than n+1" (which would erroneously execute the loop body for i = n+1).

This module implements a targeted detector to verify whether an explanation contains
this specific error pattern and whether it states the correct termination condition.
"""

import re
from typing import Optional
from eduadapt.evaluation.models import WhileLoopRegressionCheck

# Patterns indicating the erroneous claim that loop continues until i > n+1
ERRONEOUS_PATTERNS = [
    r"continues\s+until\s+[`'\"]?i[`'\"]?\s+is\s+greater\s+than\s+[`'\"]?n\s*\+\s*1[`'\"]?",
    r"continues\s+until\s+[`'\"]?i[`'\"]?\s*>\s*[`'\"]?n\s*\+\s*1[`'\"]?",
    r"continues\s+until\s+[`'\"]?i[`'\"]?\s+exceeds\s+[`'\"]?n\s*\+\s*1[`'\"]?",
    r"until\s+[`'\"]?i[`'\"]?\s+is\s+greater\s+than\s+[`'\"]?n\s*\+\s*1[`'\"]?",
    r"loop\s+runs\s+until\s+[`'\"]?i[`'\"]?\s+is\s+greater\s+than\s+[`'\"]?n\s*\+\s*1[`'\"]?",
]

# Patterns indicating a correct explanation of termination when i reaches n+1 / i <= n becomes false
CORRECT_TERMINATION_PATTERNS = [
    r"terminates?\s+(?:when|once|as\s+soon\s+as)\s+[`'\"]?i[`'\"]?\s+(?:reaches|becomes|equals|=)\s+[`'\"]?n\s*\+\s*1[`'\"]?",
    r"stops?\s+(?:when|once)\s+[`'\"]?i[`'\"]?\s+(?:reaches|becomes|equals|=)\s+[`'\"]?n\s*\+\s*1[`'\"]?",
    r"[`'\"]?i\s*<=\s*n[`'\"]?\s+becomes\s+false",
    r"[`'\"]?i\s*<=\s*n[`'\"]?\s+evaluates\s+to\s+false",
    r"condition\s+[`'\"]?i\s*<=\s*n[`'\"]?\s+is\s+false",
    r"[`'\"]?i[`'\"]?\s+reaches\s+[`'\"]?n\s*\+\s*1[`'\"]?[^.]*?condition[^.]*?false",
]


def check_while_loop_explanation(text: str) -> WhileLoopRegressionCheck:
    """Analyze text for the while-loop termination condition regression.

    Args:
        text: The generated pedagogical explanation.

    Returns:
        WhileLoopRegressionCheck with boolean pass status and explanation.
    """
    if not text:
        return WhileLoopRegressionCheck(
            checked=False,
            passed=True,
            explanation="Empty text provided; skipped regression check.",
        )

    # 1. Search for known erroneous patterns
    for pattern in ERRONEOUS_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            matched_phrase = match.group(0)
            return WhileLoopRegressionCheck(
                checked=True,
                passed=False,
                detected_error_phrase=matched_phrase,
                explanation=(
                    f"Regression detected! Flawed explanation phrase found: '{matched_phrase}'. "
                    "For 'while (i <= n)', the loop condition fails when i = n+1; "
                    "it does NOT continue until i is greater than n+1."
                ),
            )

    # 2. Check if text mentions while loop termination with n+1
    has_termination_mention = bool(
        re.search(r"while\s*\(\s*i\s*<=\s*n\s*\)", text, re.IGNORECASE)
        or re.search(r"sum\s+of\s+(?:the\s+)?first\s+n", text, re.IGNORECASE)
    )

    if has_termination_mention:
        # Check if correct termination rationale is present
        has_correct = any(
            re.search(p, text, re.IGNORECASE) for p in CORRECT_TERMINATION_PATTERNS
        )
        if has_correct:
            return WhileLoopRegressionCheck(
                checked=True,
                passed=True,
                detected_error_phrase=None,
                explanation="Passed: Correctly explains that the loop terminates when i reaches n+1 because i <= n evaluates to false.",
            )

    # If no erroneous pattern is present
    return WhileLoopRegressionCheck(
        checked=True,
        passed=True,
        detected_error_phrase=None,
        explanation="Passed: No erroneous while-loop termination patterns detected.",
    )
