#!/usr/bin/env python3
"""Guard the manually confirmed, read-only preservation inventory workflow."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "preservation-inventory.yml"
CLEANUP_WORKFLOW = ROOT / ".github" / "workflows" / "database-cleanup.yml"
STORAGE_CLI = ROOT / "backend" / "src" / "waittime" / "cli" / "storage_stats.py"
DATABASE_SERVICE = ROOT / "backend" / "src" / "waittime" / "services" / "database.py"

EXPECTED_STEPS = [
    "Checkout reviewed dispatch SHA",
    "Set up Python",
    "Install locked backend dependencies",
    "Run read-only preservation inventory",
]
INVENTORY_COMMAND = (
    "uv run --no-sync python -m waittime.cli.storage_stats --preservation-inventory"
)
DATABASE_SECRET = "$" + "{{ secrets.DATABASE_URL }}"
EXACT_SHA_REF = "$" + "{{ github.sha }}"


def _step_block(text: str, step_name: str) -> str:
    marker = f"      - name: {step_name}"
    start = text.find(marker)
    if start == -1:
        raise AssertionError(f"Missing workflow step: {step_name}")
    next_step = text.find("\n      - name: ", start + len(marker))
    return text[start:] if next_step == -1 else text[start:next_step]


def _run_body(step: str) -> str | None:
    block = re.search(
        r"(?ms)^        run: \|\n(?P<body>(?:^          .*\n)+)",
        step,
    )
    if block:
        return "\n".join(
            line[10:] for line in block.group("body").rstrip("\n").splitlines()
        )
    inline = re.search(r"(?m)^        run: (.+)$", step)
    return inline.group(1) if inline else None


def _workflow_failures(
    text: str,
    cleanup_text: str,
    cli_text: str,
    database_text: str,
) -> list[str]:
    failures: list[str] = []

    if "on:\n  workflow_dispatch:\n" not in text:
        failures.append("workflow must be manual-dispatch only")
    else:
        trigger_block = text.split("on:\n", 1)[1].split("\npermissions:\n", 1)[0]
        event_names = re.findall(r"(?m)^  ([A-Za-z0-9_-]+):\s*$", trigger_block)
        input_names = re.findall(r"(?m)^      ([A-Za-z0-9_-]+):\s*$", trigger_block)
        if event_names != ["workflow_dispatch"]:
            failures.append("workflow must have no schedule, push, or other trigger")
        if input_names != ["confirm_production_inventory"]:
            failures.append("workflow may expose only the confirmation boolean input")

    required_input_contract = [
        'description: "I am authorized to run this production inventory',
        "detailed per-source/metric counts and date ranges",
        "public Actions logs.",
        "        required: true",
        "        type: boolean",
        "        default: false",
    ]
    if any(value not in text for value in required_input_contract):
        failures.append(
            "confirmation must be required, boolean, default false, and disclose public output"
        )

    if not re.search(r"(?m)^permissions:\n  contents: read\n$", text):
        failures.append("workflow permission must be limited to contents: read")
    cleanup_lock = (
        "concurrency:\n  group: database-cleanup\n  cancel-in-progress: false"
    )
    if cleanup_lock not in text or cleanup_lock not in cleanup_text:
        failures.append(
            "inventory must share the existing non-cancelling database-cleanup lock"
        )

    job_names = re.findall(
        r"(?m)^  ([A-Za-z0-9_-]+):\s*$", text.split("jobs:\n", 1)[-1]
    )
    if job_names != ["preservation-inventory"]:
        failures.append("workflow must contain only its single inventory job")

    guard_match = re.search(
        r"(?ms)^    if: >-\n(?P<guard>(?:^      .*\n)+)",
        text,
    )
    normalized_guard = (
        " ".join(guard_match.group("guard").split()) if guard_match else ""
    )
    guard_conditions = [
        "github.event_name == 'workflow_dispatch'",
        "github.ref == 'refs/heads/main'",
        "inputs.confirm_production_inventory == true",
    ]
    if any(condition not in normalized_guard for condition in guard_conditions):
        failures.append(
            "job must require manual dispatch, main ref, and explicit confirmation"
        )
    if not re.search(r"(?m)^    timeout-minutes: 15$", text):
        failures.append("inventory job must have a 15-minute hard timeout")

    steps = re.findall(r"(?m)^      - name: (.+)$", text)
    if steps != EXPECTED_STEPS:
        failures.append(
            "workflow steps must remain limited to checkout, setup, locked install, inventory"
        )
        return failures

    checkout_step = _step_block(text, EXPECTED_STEPS[0])
    setup_step = _step_block(text, EXPECTED_STEPS[1])
    install_step = _step_block(text, EXPECTED_STEPS[2])
    inventory_step = _step_block(text, EXPECTED_STEPS[3])
    required_values = [
        "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0",
        "ref: ${{ github.sha }}",
        "persist-credentials: false",
        "actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405",
        'python-version: "3.12"',
        'python -m pip install "uv==0.11.23"',
        "uv sync --locked --no-dev",
    ]
    if any(value not in text for value in required_values):
        failures.append(
            "workflow must use pinned actions, exact SHA checkout, and locked dependencies"
        )
    if checkout_step.count(EXACT_SHA_REF) != 1:
        failures.append("checkout must use the exact dispatch SHA")
    action_refs = re.findall(r"(?m)^        uses: (.+)$", text)
    if action_refs != [
        "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0",
        "actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405",
    ]:
        failures.append("workflow may use only the two pinned setup actions")
    if "timeout-minutes: 2" not in checkout_step:
        failures.append("checkout step must have a finite two-minute timeout")
    if "timeout-minutes: 2" not in setup_step:
        failures.append("Python setup step must have a finite two-minute timeout")
    if "timeout-minutes: 8" not in install_step:
        failures.append(
            "dependency installation must have a finite eight-minute timeout"
        )
    if "timeout-minutes: 2" not in inventory_step:
        failures.append("inventory step must have a finite two-minute timeout")

    if text.count("run:") != 2:
        failures.append(
            "workflow must have only the fixed dependency install and inventory commands"
        )
    if _run_body(install_step) != (
        'python -m pip install "uv==0.11.23"\nuv sync --locked --no-dev'
    ):
        failures.append(
            "dependency setup must be limited to pinned uv and locked dependencies"
        )
    if _run_body(inventory_step) != INVENTORY_COMMAND:
        failures.append("inventory must invoke only the fixed read-only CLI command")

    if text.count(DATABASE_SECRET) != 1 or DATABASE_SECRET not in inventory_step:
        failures.append("DATABASE_URL may be exposed only to the fixed inventory step")
    prefix_before_inventory = text.split(
        "      - name: Run read-only preservation inventory", 1
    )[0]
    if (
        "DATABASE_URL" in prefix_before_inventory
        or "secrets." in prefix_before_inventory
    ):
        failures.append(
            "no database credential may be available before confirmation-gated inventory"
        )
    if "environment:" in text:
        failures.append(
            "workflow must not assume an unverified protected GitHub environment"
        )
    if 'PGCONNECT_TIMEOUT: "10"' not in inventory_step:
        failures.append(
            "database connection must have a finite ten-second connect timeout"
        )
    if 'PGOPTIONS: "-c lock_timeout=2000ms"' not in inventory_step:
        failures.append("database lock waits must have a finite two-second timeout")

    forbidden = [
        "schedule:",
        "workflow_call:",
        "workflow_run:",
        "upload-artifact",
        "actions/cache",
        "waittime.cli.scraper",
        "waittime.cli.cleanup",
        "waittime.cli.aggregate",
        "check_heartbeat",
        "refresh_analytics",
        "continue-on-error",
        "|| true",
    ]
    if any(value in text for value in forbidden):
        failures.append(
            "workflow must not add scheduling, writes, artifacts, or follow-on operations"
        )

    if (
        "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"
        not in database_text
    ):
        failures.append(
            "inventory implementation must retain its read-only transaction"
        )
    if 'PRESERVATION_INVENTORY_STATEMENT_TIMEOUT = "5000ms"' not in database_text:
        failures.append(
            "inventory implementation must retain its five-second statement timeout"
        )
    if "--preservation-inventory" not in cli_text:
        failures.append("workflow must use the existing preservation inventory CLI")

    return failures


def _mutation_failures(
    text: str,
    cleanup_text: str,
    cli_text: str,
    database_text: str,
) -> list[str]:
    mutations = [
        (
            "default confirmation",
            "        default: false",
            "        default: true",
        ),
        (
            "confirmation job gate",
            "          inputs.confirm_production_inventory == true }}",
            "          false }}",
        ),
        (
            "main-ref gate",
            "github.ref == 'refs/heads/main'",
            "github.ref == 'refs/heads/feature'",
        ),
        (
            "exact SHA checkout",
            "ref: ${{ github.sha }}",
            "ref: main",
        ),
        (
            "scheduled trigger",
            "\npermissions:\n",
            "\n  schedule:\n    - cron: '0 * * * *'\n\npermissions:\n",
        ),
        (
            "unbounded command input",
            "        default: false\n\npermissions:\n",
            "        default: false\n      command:\n"
            '        description: "Command to execute"\n'
            "        required: false\n"
            "        type: string\n\npermissions:\n",
        ),
        (
            "credential outside gated step",
            "    runs-on: ubuntu-latest\n",
            "    runs-on: ubuntu-latest\n"
            "    env:\n"
            "      DATABASE_URL: $" + "{{ secrets.DATABASE_URL }}\n",
        ),
        (
            "write-capable permission",
            "  contents: read",
            "  contents: write",
        ),
        (
            "destructive CLI",
            INVENTORY_COMMAND,
            "uv run python -m waittime.cli.cleanup --confirm-delete",
        ),
        (
            "artifact publication",
            "      - name: Run read-only preservation inventory\n",
            "      - name: Upload inventory artifact\n"
            "        uses: actions/upload-artifact@v4\n\n"
            "      - name: Run read-only preservation inventory\n",
        ),
        (
            "extra inventory shell command",
            "run: " + INVENTORY_COMMAND,
            "run: " + INVENTORY_COMMAND + " && echo extra",
        ),
        (
            "extra dependency shell command",
            "          uv sync --locked --no-dev\n",
            "          uv sync --locked --no-dev\n"
            "          python -m waittime.cli.cleanup --confirm-delete\n",
        ),
    ]
    failures: list[str] = []
    for label, needle, replacement in mutations:
        if needle not in text:
            failures.append(f"could not construct {label} mutation test")
            continue
        mutated_text = text.replace(needle, replacement, 1)
        if not _workflow_failures(mutated_text, cleanup_text, cli_text, database_text):
            failures.append(f"workflow checker did not reject {label} mutation")
    return failures


def _main() -> int:
    text = WORKFLOW.read_text(encoding="utf-8")
    cleanup_text = CLEANUP_WORKFLOW.read_text(encoding="utf-8")
    cli_text = STORAGE_CLI.read_text(encoding="utf-8")
    database_text = DATABASE_SERVICE.read_text(encoding="utf-8")

    failures = _workflow_failures(text, cleanup_text, cli_text, database_text)
    if not failures:
        failures.extend(_mutation_failures(text, cleanup_text, cli_text, database_text))

    if failures:
        print("Preservation inventory workflow guardrail check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(
        "OK: preservation inventory is manual, confirmed, read-only, bounded, and public-log disclosed."
    )
    print(
        "OK: mutation tests reject missing gates, expanded triggers/inputs, and writes."
    )
    return 0


if __name__ == "__main__":
    sys.exit(_main())
