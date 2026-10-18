from __future__ import annotations

import importlib.util
import json
import sys
import urllib.parse
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
DISPATCHER_PATH = REPO_ROOT / "backend" / "scripts" / "waittime_github_dispatcher.py"


def _load_dispatcher():
    spec = importlib.util.spec_from_file_location("waittime_github_dispatcher", DISPATCHER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _now(minute: int = 40) -> datetime:
    return datetime(2026, 10, 18, 13, minute, 12, tzinfo=UTC)


class FakeGitHub:
    def __init__(
        self,
        *,
        recent_event: str | None = None,
        active_status: str | None = None,
        post_status: int = 200,
        post_response: object | None = None,
    ) -> None:
        self.recent_event = recent_event
        self.active_status = active_status
        self.post_status = post_status
        self.post_response = (
            {"workflow_run_id": 123456, "run_url": "ignored", "html_url": "ignored"}
            if post_response is None
            else post_response
        )
        self.calls: list[tuple[str, str, str, object | None]] = []

    def __call__(
        self,
        method: str,
        path: str,
        token: str,
        payload: object | None,
    ) -> tuple[int, object | None]:
        self.calls.append((method, path, token, payload))
        if method == "POST":
            return self.post_status, self.post_response

        query = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)
        status_filter = query.get("status", [None])[0]
        event_filter = query.get("event", [None])[0]
        if self.active_status is not None and status_filter == self.active_status:
            return 200, {
                "total_count": 1,
                "workflow_runs": [{"id": 99, "status": status_filter}],
            }
        if self.recent_event is not None and event_filter == self.recent_event:
            return 200, {
                "total_count": 1,
                "workflow_runs": [{"id": 88, "event": event_filter}],
            }
        return 200, {"total_count": 0, "workflow_runs": []}


def _dispatch(module, tmp_path: Path, api: Any, **overrides: object):
    arguments: dict[str, object] = {
        "now": _now(),
        "execute": True,
        "enabled": True,
        "token": "test-token-not-a-secret",
        "state_file": tmp_path / "ledger.json",
        "api_request": api,
        "clock": lambda: _now(),
    }
    arguments.update(overrides)
    return module.dispatch_once(**arguments)


