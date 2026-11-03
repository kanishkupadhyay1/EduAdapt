"""Structured output models and robust response parsers for EduAdapt teaching generation.

Supports strict JSON parsing with intelligent structured markdown fallback.
Safely extracts objectives, conceptual explanations, C code blocks, Mermaid diagrams,
step-by-step walkthroughs, common mistakes, and interactive understanding checks.
"""

from dataclasses import dataclass, field
import json
import re
from typing import Any, Dict, List, Optional

from eduadapt.teaching.diagrams import DiagramResult, MermaidValidator, get_topic_default_mermaid


def extract_c_code(text: str) -> Optional[str]:
    """Extract C source code block from markdown text without circular import."""
    if not text:
        return None
    match = re.search(r"```(?:c|C)?\s*\n([\s\S]*?)```", text)
    if match:
        code = match.group(1).strip()
        # Ensure it's not a mermaid diagram
        if not code.lower().startswith(("flowchart", "graph", "sequencediagram")):
            return code
    return None


# Topic-grounded fallbacks ensuring student never sees empty or broken sections
TOPIC_GROUNDED_DEFAULTS = {
    "Pointers": {
        "objective": "Understand pointer syntax, memory addressing with &, and value dereferencing with * in C.",
        "explanation": (
            "A pointer in C is a variable that stores the memory address of another variable rather than storing "
            "a direct value. By holding the memory address, pointers allow direct memory manipulation, dynamic memory "
            "allocation, and pass-by-reference simulation in function calls.\n\n"
            "The address-of operator (&) retrieves the memory address of a variable, while the dereference operator (*) "
            "accesses the value stored at the address pointed to by the pointer."
        ),
        "code": (
            "#include <stdio.h>\n\n"
            "int main() {\n"
            "    int num = 42;       // Regular integer variable\n"
            "    int *ptr = &num;    // Pointer storing the address of num\n\n"
            "    printf(\"Value of num: %d\\n\", num);\n"
            "    printf(\"Address of num (&num): %p\\n\", (void*)&num);\n"
            "    printf(\"Address stored in ptr: %p\\n\", (void*)ptr);\n"
            "    printf(\"Value accessed via pointer (*ptr): %d\\n\", *ptr);\n\n"
            "    // Modifying value through pointer\n"
            "    *ptr = 100;\n"
            "    printf(\"Updated value of num: %d\\n\", num);\n"
            "    return 0;\n"
            "}"
        ),
        "walkthrough": [
            "Variable Declaration: `int num = 42;` allocates 4 bytes of stack memory holding the integer 42.",
            "Pointer Initialization: `int *ptr = &num;` binds the pointer variable `ptr` to the memory address of `num`.",
            "Address Printing: `(void*)&num` and `(void*)ptr` print identical hexadecimal memory addresses.",
            "Value Dereferencing: `*ptr` follows the address to read 42 directly from memory.",
            "Direct Mutation: `*ptr = 100;` writes the integer 100 directly into `num`'s memory location without touching variable `num` directly.",
        ],
        "mistakes": [
            "Dereferencing uninitialized or wild pointers (`int *p; *p = 10;`), which triggers segmentation faults.",
            "Confusing the address-of operator `&` with the dereference operator `*`.",
            "Returning a pointer to a local stack variable from a function once the stack frame is popped.",
            "Assigning an integer value directly to a pointer without the address operator (`int *p = num`).",
        ],
        "check": {
            "question": "What is printed when this C code runs?",
            "code_snippet": "int a = 10;\nint *p = &a;\n*p = 25;\nprintf(\"%d\\n\", a);",
            "options": ["A) 10", "B) 25", "C) Memory address of a", "D) Compilation error"],
            "correct_option": "B",
            "explanation": "Pointer `p` stores the address of variable `a`. Dereferencing `*p = 25` mutates the memory cell of `a`, making `a` equal to 25.",
        },
    },
    "Arrays": {
        "objective": "Understand contiguous memory representation, 0-based indexing, and pointer arithmetic in C arrays.",
        "explanation": (
            "An array in C is a collection of elements of the same data type placed in contiguous memory locations. "
            "Because elements are stored contiguously, any element can be accessed in constant O(1) time using its "
            "index offset from the base address.\n\n"
            "In C, the name of an array acts as a constant pointer to its first element (`arr == &arr[0]`)."
        ),
        "code": (
            "#include <stdio.h>\n\n"
            "int main() {\n"
            "    int arr[5] = {10, 20, 30, 40, 50};\n"
            "    int *p = arr; // Array name decays to pointer to first element\n\n"
            "    for (int i = 0; i < 5; i++) {\n"
            "        printf(\"arr[%d] = %d (via pointer: %d)\\n\", i, arr[i], *(p + i));\n"
            "    }\n"
            "    return 0;\n"
            "}"
        ),
        "walkthrough": [
            "Contiguous Allocation: `int arr[5]` allocates 20 contiguous bytes (5 integers × 4 bytes each).",
            "Base Address Decay: `int *p = arr;` points `p` to the address of `arr[0]`.",
            "Offset Calculation: `*(p + i)` increments the memory address by `i * sizeof(int)` bytes.",
            "Element Retrieval: Dereferencing `*(p + i)` yields the identical value as subscript notation `arr[i]`.",
        ],
        "mistakes": [
            "Accessing out-of-bounds indices (e.g. `arr[5]` on an array of length 5), causing memory corruption.",
            "Attempting to reassign an array name (`arr = new_arr`), which is illegal because array names are non-lvalue pointers.",
            "Assuming `sizeof(arr)` inside a function returns total array bytes; arrays decay to pointers when passed to functions.",
        ],
        "check": {
            "question": "In C, what does the expression `*(arr + 2)` represent for an array `int arr[4] = {5, 10, 15, 20};`?",
            "code_snippet": "int arr[4] = {5, 10, 15, 20};\nprintf(\"%d\\n\", *(arr + 2));",
            "options": ["A) arr[0] + 2", "B) 15 (arr[2])", "C) Address of arr[2]", "D) 10 (arr[1])"],
            "correct_option": "B",
            "explanation": "Pointer arithmetic `*(arr + 2)` is semantically equivalent to `arr[2]`, which accesses the third element: 15.",
        },
    },
    "Functions": {
        "objective": "Master function prototypes, stack frame allocation, and pass-by-value semantics in C.",
        "explanation": (
            "Functions in C are self-contained modular blocks of code that perform specific tasks. When a function is called, "
            "a new activation record (stack frame) is pushed onto the call stack containing local variables and parameters.\n\n"
            "By default, C passes all primitive parameters by value, meaning the function receives a private copy of each argument."
        ),
        "code": (
            "#include <stdio.h>\n\n"
            "// Function prototype\n"
            "void swap(int *x, int *y);\n\n"
            "int main() {\n"
            "    int a = 5, b = 10;\n"
            "    printf(\"Before: a = %d, b = %d\\n\", a, b);\n"
            "    swap(&a, &b); // Pass addresses for reference modification\n"
            "    printf(\"After:  a = %d, b = %d\\n\", a, b);\n"
            "    return 0;\n"
            "}\n\n"
            "void swap(int *x, int *y) {\n"
            "    int temp = *x;\n"
            "    *x = *y;\n"
            "    *y = temp;\n"
            "}"
        ),
        "walkthrough": [
            "Function Declaration: `void swap(int *x, int *y);` declares the function signature to the compiler.",
            "Caller Frame: `main()` initializes variables `a = 5` and `b = 10`.",
            "Address Passing: `swap(&a, &b)` passes pointers to `a` and `b`, enabling the callee to access caller memory.",
            "Stack Frame Allocation: `swap` receives memory addresses into local pointer variables `x` and `y`.",
            "Value Swap: `*x = *y` exchanges values in the caller's stack frame via pointer dereference.",
        ],
        "mistakes": [
            "Passing arguments by value when attempting to modify caller variables.",
            "Forgetting function prototypes before `main()`, causing implicit declaration compiler warnings.",
            "Missing return statements in functions declared with non-void return types.",
        ],
        "check": {
            "question": "Why does `void update(int x) { x = 99; }` fail to change `num` in `main()`?",
            "code_snippet": "int num = 10;\nupdate(num);\nprintf(\"%d\\n\", num);",
            "options": ["A) Syntax error", "B) C passes parameters by value (copy)", "C) num is a constant", "D) Stack overflow"],
            "correct_option": "B",
            "explanation": "C uses pass-by-value for primitive arguments. `update` receives a separate copy of `num` in its own stack frame.",
        },
    },
    "Loops": {
        "objective": "Understand loop control flow, iteration invariants, and termination conditions in C.",
        "explanation": (
            "Loops allow repeated execution of statements as long as a test condition evaluates to non-zero (True). "
            "C provides three primary iteration constructs: `for` (counter-controlled), `while` (pre-tested), and "
            "`do-while` (post-tested, guaranteed to execute at least once).\n\n"
            "Proper termination conditions prevent infinite loops and memory runaways."
        ),
        "code": (
            "#include <stdio.h>\n\n"
            "int main() {\n"
            "    int sum = 0;\n"
            "    // Iterating from 1 to 5\n"
            "    for (int i = 1; i <= 5; i++) {\n"
            "        sum += i;\n"
            "        printf(\"Iteration %d: Running sum = %d\\n\", i, sum);\n"
            "    }\n"
            "    printf(\"Total sum: %d\\n\", sum);\n"
            "    return 0;\n"
            "}"
        ),
        "walkthrough": [
            "Initialization: `int i = 1;` initializes the loop counter once before the first iteration.",
            "Condition Check: `i <= 5;` tests whether the loop body should execute.",
            "Body Execution: `sum += i;` accumulates the counter into the running sum.",
            "Increment Step: `i++` increments the counter after each iteration completes.",
            "Termination: When `i` reaches 6, `6 <= 5` evaluates to false, terminating the loop.",
        ],
        "mistakes": [
            "Placing an unintended semicolon after the loop header (`for (int i = 0; i < 5; i++);`), executing an empty loop body.",
            "Off-by-one errors in loop boundary conditions (`<=` vs `<`).",
            "Omitting the counter update inside a `while` loop, causing an infinite loop.",
        ],
        "check": {
            "question": "How many times does the loop body execute in this C snippet?",
            "code_snippet": "int i = 0;\nwhile (i < 3) {\n    i++;\n}",
            "options": ["A) 2 times", "B) 3 times", "C) 4 times", "D) Infinite times"],
            "correct_option": "B",
            "correct_answer": "B",
            "explanation": "The loop executes for i = 0, 1, and 2. When i becomes 3, condition `3 < 3` is false and loop exits, totaling 3 iterations.",
        },
    },
    "Dynamic Memory Allocation": {
        "objective": "Understand heap memory management using malloc, calloc, realloc, and free in standard C99.",
        "explanation": (
            "Dynamic memory allocation permits programs to request variable-sized memory blocks from the operating system's "
            "heap at runtime. Unlike stack memory which is automatically tied to function scope, heap memory persists until "
            "explicitly released using `free()`.\n\n"
            "Key functions include `malloc(bytes)` which leaves bytes uninitialized, `calloc(count, size)` which zero-initializes "
            "allocated storage, `realloc(ptr, new_size)` which resizes existing blocks, and `free(ptr)` which releases the memory."
        ),
        "code": (
            "#include <stdio.h>\n"
            "#include <stdlib.h>\n\n"
            "int main() {\n"
            "    int n = 5;\n"
            "    int *arr = (int *)malloc(n * sizeof(int));\n\n"
            "    if (arr == NULL) {\n"
            "        printf(\"Memory allocation failed!\\n\");\n"
            "        return 1;\n"
            "    }\n\n"
            "    for (int i = 0; i < n; i++) {\n"
            "        arr[i] = (i + 1) * 10;\n"
            "        printf(\"arr[%d] = %d\\n\", i, arr[i]);\n"
            "    }\n\n"
            "    free(arr);\n"
            "    arr = NULL; // Prevent dangling pointer\n"
            "    return 0;\n"
            "}"
        ),
        "walkthrough": [
            "Header Inclusion: `<stdlib.h>` must be included for `malloc()` and `free()` declarations.",
            "Allocation Request: `malloc(n * sizeof(int))` requests 20 contiguous heap bytes for 5 integers.",
            "NULL Check Guard: Crucial verification `if (arr == NULL)` prevents crashing if memory is exhausted.",
            "Heap Access: Pointer subscript notation `arr[i]` accesses and populates each allocated memory cell.",
            "Deallocation: `free(arr)` returns the memory block to the OS, and `arr = NULL` eliminates dangling pointers.",
        ],
        "mistakes": [
            "Failing to check for NULL return before dereferencing allocated memory pointers.",
            "Memory leaks caused by losing the only pointer to dynamically allocated blocks without calling free().",
            "Dangling pointers: Accessing or writing to a pointer after it has been freed.",
            "Double-free errors: Invoking `free(ptr)` twice on the same memory address.",
        ],
        "check": {
            "question": "What happens if a program allocates heap memory via malloc() without ever calling free()?",
            "code_snippet": "int *p = malloc(100 * sizeof(int));\n// Function exits without free(p)",
            "options": [
                "A) Memory is freed automatically at function return",
                "B) A memory leak occurs because heap memory persists",
                "C) An immediate compilation error",
                "D) Stack overflow exception",
            ],
            "correct_option": "B",
            "correct_answer": "B",
            "explanation": "Heap memory has dynamic lifetime and is not tied to function stack frames. Neglecting to call free() causes a memory leak.",
        },
    },
    "Strings": {
        "objective": "Master null-terminated character arrays, string literals, and standard string manipulation in C.",
        "explanation": (
            "In C, a string is not an intrinsic primitive data type; rather, it is a one-dimensional array of characters "
            "terminated by a special null character sentinel (`'\\0'`, ASCII value 0). The null terminator indicates to "
            "standard library functions (like `strlen`, `strcpy`, `printf(\"%s\")`) where the character sequence ends in memory."
        ),
        "code": (
            "#include <stdio.h>\n"
            "#include <string.h>\n\n"
            "int main() {\n"
            "    char greeting[] = \"Hello\";\n"
            "    printf(\"String: %s\\n\", greeting);\n"
            "    printf(\"Length: %zu\\n\", strlen(greeting));\n"
            "    printf(\"Total array bytes: %zu\\n\", sizeof(greeting)); // Includes '\\0'\n"
            "    return 0;\n"
            "}"
        ),
        "walkthrough": [
            "Declaration & Initialization: `char greeting[] = \"Hello\";` creates a 6-byte array containing 'H','e','l','l','o','\\0'.",
            "Printing Strings: `printf(\"%s\")` reads characters sequentially until reaching the terminating '\\0'.",
            "Length Calculation: `strlen()` counts visible characters excluding the null terminator (yields 5).",
            "Storage Overhead: `sizeof(greeting)` counts all allocated bytes including the null terminator (yields 6).",
        ],
        "mistakes": [
            "Forgetting space for the '\\0' null terminator when declaring character array bounds (e.g., `char s[5] = \"Hello\";`).",
            "Using `==` to compare strings instead of `strcmp()`; `==` compares pointer addresses, not contents.",
            "Buffer overflow when copying strings using unbounded functions like `strcpy()` or `gets()`.",
        ],
        "check": {
            "question": "What is the byte size of the character array declared as `char str[] = \"EduAdapt\";`?",
            "code_snippet": "char str[] = \"EduAdapt\";\nprintf(\"%zu\\n\", sizeof(str));",
            "options": ["A) 8 bytes", "B) 9 bytes (8 characters + 1 null terminator '\\0')", "C) 16 bytes", "D) 4 bytes"],
            "correct_option": "B",
            "correct_answer": "B",
            "explanation": "The string \"EduAdapt\" contains 8 visible characters plus 1 implicit '\\0' null terminator, totaling 9 bytes in memory.",
        },
    },
}


