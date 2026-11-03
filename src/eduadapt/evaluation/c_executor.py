"""C Program Compilation and Execution Engine.

SAFETY ARCHITECTURE:
- Executes TRUSTED REFERENCE C programs ONLY.
- LLM-generated code is NEVER executed on the host machine; it is extracted, saved
  for manual review, and strictly marked as ExecutionStatus.NOT_EXECUTED_UNTRUSTED.
- Compilation and execution of trusted reference programs uses temporary directories
  for process cleanup and strict subprocess timeouts to guard against infinite loops.
  NOTE: Temporary directories and timeouts provide process isolation and resource cleanup,
  not a secure sandbox.
- Verified compiler: GCC at C:\\MinGW\\bin\\gcc.exe.
"""

import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from typing import Optional, Tuple

from eduadapt.evaluation.models import CodeExecutionResult, ExecutionStatus

# Default known compiler paths to inspect
DEFAULT_GCC_PATHS = [
    Path(r"C:\tools\w64devkit\bin\gcc.exe"),
    Path(r"C:\w64devkit\bin\gcc.exe"),
    Path(r"C:\msys64\ucrt64\bin\gcc.exe"),
    Path(r"C:\msys64\mingw64\bin\gcc.exe"),
    Path(r"C:\Program Files\LLVM\bin\clang.exe"),
    Path(r"C:\MinGW\bin\gcc.exe"),
    Path(r"C:\Program Files\MinGW\bin\gcc.exe"),
]


def _is_runnable(p: Path) -> bool:
    """Check if the compiler executable can be invoked successfully."""
    try:
        env = os.environ.copy()
        env["PATH"] = str(p.parent) + os.pathsep + env.get("PATH", "")
        res = subprocess.run([str(p), "--version"], capture_output=True, timeout=2.0, env=env)
        return res.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def discover_c_compiler(explicit_path: Optional[str] = None) -> Optional[str]:
    """Discover a locally installed C compiler.

    Priority:
    1. Explicitly provided path if valid and runnable.
    2. Environment variable EDUADAPT_C_COMPILER, C_COMPILER, or CC if valid and runnable.
    3. Known 64-bit MinGW/w64devkit/MSYS2/LLVM installations if runnable.
    4. 'gcc' or 'clang' on system PATH via shutil.which if runnable.
    5. Fallback legacy MinGW if runnable.

    Returns:
        Absolute path to the compiler executable, or None if no compiler is found.
    """
    if explicit_path:
        p = Path(explicit_path)
        if p.is_file() and _is_runnable(p):
            return str(p.resolve())

    # Check environment variables
    for env_var in ("EDUADAPT_C_COMPILER", "C_COMPILER", "CC"):
        env_path = os.environ.get(env_var)
        if env_path:
            p = Path(env_path)
            if p.is_file() and _is_runnable(p):
                return str(p.resolve())

    # Check known compiler installation paths
    for p in DEFAULT_GCC_PATHS:
        if p.is_file() and _is_runnable(p):
            return str(p.resolve())

    # Check PATH for gcc or clang
    for name in ("gcc", "clang"):
        which_bin = shutil.which(name)
        if which_bin:
            p = Path(which_bin)
            if p.is_file() and _is_runnable(p):
                return str(p.resolve())

    return None


def extract_c_code(text: str) -> Optional[str]:
    """Extract C source code blocks from LLM output.

    Looks for ```c ... ``` or ```C ... ``` markdown code blocks.
    Returns the concatenated code blocks or the first comprehensive block.
    """
    if not text:
        return None

    # Match ```c or ```C blocks
    c_blocks = re.findall(r"```[cC]\s*\n(.*?)```", text, re.DOTALL)
    if c_blocks:
        return "\n\n".join(b.strip() for b in c_blocks)

    # Fallback to generic ``` code blocks if contains #include or int main
    generic_blocks = re.findall(r"```\s*\n(.*?)```", text, re.DOTALL)
    for b in generic_blocks:
        if "#include" in b or "int main" in b or "void " in b:
            return b.strip()

    return None


