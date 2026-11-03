import sys
sys.path.insert(0, "src")
from eduadapt.evaluation.c_executor import CExecutor

code = """#include <stdio.h>
#include <stdlib.h>

void createArray(int *array, int size);
void printArray(int *array, int size);

int main() {
    int size;
    if (scanf("%d", &size) != 1 || size <= 0) {
        return 0;
    }

    int *array = (int *)malloc(size * sizeof(int));
    if (array == NULL) {
        return 1;
    }

    createArray(array, size);
    printArray(array, size);

    free(array);
    return 0;
}

void createArray(int *array, int size) {
    for (int i = 0; i < size; i++) {
        scanf("%d", &array[i]);
    }
}

void printArray(int *array, int size) {
    for (int i = 0; i < size; i++) {
        printf("%d%s", array[i], (i == size - 1) ? "" : " ");
    }
    printf("\\n");
}
"""

c = CExecutor()
print("1. Testing execution without stdin input:")
res_no_stdin = c.execute_student_code(code)
print(f"Status: {res_no_stdin.status}")
print(f"Time: {res_no_stdin.execution_time_seconds}")
print(f"Exit code: {res_no_stdin.exit_code}")
print(f"Stdout: {repr(res_no_stdin.stdout)}")
print(f"Stderr: {repr(res_no_stdin.stderr)}")
print(f"Compiler output: {repr(res_no_stdin.compiler_output)}")
print(f"Notes: {repr(res_no_stdin.notes)}")