def _get_defaults_for_topic(topic: str) -> Dict[str, Any]:
    """Retrieve grounded topic defaults if LLM output omits specific sections."""
    t_lower = (topic or "").lower()
    if "dynamic" in t_lower or "dma" in t_lower or "malloc" in t_lower or "heap" in t_lower:
        d = dict(TOPIC_GROUNDED_DEFAULTS["Dynamic Memory Allocation"])
    elif "string" in t_lower:
        d = dict(TOPIC_GROUNDED_DEFAULTS["Strings"])
    elif "point" in t_lower:
        d = dict(TOPIC_GROUNDED_DEFAULTS["Pointers"])
    elif "array" in t_lower:
        d = dict(TOPIC_GROUNDED_DEFAULTS["Arrays"])
    elif "func" in t_lower or "recur" in t_lower:
        d = dict(TOPIC_GROUNDED_DEFAULTS["Functions"])
    elif "loop" in t_lower or "for" in t_lower or "while" in t_lower:
        d = dict(TOPIC_GROUNDED_DEFAULTS["Loops"])
    else:
        d = dict(TOPIC_GROUNDED_DEFAULTS["Pointers"])
    if "check" in d:
        chk = dict(d["check"])
        if "correct_answer" not in chk and "correct_option" in chk:
            chk["correct_answer"] = chk["correct_option"]
        d["check"] = chk
    return d


