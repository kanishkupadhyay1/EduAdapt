"""Structured output models and robust response parsers for EduAdapt teaching generation.

Supports strict JSON parsing with intelligent structured markdown fallback.
Safely extracts objectives, conceptual explanations, C code blocks, Mermaid diagrams,
step-by-step walkthroughs, common mistakes, and interactive understanding checks.
Provides student-adaptive educational grounding across all 10 PPS C curriculum topics
for Beginner, Intermediate, and Advanced mastery tiers.
"""

from dataclasses import dataclass, field
import json
import re
from typing import Any, Dict, List, Optional

from eduadapt.teaching.diagrams import DiagramResult, MermaidValidator, get_topic_default_mermaid


def extract_c_code(text: str) -> Optional[str]:
    """Extract C source code block from markdown text without circular import.
    
    Robustly scans for ```c / ```C blocks first. If none found, inspects all fenced blocks
    for C language markers (#include, int main, void, printf, malloc) while skipping Mermaid diagrams.
    """
    if not text:
        return None

    # 1. Search for explicit ```c or ```C blocks
    c_matches = re.findall(r"```(?:c|C)\s*\n([\s\S]*?)```", text)
    for code in c_matches:
        code_str = code.strip()
        lower = code_str.lower()
        if not lower.startswith(("flowchart", "graph", "sequencediagram", "classdiagram", "statediagram")):
            return code_str

    # 2. If no explicit ```c block, search all code blocks
    all_blocks = re.findall(r"```(?:[a-zA-Z0-9_-]*)\s*\n([\s\S]*?)```", text)
    for block in all_blocks:
        code_str = block.strip()
        lower = code_str.lower()
        if lower.startswith(("flowchart", "graph", "sequencediagram", "classdiagram", "statediagram", "erdiagram")):
            continue
        # Check for genuine C language markers
        if any(kw in code_str for kw in ("#include", "int main", "void ", "printf(", "scanf(", "return 0;", "malloc(")):
            return code_str

    return None


def normalize_topic_name(topic: str) -> str:
    """Normalize topic string to standard PPS curriculum sequence names."""
    t = (topic or "").strip().lower()
    if "dynamic" in t or "dma" in t or "malloc" in t or "heap" in t:
        return "Dynamic Memory Allocation"
    if "string" in t:
        return "Strings"
    if "point" in t:
        return "Pointers"
    if "array" in t:
        return "Arrays"
    if "func" in t or "recur" in t:
        return "Functions"
    if "loop" in t or "for" in t or "while" in t:
        return "Loops"
    if "struct" in t or "union" in t:
        return "Structures"
    if "cond" in t or "if" in t or "switch" in t:
        return "Conditionals"
    if "op" in t or "expr" in t:
        return "Operators and Expressions"
    if "var" in t or "type" in t or "data" in t:
        return "Variables and Data Types"
    return "Pointers"


