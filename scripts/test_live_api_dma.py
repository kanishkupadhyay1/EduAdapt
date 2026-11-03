import requests

# 1. Health check
res = requests.get('http://127.0.0.1:8000/health')
print('Health check status:', res.status_code, res.json())
assert res.status_code == 200

# 2. Test DMA Code Execution via API
dma_code = """#include <stdio.h>
#include <stdlib.h>

void createArray(int *array, int size);
void printArray(int *array, int size);

int main(void) {
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

# A. Test Run Code (is_submission=False)
payload_run = {
    'student_id': 'S001',
    'topic': 'Dynamic Memory Allocation',
    'source_code': dma_code,
    'stdin_input': '5\n10 20 30 40 50',
    'expected_output': None,
    'is_submission': False,
}
r_run = requests.post('http://127.0.0.1:8000/api/practice/execute', json=payload_run)
print('Run Code status:', r_run.status_code, r_run.json().get('status'))
assert r_run.json().get('status') == 'SUCCESS'
assert r_run.json().get('passed') is None

# B. Test Submit Code (is_submission=True, correct output)
payload_sub = {
    'student_id': 'S001',
    'topic': 'Dynamic Memory Allocation',
    'source_code': dma_code,
    'stdin_input': '5\n10 20 30 40 50',
    'expected_output': '10 20 30 40 50',
    'is_submission': True,
}
r_sub = requests.post('http://127.0.0.1:8000/api/practice/execute', json=payload_sub)
data_sub = r_sub.json()
print('Submit Code status:', r_sub.status_code, data_sub.get('status'))
assert data_sub.get('status') == 'ACCEPTED'
assert data_sub.get('passed') is True
assert data_sub.get('actual_output') == '10 20 30 40 50'
assert data_sub.get('updated_student') is not None
print('Learning Twin updated mastery:', data_sub.get('updated_student', {}).get('mastery'))

# C. Test Wrong Answer
payload_wrong = {
    'student_id': 'S001',
    'topic': 'Dynamic Memory Allocation',
    'source_code': dma_code,
    'stdin_input': '3\n1 2 3',
    'expected_output': '10 20 30 40 50',
    'is_submission': True,
}
r_wrong = requests.post('http://127.0.0.1:8000/api/practice/execute', json=payload_wrong)
data_wrong = r_wrong.json()
print('Wrong answer test:', data_wrong.get('status'))
assert data_wrong.get('status') == 'WRONG_ANSWER'
assert data_wrong.get('passed') is False

# D. Test Compilation Error Diagnostics
bad_code = "int main() { syntax error; }"
payload_bad = {
    'student_id': 'S001',
    'topic': 'Dynamic Memory Allocation',
    'source_code': bad_code,
    'is_submission': False,
}
r_bad = requests.post('http://127.0.0.1:8000/api/practice/execute', json=payload_bad)
data_bad = r_bad.json()
print('Compilation error test:', data_bad.get('status'))
assert data_bad.get('status') == 'COMPILATION_ERROR'
assert len(data_bad.get('compiler_output', '')) > 0

print('\nALL LIVE BACKEND API WORKFLOWS VERIFIED 100% SUCCESFULLY!')
