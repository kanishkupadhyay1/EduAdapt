import sys
import json
import requests

BASE_URL = "http://127.0.0.1:8000"

def log_pass(msg):
    print(f" [PASS] {msg}")

def log_fail(msg):
    print(f" [FAIL] {msg}")
    sys.exit(1)

print("\n=======================================================")
print(" EDUADAPT COMPREHENSIVE END-TO-END VERIFICATION AUDIT ")
print("=======================================================\n")

# 1. Health Check
try:
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert data.get("status") in ["ok", "healthy"], f"Unexpected status: {data.get('status')}"
    log_pass(f"Backend Health: OK (status={data.get('status')}, service={data.get('service')})")
except Exception as e:
    import traceback
    traceback.print_exc()
    log_fail(f"Backend Health Failed: {e}")

# 2. Curriculum Topics
try:
    r = requests.get(f"{BASE_URL}/api/curriculum/topics", timeout=5)
    assert r.status_code == 200
    topics = r.json().get("topics", [])
    expected_topics = [
        "Variables and Data Types",
        "Operators and Expressions",
        "Conditionals",
        "Loops",
        "Arrays",
        "Strings",
        "Functions",
        "Pointers",
        "Structures",
        "Dynamic Memory Allocation"
    ]
    norm_topics = [t.lower() for t in topics]
    for exp in expected_topics:
        assert exp.lower() in norm_topics, f"Topic '{exp}' missing from curriculum!"
    log_pass(f"PPS Curriculum Topics: All {len(topics)} topics present and verified.")
except Exception as e:
    log_fail(f"Curriculum Topics Failed: {e}")

# 3. Student Profile Differentiation (S001 vs S005)
try:
    r_s001 = requests.get(f"{BASE_URL}/api/student/S001", timeout=5)
    r_s005 = requests.get(f"{BASE_URL}/api/student/S005", timeout=5)
    assert r_s001.status_code == 200 and r_s005.status_code == 200
    s1 = r_s001.json()
    s5 = r_s005.json()
    assert s1["mastery"] != s5["mastery"], "S001 and S005 should have distinct mastery levels"
    log_pass(f"Student Profiles: S001 (Mastery={s1['mastery']}, Level={s1.get('predicted_mastery_level')}) vs S005 (Mastery={s5['mastery']}, Level={s5.get('predicted_mastery_level')})")
except Exception as e:
    log_fail(f"Student Profiles Failed: {e}")

# 4. AI Coding Challenge Generation Across Topics
topics_to_test = ["Dynamic Memory Allocation", "Strings"]
for t in topics_to_test:
    try:
        r = requests.post(f"{BASE_URL}/api/practice/generate", json={"student_id": "S001", "topic": t}, timeout=60)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        ch = data.get("challenge") or (data.get("practice_problems", [{}])[0])
        assert ch.get("title"), f"Missing title for {t}"
        assert ch.get("starter_code"), f"Missing starter code for {t}"
        assert ch.get("sample_input") is not None, f"Missing sample input for {t}"
        assert ch.get("sample_output"), f"Missing sample output for {t}"
        assert len(ch.get("hints", [])) >= 3, f"Expected hint ladder (>=3 hints) for {t}"
        log_pass(f"Practice Challenge [{t}]: '{ch.get('title')}' (Hints={len(ch.get('hints'))}, Sample Input='{ch.get('sample_input').strip()}')")
    except Exception as e:
        import traceback
        traceback.print_exc()
        log_fail(f"Challenge generation failed for {t}: {e}")

# 5. C Code Execution Engine & Sandbox
dma_code = """#include <stdio.h>
#include <stdlib.h>

int main() {
    int n;
    if (scanf("%d", &n) != 1 || n <= 0) return 1;
    int *arr = (int *)malloc(n * sizeof(int));
    if (arr == NULL) return 1;
    for (int i = 0; i < n; i++) scanf("%d", &arr[i]);
    for (int i = 0; i < n; i++) {
        printf("%d", arr[i]);
        if (i < n - 1) printf(" ");
    }
    printf("\\n");
    free(arr);
    return 0;
}
"""

# 5.1 Run Code with Custom Stdin
try:
    r = requests.post(f"{BASE_URL}/api/practice/execute", json={
        "student_id": "S001",
        "topic": "Dynamic Memory Allocation",
        "source_code": dma_code,
        "stdin_input": "5\n10 20 30 40 50",
        "is_submission": False
    }, timeout=10)
    assert r.status_code == 200
    res = r.json()
    assert res.get("status") == "SUCCESS", f"Expected SUCCESS, got {res.get('status')}: {res}"
    assert res.get("exit_code") == 0, f"Expected 0, got {res.get('exit_code')}"
    assert "10 20 30 40 50" in res.get("stdout", ""), f"Unexpected stdout: {res.get('stdout')}"
    log_pass("C Sandbox Execution: Custom stdin piped correctly, output='10 20 30 40 50', exit_code=0")
except Exception as e:
    import traceback
    traceback.print_exc()
    log_fail(f"C Run Code with Stdin Failed: {e}")

