"""
Autonomous Self-Healing Quarantine Loop
Runs isolated tests, parses failing tracebacks, applies LLM patches,
and verifies fixes before promoting PRs to Governing Officer Tarwater.
Governing Authority: Governing Officer Tarwater
"""

import os
import re
import sys
import logging
import subprocess
from sandbox_executor import run_isolated_test_suite
from auto_healer import request_llm_patch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

MAX_HEAL_ATTEMPTS = 3


def extract_failing_file(traceback_log: str) -> str | None:
    """
    Parses pytest failure output to locate the non-test Python source file
    most likely responsible for the failure.
    """
    # Matches standard pytest traceback lines like: path/to/file.py:42: in some_func
    matches = re.findall(r"([a-zA-Z0-9_\-./]+\.py):\d+:", traceback_log)
    
    # Prefer application/engine modules over test files when patching
    for filepath in reversed(matches):
        clean_path = filepath.lstrip("./")
        if os.path.exists(clean_path) and not os.path.basename(clean_path).startswith("test_"):
            if clean_path not in ("sandbox_executor.py", "auto_healer.py", "heal_loop.py"):
                return clean_path

    # Fallback: if only a test file is listed (e.g. syntax/import error in generated test)
    for filepath in reversed(matches):
        clean_path = filepath.lstrip("./")
        if os.path.exists(clean_path) and os.path.basename(clean_path).startswith("test_"):
            return clean_path

    return None


def commit_healed_changes(patched_files: set[str]) -> None:
    """Commits verified self-healing patches back to the active PR branch."""
    if not patched_files:
        return

    try:
        subprocess.run(["git", "config", "--local", "user.email", "sandbox-healer@autonomous-governance.local"], check=True)
        subprocess.run(["git", "config", "--local", "user.name", "Autonomous Sandbox Healer"], check=True)
        
        for f in patched_files:
            subprocess.run(["git", "add", f], check=True)
            
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if status.stdout.strip():
            file_list = ", ".join(sorted(patched_files))
            subprocess.run(
                ["git", "commit", "-m", f"[SANDBOX-HEAL] Auto-patched failing modules: {file_list}"],
                check=True
            )
            subprocess.run(["git", "push"], check=True)
            logging.info(f"Pushed healed commits for: {file_list}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Git commit/push failed during self-healing: {e}")


def execute_quarantine_and_heal() -> int:
    """Main closed-loop quarantine and self-healing execution pipeline."""
    patched_files = set()

    for attempt in range(1, MAX_HEAL_ATTEMPTS + 1):
        logging.info(f"--- Quarantine Verification Pass {attempt}/{MAX_HEAL_ATTEMPTS} ---")
        passed, logs = run_isolated_test_suite()

        if passed:
            logging.info("VERIFICATION PASSED: All tests and coverage thresholds met.")
            if patched_files:
                commit_healed_changes(patched_files)
            return 0

        logging.warning(f"Attempt {attempt} failed. Analyzing traceback for self-healing...")
        failing_file = extract_failing_file(logs)

        if not failing_file:
            logging.error("Could not isolate a specific failing source file from traceback. Escalating to Tarwater.")
            print(logs)
            return 1

        logging.info(f"Target isolated for self-healing: {failing_file}")
        with open(failing_file, "r", encoding="utf-8") as f:
            broken_code = f.read()

        try:
            patched_code = request_llm_patch(failing_file, broken_code, logs)
            with open(failing_file, "w", encoding="utf-8") as f:
                f.write(patched_code)
            patched_files.add(failing_file)
            logging.info(f"Applied LLM patch to {failing_file}. Re-running sandbox verification...")
        except Exception as e:
            logging.error(f"Self-healing patch generation failed: {e}")
            return 1

    logging.critical(
        f"ESCALATION REQUIRED: Candidate code failed sandbox verification after {MAX_HEAL_ATTEMPTS} "
        "self-healing attempts. Flagging PR for Governing Officer Tarwater."
    )
    return 1


if __name__ == "__main__":
    sys.exit(execute_quarantine_and_heal())