# Comprehensive, tier-adapted defaults for all 10 PPS topics (Beginner, Intermediate, Advanced)
TOPIC_GROUNDED_DEFAULTS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "Pointers": {
        "Beginner": {
            "objective": "Understand the meaning of memory locations, addresses with &, and pointer dereferencing with * in C.",
            "explanation": (
                "Every variable in C is stored at a unique physical memory location called its memory address. "
                "A pointer is simply a special variable designed to hold the memory address of another variable.\n\n"
                "The address-of operator (&) extracts the memory location where a variable lives. "
                "The dereference operator (*) accesses the actual value stored inside that target memory location."
            ),
            "code": (
                "#include <stdio.h>\n\n"
                "int main(void) {\n"
                "    int num = 10;          // A standard integer variable\n"
                "    int *ptr = &num;       // Pointer storing the memory address of num\n\n"
                "    printf(\"Value of num: %d\\n\", num);\n"
                "    printf(\"Address of num (&num): %p\\n\", (void*)&num);\n"
                "    printf(\"Address stored in ptr: %p\\n\", (void*)ptr);\n"
                "    printf(\"Value accessed via pointer (*ptr): %d\\n\", *ptr);\n\n"
                "    // Changing value using the pointer\n"
                "    *ptr = 25;\n"
                "    printf(\"New value of num after *ptr = 25: %d\\n\", num);\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "int num = 10;: Allocates 4 bytes in stack memory storing the integer 10 at an address such as 0x1000.",
                "int *ptr = &num;: Declares a pointer variable `ptr` and stores the address of `num` into it.",
                "printf(\"%p\", (void*)ptr): Shows the exact hexadecimal memory address pointing to `num`.",
                "*ptr = 25;: Dereferences the pointer to overwrite the contents of `num`'s memory directly.",
                "printf(\"New value...\"): Confirms that `num` now equals 25 without directly assigning to `num`.",
            ],
            "mistakes": [
                "Confusing & (address-of) with * (dereference).",
                "Using an uninitialized pointer (wild pointer) which causes segmentation faults.",
                "Assigning an integer literal directly to a pointer variable (int *p = 10).",
            ],
            "check": {
                "question": "What is printed when this C code runs?",
                "code_snippet": "int a = 10;\nint *p = &a;\n*p = 25;\nprintf(\"%d\\n\", a);",
                "options": ["A) 10", "B) 25", "C) Memory address of a", "D) Compilation error"],
                "correct_option": "B",
                "correct_answer": "B",
                "explanation": "Pointer `p` stores the address of variable `a`. Dereferencing `*p = 25` mutates the memory cell of `a`, making `a` equal to 25.",
            },
        },
        "Intermediate": {
            "objective": "Master pointer arithmetic, array-pointer duality, and pass-by-reference mechanics in C functions.",
            "explanation": (
                "In C, pointers and arrays share a deep syntactic duality: an array name evaluates to a pointer to its "
                "first element (`arr == &arr[0]`). Pointer arithmetic operates in units of the pointed-to data type's byte size.\n\n"
                "Pointers also enable functions to mutate caller variables by receiving memory addresses as parameters."
            ),
            "code": (
                "#include <stdio.h>\n\n"
                "void swap(int *x, int *y) {\n"
                "    int temp = *x;\n"
                "    *x = *y;\n"
                "    *y = temp;\n"
                "}\n\n"
                "int main(void) {\n"
                "    int arr[3] = {10, 20, 30};\n"
                "    int *p = arr;\n\n"
                "    printf(\"First element: %d\\n\", *p);\n"
                "    printf(\"Second element (p + 1): %d\\n\", *(p + 1));\n\n"
                "    swap(&arr[0], &arr[2]);\n"
                "    printf(\"After swap: arr[0]=%d, arr[2]=%d\\n\", arr[0], arr[2]);\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "void swap(int *x, int *y): Receives memory addresses, allowing direct mutation of caller arguments.",
                "int *p = arr: Array name decays to the base pointer address &arr[0].",
                "*(p + 1): Increments pointer address by 1 * sizeof(int) (4 bytes) to access the next element.",
                "swap(&arr[0], &arr[2]): Passes addresses so that changes reflect in the original array.",
            ],
            "mistakes": [
                "Passing variables by value instead of address when attempting to modify them in a function.",
                "Incrementing a pointer beyond the bounds of an allocated array.",
                "Attempting to reassign an array identifier (arr = ptr), which is a non-modifiable lvalue.",
            ],
            "check": {
                "question": "If `int *p = arr;`, what does the expression `*(p + 2)` evaluate to for `int arr[3] = {5, 10, 15};`?",
                "code_snippet": "int arr[3] = {5, 10, 15};\nint *p = arr;\nprintf(\"%d\\n\", *(p + 2));",
                "options": ["A) 5", "B) 10", "C) 15", "D) Address of arr[2]"],
                "correct_option": "C",
                "correct_answer": "C",
                "explanation": "Pointer arithmetic `*(p + 2)` is identical to `arr[2]`, retrieving the third integer value: 15.",
            },
        },
        "Advanced": {
            "objective": "Master double indirection (pointers to pointers), function pointers, and memory safety in C.",
            "explanation": (
                "Advanced C programming leverages multi-level indirection (`int **dptr`) to dynamically allocate matrices, "
                "update caller pointer targets, and manage dynamic data structures. Function pointers allow callback dispatch "
                "and runtime polymorphism while adhering to strict memory boundary safety."
            ),
            "code": (
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n\n"
                "void allocateTarget(int **ptrRef, int initialVal) {\n"
                "    *ptrRef = (int *)malloc(sizeof(int));\n"
                "    if (*ptrRef != NULL) {\n"
                "        **ptrRef = initialVal;\n"
                "    }\n"
                "}\n\n"
                "int main(void) {\n"
                "    int *data = NULL;\n"
                "    allocateTarget(&data, 99);\n\n"
                "    if (data != NULL) {\n"
                "        printf(\"Allocated value via double pointer: %d\\n\", *data);\n"
                "        free(data);\n"
                "        data = NULL; // Prevent dangling pointer\n"
                "    }\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "void allocateTarget(int **ptrRef): Receives the address of a pointer variable to modify caller pointer state.",
                "*ptrRef = malloc(...): Modifies caller's `data` pointer to point to the newly allocated heap block.",
                "**ptrRef = initialVal: Dereferences twice to assign the integer into the heap cell.",
                "free(data); data = NULL;: Deallocates memory and resets pointer to eliminate dangling references.",
            ],
            "mistakes": [
                "Dereferencing a pointer after freeing it (dangling pointer access).",
                "Passing a single pointer to a function expecting to reassign the caller's allocation.",
                "Failing to check for NULL return values from dynamic allocation before double dereference.",
            ],
            "check": {
                "question": "What is the primary purpose of passing `&data` (a pointer to pointer) to `allocateTarget`?",
                "code_snippet": "int *data = NULL;\nallocateTarget(&data, 99);",
                "options": [
                    "A) To pass data by value",
                    "B) To allow the function to modify the caller's pointer variable `data`",
                    "C) To convert integer to float",
                    "D) To suppress compiler warnings",
                ],
                "correct_option": "B",
                "correct_answer": "B",
                "explanation": "Passing `&data` provides the memory address of the pointer `data`, allowing `allocateTarget` to update what `data` points to.",
            },
        },
    },
    "Dynamic Memory Allocation": {
        "Beginner": {
            "objective": "Understand heap memory allocation with malloc, NULL check verification, and memory release with free in C.",
            "explanation": (
                "While regular variables are stored on the stack and disappear when a function finishes, dynamic memory is "
                "allocated on the system 'heap' at runtime. Heap memory persists until you explicitly release it.\n\n"
                "`malloc(size)` requests a block of bytes from the heap and returns its starting memory address. "
                "Always verify the pointer is not NULL before using it, and call `free()` when finished to prevent memory leaks."
            ),
            "code": (
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n\n"
                "int main(void) {\n"
                "    int *p = (int *)malloc(sizeof(int));\n\n"
                "    if (p == NULL) {\n"
                "        printf(\"Memory allocation failed!\\n\");\n"
                "        return 1;\n"
                "    }\n\n"
                "    *p = 50;\n"
                "    printf(\"Value stored in heap memory: %d\\n\", *p);\n\n"
                "    free(p);\n"
                "    p = NULL;\n"
                "    printf(\"Memory freed successfully.\\n\");\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "malloc(sizeof(int)): Allocates 4 bytes of heap memory and returns a void* address cast to int*.",
                "if (p == NULL): Checks if the operating system had sufficient memory available.",
                "*p = 50: Writes the value 50 into the dynamically allocated heap cell.",
                "free(p): Returns the 4 bytes back to the operating system.",
                "p = NULL: Clears the pointer variable so it cannot accidentally reference deallocated memory.",
            ],
            "mistakes": [
                "Forgetting to check if malloc returned NULL before dereferencing.",
                "Forgetting to call free(), which causes memory leaks.",
                "Using the pointer after calling free() (dangling pointer bug).",
            ],
            "check": {
                "question": "What header file must be included to use `malloc()` and `free()` in standard C?",
                "code_snippet": "#include <stdio.h>\n// What header is missing for malloc?",
                "options": ["A) <string.h>", "B) <stdlib.h>", "C) <math.h>", "D) <ctype.h>"],
                "correct_option": "B",
                "correct_answer": "B",
                "explanation": "`<stdlib.h>` declares the standard dynamic memory management functions: malloc, calloc, realloc, and free.",
            },
        },
        "Intermediate": {
            "objective": "Master dynamic arrays with malloc, user-driven sizing, and structured allocation cleanup in C.",
            "explanation": (
                "Dynamic memory allocation allows programs to handle arrays whose sizes are determined at runtime. "
                "Using `malloc(size * sizeof(int))`, contiguous heap storage is allocated, accessed via standard array subscripting, "
                "and freed when no longer needed."
            ),
            "code": (
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n\n"
                "void createArray(int *array, int size) {\n"
                "    for (int i = 0; i < size; i++) {\n"
                "        array[i] = (i + 1) * 10;\n"
                "    }\n"
                "}\n\n"
                "void printArray(int *array, int size) {\n"
                "    for (int i = 0; i < size; i++) {\n"
                "        printf(\"%d%s\", array[i], (i == size - 1) ? \"\" : \" \");\n"
                "    }\n"
                "    printf(\"\\n\");\n"
                "}\n\n"
                "int main(void) {\n"
                "    int size = 5;\n"
                "    int *array = (int *)malloc(size * sizeof(int));\n"
                "    if (array == NULL) return 1;\n\n"
                "    createArray(array, size);\n"
                "    printArray(array, size);\n\n"
                "    free(array);\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "int *array = malloc(size * sizeof(int)): Allocates 20 contiguous heap bytes for 5 integers.",
                "if (array == NULL) return 1;: Safety check preventing segmentation faults if heap is exhausted.",
                "createArray(array, size): Populates elements using pointer subscripts.",
                "printArray(array, size): Prints space-separated values followed by a newline.",
                "free(array): Releases the 20 bytes back to the heap pool.",
            ],
            "mistakes": [
                "Allocating `malloc(size)` instead of `malloc(size * sizeof(int))`, underallocating memory.",
                "Accessing memory out-of-bounds (`array[size]`), corrupting heap metadata.",
                "Double freeing the same pointer address.",
            ],
            "check": {
                "question": "What is the correct allocation expression for an array of N integers in C?",
                "code_snippet": "int *arr = /* What goes here? */;",
                "options": [
                    "A) malloc(N)",
                    "B) malloc(N * sizeof(int))",
                    "C) malloc(sizeof(int))",
                    "D) calloc(N)",
                ],
                "correct_option": "B",
                "correct_answer": "B",
                "explanation": "`malloc(N * sizeof(int))` allocates exactly N elements, where each element is `sizeof(int)` (typically 4) bytes.",
            },
        },
        "Advanced": {
            "objective": "Master realloc buffer expansion, calloc zero-initialization, memory leak prevention, and fragmentation safety.",
            "explanation": (
                "Production C systems rely on dynamic memory resizing via `realloc()`. To prevent memory leaks during reallocation, "
                "the returned pointer must be assigned to a temporary pointer variable: if `realloc()` fails, it returns NULL but "
                "leaves the original block intact."
            ),
            "code": (
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n\n"
                "int main(void) {\n"
                "    int capacity = 2;\n"
                "    int *arr = (int *)calloc(capacity, sizeof(int));\n"
                "    if (!arr) return 1;\n\n"
                "    arr[0] = 100; arr[1] = 200;\n\n"
                "    // Safe reallocation pattern\n"
                "    int newCap = 4;\n"
                "    int *temp = (int *)realloc(arr, newCap * sizeof(int));\n"
                "    if (!temp) {\n"
                "        free(arr); // Clean up original if realloc fails\n"
                "        return 1;\n"
                "    }\n"
                "    arr = temp;\n"
                "    arr[2] = 300; arr[3] = 400;\n\n"
                "    for (int i = 0; i < newCap; i++) printf(\"%d \", arr[i]);\n"
                "    printf(\"\\n\");\n\n"
                "    free(arr);\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "calloc(capacity, sizeof(int)): Allocates heap memory and initializes all bytes to zero.",
                "int *temp = realloc(arr, ...): Safe pattern avoiding pointer loss if realloc returns NULL.",
                "arr = temp: Updates main pointer only after verifying realloc succeeded.",
                "free(arr): Releases the expanded block cleanly.",
            ],
            "mistakes": [
                "Direct assignment `arr = realloc(arr, ...)` causing leak if realloc fails and returns NULL.",
                "Assuming realloc initializes newly expanded bytes to zero.",
                "Reading beyond the newly allocated capacity.",
            ],
            "check": {
                "question": "Why is `arr = realloc(arr, new_size)` considered a dangerous programming practice in C?",
                "code_snippet": "int *arr = malloc(10 * sizeof(int));\narr = realloc(arr, 20 * sizeof(int)); // Why risky?",
                "options": [
                    "A) realloc is deprecated in C99",
                    "B) If realloc fails and returns NULL, the original memory block is orphaned and leaked",
                    "C) It always causes a segmentation fault",
                    "D) arr cannot be reallocated twice",
                ],
                "correct_option": "B",
                "correct_answer": "B",
                "explanation": "If realloc fails, it returns NULL while leaving the original memory intact; directly overwriting `arr` loses the pointer, leaking memory.",
            },
        },
    },
    "Strings": {
        "Beginner": {
            "objective": "Understand null-terminated character arrays, string literals, and the role of '\\0' in C.",
            "explanation": (
                "In C, strings are not a distinct built-in type. A string is simply a one-dimensional array of characters "
                "terminated by a special null character ('\\0', ASCII value 0).\n\n"
                "The null terminator marks where the text ends in memory so that functions like `printf(\"%s\")` and `strlen()` "
                "know when to stop reading."
            ),
            "code": (
                "#include <stdio.h>\n"
                "#include <string.h>\n\n"
                "int main(void) {\n"
                "    char greeting[] = \"Hello\";\n\n"
                "    printf(\"String: %s\\n\", greeting);\n"
                "    printf(\"Length (strlen): %zu\\n\", strlen(greeting));\n"
                "    printf(\"Total Array Bytes (sizeof): %zu\\n\", sizeof(greeting));\n\n"
                "    // Inspecting characters including null terminator\n"
                "    for (int i = 0; i <= 5; i++) {\n"
                "        printf(\"Index %d: '%c' (ASCII: %d)\\n\", i, greeting[i], (int)greeting[i]);\n"
                "    }\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "char greeting[] = \"Hello\": Allocates 6 bytes: 'H', 'e', 'l', 'l', 'o', and the null terminator '\\0'.",
                "strlen(greeting): Counts visible characters up to but excluding '\\0' (yields 5).",
                "sizeof(greeting): Counts total memory bytes including '\\0' (yields 6).",
                "greeting[5] == '\\0': Shows that the final index holds ASCII 0.",
            ],
            "mistakes": [
                "Forgetting to allocate an extra byte for '\\0' (e.g., char s[5] = \"Hello\" has no room for '\\0').",
                "Using '==' to compare strings instead of `strcmp()`.",
                "Using unconstrained `gets()` which causes buffer overflow vulnerabilities.",
            ],
            "check": {
                "question": "What is the memory size in bytes of the array `char msg[] = \"C\";`?",
                "code_snippet": "char msg[] = \"C\";\nprintf(\"%zu\\n\", sizeof(msg));",
                "options": ["A) 1 byte", "B) 2 bytes (character 'C' plus null terminator '\\0')", "C) 4 bytes", "D) 8 bytes"],
                "correct_option": "B",
                "correct_answer": "B",
                "explanation": "Double-quoted string literals in C append an implicit '\\0' null terminator, requiring 2 bytes: 'C' and '\\0'.",
            },
        },
        "Intermediate": {
            "objective": "Master standard library string operations (strlen, strcpy, strcmp, strcat) and pointer iteration in C.",
            "explanation": (
                "Standard library `<string.h>` provides validated primitives for string manipulation. "
                "Because strings decay to character pointers, string functions traverse memory byte-by-byte until encountering "
                "the null sentinel."
            ),
            "code": (
                "#include <stdio.h>\n"
                "#include <string.h>\n\n"
                "int main(void) {\n"
                "    char src[] = \"Programming\";\n"
                "    char dest[32];\n\n"
                "    strcpy(dest, \"C \");\n"
                "    strcat(dest, src);\n\n"
                "    printf(\"Combined: %s\\n\", dest);\n"
                "    printf(\"Comparison: %d\\n\", strcmp(dest, \"C Programming\"));\n\n"
                "    // Pointer-based string traversal\n"
                "    char *p = dest;\n"
                "    int count = 0;\n"
                "    while (*p != '\\0') {\n"
                "        count++;\n"
                "        p++;\n"
                "    }\n"
                "    printf(\"Characters traversed via pointer: %d\\n\", count);\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "char dest[32]: Pre-allocates adequate buffer capacity to hold combined strings safely.",
                "strcpy(dest, \"C \"): Copies source characters into dest and writes '\\0'.",
                "strcat(dest, src): Appends src onto dest starting at the position of dest's original null terminator.",
                "while (*p != '\\0'): Standard pointer traversal idiom advancing until reaching null sentinel.",
            ],
            "mistakes": [
                "Concatenating into a destination buffer without sufficient allocated capacity.",
                "Passing non-null-terminated character arrays to string library functions.",
            ],
            "check": {
                "question": "What does `strcmp(str1, str2) == 0` indicate in C?",
                "code_snippet": "if (strcmp(\"apple\", \"apple\") == 0) { ... }",
                "options": [
                    "A) The strings have identical character sequences",
                    "B) The strings have different lengths",
                    "C) The strings reside at identical memory addresses",
                    "D) An error occurred",
                ],
                "correct_option": "A",
                "correct_answer": "A",
                "explanation": "`strcmp()` returns 0 if and only if both strings contain identical characters up to their null terminators.",
            },
        },
        "Advanced": {
            "objective": "Master string memory architecture, read-only string literals vs stack buffers, and bounded string security.",
            "explanation": (
                "String literals in C are placed in read-only data segments (`.rodata`); attempting to mutate them triggers "
                "hardware segmentation faults. Secure production systems employ bounded functions like `snprintf` and `strncmp` "
                "to eliminate buffer overrun vulnerabilities."
            ),
            "code": (
                "#include <stdio.h>\n"
                "#include <string.h>\n\n"
                "int main(void) {\n"
                "    // Read-only string literal pointer\n"
                "    const char *roLiteral = \"Read Only Memory\";\n"
                "    // Mutable stack buffer\n"
                "    char safeBuf[16];\n\n"
                "    // Bounded write prevents buffer overflow\n"
                "    int written = snprintf(safeBuf, sizeof(safeBuf), \"%s\", roLiteral);\n"
                "    printf(\"Safe buffer: %s (truncated: %s)\\n\", safeBuf, (written >= (int)sizeof(safeBuf)) ? \"Yes\" : \"No\");\n\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "const char *roLiteral: Points directly to read-only memory; `const` prevents illegal writes at compile time.",
                "snprintf(safeBuf, sizeof(safeBuf), ...): Enforces strict maximum write limit, guaranteeing null termination.",
                "written >= sizeof(safeBuf): Detects truncation without crashing or memory corruption.",
            ],
            "mistakes": [
                "Writing to string literals (`char *p = \"abc\"; p[0] = 'x';`), triggering crashes.",
                "Using unbounded `sprintf` instead of `snprintf`.",
            ],
            "check": {
                "question": "What happens when executing `char *s = \"hello\"; s[0] = 'H';` in standard C?",
                "code_snippet": "char *s = \"hello\";\ns[0] = 'H';",
                "options": [
                    "A) String becomes 'Hello'",
                    "B) Undefined behavior / Segmentation Fault (write to read-only memory)",
                    "C) Compile-time syntax error",
                    "D) None of the above",
                ],
                "correct_option": "B",
                "correct_answer": "B",
                "explanation": "String literals are stored in read-only memory. Attempting to modify their contents is undefined behavior and typically causes a segmentation fault.",
            },
        },
    },
    "Arrays": {
        "Beginner": {
            "objective": "Understand contiguous memory representation, zero-based indexing, and element traversal in C arrays.",
            "explanation": (
                "An array in C is a collection of elements of the same data type stored in contiguous (side-by-side) memory cells. "
                "Because elements are contiguous, accessing any element using its index (`arr[i]`) happens in constant O(1) time.\n\n"
                "C uses zero-based indexing: for an array of size N, valid indices range from 0 to N - 1."
            ),
            "code": (
                "#include <stdio.h>\n\n"
                "int main(void) {\n"
                "    int scores[4] = {85, 92, 78, 90};\n\n"
                "    for (int i = 0; i < 4; i++) {\n"
                "        printf(\"Element at index %d: %d (Address: %p)\\n\", i, scores[i], (void*)&scores[i]);\n"
                "    }\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "int scores[4]: Reserves 16 contiguous bytes (4 integers * 4 bytes each) on the stack.",
                "Zero-based indexing: scores[0] is the first element, scores[3] is the last element.",
                "Contiguous addresses: Notice each element address increases by exactly 4 bytes.",
            ],
            "mistakes": [
                "Accessing index N (e.g. scores[4] on a 4-element array), which reads garbage or corrupts memory.",
                "Forgetting array indices begin at 0 rather than 1.",
            ],
            "check": {
                "question": "What is the valid index range for an array declared as `int data[10];`?",
                "code_snippet": "int data[10];",
                "options": ["A) 1 to 10", "B) 0 to 9", "C) 0 to 10", "D) 1 to 9"],
                "correct_option": "B",
                "correct_answer": "B",
                "explanation": "C arrays use 0-based indexing, so an array of 10 elements has indices 0 through 9.",
            },
        },
        "Intermediate": {
            "objective": "Master array-pointer relationships, passing arrays to functions, and multi-element processing.",
            "explanation": (
                "When an array is passed to a function, it decays into a pointer to its first element. "
                "Because the function receives a pointer rather than a full copy, mutations directly alter the caller's array."
            ),
            "code": (
                "#include <stdio.h>\n\n"
                "void doubleArray(int arr[], int size) {\n"
                "    for (int i = 0; i < size; i++) {\n"
                "        arr[i] *= 2;\n"
                "    }\n"
                "}\n\n"
                "int main(void) {\n"
                "    int vals[3] = {5, 10, 15};\n"
                "    doubleArray(vals, 3);\n\n"
                "    for (int i = 0; i < 3; i++) printf(\"%d \", vals[i]);\n"
                "    printf(\"\\n\");\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "void doubleArray(int arr[], int size): arr decays into int* pointer.",
                "arr[i] *= 2: Modifies original elements directly in caller memory.",
                "Passing size: Functions cannot determine array length from decayed pointers.",
            ],
            "mistakes": [
                "Using `sizeof(arr)` inside a function expecting total array bytes; it returns pointer size (4 or 8 bytes).",
                "Attempting to return a local array from a function.",
            ],
            "check": {
                "question": "What does `sizeof(arr)` evaluate to inside a function `void test(int arr[10])` on a 64-bit machine?",
                "code_snippet": "void test(int arr[10]) {\n    printf(\"%zu\\n\", sizeof(arr));\n}",
                "options": ["A) 40 bytes (10 * 4)", "B) 8 bytes (pointer size)", "C) 10 bytes", "D) Compilation error"],
                "correct_option": "B",
                "correct_answer": "B",
                "explanation": "Arrays decay to pointers when passed as function parameters; `sizeof(arr)` returns the size of the pointer (8 bytes on 64-bit).",
            },
        },
        "Advanced": {
            "objective": "Master multi-dimensional array memory mapping, row-major order, and linear pointer offset formulas.",
            "explanation": (
                "2D arrays in C are stored linearly in row-major order. The element at `arr[r][c]` is mapped to linear offset "
                "`*(base + (r * COLS + c))`. Understanding this mapping is critical for high-performance matrix computation."
            ),
            "code": (
                "#include <stdio.h>\n\n"
                "#define ROWS 2\n"
                "#define COLS 3\n\n"
                "int main(void) {\n"
                "    int matrix[ROWS][COLS] = {{1, 2, 3}, {4, 5, 6}};\n"
                "    int *flat = (int *)matrix;\n\n"
                "    for (int r = 0; r < ROWS; r++) {\n"
                "        for (int c = 0; c < COLS; c++) {\n"
                "            int linearIdx = r * COLS + c;\n"
                "            printf(\"[%d][%d]=%d (flat[%d]=%d) \", r, c, matrix[r][c], linearIdx, flat[linearIdx]);\n"
                "        }\n"
                "        printf(\"\\n\");\n"
                "    }\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "Row-major layout: Row 0 is stored contiguously, immediately followed by Row 1 in memory.",
                "Linear offset: `r * COLS + c` converts 2D coordinates into a 1D memory offset.",
                "int *flat = (int*)matrix: Demonstrates that the matrix is contiguous memory.",
            ],
            "mistakes": [
                "Assuming column-major order (as in Fortran/MATLAB).",
                "Passing 2D arrays with missing column dimensions to functions.",
            ],
            "check": {
                "question": "In a 2D array `int m[3][4]`, what is the linear offset of element `m[2][1]`?",
                "code_snippet": "int m[3][4]; // Element at row 2, col 1",
                "options": ["A) Offset 9 (2 * 4 + 1)", "B) Offset 7 (2 * 3 + 1)", "C) Offset 6", "D) Offset 21"],
                "correct_option": "A",
                "correct_answer": "A",
                "explanation": "Row-major linear offset formula is `row * COLS + col`, which evaluates to `2 * 4 + 1 = 9`.",
            },
        },
    },
    "Functions": {
        "Beginner": {
            "objective": "Understand function definitions, parameter pass-by-value, return statements, and call stack flow in C.",
            "explanation": (
                "A function is a reusable, modular block of code designed to perform a specific task. "
                "By default, C passes arguments by value: the function receives a private copy of the argument, "
                "meaning changes inside the function do not affect the caller's variables."
            ),
            "code": (
                "#include <stdio.h>\n\n"
                "int add(int a, int b) {\n"
                "    return a + b;\n"
                "}\n\n"
                "int main(void) {\n"
                "    int x = 15, y = 25;\n"
                "    int sum = add(x, y);\n"
                "    printf(\"Sum of %d and %d is: %d\\n\", x, y, sum);\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "int add(int a, int b): Declares a function taking two integer parameters and returning an integer.",
                "add(x, y): Pushes copies of x and y onto the call stack and transfers execution control.",
                "return a + b: Computes result and passes it back to main().",
            ],
            "mistakes": [
                "Expecting a function to modify caller variables when passed by value.",
                "Calling a function before declaring its prototype.",
            ],
            "check": {
                "question": "What is printed when this C code runs?",
                "code_snippet": "void modify(int x) { x = 99; }\nint main() { int a = 10; modify(a); printf(\"%d\\n\", a); }",
                "options": ["A) 99", "B) 10 (pass-by-value prevents mutation)", "C) 0", "D) Compilation error"],
                "correct_option": "B",
                "correct_answer": "B",
                "explanation": "C uses pass-by-value for primitive arguments. `modify` alters only its local copy of `x`; variable `a` in `main()` remains 10.",
            },
        },
        "Intermediate": {
            "objective": "Master function prototypes, pass-by-reference simulation using pointers, and modular function decomposition.",
            "explanation": (
                "To allow a function to modify caller variables, C simulates pass-by-reference by passing memory addresses (pointers). "
                "Function prototypes inform the compiler of expected argument types before full definitions appear."
            ),
            "code": (
                "#include <stdio.h>\n\n"
                "// Function prototype\n"
                "void swapValues(int *x, int *y);\n\n"
                "int main(void) {\n"
                "    int a = 10, b = 20;\n"
                "    printf(\"Before: a=%d, b=%d\\n\", a, b);\n"
                "    swapValues(&a, &b);\n"
                "    printf(\"After:  a=%d, b=%d\\n\", a, b);\n"
                "    return 0;\n"
                "}\n\n"
                "void swapValues(int *x, int *y) {\n"
                "    int temp = *x;\n"
                "    *x = *y;\n"
                "    *y = temp;\n"
                "}"
            ),
            "walkthrough": [
                "void swapValues(int *x, int *y);: Prototype declaration before main().",
                "swapValues(&a, &b): Passes memory addresses &a and &b.",
                "*x = *y: Exchanges values directly in caller memory via pointer dereference.",
            ],
            "mistakes": [
                "Omitting function prototypes causing implicit declaration warnings.",
                "Passing variable values instead of addresses (`swapValues(a, b)`).",
            ],
            "check": {
                "question": "Why must pointers be passed to `swapValues(&a, &b)` to exchange variables in `main()`?",
                "code_snippet": "swapValues(&a, &b);",
                "options": [
                    "A) Pointers run faster",
                    "B) Because C only supports pass-by-value; passing addresses gives access to caller memory",
                    "C) Functions cannot accept integers",
                    "D) To save stack space",
                ],
                "correct_option": "B",
                "correct_answer": "B",
                "explanation": "Passing addresses allows the function to dereference and modify the caller's actual memory locations.",
            },
        },
        "Advanced": {
            "objective": "Master recursion, stack frame activation records, base case termination, and recursion safety.",
            "explanation": (
                "A recursive function solves problems by calling itself on smaller sub-problems. "
                "Every recursive call creates a new stack frame (activation record). A guaranteed base case must exist "
                "to prevent unbounded stack growth and stack overflow."
            ),
            "code": (
                "#include <stdio.h>\n\n"
                "unsigned long long factorial(int n) {\n"
                "    if (n <= 1) return 1; // Base case: stops recursion\n"
                "    return n * factorial(n - 1); // Recursive step\n"
                "}\n\n"
                "int main(void) {\n"
                "    int val = 5;\n"
                "    printf(\"Factorial of %d is: %llu\\n\", val, factorial(val));\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "if (n <= 1) return 1: Base case halts further call frame creation.",
                "n * factorial(n - 1): Pushes frames until base case is reached, then unwinds with accumulated results.",
                "Stack management: Factorial(5) creates 5 concurrent stack frames before unwinding.",
            ],
            "mistakes": [
                "Missing base case causing infinite recursion and segmentation fault (stack overflow).",
                "Using recursion for simple linear iterations where loops are more space-efficient.",
            ],
            "check": {
                "question": "What critical error occurs if a recursive function lacks a valid base case?",
                "code_snippet": "int loop(int n) { return loop(n - 1); }",
                "options": [
                    "A) Compilation error",
                    "B) Stack overflow exception (segmentation fault)",
                    "C) Automatic loop conversion",
                    "D) Division by zero",
                ],
                "correct_option": "B",
                "correct_answer": "B",
                "explanation": "Without a base case, recursive calls consume stack frames indefinitely until available stack memory is exhausted.",
            },
        },
    },
    "Loops": {
        "Beginner": {
            "objective": "Understand iteration control flow, loop initialization, condition guards, and increment steps in C.",
            "explanation": (
                "Loops automate repetitive tasks. A standard `for` loop in C contains three fundamental components: "
                "1. Initialization (sets starting counter), 2. Condition (evaluated before each iteration), and "
                "3. Increment/Update (advances counter towards termination)."
            ),
            "code": (
                "#include <stdio.h>\n\n"
                "int main(void) {\n"
                "    int sum = 0;\n"
                "    for (int i = 1; i <= 5; i++) {\n"
                "        sum += i;\n"
                "        printf(\"Adding %d, running sum = %d\\n\", i, sum);\n"
                "    }\n"
                "    printf(\"Total sum: %d\\n\", sum);\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "int i = 1: Initialization executed once.",
                "i <= 5: Guard condition checked before each iteration.",
                "sum += i: Accumulator statement.",
                "i++: Counter increment step.",
                "Terminates when i reaches 6, since 6 <= 5 is false.",
            ],
            "mistakes": [
                "Placing an unintended semicolon after loop header: `for (int i = 0; i < 5; i++);`.",
                "Off-by-one errors with `<` versus `<=`. ",
            ],
            "check": {
                "question": "How many times does this loop execute: `for (int i = 0; i < 3; i++)`?",
                "code_snippet": "for (int i = 0; i < 3; i++) { ... }",
                "options": ["A) 2 times", "B) 3 times (i = 0, 1, 2)", "C) 4 times", "D) Infinite"],
                "correct_option": "B",
                "correct_answer": "B",
                "explanation": "The loop executes for i=0, i=1, and i=2. When i reaches 3, condition (3 < 3) is false, giving exactly 3 iterations.",
            },
        },
        "Intermediate": {
            "objective": "Master while, do-while, and nested loop mechanics with break and continue statements.",
            "explanation": (
                "`while` loops test conditions before entry, whereas `do-while` loops guarantee at least one execution "
                "by testing the condition after the loop body. `break` exits the nearest loop immediately, while `continue` "
                "skips the remaining body to proceed to the next iteration."
            ),
            "code": (
                "#include <stdio.h>\n\n"
                "int main(void) {\n"
                "    int num = 1;\n"
                "    while (num <= 10) {\n"
                "        if (num == 5) {\n"
                "            num++;\n"
                "            continue; // Skip printing 5\n"
                "        }\n"
                "        if (num > 7) break; // Exit loop early\n"
                "        printf(\"%d \", num);\n"
                "        num++;\n"
                "    }\n"
                "    printf(\"\\n\");\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "while (num <= 10): Condition verified before each pass.",
                "continue: Immediately advances to next iteration.",
                "break: Terminates loop when num exceeds 7.",
            ],
            "mistakes": [
                "Forgetting to increment loop variable before calling `continue` in a `while` loop (causes infinite loop).",
                "Using `break` intending to exit multiple nested loops (it only exits the innermost loop).",
            ],
            "check": {
                "question": "What makes a `do-while` loop distinct from a `while` loop in C?",
                "code_snippet": "do { ... } while (condition);",
                "options": [
                    "A) It executes faster",
                    "B) It is guaranteed to execute its body at least once",
                    "C) It cannot contain break statements",
                    "D) It only works with integers",
                ],
                "correct_option": "B",
                "correct_answer": "B",
                "explanation": "Because `do-while` evaluates its guard condition at the bottom after the loop body, it always runs at least once.",
            },
        },
        "Advanced": {
            "objective": "Master loop invariant proofs, termination guarantees, and compiler optimization considerations.",
            "explanation": (
                "Formal reasoning about loops utilizes loop invariants (predicates that hold true before and after each iteration) "
                "and variant functions (monotonically decreasing metrics ensuring termination). Modern compilers unroll and vectorize "
                "loops when iterations are provably independent."
            ),
            "code": (
                "#include <stdio.h>\n\n"
                "int binarySearch(const int arr[], int size, int target) {\n"
                "    int left = 0, right = size - 1;\n"
                "    // Invariant: If target exists, target is in arr[left..right]\n"
                "    while (left <= right) {\n"
                "        int mid = left + (right - left) / 2; // Prevents overflow\n"
                "        if (arr[mid] == target) return mid;\n"
                "        if (arr[mid] < target) left = mid + 1;\n"
                "        else right = mid - 1;\n"
                "    }\n"
                "    return -1;\n"
                "}\n\n"
                "int main(void) {\n"
                "    int sorted[6] = {2, 5, 8, 12, 16, 23};\n"
                "    printf(\"Index of 12: %d\\n\", binarySearch(sorted, 6, 12));\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "Invariant: Target is bounded within arr[left..right].",
                "mid = left + (right - left) / 2: Avoids integer overflow associated with (left + right) / 2.",
                "Variant metric: (right - left + 1) strictly decreases every iteration, proving termination.",
            ],
            "mistakes": [
                "Integer overflow bug in midpoint calculation with large arrays.",
                "Failing to update boundary bounds by +/- 1, causing infinite loops.",
            ],
            "check": {
                "question": "Why is `mid = left + (right - left) / 2` preferred over `(left + right) / 2`?",
                "code_snippet": "int mid = left + (right - left) / 2;",
                "options": [
                    "A) It avoids potential integer overflow when left + right exceeds INT_MAX",
                    "B) It runs in fewer CPU cycles",
                    "C) It allows floating point division",
                    "D) It handles negative numbers automatically",
                ],
                "correct_option": "A",
                "correct_answer": "A",
                "explanation": "If left and right are large positive integers, `left + right` can overflow `INT_MAX`; the subtraction formula prevents this.",
            },
        },
    },
    "Conditionals": {
        "Beginner": {
            "objective": "Understand boolean logic, if-else decision branching, and relational comparisons in C.",
            "explanation": (
                "In C, decision making relies on conditional statements. Expressions evaluate to either non-zero (True) "
                "or 0 (False). The `if` statement executes its code block only when the condition is true; otherwise, "
                "the `else` block executes."
            ),
            "code": (
                "#include <stdio.h>\n\n"
                "int main(void) {\n"
                "    int score = 75;\n"
                "    if (score >= 50) {\n"
                "        printf(\"Result: Passed (Score: %d)\\n\", score);\n"
                "    } else {\n"
                "        printf(\"Result: Failed (Score: %d)\\n\", score);\n"
                "    }\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "score >= 50: Relational test evaluating to non-zero (True) since 75 >= 50.",
                "Executes if block and skips else block.",
            ],
            "mistakes": [
                "Using assignment '=' instead of equality '==' inside condition: `if (score = 50)` always evaluates to True.",
                "Omitting braces around multi-statement blocks.",
            ],
            "check": {
                "question": "What is printed by: `int x = 0; if (x = 5) printf(\"A\"); else printf(\"B\");`?",
                "code_snippet": "int x = 0;\nif (x = 5) printf(\"A\"); else printf(\"B\");",
                "options": ["A) A (because assignment evaluates to 5 which is non-zero/True)", "B) B", "C) Compilation error", "D) Nothing"],
                "correct_option": "A",
                "correct_answer": "A",
                "explanation": "`x = 5` assigns 5 to x and returns 5. In C, any non-zero integer is treated as True, so branch 'A' executes.",
            },
        },
        "Intermediate": {
            "objective": "Master else-if ladders, switch-case constructs, and boolean short-circuit evaluation in C.",
            "explanation": (
                "Multi-way branching is implemented using `if-else if-else` ladders or `switch-case` statements. "
                "Logical operators (`&&` and `||`) employ short-circuit evaluation: if the left operand determines the outcome, "
                "the right operand is not evaluated."
            ),
            "code": (
                "#include <stdio.h>\n\n"
                "int main(void) {\n"
                "    char grade = 'B';\n"
                "    switch (grade) {\n"
                "        case 'A': printf(\"Excellent\\n\"); break;\n"
                "        case 'B': printf(\"Good\\n\"); break;\n"
                "        case 'C': printf(\"Average\\n\"); break;\n"
                "        default:  printf(\"Needs Improvement\\n\"); break;\n"
                "    }\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "switch (grade): Dispatches directly to matching case.",
                "break: Crucial statement preventing fall-through into subsequent cases.",
                "default: Catch-all branch executed if no cases match.",
            ],
            "mistakes": [
                "Forgetting `break` statements causing unintentional fall-through.",
                "Trying to use switch statements on floating point numbers (switch only works on discrete integral/char types).",
            ],
            "check": {
                "question": "What happens if you omit the `break` statement at the end of a `case` block in a `switch` statement?",
                "code_snippet": "switch (x) { case 1: printf(\"1\"); /* no break */ case 2: printf(\"2\"); }",
                "options": [
                    "A) Compilation error",
                    "B) Execution falls through into the next case regardless of match",
                    "C) The program terminates immediately",
                    "D) The switch statement restarts",
                ],
                "correct_option": "B",
                "correct_answer": "B",
                "explanation": "Without a `break`, execution continues sequentially into the statements of the next case (fall-through behavior).",
            },
        },
        "Advanced": {
            "objective": "Master compiler jump table optimizations, ternary expressions, and short-circuit side-effect safety.",
            "explanation": (
                "Compilers optimize dense `switch-case` statements into jump tables (O(1) direct indexing) rather than O(N) linear comparisons. "
                "Short-circuit evaluation must be handled with care when right-hand expressions contain side effects."
            ),
            "code": (
                "#include <stdio.h>\n\n"
                "int isAuthorized(int role) {\n"
                "    // Ternary operator for concise conditional assignment\n"
                "    return (role >= 10 && role <= 20) ? 1 : 0;\n"
                "}\n\n"
                "int main(void) {\n"
                "    int role = 15;\n"
                "    int auditCount = 0;\n"
                "    // Short-circuit: auditCount++ is NOT evaluated if first condition is false\n"
                "    if (role < 10 && ++auditCount) {\n"
                "        printf(\"Audited\\n\");\n"
                "    }\n"
                "    printf(\"Authorized: %d, Audit Count: %d\\n\", isAuthorized(role), auditCount);\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "Ternary operator: `condition ? val1 : val2` provides concise expression-level branching.",
                "Short-circuit safety: Because `role < 10` is false, `++auditCount` is never executed.",
            ],
            "mistakes": [
                "Relying on side effects (like ++i) inside short-circuited logical expressions.",
                "Assuming switch case tables support non-integral or string comparison types in C.",
            ],
            "check": {
                "question": "What is the value of `count` after: `int count = 0; if (0 && ++count) { }`?",
                "code_snippet": "int count = 0;\nif (0 && ++count) { }",
                "options": ["A) 0 (due to short-circuit evaluation)", "B) 1", "C) -1", "D) Undefined"],
                "correct_option": "A",
                "correct_answer": "A",
                "explanation": "Because the left operand of `&&` evaluates to 0 (False), the right operand `++count` is never evaluated.",
            },
        },
    },
    "Structures": {
        "Beginner": {
            "objective": "Understand user-defined composite data types with struct, member declarations, and dot operator access in C.",
            "explanation": (
                "A `struct` (structure) allows you to group variables of different data types together under a single user-defined type name. "
                "Individual members within a structure are accessed using the dot operator (`.`)."
            ),
            "code": (
                "#include <stdio.h>\n"
                "#include <string.h>\n\n"
                "struct Student {\n"
                "    int id;\n"
                "    char name[20];\n"
                "    float gpa;\n"
                "};\n\n"
                "int main(void) {\n"
                "    struct Student s1;\n"
                "    s1.id = 101;\n"
                "    strcpy(s1.name, \"Alex\");\n"
                "    s1.gpa = 3.85f;\n\n"
                "    printf(\"Student ID: %d, Name: %s, GPA: %.2f\\n\", s1.id, s1.name, s1.gpa);\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "struct Student: Defines composite type containing integer, character array, and float.",
                "s1.id = 101: Accesses member using dot operator.",
                "strcpy(s1.name, \"Alex\"): Copies string into structure array member.",
            ],
            "mistakes": [
                "Forgetting the terminating semicolon after the structure definition (`struct S { ... };`).",
                "Assigning string literals directly to character arrays (`s1.name = \"Alex\"`).",
            ],
            "check": {
                "question": "Which operator is used to access members of a structure variable in C?",
                "code_snippet": "struct Student s1;\n// Access s1 id member",
                "options": ["A) Dot operator (.)", "B) Arrow operator (->)", "C) Colon (:)", "D) Double colon (::)"],
                "correct_option": "A",
                "correct_answer": "A",
                "explanation": "The dot operator (`.`) accesses members of direct structure variables; the arrow operator (`->`) is used with structure pointers.",
            },
        },
        "Intermediate": {
            "objective": "Master pointers to structures, the arrow operator (->), and passing structures to functions by reference.",
            "explanation": (
                "Passing large structures by value copies every member onto the call stack. "
                "Passing a pointer to the structure is vastly more efficient and enables functions to modify structure members "
                "using the arrow operator (`ptr->member`)."
            ),
            "code": (
                "#include <stdio.h>\n\n"
                "typedef struct {\n"
                "    int x;\n"
                "    int y;\n"
                "} Point;\n\n"
                "void translate(Point *p, int dx, int dy) {\n"
                "    p->x += dx;\n"
                "    p->y += dy;\n"
                "}\n\n"
                "int main(void) {\n"
                "    Point pt = {10, 20};\n"
                "    translate(&pt, 5, -3);\n"
                "    printf(\"New Coordinates: (%d, %d)\\n\", pt.x, pt.y);\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "typedef struct Point: Allows using `Point` directly without writing `struct Point` each time.",
                "p->x += dx: Arrow operator is shorthand for `(*p).x`.",
                "translate(&pt, ...): Passes address for efficient in-place modification.",
            ],
            "mistakes": [
                "Using dot operator with a structure pointer (`p.x` instead of `p->x`).",
                "Confusing precedence when writing `*p.x` instead of `(*p).x`.",
            ],
            "check": {
                "question": "What is `ptr->age` semantically equivalent to in C for a structure pointer `ptr`?",
                "code_snippet": "ptr->age",
                "options": ["A) (*ptr).age", "B) *ptr.age", "C) &(ptr.age)", "D) ptr.age"],
                "correct_option": "A",
                "correct_answer": "A",
                "explanation": "The arrow operator `ptr->age` dereferences the pointer first and then accesses the member, exactly identical to `(*ptr).age`.",
            },
        },
        "Advanced": {
            "objective": "Master structure memory alignment, compiler padding bytes, and bitfield configurations in C.",
            "explanation": (
                "CPUs access memory most efficiently at natural word alignment boundaries (e.g. 4-byte boundaries for integers). "
                "Compilers automatically insert unused padding bytes between structure members. As a result, `sizeof(struct)` "
                "is frequently larger than the mathematical sum of its member byte sizes."
            ),
            "code": (
                "#include <stdio.h>\n\n"
                "struct Unaligned {\n"
                "    char a;     // 1 byte + 3 padding bytes\n"
                "    int b;      // 4 bytes\n"
                "    char c;     // 1 byte + 3 padding bytes\n"
                "};              // Total: 12 bytes\n\n"
                "struct Aligned {\n"
                "    int b;      // 4 bytes\n"
                "    char a;     // 1 byte\n"
                "    char c;     // 1 byte + 2 padding bytes\n"
                "};              // Total: 8 bytes\n\n"
                "int main(void) {\n"
                "    printf(\"Unaligned size: %zu bytes\\n\", sizeof(struct Unaligned));\n"
                "    printf(\"Aligned size:   %zu bytes\\n\", sizeof(struct Aligned));\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "struct Unaligned: Placing char between int forces 6 padding bytes total.",
                "struct Aligned: Grouping members by descending size eliminates 4 bytes of padding waste.",
                "sizeof vs member sum: Shows how structure layout affects memory footprints in embedded/system software.",
            ],
            "mistakes": [
                "Assuming structure size equals the simple sum of member sizes.",
                "Writing structures directly to binary files across different compiler architectures without packing guards.",
            ],
            "check": {
                "question": "Why is `sizeof(struct S)` often larger than the sum of its individual member sizes in C?",
                "code_snippet": "struct S { char c; int i; };",
                "options": [
                    "A) Memory corruption",
                    "B) Compiler inserts padding bytes to satisfy hardware word alignment requirements",
                    "C) C adds 8 bytes of metadata to all structs",
                    "D) Structs are stored as linked lists",
                ],
                "correct_option": "B",
                "correct_answer": "B",
                "explanation": "Compilers insert padding bytes so that multi-byte fields (like 4-byte integers) reside at addresses divisible by their natural alignment.",
            },
        },
    },
    "Operators and Expressions": {
        "Beginner": {
            "objective": "Understand arithmetic, relational, and assignment operator precedence and associativity in C.",
            "explanation": (
                "An expression in C combines operands with operators to compute a value. "
                "Operator precedence dictates the order in which operations occur (e.g. multiplication occurs before addition). "
                "Parentheses `()` override standard precedence."
            ),
            "code": (
                "#include <stdio.h>\n\n"
                "int main(void) {\n"
                "    int a = 10, b = 4, c = 2;\n"
                "    int res1 = a + b * c;     // Multiplies b * c first (10 + 8 = 18)\n"
                "    int res2 = (a + b) * c;   // Evaluates parentheses first (14 * 2 = 28)\n\n"
                "    printf(\"Standard precedence: %d\\n\", res1);\n"
                "    printf(\"Parentheses override: %d\\n\", res2);\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "a + b * c: Multiplication has higher precedence than addition.",
                "(a + b) * c: Parentheses force addition to evaluate first.",
            ],
            "mistakes": [
                "Expecting integer division `1 / 2` to yield 0.5 (in C, integer division truncates to 0).",
                "Confusing assignment `=` with equality `==`.",
            ],
            "check": {
                "question": "What is the value of integer expression `7 / 2` in C?",
                "code_snippet": "int result = 7 / 2;",
                "options": ["A) 3.5", "B) 3 (integer division truncates decimal part)", "C) 4", "D) Compilation error"],
                "correct_option": "B",
                "correct_answer": "B",
                "explanation": "When both operands of division are integers, C truncates the fractional portion, returning 3.",
            },
        },
        "Intermediate": {
            "objective": "Master implicit type conversion, explicit type casting, and prefix vs postfix increment operators.",
            "explanation": (
                "Type casting converts values between compatible datatypes. Prefix increment (`++i`) increments the variable "
                "before using its value in an expression, whereas postfix increment (`i++`) yields the original value before incrementing."
            ),
            "code": (
                "#include <stdio.h>\n\n"
                "int main(void) {\n"
                "    int a = 7, b = 2;\n"
                "    double accurateDiv = (double)a / b; // Explicit cast to double\n\n"
                "    int x = 5;\n"
                "    int post = x++; // post = 5, x becomes 6\n"
                "    int pre = ++x;  // x becomes 7, pre = 7\n\n"
                "    printf(\"Accurate division: %.2f\\n\", accurateDiv);\n"
                "    printf(\"post: %d, pre: %d, final x: %d\\n\", post, pre, x);\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "(double)a / b: Casts variable a to double so standard floating-point division occurs.",
                "x++: Postfix returns original value then increments.",
                "++x: Prefix increments then returns updated value.",
            ],
            "mistakes": [
                "Casting after division `(double)(a / b)` which truncates before conversion.",
                "Modifying a variable multiple times in a single unsequenced expression (`i = i++ + ++i`), which is undefined behavior.",
            ],
            "check": {
                "question": "What is the result of `(double)(5 / 2)` in C?",
                "code_snippet": "double val = (double)(5 / 2);",
                "options": ["A) 2.5", "B) 2.0 (integer division occurs inside parentheses first)", "C) 2", "D) Compilation error"],
                "correct_option": "B",
                "correct_answer": "B",
                "explanation": "`5 / 2` evaluates first as integer division (2), and casting 2 to double produces 2.0.",
            },
        },
        "Advanced": {
            "objective": "Master bitwise operators, bitmasking, and bit-level flag register manipulation in C.",
            "explanation": (
                "Bitwise operators (`&`, `|`, `^`, `~`, `<<`, `>>`) manipulate individual bits directly. "
                "Bit manipulation is fundamental for embedded hardware registers, network packet protocols, and high-speed hashing."
            ),
            "code": (
                "#include <stdio.h>\n\n"
                "#define FLAG_READ   (1 << 0) // Bit 0 (0x01)\n"
                "#define FLAG_WRITE  (1 << 1) // Bit 1 (0x02)\n"
                "#define FLAG_EXEC   (1 << 2) // Bit 2 (0x04)\n\n"
                "int main(void) {\n"
                "    unsigned char permissions = 0;\n\n"
                "    // Setting bits (OR)\n"
                "    permissions |= (FLAG_READ | FLAG_WRITE);\n\n"
                "    // Testing bits (AND)\n"
                "    if (permissions & FLAG_READ) printf(\"Read enabled\\n\");\n"
                "    if (permissions & FLAG_EXEC) printf(\"Exec enabled\\n\");\n"
                "    else printf(\"Exec disabled\\n\");\n\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "1 << bit: Shifts 1 into target bit position.",
                "permissions |= FLAG: Sets specific bit high without disturbing other bits.",
                "permissions & FLAG: Masks and verifies whether target bit is set.",
            ],
            "mistakes": [
                "Confusing bitwise `&` with logical `&&`.",
                "Shifting by a negative count or by more bits than the datatype width (undefined behavior).",
            ],
            "check": {
                "question": "What is the bitwise operation used to set the 3rd bit of an integer `x` without altering other bits?",
                "code_snippet": "// Set 3rd bit of x",
                "options": ["A) x = x & (1 << 3)", "B) x = x | (1 << 3)", "C) x = x ^ (1 << 3)", "D) x = x >> 3"],
                "correct_option": "B",
                "correct_answer": "B",
                "explanation": "Bitwise OR (`|`) with mask `(1 << 3)` sets bit 3 high while leaving all other bits unchanged.",
            },
        },
    },
    "Variables and Data Types": {
        "Beginner": {
            "objective": "Understand basic data types (char, int, float, double), variable declarations, and memory allocation in C.",
            "explanation": (
                "A variable is a named storage location in computer memory. Every variable must be declared with a data type "
                "that tells the compiler how much memory to reserve and how to interpret the binary bits.\n\n"
                "Standard C primitive types include `char` (1 byte, characters/small numbers), `int` (4 bytes, whole numbers), "
                "`float` (4 bytes, single-precision decimals), and `double` (8 bytes, high-precision decimals)."
            ),
            "code": (
                "#include <stdio.h>\n\n"
                "int main(void) {\n"
                "    char letter = 'A';\n"
                "    int count = 42;\n"
                "    float price = 19.99f;\n"
                "    double pi = 3.1415926535;\n\n"
                "    printf(\"char: %c (Size: %zu byte)\\n\", letter, sizeof(letter));\n"
                "    printf(\"int: %d (Size: %zu bytes)\\n\", count, sizeof(count));\n"
                "    printf(\"float: %.2f (Size: %zu bytes)\\n\", price, sizeof(price));\n"
                "    printf(\"double: %.10f (Size: %zu bytes)\\n\", pi, sizeof(pi));\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "char letter = 'A': Allocates 1 byte storing ASCII 65.",
                "int count = 42: Allocates 4 bytes storing signed integer.",
                "sizeof operator: Queries exact byte footprint from the compiler.",
            ],
            "mistakes": [
                "Using double quotes for characters (`char c = \"A\"` instead of `'A'`).",
                "Using variables before declaring them.",
            ],
            "check": {
                "question": "What is the memory size guaranteed for a standard `char` in C?",
                "code_snippet": "char c = 'Z';\nprintf(\"%zu\\n\", sizeof(c));",
                "options": ["A) Exactly 1 byte", "B) 2 bytes", "C) 4 bytes", "D) Depends on processor"],
                "correct_option": "A",
                "correct_answer": "A",
                "explanation": "The C standard specifies that `sizeof(char)` is always exactly 1 byte.",
            },
        },
        "Intermediate": {
            "objective": "Master type modifiers (signed, unsigned, short, long) and integer overflow boundaries in C.",
            "explanation": (
                "Type modifiers adjust integer capacities and sign representations. An `unsigned int` uses all 32 bits "
                "for magnitude (0 to 4,294,967,295), whereas a signed `int` reserves the leading bit for positive/negative signs."
            ),
            "code": (
                "#include <stdio.h>\n"
                "#include <limits.h>\n\n"
                "int main(void) {\n"
                "    signed int maxInt = INT_MAX;\n"
                "    unsigned int uMax = UINT_MAX;\n\n"
                "    printf(\"Signed int max:   %d\\n\", maxInt);\n"
                "    printf(\"Unsigned int max: %u\\n\", uMax);\n\n"
                "    // Demonstrating unsigned modular wraparound\n"
                "    unsigned int wrap = uMax + 1;\n"
                "    printf(\"Unsigned wraparound (UINT_MAX + 1): %u\\n\", wrap);\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "INT_MAX: Defined in `<limits.h>` as 2,147,483,647.",
                "UINT_MAX + 1: Unsigned integers are defined by the C standard to wrap around modulo 2^N to 0.",
            ],
            "mistakes": [
                "Signed integer overflow is undefined behavior (unlike unsigned modular wraparound).",
                "Comparing signed and unsigned variables with `<` or `>`, causing implicit promotion bugs.",
            ],
            "check": {
                "question": "What does an unsigned integer evaluate to if incremented past its maximum value in C?",
                "code_snippet": "unsigned int x = UINT_MAX;\nx = x + 1;",
                "options": ["A) 0 (modular arithmetic wraparound)", "B) Negative number", "C) Runtime crash", "D) INT_MAX"],
                "correct_option": "A",
                "correct_answer": "A",
                "explanation": "The C standard defines unsigned arithmetic as modular (modulo 2^N), so `UINT_MAX + 1` wraps around cleanly to 0.",
            },
        },
        "Advanced": {
            "objective": "Master storage classes (auto, static, extern, register), linkage, and memory variable lifecycles.",
            "explanation": (
                "Storage classes define variable scope, lifetime, and linkage across translation units. "
                "A `static` local variable persists in the data/BSS segment across function calls, preserving state between invocations."
            ),
            "code": (
                "#include <stdio.h>\n\n"
                "void countCalls(void) {\n"
                "    // Static variable initialized once, persists throughout program execution\n"
                "    static int callCount = 0;\n"
                "    int localCount = 0; // Automatic stack variable\n\n"
                "    callCount++;\n"
                "    localCount++;\n\n"
                "    printf(\"static callCount=%d, auto localCount=%d\\n\", callCount, localCount);\n"
                "}\n\n"
                "int main(void) {\n"
                "    countCalls();\n"
                "    countCalls();\n"
                "    countCalls();\n"
                "    return 0;\n"
                "}"
            ),
            "walkthrough": [
                "static int callCount = 0: Allocated in data segment; retains value between function calls.",
                "int localCount = 0: Recreated and destroyed on the stack each invocation.",
                "Consecutive calls show callCount incrementing (1, 2, 3) while localCount remains 1.",
            ],
            "mistakes": [
                "Assuming static local variables are reinitialized each time a function is called.",
                "Using `extern` without matching definition in another translation unit.",
            ],
            "check": {
                "question": "What is the value of `callCount` on the third invocation of `countCalls()`?",
                "code_snippet": "void countCalls() { static int callCount = 0; callCount++; }",
                "options": ["A) 1", "B) 3", "C) 0", "D) Undefined"],
                "correct_option": "B",
                "correct_answer": "B",
                "explanation": "Static variables retain their values between function calls throughout program execution, reaching 3 on the third call.",
            },
        },
    },
}