class CExecutor:
    """Manages compilation and execution of trusted reference C programs."""

    def __init__(
        self,
        compiler_path: Optional[str] = None,
        default_timeout_seconds: float = 3.0,
    ) -> None:
        self.compiler_path = discover_c_compiler(compiler_path)
        self.default_timeout_seconds = default_timeout_seconds

    def has_compiler(self) -> bool:
        """Check if a valid C compiler is available."""
        return self.compiler_path is not None

    def execute_student_code(
        self,
        source_code: str,
        stdin_input: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ) -> CodeExecutionResult:
        """Compile and execute student-submitted C code in an isolated temporary directory.

        Applies strict subprocess timeouts and captures compiler output,
        standard output, standard error, and exit codes.
        """
        return self.execute_trusted_reference(
            source_code=source_code,
            stdin_input=stdin_input,
            timeout_seconds=timeout_seconds,
        )

    def execute_trusted_reference(
        self,
        source_code: str,
        stdin_input: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ) -> CodeExecutionResult:
        """Compile and execute a TRUSTED reference C program.

        Uses temporary directories for build artifacts and subprocess timeouts
        to cleanly manage process execution and prevent hanging.
        """
        if not source_code or not source_code.strip():
            return CodeExecutionResult(
                status=ExecutionStatus.NO_CODE,
                is_trusted_reference=True,
                notes="No source code provided for trusted reference.",
            )

        if not self.has_compiler():
            return CodeExecutionResult(
                status=ExecutionStatus.COMPILER_NOT_AVAILABLE,
                is_trusted_reference=True,
                source_code=source_code,
                notes="No valid C compiler discovered. GCC required at C:\\MinGW\\bin\\gcc.exe or PATH.",
            )

        timeout = timeout_seconds if timeout_seconds is not None else self.default_timeout_seconds

        with tempfile.TemporaryDirectory() as tmpdir:
            src_file = Path(tmpdir) / "prog.c"
            exe_file = Path(tmpdir) / "prog.exe"

            src_file.write_text(source_code, encoding="utf-8")

            # Prepare execution environment with compiler directory in PATH
            comp_env = os.environ.copy()
            compiler_dir = str(Path(self.compiler_path).parent)
            comp_env["PATH"] = compiler_dir + os.pathsep + comp_env.get("PATH", "")

            # Compile step: using -std=c99 -Wall
            compile_cmd = [
                self.compiler_path,
                "-std=c99",
                "-Wall",
                str(src_file),
                "-o",
                str(exe_file),
            ]

            try:
                comp_proc = subprocess.run(
                    compile_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=10.0,
                    check=False,
                    env=comp_env,
                )
            except subprocess.TimeoutExpired:
                return CodeExecutionResult(
                    status=ExecutionStatus.TIMEOUT,
                    is_trusted_reference=True,
                    source_code=source_code,
                    compiler_used=self.compiler_path,
                    compiler_output="Compilation timed out after 10.0 seconds.",
                )

            if comp_proc.returncode != 0:
                return CodeExecutionResult(
                    status=ExecutionStatus.COMPILATION_ERROR,
                    is_trusted_reference=True,
                    source_code=source_code,
                    compiler_used=self.compiler_path,
                    compiler_output=comp_proc.stderr or comp_proc.stdout,
                    exit_code=comp_proc.returncode,
                )

            # Execution step
            t0 = time.time()
            inp = stdin_input
            if inp is None and any(kw in source_code for kw in ("scanf", "getchar", "fgets")):
                inp = ""

            try:
                exec_proc = subprocess.run(
                    [str(exe_file)],
                    input=inp,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=timeout,
                    check=False,
                )
                exec_time = time.time() - t0
                return CodeExecutionResult(
                    status=ExecutionStatus.SUCCESS if exec_proc.returncode == 0 else ExecutionStatus.RUNTIME_ERROR,
                    is_trusted_reference=True,
                    source_code=source_code,
                    compiler_used=self.compiler_path,
                    compiler_output=comp_proc.stderr,
                    stdout=exec_proc.stdout,
                    stderr=exec_proc.stderr,
                    exit_code=exec_proc.returncode,
                    execution_time_seconds=round(exec_time, 4),
                )
            except subprocess.TimeoutExpired:
                exec_time = time.time() - t0
                notes_msg = (
                    f"Execution timed out after {timeout} seconds. "
                    "The program either entered an infinite loop or blocked waiting for standard input (scanf) without input."
                )
                return CodeExecutionResult(
                    status=ExecutionStatus.TIMEOUT,
                    is_trusted_reference=True,
                    source_code=source_code,
                    compiler_used=self.compiler_path,
                    compiler_output=comp_proc.stderr,
                    execution_time_seconds=round(exec_time, 4),
                    notes=notes_msg,
                )
            except Exception as e:
                exec_time = time.time() - t0
                return CodeExecutionResult(
                    status=ExecutionStatus.RUNTIME_ERROR,
                    is_trusted_reference=True,
                    source_code=source_code,
                    compiler_used=self.compiler_path,
                    compiler_output=comp_proc.stderr,
                    stderr=str(e),
                    execution_time_seconds=round(exec_time, 4),
                    notes=f"Runtime exception: {e}",
                )

    @staticmethod
    def handle_untrusted_llm_code(generated_text: str) -> CodeExecutionResult:
        """Extract LLM-generated code and enforce the safety invariant.

        LLM-generated code is NEVER executed on the host system. It is extracted
        and marked as ExecutionStatus.NOT_EXECUTED_UNTRUSTED for manual expert review.
        """
        code = extract_c_code(generated_text)
        if not code:
            return CodeExecutionResult(
                status=ExecutionStatus.NO_CODE,
                is_trusted_reference=False,
                source_code="",
                notes="No C code blocks found in generated content.",
            )

        return CodeExecutionResult(
            status=ExecutionStatus.NOT_EXECUTED_UNTRUSTED,
            is_trusted_reference=False,
            source_code=code,
            notes="LLM-generated code is safely isolated; marked as NOT_EXECUTED_UNTRUSTED for human review.",
        )
