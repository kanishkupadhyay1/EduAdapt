import React, { useState, useRef, useEffect } from 'react';
import MermaidDiagram from './MermaidDiagram';
import { synthesizeLessonAudio } from '../api/learningApi';

/**
 * Normalizes text by removing raw escaped newlines and outer quotation marks.
 */
function cleanText(txt) {
  if (!txt) return '';
  return String(txt)
    .replace(/\\n/g, '\n')
    .replace(/^["']|["']$/g, '')
    .trim();
}

/**
 * Fallback defaults for all 10 PPS C curriculum topics ensuring complete, grounded instruction.
 */
const TOPIC_FALLBACKS = {
  Pointers: {
    learning_objective: 'Understand the concept of memory addresses, pointer declaration, dereferencing, and pointer arithmetic in C99.',
    explanation: 'A pointer in C is a variable that stores the memory address of another variable. By storing addresses rather than values, pointers enable efficient array navigation, dynamic memory allocation, and passing variables by reference to functions.',
    c_code: `#include <stdio.h>

int main(void) {
    int value = 42;
    int *ptr = &value;

    printf("Value: %d\\n", value);
    printf("Address: %p\\n", (void *)ptr);
    printf("Dereferenced: %d\\n", *ptr);

    *ptr = 100;
    printf("Updated Value: %d\\n", value);

    return 0;
}`,
    c_code_title: 'Pointer Declaration and Dereferencing in C99',
    c_code_explanation: 'Demonstrates referencing with & to get an address and dereferencing with * to read or write the underlying value.',
    walkthrough_steps: [
      'int value = 42: Allocates 4 bytes on the stack and initializes the value to 42.',
      'int *ptr = &value: Declares pointer ptr and assigns it the memory address of variable value.',
      'printf("%p", (void *)ptr): Displays the hexadecimal memory address stored in ptr.',
      '*ptr = 100: Dereferences ptr to directly overwrite the contents at that memory address with 100.'
    ],
    common_mistakes: [
      'Dereferencing an uninitialized (wild) pointer leading to segmentation fault.',
      'Confusing the address-of operator (&) with the dereference operator (*).',
      'Failing to cast pointers to (void *) when printing with the %p format specifier.'
    ],
    understanding_check: {
      question: 'What does the expression *ptr evaluate to when ptr points to int num = 25?',
      options: [
        'The memory address of num',
        'The integer value 25 stored at num',
        'The size in bytes of an integer pointer',
        'A compile-time type error'
      ],
      correct_answer: 'The integer value 25 stored at num',
      explanation: 'The asterisk (*) operator dereferences the pointer, fetching the actual value stored at the target memory location.'
    }
  },
  'Dynamic Memory Allocation': {
    learning_objective: 'Master heap memory management using malloc, calloc, realloc, and free in standard C99.',
    explanation: 'Dynamic memory allocation permits programs to request variable-sized memory blocks from the operating system heap at runtime. Unlike stack memory which is automatically tied to function scope, heap memory persists until explicitly released using free().',
    c_code: `#include <stdio.h>
#include <stdlib.h>

void createArray(int *array, int size) {
    for (int i = 0; i < size; i++) {
        array[i] = (i + 1) * 10;
    }
}

void printArray(int *array, int size) {
    for (int i = 0; i < size; i++) {
        printf("%d%s", array[i], (i == size - 1) ? "" : " ");
    }
    printf("\\n");
}

int main(void) {
    int size = 5;
    int *array = (int *)malloc(size * sizeof(int));

    if (array == NULL) {
        printf("Memory allocation failed!\\n");
        return 1;
    }

    createArray(array, size);
    printArray(array, size);

    free(array);
    array = NULL;
    return 0;
}`,
    c_code_title: 'Dynamic Array Allocation and Safe Deallocation in C99',
    c_code_explanation: 'Allocates an integer array on the heap using malloc, checks for NULL, populates and prints elements, and safely frees memory.',
    walkthrough_steps: [
      'malloc(size * sizeof(int)): Allocates 20 contiguous bytes on the heap for 5 integers.',
      'if (array == NULL): Critical verification preventing crashes if system memory is exhausted.',
      'createArray(array, size): Populates allocated heap cells through pointer subscripting.',
      'printArray(array, size): Formats and displays space-separated integers.',
      'free(array); array = NULL: Releases memory back to the OS and prevents dangling pointer bugs.'
    ],
    common_mistakes: [
      'Failing to verify malloc return value before dereferencing.',
      'Memory leaks caused by forgetting to call free() before pointer variables go out of scope.',
      'Accessing memory after it has been freed (dangling pointer access).'
    ],
    understanding_check: {
      question: 'What happens if a program repeatedly calls malloc() without ever calling free()?',
      options: [
        'Heap memory is released automatically at function return',
        'A memory leak occurs because heap memory persists across function calls',
        'The compiler throws a syntax error',
        'Stack overflow exception occurs'
      ],
      correct_answer: 'A memory leak occurs because heap memory persists across function calls',
      explanation: 'Heap memory has a dynamic lifetime that persists until explicitly released with free(). Omitting free() creates a memory leak.'
    }
  },
  Strings: {
    learning_objective: 'Master null-terminated character arrays, string literals, and standard string manipulation in C.',
    explanation: 'In C, strings are one-dimensional arrays of characters terminated by a special null character sentinel (\'\\0\', ASCII value 0). The null terminator indicates to standard library functions (like strlen and printf) where the text sequence terminates in memory.',
    c_code: `#include <stdio.h>
#include <string.h>

int main(void) {
    char greeting[] = "Hello";

    printf("String: %s\\n", greeting);
    printf("Length (strlen): %zu\\n", strlen(greeting));
    printf("Allocated Bytes (sizeof): %zu\\n", sizeof(greeting));

    for (int i = 0; i <= 5; i++) {
        printf("Index %d: '%c' (ASCII: %d)\\n", i, greeting[i], (int)greeting[i]);
    }
    return 0;
}`,
    c_code_title: 'Null-Terminated Character Array Inspection in C99',
    c_code_explanation: 'Inspects character elements, length calculation via strlen, and the mandatory terminating \\0 byte.',
    walkthrough_steps: [
      'char greeting[] = "Hello": Creates a 6-byte array containing \'H\', \'e\', \'l\', \'l\', \'o\', and \'\\0\'.',
      'strlen(greeting): Traverses characters until reaching \'\\0\' (counts 5 visible characters).',
      'sizeof(greeting): Counts all allocated bytes including the \'\\0\' sentinel (yields 6 bytes).'
    ],
    common_mistakes: [
      'Forgetting space for the \'\\0\' null terminator when declaring character array dimensions.',
      'Using \'==\' to compare string contents instead of strcmp().',
      'Buffer overflows when copying unbounded inputs into fixed-size character arrays.'
    ],
    understanding_check: {
      question: 'What is the byte size of the character array declared as char str[] = "EduAdapt";?',
      options: [
        '8 bytes',
        '9 bytes (8 visible characters + 1 null terminator \'\\0\')',
        '16 bytes',
        '4 bytes'
      ],
      correct_answer: '9 bytes (8 visible characters + 1 null terminator \'\\0\')',
      explanation: 'In C, string literals append an implicit null terminator \'\\0\', requiring 8 + 1 = 9 bytes in memory.'
    }
  },
  Arrays: {
    learning_objective: 'Master contiguous memory allocation, zero-indexed element access, and the relationship between arrays and pointers.',
    explanation: 'An array is a contiguous block of homogeneous memory cells. In C, array names decay to a pointer to their first element in most expressions, which forms the basis for pointer arithmetic and buffer iteration.',
    c_code: `#include <stdio.h>

int main(void) {
    int numbers[5] = {10, 20, 30, 40, 50};

    for (int i = 0; i < 5; i++) {
        printf("Index %d: value = %d (address = %p)\\n", i, numbers[i], (void *)&numbers[i]);
    }

    return 0;
}`,
    c_code_title: 'Array Traversal and Contiguous Memory Inspection',
    c_code_explanation: 'Shows element access using standard indexing and reveals the exact byte offsets in memory.',
    walkthrough_steps: [
      'int numbers[5] = {...}: Allocates 5 contiguous integer slots sequentially in memory.',
      'Loop from i = 0 to 4: Iterates through each index safely within array bounds.',
      '&numbers[i]: Shows that each adjacent element address increases by sizeof(int) (typically 4 bytes).'
    ],
    common_mistakes: [
      'Off-by-one errors accessing index 5 in a 5-element array (valid indices are 0 to 4).',
      'Attempting to reassign an array name directly (array names are non-modifiable lvalues).'
    ],
    understanding_check: {
      question: 'In C, what is the memory relationship between numbers[0] and numbers[1] for an int array?',
      options: [
        'They are stored in arbitrary non-contiguous memory locations.',
        'numbers[1] is located exactly sizeof(int) bytes after numbers[0].',
        'They always share the identical memory address.',
        'numbers[1] is placed at a randomized heap address.'
      ],
      correct_answer: 'numbers[1] is located exactly sizeof(int) bytes after numbers[0].',
      explanation: 'C arrays are guaranteed by the standard to occupy contiguous blocks of memory.'
    }
  },
  Loops: {
    learning_objective: 'Understand control flow mechanics of while, for, and do-while loops in C, including loop invariants and termination.',
    explanation: 'Loops automate repetitive computation by testing conditions before or after each iteration. Correct loop construction requires an initialization, a termination predicate, and a monotonic progress step to avoid infinite cycles.',
    c_code: `#include <stdio.h>

int main(void) {
    int sum = 0;
    for (int i = 1; i <= 5; i++) {
        sum += i;
    }
    printf("Sum of 1 to 5 is: %d\\n", sum);
    return 0;
}`,
    c_code_title: 'Deterministic Loop Iteration and Accumulator Pattern',
    c_code_explanation: 'Standard for loop structure with initialization, bound checking, and incrementing step.',
    walkthrough_steps: [
      'int i = 1: Initialization step executed once before the loop begins.',
      'i <= 5: Guard condition evaluated before each iteration.',
      'sum += i: Loop body accumulating the current counter value.',
      'i++: Step expression incrementing the counter towards termination.'
    ],
    common_mistakes: [
      'Infinite loops caused by forgetting to update the loop counter inside a while loop.',
      'Accidentally placing a semicolon directly after the for(...) header.',
      'Off-by-one boundary errors with < versus <=.'
    ],
    understanding_check: {
      question: 'What is the final value of counter after while (counter < 3) { counter++; } if initialized to 0?',
      options: ['2', '3', '4', '0'],
      correct_answer: '3',
      explanation: 'The loop executes for counter=0, 1, 2. When counter reaches 3, the condition (3 < 3) evaluates to false, terminating the loop.'
    }
  },
  Functions: {
    learning_objective: 'Master function signatures, prototypes, call stacks, return types, and call-by-value semantics in C.',
    explanation: 'Functions promote modularity and code reuse. In C, arguments are passed by value, meaning the function receives a copy of each variable unless pointers are explicitly passed to simulate pass-by-reference.',
    c_code: `#include <stdio.h>

int add(int a, int b) {
    return a + b;
}

int main(void) {
    int result = add(15, 27);
    printf("Result: %d\\n", result);
    return 0;
}`,
    c_code_title: 'Function Definition, Prototyping, and Invocation',
    c_code_explanation: 'Illustrates function parameter passing, execution frame allocation, and returning a computed result.',
    walkthrough_steps: [
      'int add(int a, int b): Defines a function accepting two integer parameters and returning an integer.',
      'add(15, 27): Pushes arguments onto the call stack and transfers execution control to add.',
      'return a + b: Calculates the sum and returns it to the caller frame in main.',
      'int result = ...: Stores the returned value in the local stack variable.'
    ],
    common_mistakes: [
      'Calling a function before declaring its prototype or definition.',
      'Expecting a function to modify caller variables without passing pointers.',
      'Returning a pointer to a local automatic variable allocated on the function stack.'
    ],
    understanding_check: {
      question: 'Why does void modify(int x) { x = 99; } fail to change the caller variable in main?',
      options: [
        'C functions cannot accept integers.',
        'C uses call-by-value, so the function only modifies a local copy of x.',
        'The variable x is marked constant by default.',
        'The return type must be int.'
      ],
      correct_answer: 'C uses call-by-value, so the function only modifies a local copy of x.',
      explanation: 'In C, parameters are passed by value. To modify caller memory, a pointer (memory address) must be passed.'
    }
  },
  Conditionals: {
    learning_objective: 'Understand boolean logic, if-else decision branching, and relational comparisons in C.',
    explanation: 'Conditionals evaluate non-zero (True) and zero (False) expressions to direct programmatic execution paths. Branching allows programs to adapt behavior depending on input state and boundary invariants.',
    c_code: `#include <stdio.h>

int main(void) {
    int score = 75;
    if (score >= 50) {
        printf("Result: Passed (Score: %d)\\n", score);
    } else {
        printf("Result: Failed (Score: %d)\\n", score);
    }
    return 0;
}`,
    c_code_title: 'Conditional Branching with If-Else in C99',
    c_code_explanation: 'Evaluates relational condition and executes the appropriate branch body.',
    walkthrough_steps: [
      'score >= 50: Evaluates to 1 (True) because 75 is greater than or equal to 50.',
      'Executes the if block body and skips the else block.'
    ],
    common_mistakes: [
      'Using assignment = instead of equality == inside if statements.',
      'Omitting braces around multi-statement blocks.'
    ],
    understanding_check: {
      question: 'What is the boolean evaluation of if (5) in C?',
      options: ['True (any non-zero integer is True)', 'False', 'Compilation error', 'Undefined'],
      correct_answer: 'True (any non-zero integer is True)',
      explanation: 'In C, any non-zero numeric value is evaluated as boolean True; only 0 is evaluated as False.'
    }
  },
  Structures: {
    learning_objective: 'Understand user-defined composite data types with struct, member declarations, and dot operator access in C.',
    explanation: 'A structure allows grouping heterogeneous variables of different data types together under a single user-defined record name. Members are accessed via the dot operator (.) for values and arrow operator (->) for pointers.',
    c_code: `#include <stdio.h>
#include <string.h>

struct Student {
    int id;
    char name[20];
    float gpa;
};

int main(void) {
    struct Student s1;
    s1.id = 101;
    strcpy(s1.name, "Alex");
    s1.gpa = 3.85f;

    printf("Student ID: %d, Name: %s, GPA: %.2f\\n", s1.id, s1.name, s1.gpa);
    return 0;
}`,
    c_code_title: 'Structure Declaration and Member Access in C99',
    c_code_explanation: 'Defines a composite student record, populates fields, and prints member data.',
    walkthrough_steps: [
      'struct Student: Declares composite structure layout.',
      's1.id = 101: Accesses member using dot operator.',
      'strcpy(s1.name, "Alex"): Copies string into character array member.'
    ],
    common_mistakes: [
      'Forgetting the terminating semicolon after the structure declaration body.',
      'Using dot operator with a pointer to structure without dereferencing.'
    ],
    understanding_check: {
      question: 'Which operator is used to access members through a structure pointer in C?',
      options: ['Arrow operator (->)', 'Dot operator (.)', 'Asterisk (*)', 'Ampersand (&)'],
      correct_answer: 'Arrow operator (->)',
      explanation: 'The arrow operator (`->`) dereferences a structure pointer and accesses the member directly (identical to (*ptr).member).'
    }
  },
  'Operators and Expressions': {
    learning_objective: 'Understand operator precedence, associativity, and expression evaluation in C.',
    explanation: 'Expressions combine operators and operands to produce values. Operator precedence rules dictate the execution order, with parentheses overriding default precedence.',
    c_code: `#include <stdio.h>

int main(void) {
    int a = 10, b = 4, c = 2;
    int res1 = a + b * c;     // Multiplies first (10 + 8 = 18)
    int res2 = (a + b) * c;   // Parentheses first (14 * 2 = 28)

    printf("res1: %d, res2: %d\\n", res1, res2);
    return 0;
}`,
    c_code_title: 'Operator Precedence and Evaluation in C99',
    c_code_explanation: 'Compares default precedence with explicit parenthetical overrides.',
    walkthrough_steps: [
      'b * c: Multiplication has higher precedence than addition.',
      '(a + b) * c: Parentheses force addition to evaluate before multiplication.'
    ],
    common_mistakes: [
      'Expecting integer division 7 / 2 to return 3.5 (it truncates to 3).',
      'Confusing bitwise & with logical &&.'
    ],
    understanding_check: {
      question: 'What is the value of integer expression 7 / 2 in C?',
      options: ['3 (integer division truncates)', '3.5', '4', 'Undefined'],
      correct_answer: '3 (integer division truncates)',
      explanation: 'Dividing two integers in C performs integer truncation, discarding any fractional remainder.'
    }
  },
  'Variables and Data Types': {
    learning_objective: 'Understand fundamental data types (char, int, float, double), declarations, and memory footprints in C.',
    explanation: 'Variables represent named memory locations. Data types specify the byte footprint and bit interpretation for stored values.',
    c_code: `#include <stdio.h>

int main(void) {
    char letter = 'A';
    int count = 42;
    float price = 19.99f;
    double pi = 3.1415926535;

    printf("char: %c (%zu B), int: %d (%zu B), float: %.2f (%zu B)\\n",
           letter, sizeof(letter), count, sizeof(count), price, sizeof(price));
    return 0;
}`,
    c_code_title: 'Fundamental Data Types and sizeof Inspection in C99',
    c_code_explanation: 'Demonstrates declarations, format specifiers, and queries exact byte footprints using sizeof.',
    walkthrough_steps: [
      'char letter = \'A\': Allocates 1 byte.',
      'int count = 42: Allocates 4 bytes.',
      'sizeof operator: Queries exact byte footprints from compiler.'
    ],
    common_mistakes: [
      'Using single quotes for strings or double quotes for characters.',
      'Using variables before declaring them.'
    ],
    understanding_check: {
      question: 'What is the guaranteed byte size of a char in C?',
      options: ['Exactly 1 byte', '2 bytes', '4 bytes', '8 bytes'],
      correct_answer: 'Exactly 1 byte',
      explanation: 'By standard C specification, sizeof(char) is always exactly 1 byte.'
    }
  }
};

/**
 * Normalized helper retrieving topic-specific fallback matching any curriculum alias.
 */
function getTopicFallback(topic = '') {
  const t = String(topic).toLowerCase();
  if (t.includes('dynamic') || t.includes('malloc') || t.includes('dma') || t.includes('heap')) {
    return TOPIC_FALLBACKS['Dynamic Memory Allocation'];
  }
  if (t.includes('string')) return TOPIC_FALLBACKS.Strings;
  if (t.includes('point')) return TOPIC_FALLBACKS.Pointers;
  if (t.includes('array')) return TOPIC_FALLBACKS.Arrays;
  if (t.includes('struct')) return TOPIC_FALLBACKS.Structures;
  if (t.includes('func') || t.includes('recur')) return TOPIC_FALLBACKS.Functions;
  if (t.includes('loop') || t.includes('for') || t.includes('while')) return TOPIC_FALLBACKS.Loops;
  if (t.includes('cond') || t.includes('if') || t.includes('switch')) return TOPIC_FALLBACKS.Conditionals;
  if (t.includes('op') || t.includes('expr')) return TOPIC_FALLBACKS['Operators and Expressions'];
  if (t.includes('var') || t.includes('type') || t.includes('data')) return TOPIC_FALLBACKS['Variables and Data Types'];
  return TOPIC_FALLBACKS.Pointers;
}

/**
 * Extracts and structures the lesson fields from either structured_response or parsed content.
 */
function extractLessonData(teaching, currentTopic) {
  const fallback = getTopicFallback(currentTopic);
  const sr = teaching?.structured_response || {};

  // 1. Learning Objective
  let objective = cleanText(sr.learning_objective);
  if (!objective) {
    const objMatch = (teaching?.generated_teaching_content || '').match(/###\s*(?:1\.?\s*)?Learning Objective\s*([\s\S]*?)(?=###|$)/i);
    if (objMatch && objMatch[1].trim()) {
      objective = cleanText(objMatch[1]);
    }
  }
  if (!objective) objective = fallback.learning_objective;

  // 2. Conceptual Explanation
  let explanation = cleanText(sr.explanation);
  if (!explanation) {
    const expMatch = (teaching?.generated_teaching_content || '').match(/###\s*(?:2\.?\s*)?Conceptual Explanation\s*([\s\S]*?)(?=###|$)/i);
    if (expMatch && expMatch[1].trim()) {
      explanation = cleanText(expMatch[1]);
    }
  }
  if (!explanation) explanation = fallback.explanation;

  // Filter out any leaked markdown code fences or JSON delimiters from explanation
  explanation = explanation
    .replace(/```[a-z]*[\s\S]*?```/gi, '')
    .replace(/^\{[\s\S]*\}$/g, '')
    .trim();

  // 3. Diagram code and metadata (Multi-Diagram Support)
  let diagrams = [];
  if (Array.isArray(sr.diagrams) && sr.diagrams.length > 0) {
    diagrams = sr.diagrams
      .filter((d) => d && (d.mermaid_code || d.code))
      .map((d, idx) => ({
        mermaid_code: cleanText(d.mermaid_code || d.code),
        title: cleanText(d.title) || `${currentTopic} Architecture Flow ${idx + 1}`,
        explanation: cleanText(d.explanation) || '',
      }));
  }
  if (diagrams.length === 0) {
    let singleDiag = sr.visual_diagram || sr.diagram || teaching?.diagram || {};
    let mCode = cleanText(singleDiag.mermaid_code || singleDiag.code);
    if (mCode) {
      diagrams.push({
        mermaid_code: mCode,
        title: cleanText(singleDiag.title) || `${currentTopic} Architecture Flow`,
        explanation: cleanText(singleDiag.explanation) || '',
      });
    }
  }

  // 4. C Code Implementation
  let cCode = cleanText(sr.c_code);
  let cCodeTitle = cleanText(sr.c_code_title) || `${currentTopic} C Implementation (C99)`;
  let cCodeExplanation = cleanText(sr.c_code_explanation) || '';

  if (!cCode) {
    const codeMatch = (teaching?.generated_teaching_content || '').match(/```(?:c|C)\s*([\s\S]*?)```/);
    if (codeMatch && codeMatch[1].trim()) {
      cCode = codeMatch[1].trim();
    }
  }
  if (!cCode) {
    cCode = fallback.c_code;
    cCodeTitle = fallback.c_code_title;
    cCodeExplanation = fallback.c_code_explanation;
  }

  // 5. Walkthrough steps
  let walkthroughSteps = Array.isArray(sr.walkthrough_steps) && sr.walkthrough_steps.length > 0
    ? sr.walkthrough_steps.map(cleanText)
    : [];

  if (walkthroughSteps.length === 0) {
    const walkMatch = (teaching?.generated_teaching_content || '').match(/###\s*(?:5\.?\s*)?Step-by-Step Code Walkthrough\s*([\s\S]*?)(?=###|$)/i);
    if (walkMatch && walkMatch[1].trim()) {
      walkthroughSteps = walkMatch[1]
        .split('\n')
        .map((l) => l.replace(/^\d+\.\s*|^[-*]\s*/, '').trim())
        .filter(Boolean);
    }
  }
  if (walkthroughSteps.length === 0) walkthroughSteps = fallback.walkthrough_steps;

  // 6. Common mistakes
  let commonMistakes = Array.isArray(sr.common_mistakes) && sr.common_mistakes.length > 0
    ? sr.common_mistakes.map(cleanText)
    : [];

  if (commonMistakes.length === 0) {
    const misMatch = (teaching?.generated_teaching_content || '').match(/###\s*(?:6\.?\s*)?Common Mistakes to Avoid\s*([\s\S]*?)(?=###|$)/i);
    if (misMatch && misMatch[1].trim()) {
      commonMistakes = misMatch[1]
        .split('\n')
        .map((l) => l.replace(/^\d+\.\s*|^[-*]\s*/, '').trim())
        .filter(Boolean);
    }
  }
  if (commonMistakes.length === 0) commonMistakes = fallback.common_mistakes;

  // 7. Quick understanding check
  let understandingCheck = sr.understanding_check || null;
  if (!understandingCheck || !understandingCheck.question || !Array.isArray(understandingCheck.options)) {
    understandingCheck = fallback.understanding_check;
  }

  return {
    objective,
    explanation,
    diagrams,
    mermaidCode: diagrams[0]?.mermaid_code || '',
    diagramTitle: diagrams[0]?.title || `${currentTopic} Architecture Flow`,
    diagramExplanation: diagrams[0]?.explanation || '',
    cCode,
    cCodeTitle,
    cCodeExplanation,
    walkthroughSteps,
    commonMistakes,
    understandingCheck,
  };
}

export default function TeachingContent({
  teaching,
  studentProfile,
  currentTopic,
  onNavigate,
  onOpenTutorWithCode,
}) {
  const topic = currentTopic || 'Pointers';
  const difficulty = studentProfile?.recommended_difficulty || 'Adaptive';
  const pace = studentProfile?.learning_pace || 'Adaptive';
  const studentId = studentProfile?.student_id || 'S001';

  const personalizationApplied = teaching?.personalization_applied || {};
  const personalizationBullets = teaching?.personalization_bullets || [];

  const lesson = extractLessonData(teaching, topic);

  // Copy code feedback state with clipboard fallback
  const [copied, setCopied] = useState(false);
  const handleCopyCode = () => {
    if (!lesson.cCode) return;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(lesson.cCode).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }).catch(() => {
        fallbackCopyText(lesson.cCode);
      });
    } else {
      fallbackCopyText(lesson.cCode);
    }
  };

  const fallbackCopyText = (text) => {
    try {
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.opacity = '0';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Ignored
    }
  };

  // Understanding check interactive state
  const [selectedOption, setSelectedOption] = useState(null);
  const [submittedCheck, setSubmittedCheck] = useState(false);
  const [isCorrect, setIsCorrect] = useState(null);

  // Reset check when topic changes
  useEffect(() => {
    setSelectedOption(null);
    setSubmittedCheck(false);
    setIsCorrect(null);
  }, [topic]);

  const handleSubmitCheck = () => {
    if (selectedOption === null || !lesson.understandingCheck) return;
    const options = lesson.understandingCheck.options || [];
    const userSelectedText = String(options[selectedOption] || '').trim();
    const correctRaw = String(
      lesson.understandingCheck.correct_answer ||
      lesson.understandingCheck.correct_option ||
      lesson.understandingCheck.answer ||
      lesson.understandingCheck.correct ||
      ''
    ).trim();

    if (!correctRaw) {
      setIsCorrect(true);
      setSubmittedCheck(true);
      return;
    }

    const userSelectedLower = userSelectedText.toLowerCase();
    const correctLower = correctRaw.toLowerCase();

    // Check letter match (e.g. "B" vs "B) 25")
    const selectedLetter = userSelectedText.charAt(0).toUpperCase();
    const correctLetter = correctRaw.charAt(0).toUpperCase();
    const isLetterKey = correctRaw.length === 1 && /[A-D]/i.test(correctRaw);
    const letterMatches = isLetterKey && selectedLetter === correctLetter;

    // Check text/substring match
    const textMatches = userSelectedLower === correctLower ||
      (correctLower.length > 3 && userSelectedLower.includes(correctLower)) ||
      (userSelectedLower.length > 3 && correctLower.includes(userSelectedLower));

    setIsCorrect(letterMatches || textMatches);
    setSubmittedCheck(true);
  };

  const handleResetCheck = () => {
    setSelectedOption(null);
    setSubmittedCheck(false);
    setIsCorrect(null);
  };

  // Audio reader state
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [isAudioLoading, setIsAudioLoading] = useState(false);
  const [audioError, setAudioError] = useState(null);
  const [audioSpeed, setAudioSpeed] = useState(1.0);
  const audioRef = useRef(null);
  const audioUrlRef = useRef(null);

  useEffect(() => {
    return () => {
      if (audioRef.current) audioRef.current.pause();
      if (audioUrlRef.current) URL.revokeObjectURL(audioUrlRef.current);
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const handleStopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setIsPlayingAudio(false);
    setIsAudioLoading(false);
  };

  const handleToggleAudio = async () => {
    if (isPlayingAudio || isAudioLoading) {
      handleStopAudio();
      return;
    }

    setIsAudioLoading(true);
    setAudioError(null);

    // Build clean spoken narration (objective + conceptual explanation + common mistakes)
    const spokenNarrative = [
      `Learning objective for ${topic}: ${lesson.objective}.`,
      lesson.explanation,
      `Key concepts to remember: ${lesson.walkthroughSteps.slice(0, 3).join('. ')}.`,
      `Common mistakes: ${lesson.commonMistakes.join('. ')}.`
    ].join(' ');

    try {
      const blob = await synthesizeLessonAudio(spokenNarrative, Math.round(170 * audioSpeed));
      if (audioUrlRef.current) URL.revokeObjectURL(audioUrlRef.current);
      const url = URL.createObjectURL(blob);
      audioUrlRef.current = url;

      if (!audioRef.current) audioRef.current = new Audio();
      audioRef.current.src = url;
      audioRef.current.playbackRate = audioSpeed;
      audioRef.current.onended = () => setIsPlayingAudio(false);
      audioRef.current.onerror = () => {
        setIsPlayingAudio(false);
        setAudioError('Audio playback failed.');
      };
      await audioRef.current.play();
      setIsPlayingAudio(true);
      setIsAudioLoading(false);
      return;
    } catch (err) {
      // Browser Web Speech API fallback
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        try {
          window.speechSynthesis.cancel();
          const utterance = new SpeechSynthesisUtterance(spokenNarrative);
          utterance.rate = audioSpeed;
          utterance.onend = () => setIsPlayingAudio(false);
          utterance.onerror = () => setIsPlayingAudio(false);
          window.speechSynthesis.speak(utterance);
          setIsPlayingAudio(true);
          setIsAudioLoading(false);
          return;
        } catch (synthErr) {
          console.warn('Browser speech synthesis fallback failed:', synthErr);
        }
      }
      setIsAudioLoading(false);
      setAudioError('Text-to-speech could not be generated. Please ensure audio output is configured.');
    }
  };

  return (
    <section className="panel" aria-labelledby="teaching-heading">
      {/* Panel Header */}
      <div className="panel-header">
        <div>
          <h2 id="teaching-heading" className="panel-title">{topic} — Adaptive Lesson</h2>
          <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
            Personalized for Student {studentId} • {difficulty} Tier • {pace} Pace
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="badge-blue">GenAI PPS Grounded</span>
          <span className="badge-green">Mistral 7B</span>
        </div>
      </div>

      <div className="panel-body">
        {/* Accessible Audio Lesson Reader Toolbar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'var(--color-surface-subtle)',
            padding: '8px 14px',
            borderRadius: 'var(--radius-sm)',
            marginBottom: '16px',
            border: '1px solid var(--color-border)',
            flexWrap: 'wrap',
            gap: '8px',
          }}
          role="region"
          aria-label="Audio Lesson Reader"
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              type="button"
              className="btn-pill"
              onClick={handleToggleAudio}
              disabled={isAudioLoading}
              aria-pressed={isPlayingAudio}
              aria-label={isPlayingAudio ? 'Stop reading lesson aloud' : 'Read lesson aloud'}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontWeight: 600,
                backgroundColor: isPlayingAudio ? '#ef4444' : undefined,
                color: isPlayingAudio ? '#ffffff' : undefined,
              }}
            >
              {isAudioLoading ? 'Synthesizing Audio...' : isPlayingAudio ? '⏹ Stop Reading' : '🔊 Read Lesson Aloud'}
            </button>
            {isPlayingAudio && (
              <span className="badge-green" aria-live="polite">
                Speaking ({audioSpeed}x)
              </span>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <label style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--color-text-secondary)' }}>
              <span>Speed:</span>
              <select
                value={audioSpeed}
                onChange={(e) => {
                  const s = parseFloat(e.target.value);
                  setAudioSpeed(s);
                  if (audioRef.current) audioRef.current.playbackRate = s;
                }}
                style={{
                  padding: '3px 8px',
                  borderRadius: '4px',
                  border: '1px solid var(--color-border)',
                  fontSize: '12px',
                  background: 'var(--color-surface)',
                  color: 'inherit',
                }}
                aria-label="Playback speed"
              >
                <option value="0.8">0.8x</option>
                <option value="1.0">1.0x</option>
                <option value="1.2">1.2x</option>
                <option value="1.5">1.5x</option>
              </select>
            </label>
          </div>
          {audioError && (
            <div style={{ width: '100%', fontSize: '12px', color: 'var(--color-red)' }} role="alert">
              {audioError}
            </div>
          )}
        </div>

        {/* Dynamic Personalization Applied Banner */}
        {(personalizationBullets.length > 0 || Object.keys(personalizationApplied).length > 0) && (
          <div className="personalization-card" role="region" aria-label="Personalization Applied Details">
            <div className="personalization-header">
              <span className="personalization-title">
                Personalization Applied (Learning Twin & Profile Driven)
              </span>
              <span className="badge-green">
                Tier: {personalizationApplied.mastery_tier || difficulty} ({personalizationApplied.topic_mastery ? `${Number(personalizationApplied.topic_mastery).toFixed(2)}` : 'Adaptive'})
              </span>
            </div>

            {personalizationApplied.rationale && (
              <div
                style={{
                  backgroundColor: 'rgba(59, 130, 246, 0.08)',
                  borderLeft: '3px solid var(--color-blue)',
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-sm)',
                  marginBottom: '12px',
                  fontSize: '12px',
                  color: 'var(--color-text-primary)',
                  lineHeight: 1.5,
                }}
              >
                <strong>Pedagogical Adaptation:</strong> {personalizationApplied.rationale}
              </div>
            )}

            <div className="personalization-grid">
              {personalizationBullets.length > 0 ? (
                personalizationBullets.map((bullet, idx) => {
                  const parts = bullet.split(':');
                  return (
                    <div key={idx} className="personalization-item">
                      <span className="personalization-item-label">{parts[0]}:</span>
                      <span className="personalization-item-value">{parts.slice(1).join(':').trim()}</span>
                    </div>
                  );
                })
              ) : (
                Object.entries(personalizationApplied).map(([key, val]) => (
                  <div key={key} className="personalization-item">
                    <span className="personalization-item-label">
                      {key.replace(/_/g, ' ')}:
                    </span>
                    <span className="personalization-item-value">{String(val)}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* SECTION 1: LEARNING OBJECTIVE */}
        <div
          style={{
            borderLeft: '4px solid var(--color-blue)',
            background: 'var(--color-blue-light)',
            padding: '14px 18px',
            borderRadius: 'var(--radius-sm)',
            marginBottom: '20px',
          }}
          role="region"
          aria-labelledby="section-learning-objective"
        >
          <div
            id="section-learning-objective"
            style={{
              fontSize: '11px',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.6px',
              color: 'var(--color-blue)',
              marginBottom: '4px',
            }}
          >
            Learning Objective
          </div>
          <p style={{ fontSize: '14px', color: 'var(--color-text-primary)', lineHeight: '1.5', margin: 0 }}>
            {lesson.objective}
          </p>
        </div>

        {/* SECTION 2: CONCEPTUAL EXPLANATION */}
        <div style={{ marginBottom: '22px' }} role="region" aria-labelledby="section-conceptual-explanation">
          <h3
            id="section-conceptual-explanation"
            style={{
              fontSize: '15px',
              fontWeight: 700,
              color: 'var(--color-text-primary)',
              marginBottom: '10px',
              borderBottom: '1px solid var(--color-border)',
              paddingBottom: '6px',
            }}
          >
            Conceptual Explanation
          </h3>
          <div style={{ fontSize: '14px', lineHeight: '1.65', color: 'var(--color-text-secondary)' }}>
            {lesson.explanation.split('\n\n').map((paragraph, pIdx) => (
              <p key={pIdx} style={{ marginBottom: '12px' }}>
                {paragraph}
              </p>
            ))}
          </div>
        </div>

        {/* SECTION 3: VISUAL ARCHITECTURE DIAGRAM(S) */}
        {lesson.diagrams && lesson.diagrams.length > 0 && (
          <div style={{ marginBottom: '24px' }} role="region" aria-labelledby="section-visual-diagram">
            <h3
              id="section-visual-diagram"
              style={{
                fontSize: '15px',
                fontWeight: 700,
                color: 'var(--color-text-primary)',
                marginBottom: '10px',
                borderBottom: '1px solid var(--color-border)',
                paddingBottom: '6px',
              }}
            >
              Visual Concept Architecture {lesson.diagrams.length > 1 ? `(${lesson.diagrams.length} Architectural Views)` : ''}
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {lesson.diagrams.map((diag, dIdx) => (
                <MermaidDiagram
                  key={`diag_${dIdx}_${topic}`}
                  code={diag.mermaid_code}
                  title={diag.title || `${topic} Visual Flow ${dIdx + 1}`}
                  explanation={diag.explanation}
                  topic={topic}
                />
              ))}
            </div>
          </div>
        )}

        {/* SECTION 4: C CODE IMPLEMENTATION */}
        <div style={{ marginBottom: '24px' }} role="region" aria-labelledby="section-c-code">
          <h3
            id="section-c-code"
            style={{
              fontSize: '15px',
              fontWeight: 700,
              color: 'var(--color-text-primary)',
              marginBottom: '10px',
              borderBottom: '1px solid var(--color-border)',
              paddingBottom: '6px',
            }}
          >
            C Implementation (C99)
          </h3>

          <div className="code-container">
            <div className="code-header">
              <span>{lesson.cCodeTitle}</span>
              <button
                type="button"
                className="code-copy-btn"
                onClick={handleCopyCode}
                aria-label="Copy C code to clipboard"
              >
                {copied ? '✓ Copied' : 'Copy Code'}
              </button>
            </div>
            <pre className="code-block">
              <code>{lesson.cCode}</code>
            </pre>
          </div>

          {lesson.cCodeExplanation && (
            <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', marginTop: '6px' }}>
              {lesson.cCodeExplanation}
            </p>
          )}
        </div>

        {/* SECTION 5: STEP-BY-STEP CODE WALKTHROUGH */}
        {lesson.walkthroughSteps && lesson.walkthroughSteps.length > 0 && (
          <div style={{ marginBottom: '24px' }} role="region" aria-labelledby="section-walkthrough">
            <h3
              id="section-walkthrough"
              style={{
                fontSize: '15px',
                fontWeight: 700,
                color: 'var(--color-text-primary)',
                marginBottom: '10px',
                borderBottom: '1px solid var(--color-border)',
                paddingBottom: '6px',
              }}
            >
              Step-by-Step Code Walkthrough
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {lesson.walkthroughSteps.map((step, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px',
                    padding: '10px 14px',
                    background: 'var(--color-surface-subtle)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-sm)',
                  }}
                >
                  <span
                    style={{
                      background: 'var(--color-blue)',
                      color: '#ffffff',
                      fontSize: '11px',
                      fontWeight: 700,
                      borderRadius: '50%',
                      width: '20px',
                      height: '20px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                      marginTop: '2px',
                    }}
                  >
                    {idx + 1}
                  </span>
                  <div style={{ fontSize: '13px', lineHeight: '1.5', color: 'var(--color-text-secondary)' }}>
                    {step}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* SECTION 6: COMMON MISTAKES TO AVOID */}
        {lesson.commonMistakes && lesson.commonMistakes.length > 0 && (
          <div style={{ marginBottom: '24px' }} role="region" aria-labelledby="section-common-mistakes">
            <h3
              id="section-common-mistakes"
              style={{
                fontSize: '15px',
                fontWeight: 700,
                color: 'var(--color-text-primary)',
                marginBottom: '10px',
                borderBottom: '1px solid var(--color-border)',
                paddingBottom: '6px',
              }}
            >
              Common Mistakes to Avoid
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {lesson.commonMistakes.map((mistake, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '10px',
                    padding: '10px 14px',
                    background: 'var(--color-red-light)',
                    border: '1px solid var(--color-red-border)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--color-red)',
                    fontSize: '13px',
                    lineHeight: '1.45',
                  }}
                >
                  <span style={{ fontWeight: 700, flexShrink: 0 }}>⚠️</span>
                  <span>{mistake}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* SECTION 7: INTERACTIVE QUICK UNDERSTANDING CHECK */}
        {lesson.understandingCheck && (
          <div
            style={{
              marginBottom: '26px',
              padding: '16px 18px',
              background: 'var(--color-surface-subtle)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
            }}
            role="region"
            aria-labelledby="section-quick-check"
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <h3
                id="section-quick-check"
                style={{
                  fontSize: '15px',
                  fontWeight: 700,
                  color: 'var(--color-text-primary)',
                  margin: 0,
                }}
              >
                Quick Understanding Check
              </h3>
              <span className="badge-blue">Interactive Concept Check</span>
            </div>

            <p style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: '12px' }}>
              {lesson.understandingCheck.question}
            </p>

            {lesson.understandingCheck.code_snippet && (
              <pre
                style={{
                  background: '#0f172a',
                  color: '#f8fafc',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '12px',
                  fontFamily: 'var(--font-mono)',
                  marginBottom: '14px',
                  overflowX: 'auto',
                }}
              >
                <code>{lesson.understandingCheck.code_snippet}</code>
              </pre>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '14px' }}>
              {lesson.understandingCheck.options.map((opt, optIdx) => {
                const isSelected = selectedOption === optIdx;
                return (
                  <label
                    key={optIdx}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      padding: '8px 12px',
                      background: isSelected ? 'var(--color-blue-light)' : '#ffffff',
                      border: `1px solid ${isSelected ? 'var(--color-blue)' : 'var(--color-border)'}`,
                      borderRadius: 'var(--radius-sm)',
                      cursor: submittedCheck ? 'default' : 'pointer',
                      fontSize: '13px',
                      color: 'var(--color-text-primary)',
                      transition: 'all 0.1s ease',
                    }}
                  >
                    <input
                      type="radio"
                      name="understanding-check-option"
                      checked={isSelected}
                      disabled={submittedCheck}
                      onChange={() => setSelectedOption(optIdx)}
                      style={{ cursor: submittedCheck ? 'default' : 'pointer' }}
                    />
                    <span>{opt}</span>
                  </label>
                );
              })}
            </div>

            {!submittedCheck ? (
              <button
                type="button"
                className="btn-primary"
                onClick={handleSubmitCheck}
                disabled={selectedOption === null}
                style={{ padding: '6px 14px', fontSize: '13px' }}
              >
                Check Answer
              </button>
            ) : (
              <div>
                <div
                  style={{
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-sm)',
                    marginBottom: '10px',
                    background: isCorrect ? 'var(--color-green-light)' : 'var(--color-red-light)',
                    border: `1px solid ${isCorrect ? 'var(--color-green-border)' : 'var(--color-red-border)'}`,
                    color: isCorrect ? 'var(--color-green)' : 'var(--color-red)',
                    fontSize: '13px',
                  }}
                >
                  <div style={{ fontWeight: 700, marginBottom: '4px' }}>
                    {isCorrect ? '✓ Correct! Great job.' : '✗ Not quite right.'}
                  </div>
                  <div>
                    {lesson.understandingCheck.explanation ||
                      `Correct Answer: ${lesson.understandingCheck.correct_answer || lesson.understandingCheck.correct_option || 'Verified Answer'}`}
                  </div>
                </div>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={handleResetCheck}
                  style={{ padding: '5px 12px', fontSize: '12px' }}
                >
                  Try Again
                </button>
              </div>
            )}
          </div>
        )}

        {/* Integration and Action Buttons */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            paddingTop: '16px',
            borderTop: '1px solid var(--color-border)',
            flexWrap: 'wrap',
            gap: '10px',
          }}
        >
          <button
            type="button"
            className="btn-secondary"
            onClick={() => {
              if (onOpenTutorWithCode && lesson.cCode) {
                onOpenTutorWithCode(lesson.cCode);
              } else if (onNavigate) {
                onNavigate('tutor');
              }
            }}
          >
            Ask AI Tutor ?
          </button>

          <div style={{ display: 'flex', gap: '10px' }}>
            {onNavigate && (
              <button
                type="button"
                className="btn-secondary"
                onClick={() => onNavigate('roadmap')}
              >
                View Adaptive Roadmap ☵
              </button>
            )}
            {onNavigate && (
              <button
                type="button"
                className="btn-primary"
                onClick={() => onNavigate('practice')}
              >
                Practice This Concept →
              </button>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
