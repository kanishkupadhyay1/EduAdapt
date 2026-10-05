# PPS Teaching Evaluation Framework: Manual Review Rubric

This rubric establishes explicit criteria for authorized human educators and subject-matter experts to evaluate LLM-generated explanations across five core pedagogical and technical dimensions.

> [!IMPORTANT]
> **Separation of Automated Indicators and Educational Validation**:
> Automated metrics (such as keyword presence, regex checks, and token counts) provide automated indicators of coverage only. They do **not** constitute proof of pedagogical efficacy, technical rigor, or conceptual accuracy. Educational validation is **only complete when an expert human reviewer has evaluated the outputs** using this rubric.

---

## 1. Five Core Evaluation Dimensions

Each dimension is scored on an integer scale from **1 (Unacceptable / Fatal Flaw)** to **5 (Exemplary / Mastery)**.

### Dimension 1: Conceptual Correctness (C Standard Conformance)
Evaluates whether the explanation adheres strictly to the ISO C standard (C99 / C11) and avoids presenting undefined, unspecified, or implementation-defined behavior as universal truth.

| Score | Description | Specific PPS Indicators |
|---|---|---|
| **5 (Exemplary)** | Flawless technical precision. C standards nuances correctly articulated; undefined behavior (UB), implementation-defined behavior, and sequence points accurately framed. | Correctly distinguishes signed overflow (UB) from unsigned modulo wrap-around; explains that bounds checking is absent and out-of-bounds access is UB; clarifies character contiguity guarantees without assuming ASCII. |
| **4 (Proficient)** | Accurate in all core concepts with minor omission of deep standard subtleties that do not mislead the student. | Accurately explains execution and memory rules; may omit explicit reference to ISO clause numbers. |
| **3 (Developing)** | Mostly correct, but contains imprecise terminology or oversimplifications that could foster subsequent confusion. | Describes out-of-bounds access merely as "printing garbage" rather than explaining Undefined Behavior. |
| **2 (Flawed)** | Contains notable conceptual errors or promotes inaccurate mental models of C program execution. | Confuses pointer syntax; misstates condition evaluation timing; or implies that operator precedence determines evaluation order of unsequenced side effects. |
| **1 (Unacceptable)** | Fatal conceptual error. Conflates core language constructs or states false execution rules. | States that a `while (i <= n)` loop "continues until `i` is greater than `n+1`"; claims signed integer overflow wraps safely; or advises using `i = i++`. |

---

### Dimension 2: Code Correctness and Idiomatic Quality
Evaluates the syntactical, semantic, and stylistic validity of the C code examples provided in the explanation.

| Score | Description | Specific PPS Indicators |
|---|---|---|
| **5 (Exemplary)** | Syntactically flawless, standard-conforming (C99/C11), compiles cleanly with `-Wall -Wextra`, memory-safe, and free of undefined behavior. | Clean formatting, correct header includes (`<stdio.h>`), explicit braces, idiomatic variable names, and clear comments. |
| **4 (Proficient)** | Syntactically correct and compilable with no runtime errors; minor stylistic deviations. | Valid C code, but missing a recommended compiler warning flag practice or minor layout inconsistency. |
| **3 (Developing)** | Compiles with warnings or uses outdated idioms (e.g. implicit int, legacy K&R styles) or lacks defensive checks. | Code compiles, but produces compiler warnings (e.g., format specifier mismatch in `printf`). |
| **2 (Flawed)** | Fails to compile due to syntax errors, or exhibits runtime errors (e.g., off-by-one bounds breach). | Missing semicolons, mismatched types, or invalid pointer assignments. |
| **1 (Unacceptable)** | Non-compilable, hallucinates non-existent C syntax (mixing in Python/C++ constructs), or contains dangerous undefined behavior. | Uses C++ references (`int &x`), calls undefined functions, or dereferences uninitialized pointers. |

---

### Dimension 3: Explanation Clarity and Pedagogical Structure
Evaluates how effectively the explanation conveys complex programming concepts to an engineering student.