# 5.2 Submit Code Evaluation (Accepted)
try:
    r = requests.post(f"{BASE_URL}/api/practice/execute", json={
        "student_id": "S001",
        "topic": "Dynamic Memory Allocation",
        "source_code": dma_code,
        "stdin_input": "5\n10 20 30 40 50",
        "expected_output": "10 20 30 40 50",
        "is_submission": True
    }, timeout=10)
    assert r.status_code == 200
    res = r.json()
    assert res.get("status") == "ACCEPTED", f"Expected ACCEPTED, got {res.get('status')}: {res}"
    assert res.get("passed") is True
    assert res.get("updated_student") is not None
    log_pass("C Code Submission (Correct): Status=ACCEPTED, passed=True, Learning Twin state synchronized.")
except Exception as e:
    import traceback
    traceback.print_exc()
    log_fail(f"C Code Submission Failed: {e}")

# 5.3 Submit Code Evaluation (Wrong Answer)
try:
    r = requests.post(f"{BASE_URL}/api/practice/execute", json={
        "student_id": "S001",
        "topic": "Dynamic Memory Allocation",
        "source_code": dma_code,
        "stdin_input": "5\n10 20 30 40 50",
        "expected_output": "99 99 99",
        "is_submission": True
    }, timeout=10)
    assert r.status_code == 200
    res = r.json()
    assert res.get("status") == "WRONG_ANSWER"
    assert res.get("passed") is False
    log_pass("C Code Submission (Mismatch): Status=WRONG_ANSWER, passed=False.")
except Exception as e:
    import traceback
    traceback.print_exc()
    log_fail(f"C Code Mismatch Failed: {e}")

# 5.4 Compilation Error Diagnostics
bad_syntax_code = "int main() { syntax error; }"
try:
    r = requests.post(f"{BASE_URL}/api/practice/execute", json={
        "student_id": "S001",
        "topic": "Dynamic Memory Allocation",
        "source_code": bad_syntax_code,
        "is_submission": False
    }, timeout=10)
    assert r.status_code == 200
    res = r.json()
    assert res.get("status") == "COMPILATION_ERROR", f"Expected COMPILATION_ERROR, got {res.get('status')}"
    diag = res.get("compiler_output") or res.get("stderr") or ""
    assert len(diag) > 0, "Compiler diagnostics must not be empty"
    diag_line = diag.strip().splitlines()[-1] if diag.strip().splitlines() else diag
    log_pass(f"C Compiler Error Diagnostics: Status=COMPILATION_ERROR, captured diagnostic='{diag_line}'")
except Exception as e:
    import traceback
    traceback.print_exc()
    log_fail(f"Compilation Error Diagnostics Failed: {e}")
    log_fail(f"Compilation Error Diagnostics Failed: {e}")

# 6. Learning Session & Content Integrity
try:
    r = requests.post(f"{BASE_URL}/api/session/generate", json={
        "student_id": "S001",
        "topic": "Dynamic Memory Allocation",
        "top_k": 3
    }, timeout=120)
    assert r.status_code == 200
    data = r.json()
    teaching = data.get("teaching", {})
    struct = teaching.get("structured_response", {})
    
    # Check learning objective
    assert struct.get("learning_objective"), "Learning objective must not be empty"
    # Check C code
    c_code = struct.get("c_code", "")
    assert c_code and ("malloc" in c_code or "free" in c_code or "sizeof" in c_code), f"Expected C code with DMA, got: {c_code[:80]}"
    # Check code walkthrough
    walkthrough = struct.get("code_walkthrough") or struct.get("walkthrough_steps", [])
    assert len(walkthrough) > 0, "Code walkthrough must not be empty"
    # Check Mermaid diagram
    diag_obj = teaching.get("diagram") or struct.get("diagram") or {}
    diagram_code = diag_obj.get("mermaid_code", "") if isinstance(diag_obj, dict) else str(diag_obj)
    assert diagram_code.strip().startswith("flowchart") or diagram_code.strip().startswith("graph"), f"Invalid diagram header: {diagram_code[:40]}"
    assert "syntax error" not in diagram_code.lower()
    # Check pedagogical rationale
    p_applied = teaching.get("personalization_applied", {}) or struct.get("personalization_applied", {})
    assert p_applied.get("instructional_strategy"), "Instructional strategy must be present"
    assert p_applied.get("rationale"), "Pedagogical rationale must be present"

    log_pass("Learning Session Content Integrity:")
    print(f"       * Objective: {struct.get('learning_objective')}")
    print(f"       * C Code extracted: {len(c_code)} chars (starts with {c_code.splitlines()[0]})")
    print(f"       * Walkthrough: {len(walkthrough)} line annotations")
    print(f"       * Diagram: {diagram_code.splitlines()[0]} ({len(diagram_code.splitlines())} lines)")
    print(f"       * Strategy: {p_applied.get('instructional_strategy')}")
    print(f"       * Rationale: {p_applied.get('rationale')}")
except Exception as e:
    log_fail(f"Learning Session Content Check Failed: {e}")

print("\n=======================================================")
print(" ALL AUDIT CHECKS PASSED: SYSTEM 100% HEALTHY & ACCURATE")
print("=======================================================\n")
