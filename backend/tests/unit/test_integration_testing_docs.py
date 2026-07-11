"""Repository contracts for the backend integration testing guide."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
INTEGRATION_GUIDE = REPO_ROOT / "backend" / "docs" / "integration-testing.md"


def test_integration_guide_uses_current_migration_runner() -> None:
    contents = INTEGRATION_GUIDE.read_text(encoding="utf-8")

    assert "uv run python run_migrations.py" in contents
    assert "](../run_migrations.py)" in contents
    assert "backend/scripts/migrate-structure.sh" not in contents