def _get_defaults_for_topic(topic: str, mastery_tier: str = "Beginner") -> Dict[str, Any]:
    """Retrieve grounded topic defaults adapted to student mastery tier."""
    norm_topic = normalize_topic_name(topic)
    tier = (mastery_tier or "Beginner").strip().capitalize()
    if tier not in ("Beginner", "Intermediate", "Advanced"):
        tier = "Beginner"

    topic_dict = TOPIC_GROUNDED_DEFAULTS.get(norm_topic, TOPIC_GROUNDED_DEFAULTS["Pointers"])
    tier_data = topic_dict.get(tier, topic_dict.get("Beginner", TOPIC_GROUNDED_DEFAULTS["Pointers"]["Beginner"]))

    result = dict(tier_data)
    if "check" in result:
        chk = dict(result["check"])
        if "correct_answer" not in chk and "correct_option" in chk:
            chk["correct_answer"] = chk["correct_option"]
        result["check"] = chk
    return result


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
        mastery_tier: str = "Beginner",
    ) -> TeachingResponse:
        """Parse raw LLM output into a standardized, fully structured TeachingResponse."""
        summary = personalization_summary or {}
        tier = summary.get("mastery_tier") or mastery_tier or "Beginner"
        norm_topic = normalize_topic_name(topic)
        defaults = _get_defaults_for_topic(norm_topic, tier)

        if not raw_text or not raw_text.strip():
            default_diag = {
                "is_valid": True,
                "diagram_type": diagram_type,
                "mermaid_code": get_topic_default_mermaid(norm_topic, tier),
                "title": f"{norm_topic} Architecture Diagram",
                "explanation": f"Visual representation of {norm_topic} mechanics and flow.",
                "validation_error": None,
            }
            return TeachingResponse(
                learning_objective=defaults["objective"],
                explanation=defaults["explanation"],
                c_code=defaults["code"],
                visual_diagram=default_diag,
                diagram=default_diag,
                diagrams=[default_diag],
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
            return cls._build_from_json(json_obj, text, norm_topic, diagram_type, summary, tier)

        # 3. Structured Markdown parsing
        return cls._build_from_markdown(text, norm_topic, diagram_type, summary, tier)

    @classmethod
    def _try_parse_json(cls, text: str) -> Optional[Dict[str, Any]]:
        """Try parsing JSON from code blocks or raw string."""
        json_block_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
        candidate = json_block_match.group(1).strip() if json_block_match else text

        if candidate.startswith("{") and candidate.endswith("}"):
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict) and ("learning_objective" in parsed or "explanation" in parsed):
                    return parsed
            except Exception:
                pass

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
        mastery_tier: str = "Beginner",
    ) -> TeachingResponse:
        """Construct TeachingResponse from validated JSON dictionary."""
        defaults = _get_defaults_for_topic(topic, mastery_tier)

        objective = str(data.get("learning_objective") or defaults["objective"]).strip()
        explanation = str(data.get("explanation") or data.get("conceptual_explanation") or defaults["explanation"]).strip()
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

        c_code = re.sub(r"^```(?:c|C)?\s*\n", "", c_code).strip()
        c_code = re.sub(r"```$", "", c_code).strip()
        c_code = c_code.replace("NOT_EXECUTED_UNTRUSTED", "Educational C Reference")

        # Extract Diagram
        diag_raw = data.get("diagram") or data.get("visual_diagram") or data.get("mermaid")
        diag_code = ""
        if isinstance(diag_raw, dict):
            diag_code = str(diag_raw.get("mermaid_code") or diag_raw.get("code") or "")
        elif isinstance(diag_raw, str):
            diag_code = diag_raw

        if not diag_code:
            diag_code = MermaidValidator.extract_mermaid_code(raw_text) or ""

        diag_res = MermaidValidator.validate_and_sanitize(diag_code, topic=topic, diagram_type=diagram_type, mastery_tier=mastery_tier)
        if not diag_res.is_valid or not diag_res.mermaid_code:
            diag_dict = {
                "is_valid": True,
                "diagram_type": diagram_type,
                "mermaid_code": get_topic_default_mermaid(topic, mastery_tier=mastery_tier),
                "title": f"{topic} Architecture Diagram",
                "explanation": f"Visual representation of {topic} mechanics and flow.",
                "validation_error": None,
            }
        else:
            diag_dict = diag_res.to_dict()

        # Multi-diagram support
        all_blocks: List[str] = MermaidValidator.extract_all_mermaid_blocks(raw_text)
        if not all_blocks and diag_code and diag_code.strip():
            all_blocks = [diag_code.strip()]

        multi_res = MermaidValidator.validate_and_sanitize_all(all_blocks, topic=topic, diagram_type=diagram_type, mastery_tier=mastery_tier)
        diagrams_list = []
        for r in multi_res:
            if not r.is_valid or not r.mermaid_code:
                diagrams_list.append({
                    "is_valid": True,
                    "diagram_type": diagram_type,
                    "mermaid_code": get_topic_default_mermaid(topic, mastery_tier=mastery_tier),
                    "title": r.title or f"{topic} Architecture Diagram",
                    "explanation": f"Visual representation of {topic} mechanics and flow.",
                    "validation_error": None,
                })
            else:
                diagrams_list.append(r.to_dict())

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
        mastery_tier: str = "Beginner",
    ) -> TeachingResponse:
        """Construct structured TeachingResponse by cleanly isolating each markdown section."""
        defaults = _get_defaults_for_topic(topic, mastery_tier)

        # 1. Objective extraction
        obj_match = re.search(
            r"###?\s*Learning Objective[s]?\s*([^\n#]+)",
            text,
            re.IGNORECASE,
        )
        objective = obj_match.group(1).strip().strip("*`") if obj_match else defaults["objective"]

        # 2. Extract C code block using robust scanner
        c_code = extract_c_code(text) or defaults["code"]
        c_code = re.sub(r"^```(?:c|C)?\s*\n", "", c_code).strip()
        c_code = re.sub(r"```$", "", c_code).strip()
        c_code = c_code.replace("NOT_EXECUTED_UNTRUSTED", "Educational C Reference")

        # 3. Extract Mermaid diagram
        diag_code = MermaidValidator.extract_mermaid_code(text)
        diag_res = MermaidValidator.validate_and_sanitize(diag_code, topic=topic, diagram_type=diagram_type, mastery_tier=mastery_tier)
        if not diag_res.is_valid or not diag_res.mermaid_code:
            diag_dict = {
                "is_valid": True,
                "diagram_type": diagram_type,
                "mermaid_code": get_topic_default_mermaid(topic, mastery_tier=mastery_tier),
                "title": f"{topic} Architecture Diagram",
                "explanation": f"Visual representation of {topic} mechanics and flow.",
                "validation_error": None,
            }
        else:
            diag_dict = diag_res.to_dict()

        # Multi-diagram extraction
        all_blocks: List[str] = MermaidValidator.extract_all_mermaid_blocks(text)
        if not all_blocks and diag_code and diag_code.strip():
            all_blocks = [diag_code.strip()]

        multi_res = MermaidValidator.validate_and_sanitize_all(all_blocks, topic=topic, diagram_type=diagram_type, mastery_tier=mastery_tier)
        diagrams_list = []
        for r in multi_res:
            if not r.is_valid or not r.mermaid_code:
                diagrams_list.append({
                    "is_valid": True,
                    "diagram_type": diagram_type,
                    "mermaid_code": get_topic_default_mermaid(topic, mastery_tier=mastery_tier),
                    "title": r.title or f"{topic} Architecture Diagram",
                    "explanation": f"Visual representation of {topic} mechanics and flow.",
                    "validation_error": None,
                })
            else:
                diagrams_list.append(r.to_dict())

        # 4. Extract Conceptual Explanation
        exp_match = re.search(
            r"###?\s*Conceptual Explanation\s*([\s\S]*?)(?=###?\s*Visual Architecture|###?\s*C Code Implementation|###?\s*Step-by-Step|\Z)",
            text,
            re.IGNORECASE,
        )
        if exp_match:
            raw_exp = exp_match.group(1).strip()
            raw_exp = re.sub(r"```(?:c|C|mermaid|json)?[\s\S]*?```", "", raw_exp).strip()
            explanation = raw_exp if len(raw_exp) > 20 else defaults["explanation"]
        else:
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
                    "correct_option": "B",
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
        Provides accurate, runnable topic-specific fallback challenges for all 10 topics.
        """
        text = raw_text.strip() if raw_text else ""
        norm_topic = normalize_topic_name(topic)

        # 1. Title
        title_match = re.search(r"###?\s*Title:?\s*([^\n]+)", text, re.IGNORECASE)
        if not title_match:
            title_match = re.search(r"(?:###?|Challenge:?|Exercise\s*2:?)\s*([^\n#]+)", text, re.IGNORECASE)
        title = title_match.group(1).strip().strip("*`") if title_match else f"{norm_topic}: Adaptive C Coding Challenge"

        # 2. Extract C code blocks
        code_blocks = re.findall(r"```(?:c|C)?\s*\n([\s\S]*?)```", text)
        starter_code = ""
        if code_blocks:
            main_blocks = [b.strip() for b in code_blocks if "main" in b]
            starter_code = main_blocks[-1] if main_blocks else code_blocks[-1].strip()

        # 3. Problem Statement / Description
        desc_match = re.search(
            r"###?\s*Problem Statement:?\s*([\s\S]*?)(?=###?\s*Starter Code|###?\s*Expected Output|###?\s*Hint Ladder|\Z)",
            text,
            re.IGNORECASE,
        )
        problem_statement = ""
        if desc_match:
            raw_desc = desc_match.group(1).strip()
            desc_lines = []
            for line in raw_desc.splitlines():
                if not re.match(r"^\s*[-*]\s*\*\*(?:Input|Output|Constraints|Sample|Explanation)", line):
                    desc_lines.append(line)
            problem_statement = "\n".join(desc_lines).strip()
        elif text:
            parts = re.split(r"```", text, maxsplit=1)
            problem_statement = parts[0].strip() if parts else ""

        # 4. Specifications
        def _extract_field(pattern: str, default: str) -> str:
            m = re.search(pattern, text, re.IGNORECASE)
            return m.group(1).strip().strip("*`") if m else default

        input_format = _extract_field(
            r"(?:[-*]\s*)?\*\*Input Format\*\*:?\s*([^\n#]+)",
            "",
        )
        output_format = _extract_field(
            r"(?:[-*]\s*)?\*\*Output Format\*\*:?\s*([^\n#]+)",
            "",
        )
        constraints = _extract_field(
            r"(?:[-*]\s*)?\*\*Constraints\*\*:?\s*([^\n#]+)",
            "",
        )
        sample_input = _extract_field(
            r"(?:[-*]\s*)?\*\*Sample Input\*\*:?\s*([^\n#]+)",
            "",
        )
        sample_output = _extract_field(
            r"(?:[-*]\s*)?\*\*Sample Output\*\*:?\s*([^\n#]+)",
            "",
        )
        sample_explanation = _extract_field(
            r"(?:[-*]\s*)?\*\*Explanation\*\*:?\s*([^\n#]+)",
            "",
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

        # Clean filler text from sample input/output
        if "configured in main" in sample_input.lower() or "test harness" in sample_input.lower():
            sample_input = ""
        if "printed via printf" in sample_output.lower():
            sample_output = ""
        if "printed via printf" in expected_output.lower():
            expected_output = ""

        # 6. Topic-specific robust defaults
        topic_defaults = _get_challenge_defaults(norm_topic)
        if not starter_code:
            starter_code = topic_defaults["starter_code"]
        if not problem_statement:
            problem_statement = topic_defaults["problem_statement"]
        if not input_format:
            input_format = topic_defaults["input_format"]
        if not output_format:
            output_format = topic_defaults["output_format"]
        if not constraints:
            constraints = topic_defaults["constraints"]
        if not sample_input:
            sample_input = topic_defaults["sample_input"]
        if not sample_output or not expected_output:
            sample_output = topic_defaults["sample_output"]
            expected_output = topic_defaults["expected_output"]
        if not sample_explanation:
            sample_explanation = topic_defaults["sample_explanation"]

        # 7. Hint Ladder
        hints: List[str] = []
        hint_matches = re.findall(
            r"(?:[-*]\s*)?\*\*Hint\s*\d[^:]*\*\*:?\s*([^\n]+)",
            text,
            re.IGNORECASE,
        )
        if hint_matches:
            hints = [h.strip().strip("*`") for h in hint_matches if h.strip()]

        fallback_hints = [
            f"Review the foundational concepts of {norm_topic} in C and examine how memory/variables are structured.",
            f"Identify the key operations needed for {norm_topic} and map out your variable declarations and pointers.",
            f"Trace the logic step-by-step to handle boundary conditions and verify the data flow.",
            f"Write the implementation using the provided starter function signature and verify return/output values.",
        ]
        topic_hints = topic_defaults.get("hints", [])
        for h in topic_hints:
            if h and h not in hints and len(hints) < 4:
                hints.append(h)
        for h in fallback_hints:
            if len(hints) < 4 and h not in hints:
                hints.append(h)

        return {
            "title": title,
            "topic": norm_topic,
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


def _get_challenge_defaults(topic: str) -> Dict[str, Any]:
    """Provide verified, runnable coding challenge specifications for each PPS topic."""
    norm = normalize_topic_name(topic)

    if norm == "Dynamic Memory Allocation":
        return {
            "problem_statement": (
                "Write a C program that dynamically allocates memory on the heap for an array of integers using `malloc()`.\n"
                "The program must first read an integer `size` indicating the number of elements.\n"
                "Next, read `size` integers into the dynamically allocated array.\n"
                "Print the elements separated by a space followed by a newline.\n"
                "Finally, release the allocated memory using `free()`."
            ),
            "input_format": "An integer `size` followed by `size` space-separated integers on standard input.",
            "output_format": "The array elements separated by a single space.",
            "constraints": "1 <= size <= 1000; valid C99; NULL check guard; free memory before return.",
            "sample_input": "5\n10 20 30 40 50",
            "sample_output": "10 20 30 40 50",
            "expected_output": "10 20 30 40 50",
            "sample_explanation": "Memory for 5 integers is allocated on the heap, filled with the 5 numbers, printed, and freed.",
            "starter_code": (
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n\n"
                "void createArray(int *array, int size);\n"
                "void printArray(int *array, int size);\n\n"
                "int main(void) {\n"
                "    int size;\n"
                "    if (scanf(\"%d\", &size) != 1 || size <= 0) {\n"
                "        return 0;\n"
                "    }\n\n"
                "    int *array = (int *)malloc(size * sizeof(int));\n"
                "    if (array == NULL) {\n"
                "        return 1;\n"
                "    }\n\n"
                "    createArray(array, size);\n"
                "    printArray(array, size);\n\n"
                "    free(array);\n"
                "    return 0;\n"
                "}\n\n"
                "void createArray(int *array, int size) {\n"
                "    for (int i = 0; i < size; i++) {\n"
                "        scanf(\"%d\", &array[i]);\n"
                "    }\n"
                "}\n\n"
                "void printArray(int *array, int size) {\n"
                "    for (int i = 0; i < size; i++) {\n"
                "        printf(\"%d%s\", array[i], (i == size - 1) ? \"\" : \" \");\n"
                "    }\n"
                "    printf(\"\\n\");\n"
                "}"
            ),
            "hints": [
                "Use `malloc(size * sizeof(int))` to request contiguous memory on the heap.",
                "Always check `if (array == NULL)` before accessing the allocated memory.",
                "Read the integers into `array[i]` using standard subscript or pointer arithmetic.",
                "Do not forget to call `free(array)` at the end to avoid memory leaks.",
            ],
        }

    elif norm == "Pointers":
        return {
            "problem_statement": (
                "Write a C program that swaps the values of two integers using pointers and a helper function `swap(int *a, int *b)`.\n"
                "Read two integers from standard input, swap their values using their memory addresses, and print the swapped values."
            ),
            "input_format": "Two space-separated integers on standard input.",
            "output_format": "The two integers swapped, separated by a space.",
            "constraints": "Standard C99; mutation must occur through pointer dereferencing.",
            "sample_input": "15 27",
            "sample_output": "27 15",
            "expected_output": "27 15",
            "sample_explanation": "The addresses of 15 and 27 are passed to swap(), exchanging their values in-place.",
            "starter_code": (
                "#include <stdio.h>\n\n"
                "void swap(int *a, int *b) {\n"
                "    int temp = *a;\n"
                "    *a = *b;\n"
                "    *b = temp;\n"
                "}\n\n"
                "int main(void) {\n"
                "    int x, y;\n"
                "    if (scanf(\"%d %d\", &x, &y) == 2) {\n"
                "        swap(&x, &y);\n"
                "        printf(\"%d %d\\n\", x, y);\n"
                "    }\n"
                "    return 0;\n"
                "}"
            ),
            "hints": [
                "Pass the memory addresses of x and y using the `&` operator: `swap(&x, &y)`.",
                "In the swap function, dereference the pointers using `*a` and `*b`.",
                "Use an intermediate temporary variable `int temp = *a;` to hold the value during exchange.",
                "Print the final values separated by a space.",
            ],
        }

    elif norm == "Strings":
        return {
            "problem_statement": (
                "Write a C program that reads a string (up to 100 characters) and prints it reversed.\n"
                "You must respect the terminating null character `'\\0'`."
            ),
            "input_format": "A single-word string on standard input.",
            "output_format": "The reversed string printed to standard output.",
            "constraints": "Max length 100 characters; proper null termination.",
            "sample_input": "hello",
            "sample_output": "olleh",
            "expected_output": "olleh",
            "sample_explanation": "The characters of 'hello' are printed from index 4 down to 0.",
            "starter_code": (
                "#include <stdio.h>\n"
                "#include <string.h>\n\n"
                "int main(void) {\n"
                "    char str[128];\n"
                "    if (scanf(\"%127s\", str) == 1) {\n"
                "        int len = strlen(str);\n"
                "        for (int i = len - 1; i >= 0; i--) {\n"
                "            putchar(str[i]);\n"
                "        }\n"
                "        putchar('\\n');\n"
                "    }\n"
                "    return 0;\n"
                "}"
            ),
            "hints": [
                "Find the length of the string using `strlen(str)`.",
                "Start iterating backwards from `len - 1` down to `0`.",
                "Print each character using `putchar()` or `printf(\"%c\", str[i])`.",
                "Print a trailing newline `\\n` after the reversed string.",
            ],
        }

    elif norm == "Arrays":
        return {
            "problem_statement": (
                "Write a C program that reads an integer `N`, followed by `N` integers into an array.\n"
                "Find and print the maximum integer element in the array."
            ),
            "input_format": "An integer N, followed by N space-separated integers.",
            "output_format": "The maximum integer in the array.",
            "constraints": "1 <= N <= 100; standard C99.",
            "sample_input": "5\n12 45 7 89 23",
            "sample_output": "89",
            "expected_output": "89",
            "sample_explanation": "Among the 5 integers {12, 45, 7, 89, 23}, 89 is the largest.",
            "starter_code": (
                "#include <stdio.h>\n\n"
                "int main(void) {\n"
                "    int n;\n"
                "    if (scanf(\"%d\", &n) != 1 || n <= 0) return 0;\n"
                "    int arr[128];\n"
                "    for (int i = 0; i < n; i++) scanf(\"%d\", &arr[i]);\n\n"
                "    int maxVal = arr[0];\n"
                "    for (int i = 1; i < n; i++) {\n"
                "        if (arr[i] > maxVal) maxVal = arr[i];\n"
                "    }\n"
                "    printf(\"%d\\n\", maxVal);\n"
                "    return 0;\n"
                "}"
            ),
            "hints": [
                "Initialize `maxVal = arr[0]` with the first element of the array.",
                "Loop from index 1 to N - 1.",
                "Whenever `arr[i] > maxVal`, update `maxVal = arr[i]`.",
                "Print the final `maxVal` followed by a newline.",
            ],
        }

    elif norm == "Functions":
        return {
            "problem_statement": (
                "Write a C program that computes the factorial of an integer `N` using a recursive function `factorial(int n)`.\n"
                "Read N from standard input and print `N!`."
            ),
            "input_format": "A single non-negative integer N (0 <= N <= 12).",
            "output_format": "The factorial of N.",
            "constraints": "Use a recursive function; 0 <= N <= 12.",
            "sample_input": "5",
            "sample_output": "120",
            "expected_output": "120",
            "sample_explanation": "5! = 5 * 4 * 3 * 2 * 1 = 120.",
            "starter_code": (
                "#include <stdio.h>\n\n"
                "long long factorial(int n) {\n"
                "    if (n <= 1) return 1;\n"
                "    return n * factorial(n - 1);\n"
                "}\n\n"
                "int main(void) {\n"
                "    int n;\n"
                "    if (scanf(\"%d\", &n) == 1 && n >= 0) {\n"
                "        printf(\"%lld\\n\", factorial(n));\n"
                "    }\n"
                "    return 0;\n"
                "}"
            ),
            "hints": [
                "Define base case: if `n <= 1`, return `1`.",
                "In recursive step, return `n * factorial(n - 1)`.",
                "Use `long long` for return type to handle larger factorial values.",
            ],
        }

    elif norm == "Loops":
        return {
            "problem_statement": (
                "Write a C program that reads an integer `N` and computes the sum of the first N natural numbers (1 to N) using a loop."
            ),
            "input_format": "A single positive integer N.",
            "output_format": "The total sum.",
            "constraints": "1 <= N <= 1000.",
            "sample_input": "5",
            "sample_output": "15",
            "expected_output": "15",
            "sample_explanation": "1 + 2 + 3 + 4 + 5 = 15.",
            "starter_code": (
                "#include <stdio.h>\n\n"
                "int main(void) {\n"
                "    int n;\n"
                "    if (scanf(\"%d\", &n) != 1 || n <= 0) return 0;\n"
                "    int sum = 0;\n"
                "    for (int i = 1; i <= n; i++) {\n"
                "        sum += i;\n"
                "    }\n"
                "    printf(\"%d\\n\", sum);\n"
                "    return 0;\n"
                "}"
            ),
            "hints": [
                "Initialize `int sum = 0;` before entering the loop.",
                "Iterate from `i = 1` up to and including `n`.",
                "Add `i` to `sum` in each iteration: `sum += i;`.",
            ],
        }

    elif norm == "Conditionals":
        return {
            "problem_statement": (
                "Write a C program that reads an integer and prints 'Positive', 'Negative', or 'Zero' depending on its value."
            ),
            "input_format": "A single integer on standard input.",
            "output_format": "'Positive', 'Negative', or 'Zero'.",
            "constraints": "Standard C99 if-else construct.",
            "sample_input": "-7",
            "sample_output": "Negative",
            "expected_output": "Negative",
            "sample_explanation": "-7 is less than zero, so 'Negative' is printed.",
            "starter_code": (
                "#include <stdio.h>\n\n"
                "int main(void) {\n"
                "    int num;\n"
                "    if (scanf(\"%d\", &num) == 1) {\n"
                "        if (num > 0) printf(\"Positive\\n\");\n"
                "        else if (num < 0) printf(\"Negative\\n\");\n"
                "        else printf(\"Zero\\n\");\n"
                "    }\n"
                "    return 0;\n"
                "}"
            ),
            "hints": [
                "Use `if (num > 0)` for positive numbers.",
                "Use `else if (num < 0)` for negative numbers.",
                "Use `else` for zero.",
            ],
        }

    elif norm == "Structures":
        return {
            "problem_statement": (
                "Define a structure `struct Student` with fields `int id` and `int marks`.\n"
                "Read `id` and `marks` from standard input, store them in a structure variable, and print them formatted as `ID: <id>, Marks: <marks>`."
            ),
            "input_format": "Two space-separated integers: id and marks.",
            "output_format": "Formatted string: ID: <id>, Marks: <marks>",
            "constraints": "Standard C99 struct definition.",
            "sample_input": "101 95",
            "sample_output": "ID: 101, Marks: 95",
            "expected_output": "ID: 101, Marks: 95",
            "sample_explanation": "Structure members are populated with 101 and 95 and printed.",
            "starter_code": (
                "#include <stdio.h>\n\n"
                "struct Student {\n"
                "    int id;\n"
                "    int marks;\n"
                "};\n\n"
                "int main(void) {\n"
                "    struct Student s;\n"
                "    if (scanf(\"%d %d\", &s.id, &s.marks) == 2) {\n"
                "        printf(\"ID: %d, Marks: %d\\n\", s.id, s.marks);\n"
                "    }\n"
                "    return 0;\n"
                "}"
            ),
            "hints": [
                "Declare `struct Student { int id; int marks; };` before `main()`.",
                "Access structure fields using the dot operator: `s.id` and `s.marks`.",
                "Print the exact formatted output: `ID: %d, Marks: %d\\n`.",
            ],
        }

    elif norm == "Operators and Expressions":
        return {
            "problem_statement": (
                "Write a C program that reads three integers `a`, `b`, and `c` and evaluates the expression `(a + b) * c`.\n"
                "Print the integer result."
            ),
            "input_format": "Three space-separated integers.",
            "output_format": "The integer result of (a + b) * c.",
            "constraints": "Standard operator evaluation.",
            "sample_input": "3 4 5",
            "sample_output": "35",
            "expected_output": "35",
            "sample_explanation": "(3 + 4) * 5 = 7 * 5 = 35.",
            "starter_code": (
                "#include <stdio.h>\n\n"
                "int main(void) {\n"
                "    int a, b, c;\n"
                "    if (scanf(\"%d %d %d\", &a, &b, &c) == 3) {\n"
                "        int result = (a + b) * c;\n"
                "        printf(\"%d\\n\", result);\n"
                "    }\n"
                "    return 0;\n"
                "}"
            ),
            "hints": [
                "Use parentheses `(a + b)` so addition evaluates before multiplication.",
                "Multiply by `c`: `(a + b) * c`.",
            ],
        }

    else:  # Variables and Data Types
        return {
            "problem_statement": (
                "Write a C program that prints the byte size of standard C datatypes: `char`, `int`, and `float`.\n"
                "Output must be formatted as: `char: 1, int: 4, float: 4`."
            ),
            "input_format": "No standard input required.",
            "output_format": "char: 1, int: 4, float: 4",
            "constraints": "Standard sizeof operator usage.",
            "sample_input": "",
            "sample_output": "char: 1, int: 4, float: 4",
            "expected_output": "char: 1, int: 4, float: 4",
            "sample_explanation": "sizeof operator evaluates byte footprints of char, int, and float.",
            "starter_code": (
                "#include <stdio.h>\n\n"
                "int main(void) {\n"
                "    printf(\"char: %zu, int: %zu, float: %zu\\n\", sizeof(char), sizeof(int), sizeof(float));\n"
                "    return 0;\n"
                "}"
            ),
            "hints": [
                "Use `sizeof(type)` operator to query byte sizes.",
                "Format using `%zu` specifier for `size_t`.",
            ],
        }