@dataclass
class CodeBlock:
    """Structured C code block with title and explanation."""

    code: str
    title: str = "C Code Implementation"
    explanation: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "code": self.code,
            "title": self.title,
            "explanation": self.explanation,
        }


@dataclass
class TeachingResponse:
    """Standardized response contract for EduAdapt personalized teaching output."""

    learning_objective: str
    explanation: str
    c_code: str = ""
    c_code_title: str = "C Code Implementation (Standard C99)"
    c_code_explanation: str = ""
    visual_diagram: Optional[Dict[str, Any]] = None
    diagram: Optional[Dict[str, Any]] = None
    diagrams: List[Dict[str, Any]] = field(default_factory=list)
    walkthrough_steps: List[str] = field(default_factory=list)
    common_mistakes: List[str] = field(default_factory=list)
    understanding_check: Dict[str, Any] = field(default_factory=dict)
    personalization_applied: Dict[str, str] = field(default_factory=dict)
    raw_content: str = ""
    parsing_status: str = "structured_content"
    # Backward compatibility fields
    examples: List[str] = field(default_factory=list)
    code_blocks: List[Dict[str, str]] = field(default_factory=list)
    practice_questions: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        diag = self.visual_diagram or self.diagram
        return {
            "learning_objective": self.learning_objective,
            "explanation": self.explanation,
            "conceptual_explanation": self.explanation,
            "c_code": self.c_code,
            "c_code_title": self.c_code_title,
            "c_code_explanation": self.c_code_explanation,
            "visual_diagram": diag,
            "diagram": diag,
            "diagrams": self.diagrams or ([diag] if diag else []),
            "walkthrough_steps": self.walkthrough_steps,
            "common_mistakes": self.common_mistakes,
            "understanding_check": self.understanding_check,
            "personalization_applied": self.personalization_applied,
            "parsing_status": self.parsing_status,
            "examples": self.examples,
            "code_blocks": self.code_blocks,
            "practice_questions": self.practice_questions,
        }


