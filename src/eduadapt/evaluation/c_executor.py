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
    Path(r"C:\MinGW\bin\gcc.exe"),
    Path(r"C:\Program Files\MinGW\bin\gcc.exe"),
    Path(r"C:\msys64\mingw64\bin\gcc.exe"),
]


def discover_c_compiler(explicit_path: Optional[str] = None) -> Optional[str]:
    """Discover a locally installed C compiler.

    Priority:
    1. Explicitly provided path if valid.
    2. Known MinGW installation at C:\\MinGW\\bin\\gcc.exe.
    3. 'gcc' on system PATH via shutil.which.

    Returns:
        Absolute path to the compiler executable, or None if no compiler is found.
    """
    if explicit_path:
        p = Path(explicit_path)
        if p.is_file():
            return str(p.resolve())

    # Check known MinGW installation paths
    for p in DEFAULT_GCC_PATHS:
        if p.is_file():
            return str(p.resolve())

    # Check PATH for gcc
    which_gcc = shutil.which("gcc")
    if which_gcc:
        return str(Path(which_gcc).resolve())

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

    def execute_trusted_reference(
        self,
        source_code: str,
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
            try:
                exec_proc = subprocess.run(
                    [str(exe_file)],
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
                return CodeExecutionResult(
                    status=ExecutionStatus.TIMEOUT,
                    is_trusted_reference=True,
                    source_code=source_code,
                    compiler_used=self.compiler_path,
                    compiler_output=comp_proc.stderr,
                    execution_time_seconds=round(exec_time, 4),
                    notes=f"Execution timed out after {timeout} seconds.",
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
