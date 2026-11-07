"""
Autonomous Sandbox Execution Engine
Quarantines candidate branches/PRs, runs automated unit tests, 
and evaluates compliance against constitutional baselines.
Governing Authority: Governing Officer Tarwater
"""

import os
import sys
import yaml
import subprocess
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

CONFIG_PATH = "governance_config.yaml"


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {"architectural_safeguards": {"quality_baseline": {"min_test_coverage_percent": 85.0}}}


def run_isolated_test_suite() -> tuple[bool, str]:
    """
    Executes pytest with coverage tracking in the current isolated workspace.
    Returns (success_status, test_output_log).
    """
    logging.info("Running isolated test suite with coverage enforcement...")
    
    config = load_config()
    min_cov = config["architectural_safeguards"]["quality_baseline"]["min_test_coverage_percent"]

    cmd = [
        sys.executable, "-m", "pytest",
        "--cov=.",
        f"--cov-fail-under={min_cov}",
        "-v"
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=120
        )
        output = result.stdout
        success = (result.returncode == 0)
        
        if success:
            logging.info("Sandbox test suite passed successfully with required coverage.")
        else:
            logging.warning("Sandbox test suite failed or breached quality baseline.")
            
        return success, output
    except subprocess.TimeoutExpired:
        return False, "ERROR: Test execution timed out after 120 seconds."
    except Exception as e:
        return False, f"ERROR: Exception during test execution: {str(e)}"


if __name__ == "__main__":
    passed, logs = run_isolated_test_suite()
    print(logs)
    sys.exit(0 if passed else 1)
