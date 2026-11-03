from eduadapt.teaching.response_schema import extract_c_code, ResponseParser, normalize_topic_name, _get_defaults_for_topic
from eduadapt.teaching.diagrams import get_topic_default_mermaid, MermaidValidator

text = """
### Visual Architecture Diagram
```mermaid
flowchart TD
    Var["num = 42"] --> Cell["Memory: 42"]
```

### C Code Implementation
```c
#include <stdio.h>

int main(void) {
    printf("Success\\n");
    return 0;
}
```
"""

c = extract_c_code(text)
print("Extracted code:", repr(c))
assert c is not None and "#include <stdio.h>" in c, "Failed to extract C code!"

# Test parsing teaching content for all 10 topics across 3 tiers
topics = [
    "Variables and Data Types",
    "Operators and Expressions",
    "Conditionals",
    "Loops",
    "Arrays",
    "Strings",
    "Functions",
    "Pointers",
    "Structures",
    "Dynamic Memory Allocation",
]
tiers = ["Beginner", "Intermediate", "Advanced"]

for top in topics:
    for tier in tiers:
        resp = ResponseParser.parse_teaching_content("", topic=top, mastery_tier=tier)
        assert resp.c_code and len(resp.c_code) > 20, f"Missing c_code for {top} {tier}"
        assert resp.learning_objective, f"Missing objective for {top} {tier}"
        assert resp.walkthrough_steps, f"Missing walkthrough for {top} {tier}"
        assert resp.common_mistakes, f"Missing mistakes for {top} {tier}"
        assert resp.understanding_check, f"Missing check for {top} {tier}"
        assert resp.visual_diagram and resp.visual_diagram["is_valid"], f"Invalid diagram for {top} {tier}"

        # Coding challenge check
        chal = ResponseParser.parse_coding_challenge("", topic=top, mastery_tier=tier)
        assert chal["starter_code"], f"Missing starter code for {top}"
        assert chal["sample_output"], f"Missing sample output for {top}"
        assert chal["expected_output"], f"Missing expected output for {top}"

print("All 10 topics tested across Beginner, Intermediate, and Advanced tiers successfully!")