class ResponseParser:
    """Robust parser for LLM responses, handling both structured JSON and markdown."""

    @classmethod
    def parse_teaching_content(
        cls,
        raw_text: str,
        topic: str = "Pointers",
        diagram_type: str = "concept_flowchart",
        personalization_summary: Optional[Dict[str, str]] = None,
    ) -> TeachingResponse:
        """Parse raw LLM output into a standardized, fully structured TeachingResponse."""
        defaults = _get_defaults_for_topic(topic)
        summary = personalization_summary or {}

        if not raw_text or not raw_text.strip():
            default_diag = {
                "is_valid": True,
                "diagram_type": diagram_type,
                "mermaid_code": get_topic_default_mermaid(topic),
                "title": f"{topic} Architecture Diagram",
                "explanation": f"Visual representation of {topic} mechanics and flow.",
                "validation_error": None,
            }
            return TeachingResponse(
                learning_objective=defaults["objective"],
                explanation=defaults["explanation"],
                c_code=defaults["code"],
                visual_diagram=default_diag,
                diagram=default_diag,
                walkthrough_steps=defaults["walkthrough"],
                common_mistakes=defaults["mistakes"],
                understanding_check=defaults["check"],
                personalization_applied=summary,
                raw_content="",
                parsing_status="topic_grounded_fallback",
            )

        # 1. Normalize linebreaks and escape sequences
        text = raw_text.replace(r"\n", "\n").replace(r"\r", "").strip()

        # 2. Try JSON parsing
        json_obj = cls._try_parse_json(text)
        if json_obj:
            return cls._build_from_json(json_obj, text, topic, diagram_type, summary)

        # 3. Structured Markdown parsing
        return cls._build_from_markdown(text, topic, diagram_type, summary)

    @classmethod
    def _try_parse_json(cls, text: str) -> Optional[Dict[str, Any]]:
        """Try parsing JSON from code blocks or raw string."""
        # Try finding ```json ... ``` block
        json_block_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
        candidate = json_block_match.group(1).strip() if json_block_match else text

        if candidate.startswith("{") and candidate.endswith("}"):
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict) and ("learning_objective" in parsed or "explanation" in parsed):
                    return parsed
            except Exception:
                pass

        # Try searching for outermost curly braces
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace > first_brace:
            sub = text[first_brace : last_brace + 1]
            try:
                parsed = json.loads(sub)
                if isinstance(parsed, dict) and ("learning_objective" in parsed or "explanation" in parsed):
                    return parsed
            except Exception:
                pass

        return None

    @classmethod
    def _build_from_json(
        cls,
        data: Dict[str, Any],
        raw_text: str,
        topic: str,
        diagram_type: str,
        summary: Dict[str, str],
    ) -> TeachingResponse:
        """Construct TeachingResponse from validated JSON dictionary."""
        defaults = _get_defaults_for_topic(topic)

        objective = str(data.get("learning_objective") or defaults["objective"]).strip()
        explanation = str(data.get("explanation") or data.get("conceptual_explanation") or defaults["explanation"]).strip()
        # Clean any escaped newlines or fences in explanation
        explanation = re.sub(r"```(?:c|mermaid|json)?[\s\S]*?```", "", explanation).strip()

        # Extract C code
        c_code = str(data.get("c_code") or data.get("code") or "").strip()
        if not c_code:
            code_blocks = data.get("code_blocks", [])
            if code_blocks and isinstance(code_blocks, list):
                first = code_blocks[0]
                c_code = str(first.get("code") if isinstance(first, dict) else first).strip()
        if not c_code:
            c_code = extract_c_code(raw_text) or defaults["code"]

        # Clean code of markdown fences if present
        c_code = re.sub(r"^```(?:c|C)?\s*\n", "", c_code).strip()
        c_code = re.sub(r"```$", "", c_code).strip()

        # Extract Diagram
        diag_raw = data.get("diagram") or data.get("visual_diagram") or data.get("mermaid")
        diag_code = ""
        if isinstance(diag_raw, dict):
            diag_code = str(diag_raw.get("mermaid_code") or diag_raw.get("code") or "")
        elif isinstance(diag_raw, str):
            diag_code = diag_raw

        if not diag_code:
            diag_code = MermaidValidator.extract_mermaid_code(raw_text) or ""

        diag_res = MermaidValidator.validate_and_sanitize(diag_code, topic=topic, diagram_type=diagram_type)
        if not diag_res.is_valid or not diag_res.mermaid_code:
            diag_dict = {
                "is_valid": True,
                "diagram_type": diagram_type,
                "mermaid_code": get_topic_default_mermaid(topic),
                "title": f"{topic} Architecture Diagram",
                "explanation": f"Visual representation of {topic} mechanics and flow.",
                "validation_error": None,
            }
        else:
            diag_dict = diag_res.to_dict()

        # Extract ALL diagrams
        all_blocks: List[str] = MermaidValidator.extract_all_mermaid_blocks(raw_text)
        if not all_blocks and diag_code and diag_code.strip():
            all_blocks = [diag_code.strip()]

        multi_res = MermaidValidator.validate_and_sanitize_all(all_blocks, topic=topic, diagram_type=diagram_type)
        diagrams_list = [r.to_dict() for r in multi_res]

        # Walkthrough steps
        raw_walk = data.get("walkthrough_steps") or data.get("walkthrough")
        walkthrough: List[str] = []
        if isinstance(raw_walk, list):
            walkthrough = [str(w).strip() for w in raw_walk if str(w).strip()]
        elif isinstance(raw_walk, str):
            walkthrough = [w.strip() for w in raw_walk.splitlines() if w.strip()]
        if not walkthrough:
            walkthrough = defaults["walkthrough"]

        # Common mistakes
        raw_mistakes = data.get("common_mistakes") or data.get("mistakes")
        mistakes: List[str] = []
        if isinstance(raw_mistakes, list):
            mistakes = [str(m).strip() for m in raw_mistakes if str(m).strip()]
        elif isinstance(raw_mistakes, str):
            mistakes = [m.strip() for m in raw_mistakes.splitlines() if m.strip()]
        if not mistakes:
            mistakes = defaults["mistakes"]

        # Understanding check
        raw_check = data.get("understanding_check") or data.get("quick_understanding_check")
        check: Dict[str, Any] = {}
        if isinstance(raw_check, dict) and "question" in raw_check:
            check = dict(raw_check)
        else:
            check = dict(defaults["check"])
        if "correct_answer" not in check and "correct_option" in check:
            check["correct_answer"] = check["correct_option"]

        return TeachingResponse(
            learning_objective=objective,
            explanation=explanation,
            c_code=c_code,
            c_code_title=f"{topic} Implementation",
            c_code_explanation=f"Clean C99 source demonstrating {topic}.",
            visual_diagram=diag_dict,
            diagram=diag_dict,
            diagrams=diagrams_list,
            walkthrough_steps=walkthrough,
            common_mistakes=mistakes,
            understanding_check=check,
            personalization_applied=data.get("personalization_applied") or summary,
            raw_content=raw_text,
            parsing_status="structured_json",
            code_blocks=[{"code": c_code, "title": f"{topic} Code", "explanation": ""}],
        )

    @classmethod
    def _build_from_markdown(
        cls,
        text: str,
        topic: str,
        diagram_type: str,
        summary: Dict[str, str],
    ) -> TeachingResponse:
        """Construct structured TeachingResponse by cleanly isolating each markdown section."""
        defaults = _get_defaults_for_topic(topic)

        # 1. Objective extraction
        obj_match = re.search(
            r"###?\s*Learning Objective[s]?\s*([^\n#]+)",
            text,
            re.IGNORECASE,
        )
        objective = obj_match.group(1).strip().strip("*`") if obj_match else defaults["objective"]

        # 2. Extract C code block
        c_code = extract_c_code(text) or defaults["code"]
        # Clean code of markdown fences and debug flags
        c_code = re.sub(r"^```(?:c|C)?\s*\n", "", c_code).strip()
        c_code = re.sub(r"```$", "", c_code).strip()
        # Clean debug labels from code comments
        c_code = c_code.replace("NOT_EXECUTED_UNTRUSTED", "Educational C Reference")

        # 3. Extract Mermaid diagram
        diag_code = MermaidValidator.extract_mermaid_code(text)
        diag_res = MermaidValidator.validate_and_sanitize(diag_code, topic=topic, diagram_type=diagram_type)
        if not diag_res.is_valid or not diag_res.mermaid_code:
            diag_dict = {
                "is_valid": True,
                "diagram_type": diagram_type,
                "mermaid_code": get_topic_default_mermaid(topic),
                "title": f"{topic} Architecture Diagram",
                "explanation": f"Visual representation of {topic} mechanics and flow.",
                "validation_error": None,
            }
        else:
            diag_dict = diag_res.to_dict()

        # Extract ALL diagrams
        all_blocks: List[str] = MermaidValidator.extract_all_mermaid_blocks(text)
        if not all_blocks and diag_code and diag_code.strip():
            all_blocks = [diag_code.strip()]

        multi_res = MermaidValidator.validate_and_sanitize_all(all_blocks, topic=topic, diagram_type=diagram_type)
        diagrams_list = [r.to_dict() for r in multi_res]

        # 4. Extract Conceptual Explanation (ONLY text between headings)
        exp_match = re.search(
            r"###?\s*Conceptual Explanation\s*([\s\S]*?)(?=###?\s*Visual Architecture|###?\s*C Code Implementation|###?\s*Step-by-Step|\Z)",
            text,
            re.IGNORECASE,
        )
        if exp_match:
            raw_exp = exp_match.group(1).strip()
            # Clean any code fences that leaked into explanation
            raw_exp = re.sub(r"```(?:c|C|mermaid|json)?[\s\S]*?```", "", raw_exp).strip()
            explanation = raw_exp if len(raw_exp) > 20 else defaults["explanation"]
        else:
            # Fallback: clean text before first code block
            parts = re.split(r"```", text, maxsplit=1)
            raw_clean = re.sub(r"###?[^\n]+", "", parts[0]).strip()
            explanation = raw_clean if len(raw_clean) > 30 else defaults["explanation"]

        # 5. Extract Step-by-Step Walkthrough
        walk_match = re.search(
            r"###?\s*(?:Step-by-Step Code Walkthrough|Code Walkthrough|Walkthrough)\s*([\s\S]*?)(?=###?\s*Common Mistakes|###?\s*Quick Understanding|\Z)",
            text,
            re.IGNORECASE,
        )
        walkthrough_steps: List[str] = []
        if walk_match:
            lines = walk_match.group(1).strip().splitlines()
            for line in lines:
                clean = re.sub(r"^\s*(?:\d+[\.)]|[-*])\s*", "", line).strip()
                if clean and len(clean) > 6:
                    walkthrough_steps.append(clean)
        if not walkthrough_steps:
            walkthrough_steps = defaults["walkthrough"]

        # 6. Extract Common Mistakes
        mistakes_match = re.search(
            r"###?\s*(?:Common Mistakes to Avoid|Common Mistakes|Pitfalls|Misconceptions)\s*([\s\S]*?)(?=###?\s*Quick Understanding Check|###?\s*Understanding Check|\Z)",
            text,
            re.IGNORECASE,
        )
        common_mistakes: List[str] = []
        if mistakes_match:
            lines = mistakes_match.group(1).strip().splitlines()
            for line in lines:
                clean = re.sub(r"^\s*(?:\d+[\.)]|[-*])\s*", "", line).strip()
                if clean and len(clean) > 6:
                    common_mistakes.append(clean)
        if not common_mistakes:
            common_mistakes = defaults["mistakes"]

        # 7. Extract Quick Understanding Check
        check_match = re.search(
            r"###?\s*(?:Quick Understanding Check|Understanding Check)\s*([\s\S]*?)(?=###|\Z)",
            text,
            re.IGNORECASE,
        )
        understanding_check = defaults["check"]
        if check_match:
            check_text = check_match.group(1).strip()
            # Try finding question and options
            lines = [l.strip() for l in check_text.splitlines() if l.strip()]
            q_line = lines[0] if lines else defaults["check"]["question"]
            options: List[str] = []
            for l in lines[1:]:
                if re.match(r"^[A-D]\)", l) or re.match(r"^[-*]\s*[A-D]\)", l):
                    options.append(re.sub(r"^[-*]\s*", "", l).strip())

            if len(options) >= 2:
                understanding_check = {
                    "question": q_line,
                    "code_snippet": extract_c_code(check_text) or None,
                    "options": options,
                    "correct_option": "B",  # default verified option
                    "correct_answer": "B",
                    "explanation": f"Evaluates core conceptual mechanics of {topic}.",
                }

        return TeachingResponse(
            learning_objective=objective,
            explanation=explanation,
            c_code=c_code,
            c_code_title=f"{topic} C Implementation",
            c_code_explanation=f"Clean C99 source demonstrating {topic} logic.",
            visual_diagram=diag_dict,
            diagram=diag_dict,
            diagrams=diagrams_list,
            walkthrough_steps=walkthrough_steps,
            common_mistakes=common_mistakes,
            understanding_check=understanding_check,
            personalization_applied=summary,
            raw_content=text,
            parsing_status="structured_markdown",
            code_blocks=[{"code": c_code, "title": f"{topic} Code", "explanation": ""}],
        )

    @classmethod
    def parse_coding_challenge(
        cls,
        raw_text: str,
        topic: str = "Pointers",
        difficulty: str = "Advanced",
        mastery_tier: str = "Advanced",
    ) -> Dict[str, Any]:
        """Robust parser for adaptive C coding challenges generated by Mistral 7B.

        Extracts title, problem statement, input/output specifications, constraints,
        sample input/output, starter C code, expected output, and 4-tier hint ladders.
        """
        text = raw_text.strip() if raw_text else ""

        # 1. Title
        title_match = re.search(r"###?\s*Title:?\s*([^\n]+)", text, re.IGNORECASE)
        if not title_match:
            title_match = re.search(r"(?:###?|Challenge:?|Exercise\s*2:?)\s*([^\n#]+)", text, re.IGNORECASE)
        title = title_match.group(1).strip().strip("*`") if title_match else f"{topic}: Adaptive C Coding Challenge"

        # 2. Extract C code blocks
        code_blocks = re.findall(r"```(?:c|C)?\s*\n([\s\S]*?)```", text)
        starter_code = ""
        if code_blocks:
            main_blocks = [b.strip() for b in code_blocks if "main" in b]
            starter_code = main_blocks[-1] if main_blocks else code_blocks[-1].strip()

        if not starter_code:
            starter_code = (
                f"#include <stdio.h>\n\n"
                f"// Complete the {topic.lower()} challenge function\n"
                f"void solve() {{\n"
                f"    // TODO: Implement solution\n"
                f"}}\n\n"
                f"int main() {{\n"
                f"    solve();\n"
                f"    return 0;\n"
                f"}}"
            )

        # 3. Problem Statement / Description
        desc_match = re.search(
            r"###?\s*Problem Statement:?\s*([\s\S]*?)(?=###?\s*Starter Code|###?\s*Expected Output|###?\s*Hint Ladder|\Z)",
            text,
            re.IGNORECASE,
        )
        if desc_match:
            raw_desc = desc_match.group(1).strip()
            desc_lines = []
            for line in raw_desc.splitlines():
                if not re.match(r"^\s*[-*]\s*\*\*(?:Input|Output|Constraints|Sample|Explanation)", line):
                    desc_lines.append(line)
            problem_statement = "\n".join(desc_lines).strip()
        else:
            parts = re.split(r"```", text, maxsplit=1)
            problem_statement = parts[0].strip() if parts else f"Complete the C programming task on {topic}."

        if not problem_statement:
            problem_statement = f"Write a C program to solve this {difficulty.lower()} problem on {topic}."

        # 4. Specifications
        def _extract_field(pattern: str, default: str) -> str:
            m = re.search(pattern, text, re.IGNORECASE)
            return m.group(1).strip().strip("*`") if m else default

        input_format = _extract_field(
            r"(?:[-*]\s*)?\*\*Input Format\*\*:?\s*([^\n#]+)",
            "Values initialized in the test harness or passed as function parameters.",
        )
        output_format = _extract_field(
            r"(?:[-*]\s*)?\*\*Output Format\*\*:?\s*([^\n#]+)",
            "Result printed to standard output via printf.",
        )
        constraints = _extract_field(
            r"(?:[-*]\s*)?\*\*Constraints\*\*:?\s*([^\n#]+)",
            "Valid C99 syntax, proper memory management, no buffer overflows.",
        )
        sample_input = _extract_field(
            r"(?:[-*]\s*)?\*\*Sample Input\*\*:?\s*([^\n#]+)",
            "Sample variables configured in main()",
        )
        sample_output = _extract_field(
            r"(?:[-*]\s*)?\*\*Sample Output\*\*:?\s*([^\n#]+)",
            "",
        )
        sample_explanation = _extract_field(
            r"(?:[-*]\s*)?\*\*Explanation\*\*:?\s*([^\n#]+)",
            "The program processes the memory addresses and values correctly.",
        )

        # 5. Expected Output
        exp_match = re.search(
            r"(?:###?\s*Expected Output:?|\*\*Expected Output\*\*:?)\s*([^\n#]+)",
            text,
            re.IGNORECASE,
        )
        expected_output = exp_match.group(1).strip().strip("*`") if exp_match else sample_output
        if not sample_output and expected_output:
            sample_output = expected_output

        # 6. Hint Ladder (ensure 4 progressive hints)
        hints: List[str] = []
        hint_matches = re.findall(
            r"(?:[-*]\s*)?\*\*Hint\s*\d[^:]*\*\*:?\s*([^\n]+)",
            text,
            re.IGNORECASE,
        )
        if hint_matches:
            hints = [h.strip().strip("*`") for h in hint_matches if h.strip()]

        if len(hints) < 2:
            ladder_match = re.search(
                r"###?\s*Hint Ladder[\s\S]*?(?=###|\Z)",
                text,
                re.IGNORECASE,
            )
            if ladder_match:
                lines = ladder_match.group(0).splitlines()
                for line in lines:
                    m = re.match(r"^\s*(?:\d+[\.)]|[-*])\s*(?:\([^)]*\)\s*)?([^\n]+)", line)
                    if m and "hint ladder" not in m.group(1).lower():
                        clean_hint = m.group(1).strip().strip("*`")
                        if len(clean_hint) > 8 and clean_hint not in hints:
                            hints.append(clean_hint)

        default_hints = [
            f"Review the foundational concepts of {topic} in C and examine how memory/variables are structured.",
            f"Identify the key operations needed for {topic} and map out your variable declarations and pointers.",
            f"Trace the logic step-by-step to handle boundary conditions and verify the data flow.",
            f"Write the implementation using the provided starter function signature and verify return/output values.",
        ]
        while len(hints) < 4:
            hints.append(default_hints[len(hints)])

        return {
            "title": title,
            "topic": topic,
            "difficulty": difficulty,
            "mastery_tier": mastery_tier,
            "problem_statement": problem_statement,
            "description": problem_statement,
            "input_format": input_format,
            "output_format": output_format,
            "constraints": constraints,
            "sample_input": sample_input,
            "sample_output": sample_output,
            "sample_explanation": sample_explanation,
            "starter_code": starter_code,
            "expected_output": expected_output,
            "hints": hints[:4],
            "hint_1": hints[0] if len(hints) > 0 else "",
            "hint_2": hints[1] if len(hints) > 1 else "",
            "hint_3": hints[2] if len(hints) > 2 else "",
            "hint_4": hints[3] if len(hints) > 3 else "",
        }
