from pathlib import Path

WORKFLOW_PATH = (
    Path(__file__).resolve().parents[3] / ".github" / "workflows" / "database-cleanup.yml"
)


def test_database_cleanup_workflow_requires_explicit_confirmation():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "workflow_dispatch:\n    inputs:\n      confirm_delete:\n" in workflow
    assert "        required: true\n        type: boolean\n        default: false\n" in workflow
    assert "    if: ${{ inputs.confirm_delete == true }}\n" in workflow
    assert "python -m waittime.cli.cleanup" in workflow
    assert "--confirm-delete" in workflow
    assert "schedule:" not in workflow
