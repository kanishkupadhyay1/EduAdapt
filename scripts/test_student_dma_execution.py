import sys
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

ex = CExecutor()
print("1. Testing with stdin '5\\n10 20 30 40 50':")
r = ex.execute_student_code(code, stdin_input="5\n10 20 30 40 50")
print("Status:", r.status)
print("Stdout:", repr(r.stdout))
print("Exit code:", r.exit_code)
print("Stderr:", repr(r.stderr))

print("\n2. Testing with empty stdin:")
r2 = ex.execute_student_code(code, stdin_input="")
print("Status:", r2.status)
print("Stdout:", repr(r2.stdout))
print("Exit code:", r2.exit_code)

print("\n3. Testing with None stdin:")
r3 = ex.execute_student_code(code, stdin_input=None)
print("Status:", r3.status)
print("Stdout:", repr(r3.stdout))
print("Exit code:", r3.exit_code)
