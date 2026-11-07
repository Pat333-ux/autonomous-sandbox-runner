"""
Autonomous Self-Healing Agent
Receives failing test tracebacks, queries an LLM for code patches,
applies fixes, and re-runs the sandbox.
Governing Authority: Governing Officer Tarwater
"""

import os
import sys
import logging
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


def request_llm_patch(failing_file: str, source_code: str, traceback_log: str) -> str:
    """Sends failing test output and source code to the LLM to generate a corrected patch."""
    api_key = os.getenv("LLM_API_KEY")
    api_url = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
    model = os.getenv("LLM_MODEL", "gpt-4o")

    if not api_key:
        raise EnvironmentError("Missing LLM_API_KEY for self-healing agent.")

    system_prompt = (
        "You are an expert Autonomous Self-Healing Agent operating under Governing Officer Tarwater. "
        "Your task is to fix Python code that failed a test suite. Analyze the error traceback, locate the bug, "
        "and return ONLY the corrected, complete Python code for the file with no markdown code fences or conversational text."
    )

    user_prompt = (
        f"Target File: {failing_file}\n\n"
        f"Failing Source Code:\n{source_code}\n\n"
        f"Test Traceback / Error Log:\n{traceback_log}\n\n"
        "Provide the corrected code that resolves this error."
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1
    }

    resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"].strip()

    if content.startswith("```"):
        lines = content.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    return content + "\n"