def _ledger(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _slot_entry(path: Path) -> dict[str, object]:
    ledger = _ledger(path)
    slots = ledger["slots"]
    assert isinstance(slots, dict)
    entry = slots["2026-10-18T13:29:00Z"]
    assert isinstance(entry, dict)
    return entry


@pytest.mark.unit
def test_dry_run_and_eligibility_window_are_io_free(tmp_path: Path) -> None:
    dispatcher = _load_dispatcher()
    calls: list[object] = []

    def no_api(*args: object, **kwargs: object) -> object:
        calls.append((args, kwargs))
        raise AssertionError("dry run must not contact the API")

    for minute in (39, 40, 43):
        result = dispatcher.dispatch_once(
            now=_now(minute),
            execute=False,
            enabled=False,
            token=None,
            state_file=tmp_path / "ledger.json",
            api_request=no_api,
        )
        assert result.status == "dry_run"
        assert result.slot == "2026-10-18T13:29:00Z"

    for minute in (38, 44):
        result = dispatcher.dispatch_once(
            now=_now(minute),
            execute=False,
            enabled=False,
            token=None,
            state_file=tmp_path / "ledger.json",
            api_request=no_api,
        )
        assert result.reason == "outside_eligibility_window"

    assert calls == []
    assert not (tmp_path / "ledger.json").exists()


@pytest.mark.unit
def test_explicit_execution_requires_default_off_gate_before_api(tmp_path: Path) -> None:
    dispatcher = _load_dispatcher()
    api = FakeGitHub()

    result = _dispatch(dispatcher, tmp_path, api, enabled=False)

    assert result.reason == "execution_disabled"
    assert api.calls == []
    assert not (tmp_path / "ledger.json").exists()


@pytest.mark.unit
def test_success_persists_intent_before_post_then_receipt_without_urls(tmp_path: Path) -> None:
    dispatcher = _load_dispatcher()
    state_file = tmp_path / "ledger.json"

    class InspectingGitHub(FakeGitHub):
        def __call__(self, method: str, path: str, token: str, payload: object | None):
            if method == "POST":
                assert _slot_entry(state_file)["state"] == "in_flight"
                assert path.endswith("/dispatches")
                assert payload == {
                    "ref": "main",
                    "inputs": {"refresh_analytics": False},
                    "return_run_details": True,
                }
            return super().__call__(method, path, token, payload)

    api = InspectingGitHub()
    result = _dispatch(dispatcher, tmp_path, api)

    assert result.status == "accepted"
    assert result.run_id == 123456
    entry = _slot_entry(state_file)
    assert entry["state"] == "accepted"
    assert entry["run_id"] == 123456
    assert "run_url" not in entry and "html_url" not in entry
    assert len([call for call in api.calls if call[0] == "POST"]) == 1


@pytest.mark.unit
@pytest.mark.parametrize("state", ["in_flight", "accepted", "ambiguous"])
def test_any_existing_slot_state_blocks_second_post(tmp_path: Path, state: str) -> None:
    dispatcher = _load_dispatcher()
    state_file = tmp_path / "ledger.json"
    state_file.write_text(
        json.dumps(
            {
                "version": 1,
                "slots": {
                    "2026-10-18T13:29:00Z": {
                        "state": state,
                        "updated_at": "2026-10-18T13:40:00Z",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    state_file.chmod(0o600)
    api = FakeGitHub()

    result = _dispatch(dispatcher, tmp_path, api)

    assert result.reason == "slot_already_attempted"
    assert api.calls == []


@pytest.mark.unit
@pytest.mark.parametrize("event", ["schedule", "workflow_dispatch"])
def test_recent_scheduled_or_manual_run_blocks_dispatch(tmp_path: Path, event: str) -> None:
    dispatcher = _load_dispatcher()
    api = FakeGitHub(recent_event=event)

    result = _dispatch(dispatcher, tmp_path, api)

    assert result.reason == "recent_workflow_run"
    assert not any(call[0] == "POST" for call in api.calls)
    recent_calls = [
        call
        for call in api.calls
        if "created" in urllib.parse.parse_qs(urllib.parse.urlparse(call[1]).query)
    ]
    assert len(recent_calls) == (1 if event == "schedule" else 2)
    assert "created=%3E%3D2026-10-18T13%3A29%3A00Z" in recent_calls[-1][1]


@pytest.mark.unit
def test_old_active_run_blocks_dispatch_without_date_filter(tmp_path: Path) -> None:
    dispatcher = _load_dispatcher()
    api = FakeGitHub(active_status="waiting")

    result = _dispatch(dispatcher, tmp_path, api)

    assert result.reason == "active_workflow_run"
    assert not any(call[0] == "POST" for call in api.calls)
    active_calls = [
        call
        for call in api.calls
        if "status" in urllib.parse.parse_qs(urllib.parse.urlparse(call[1]).query)
    ]
    assert len(active_calls) == 4
    assert all("created" not in call[1] for call in active_calls)


@pytest.mark.unit
def test_incomplete_recent_page_fails_closed(tmp_path: Path) -> None:
    dispatcher = _load_dispatcher()

    def incomplete_api(
        method: str, path: str, token: str, payload: object | None
    ) -> tuple[int, object | None]:
        query = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)
        if method == "GET" and "status" in query:
            return 200, {"total_count": 0, "workflow_runs": []}
        if method == "GET" and query.get("event") == ["schedule"]:
            page = int(query["page"][0])
            if page == 1:
                return 200, {
                    "total_count": 101,
                    "workflow_runs": [{"id": i + 1, "event": "schedule"} for i in range(100)],
                }
            return 200, {"total_count": 101, "workflow_runs": []}
        return 200, {"total_count": 0, "workflow_runs": []}

    result = _dispatch(dispatcher, tmp_path, incomplete_api)

    assert result.reason == "incomplete_run_list"


@pytest.mark.unit
def test_unknown_active_status_response_fails_closed(tmp_path: Path) -> None:
    dispatcher = _load_dispatcher()

    def malformed_api(
        method: str, path: str, token: str, payload: object | None
    ) -> tuple[int, object | None]:
        query = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)
        if query.get("status") == ["queued"]:
            return 200, {
                "total_count": 1,
                "workflow_runs": [{"id": 90, "status": "future_status"}],
            }
        return 200, {"total_count": 0, "workflow_runs": []}

    result = _dispatch(dispatcher, tmp_path, malformed_api)

    assert result.reason == "malformed_active_run_record"


@pytest.mark.unit
def test_corrupt_ledger_fails_closed_before_api(tmp_path: Path) -> None:
    dispatcher = _load_dispatcher()
    state_file = tmp_path / "ledger.json"
    state_file.write_text("not json", encoding="utf-8")
    api = FakeGitHub()

    result = _dispatch(dispatcher, tmp_path, api)

    assert result.reason == "ledger_unavailable"
    assert api.calls == []


@pytest.mark.unit
def test_malformed_ledger_shape_fails_closed_before_api(tmp_path: Path) -> None:
    dispatcher = _load_dispatcher()
    state_file = tmp_path / "ledger.json"
    state_file.write_text('{"version":1,"slots":[]}', encoding="utf-8")
    state_file.chmod(0o600)
    api = FakeGitHub()

    result = _dispatch(dispatcher, tmp_path, api, state_file=state_file)

    assert result.reason == "ledger_unavailable"
    assert api.calls == []


@pytest.mark.unit
def test_busy_local_lock_fails_closed(tmp_path: Path) -> None:
    dispatcher = _load_dispatcher()
    state_file = tmp_path / "ledger.json"
    api = FakeGitHub()

    with dispatcher._slot_lock(state_file):
        result = _dispatch(dispatcher, tmp_path, api)

    assert result.reason == "another_local_dispatcher_active"
    assert api.calls == []


@pytest.mark.unit
def test_local_lock_oserror_is_sanitized_and_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dispatcher = _load_dispatcher()
    api = FakeGitHub()

    def fail_lock(*args: object, **kwargs: object) -> None:
        raise PermissionError("private local lock detail")

    monkeypatch.setattr(dispatcher.fcntl, "flock", fail_lock)

    result = _dispatch(dispatcher, tmp_path, api)

    assert result.reason == "ledger_unavailable"
    assert api.calls == []


@pytest.mark.unit
def test_symlink_state_parent_is_rejected(tmp_path: Path) -> None:
    dispatcher = _load_dispatcher()
    real_parent = tmp_path / "owned-state"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked-state"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    api = FakeGitHub()

    result = _dispatch(
        dispatcher,
        tmp_path,
        api,
        state_file=linked_parent / "ledger.json",
    )

    assert result.reason == "ledger_unavailable"
    assert api.calls == []


@pytest.mark.unit
def test_lost_post_response_is_ambiguous_and_never_retried(tmp_path: Path) -> None:
    dispatcher = _load_dispatcher()
    state_file = tmp_path / "ledger.json"

    class LostResponse(FakeGitHub):
        def __call__(self, method: str, path: str, token: str, payload: object | None):
            if method == "POST":
                self.calls.append((method, path, token, payload))
                raise TimeoutError("fake lost response")
            return super().__call__(method, path, token, payload)

    first_api = LostResponse()
    first = _dispatch(dispatcher, tmp_path, first_api)
    second_api = FakeGitHub()
    second = _dispatch(dispatcher, tmp_path, second_api)

    assert first.reason == "dispatch_outcome_ambiguous"
    assert _slot_entry(state_file)["state"] == "ambiguous"
    assert second.reason == "slot_already_attempted"
    assert sum(call[0] == "POST" for call in first_api.calls) == 1
    assert second_api.calls == []


@pytest.mark.unit
def test_ambiguous_result_emits_only_fixed_safe_fields(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    dispatcher = _load_dispatcher()
    private_detail = "token-and-response-detail-must-not-appear"

    class UntrustedError(FakeGitHub):
        def __call__(self, method: str, path: str, token: str, payload: object | None):
            if method == "POST":
                self.calls.append((method, path, token, payload))
                raise TimeoutError(private_detail)
            return super().__call__(method, path, token, payload)

    result = _dispatch(dispatcher, tmp_path, UntrustedError())
    dispatcher._emit(result)
    output = capsys.readouterr().out

    assert '"reason": "dispatch_outcome_ambiguous"' in output
    assert private_detail not in output
    assert "test-token-not-a-secret" not in output


@pytest.mark.unit
def test_cli_defaults_to_dry_run_without_reading_token_or_dispatching(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    dispatcher = _load_dispatcher()

    class FrozenDateTime:
        @staticmethod
        def now(tz: object = None) -> datetime:
            return _now()

    monkeypatch.setattr(dispatcher, "datetime", FrozenDateTime)
    monkeypatch.setenv("WTC_GITHUB_DISPATCH_ENABLED", "1")
    monkeypatch.setenv("GITHUB_TOKEN", "must-not-be-used")
    monkeypatch.setattr(
        dispatcher,
        "_json_request",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("API called")),
    )

    exit_code = dispatcher.main([])
    output = capsys.readouterr().out

    assert exit_code == dispatcher.EXIT_OK
    assert '"status": "dry_run"' in output
    assert "must-not-be-used" not in output


@pytest.mark.unit
@pytest.mark.parametrize(
    ("status", "response"),
    [(204, None), (200, {"workflow_run_id": 0}), (200, {"workflow_run_id": "123"})],
)
def test_missing_or_malformed_receipt_is_ambiguous(
    tmp_path: Path, status: int, response: object
) -> None:
    dispatcher = _load_dispatcher()
    state_file = tmp_path / "ledger.json"
    api = FakeGitHub(post_status=status, post_response=response)

    result = _dispatch(dispatcher, tmp_path, api)

    assert result.reason == "dispatch_outcome_ambiguous"
    assert _slot_entry(state_file)["state"] == "ambiguous"
    assert sum(call[0] == "POST" for call in api.calls) == 1


@pytest.mark.unit
def test_restart_after_intent_before_post_does_not_retry(tmp_path: Path) -> None:
    dispatcher = _load_dispatcher()
    state_file = tmp_path / "ledger.json"

    class CrashBeforeReceipt(FakeGitHub):
        def __call__(self, method: str, path: str, token: str, payload: object | None):
            if method == "POST":
                self.calls.append((method, path, token, payload))
                raise KeyboardInterrupt
            return super().__call__(method, path, token, payload)

    crashed_api = CrashBeforeReceipt()
    with pytest.raises(KeyboardInterrupt):
        _dispatch(dispatcher, tmp_path, crashed_api)
    assert _slot_entry(state_file)["state"] == "in_flight"

    restarted_api = FakeGitHub()
    restarted = _dispatch(dispatcher, tmp_path, restarted_api)
    assert restarted.reason == "slot_already_attempted"
    assert sum(call[0] == "POST" for call in crashed_api.calls) == 1
    assert restarted_api.calls == []


@pytest.mark.unit
def test_restart_after_success_before_receipt_persistence_does_not_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dispatcher = _load_dispatcher()
    state_file = tmp_path / "ledger.json"
    original_write = dispatcher._write_ledger

    def fail_accepted_write(path: Path, ledger: dict[str, object]) -> None:
        slots = ledger["slots"]
        assert isinstance(slots, dict)
        if slots["2026-10-18T13:29:00Z"]["state"] == "accepted":
            raise OSError("fake local receipt write failure")
        original_write(path, ledger)

    monkeypatch.setattr(dispatcher, "_write_ledger", fail_accepted_write)
    api = FakeGitHub()

    result = _dispatch(dispatcher, tmp_path, api)
    assert result.reason == "receipt_persistence_failed"
    assert _slot_entry(state_file)["state"] == "in_flight"
    assert sum(call[0] == "POST" for call in api.calls) == 1

    restarted_api = FakeGitHub()
    restarted = _dispatch(dispatcher, tmp_path, restarted_api)
    assert restarted.reason == "slot_already_attempted"
    assert restarted_api.calls == []


@pytest.mark.unit
def test_all_api_pages_are_count_checked_and_capped(tmp_path: Path) -> None:
    dispatcher = _load_dispatcher()

    def too_many_api(
        method: str, path: str, token: str, payload: object | None
    ) -> tuple[int, object | None]:
        query = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)
        if "status" in query:
            return 200, {"total_count": 0, "workflow_runs": []}
        return 200, {"total_count": 1001, "workflow_runs": []}

    result = _dispatch(dispatcher, tmp_path, too_many_api)

    assert result.reason == "run_list_too_large"


@pytest.mark.unit
def test_expired_window_after_preflight_does_not_write_or_post(tmp_path: Path) -> None:
    dispatcher = _load_dispatcher()
    api = FakeGitHub()
    clock_calls = iter((_now(44),))
    result = _dispatch(dispatcher, tmp_path, api, clock=lambda: next(clock_calls))

    assert result.reason == "eligibility_window_elapsed"
    assert not any(call[0] == "POST" for call in api.calls)
    assert not (tmp_path / "ledger.json").exists()


@pytest.mark.unit
def test_window_expiry_after_intent_leaves_blocking_state_without_post(tmp_path: Path) -> None:
    dispatcher = _load_dispatcher()
    state_file = tmp_path / "ledger.json"
    clock_calls = iter((_now(), _now(44)))
    api = FakeGitHub()

    result = _dispatch(
        dispatcher,
        tmp_path,
        api,
        state_file=state_file,
        clock=lambda: next(clock_calls),
    )

    assert result.reason == "eligibility_window_elapsed"
    assert _slot_entry(state_file)["state"] == "in_flight"
    assert not any(call[0] == "POST" for call in api.calls)