| Score | Description | Specific PPS Indicators |
|---|---|---|
| **5 (Exemplary)** | Highly structured, lucid, logical progression from concrete to abstract, accompanied by step-by-step traces or memory layout diagrams. | Clear execution trace table showing variable state changes at each step; explains the 'why' behind language rules. |
| **4 (Proficient)** | Clear, coherent, and readable; good logical flow with helpful code explanations. | Easy to follow; minor areas where additional visual tracing would enhance comprehension. |
| **3 (Developing)** | Understandable but verbose, unstructured, or moderately disjointed. | Long paragraphs without bullet points or code walkthrough steps; somewhat difficult for a struggling student to navigate. |
| **2 (Flawed)** | Disorganized, confusing terminology, or contradictory statements. | Explanations leap across topics without connective tissue; contradictory descriptions of control flow. |
| **1 (Unacceptable)** | Incomprehensible, misleading, or excessively jargon-laden without explanatory value. | Gibberish or so disorganized that a novice student will be more confused after reading. |

---

### Dimension 4: Appropriateness for Student Mastery
Evaluates whether the cognitive depth, pacing, and scaffolding are appropriately calibrated to the student's mastery profile.

| Score | Description | Specific PPS Indicators |
|---|---|---|
| **5 (Exemplary)** | Perfectly calibrated to the student's mastery score, performance history, and requested response format. | For a beginner (mastery 0.20): provides patient scaffolding, concrete traces, and foundational analogies. For an advanced student (mastery 0.85): delivers technical rigor, cache locality, and complexity analysis. |
| **4 (Proficient)** | Well-adapted to student level with minor misalignment in pacing or depth. | Tailors examples well; slightly more advanced or elementary than optimal, but very usable. |
| **3 (Developing)** | One-size-fits-all explanation that acknowledges the student level but fails to meaningfully adapt explanation depth. | Mentions student background in passing but delivers the exact same generic lecture text. |
| **2 (Flawed)** | Poorly calibrated: overwhelm a beginner with advanced compiler theory, or bore an advanced student with trivialities. | Beginners given raw memory pointer arithmetic without scaffolding; advanced students given kindergarten analogies. |
| **1 (Unacceptable)** | Completely tone-deaf, condescending, or inaccessible to the target student profile. | Derisive tone or completely inaccessible jargon for novice engineers. |

---

### Dimension 5: Misconception Handling
Evaluates whether the explanation actively identifies, clarifies, and dismantles common student misconceptions without reinforcing them.

| Score | Description | Specific PPS Indicators |
|---|---|---|
| **5 (Exemplary)** | Proactively targets known misconceptions, clearly contrasts the flawed mental model with actual C semantics, and explains why the error occurs. | Explicitly addresses: "Students often believe the update `i++` runs before the loop body. In reality, C executes Init -> Condition -> Body -> Update." |
| **4 (Proficient)** | Correctly highlights the misconception and warns the student against it. | Cautions against the misconception with an example of what to avoid. |
| **3 (Developing)** | Mentions the correct behavior, but does not explicitly contrast it with the misconception. | The correct rule is stated, but the underlying reason why students get confused is left unaddressed. |
| **2 (Flawed)** | Ignores the specified misconceptions entirely, leaving the student prone to repeat the mistake. | Student profile notes confusion between `=` and `==`, but explanation does not mention assignment in conditionals. |
| **1 (Unacceptable)** | Actively introduces, validates, or reinforces a misconception. | Confirms a false mental model or generates the error itself (e.g., claiming while-loop terminates at `n+2`). |

---

## 2. Review Scoring Template

When an authorized human evaluator reviews each item in `data/evaluation_results_mistral7b.json`, they fill out the `manual_review` block:

```json
{
  "benchmark_id": "pps_11",
  "manual_review": {
    "conceptual_correctness": 5,
    "code_correctness": 5,
    "explanation_clarity": 4,
    "appropriateness_for_student_mastery": 5,
    "misconception_handling": 5,
    "reviewer_notes": "Explicitly dismantled the 'continues until i > n+1' error. Excellent trace table.",
    "evaluated_by": "Prof. PPS Reviewer",
    "is_reviewed": true
  }
}
```

---

## 3. Decision Guidelines for Pre-Fine-Tuning Readiness

A model is deemed ready for PPS student deployment or pedagogical fine-tuning only if:
1. **Zero Fatal Regressions**: The while-loop regression detector passes on all loop termination prompts.
2. **Conceptual Correctness >= 4.0 average**: No items score 1 or 2 in Conceptual Correctness.
3. **Code Correctness >= 4.5 average**: Code must be syntactically valid and free of undefined behavior.
4. **Misconception Handling >= 3.5 average**: Explanations must actively counter common student traps.
