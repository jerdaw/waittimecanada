#!/usr/bin/env python3
"""Prepare or explicitly request one guarded Wait Time Canada scraper run."""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import os
import stat
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPOSITORY = "jerdaw/waittimecanada"
WORKFLOW = "scraper-cron.yml"
WORKFLOW_API_PATH = f"/repos/{REPOSITORY}/actions/workflows/{WORKFLOW}"
API_ROOT = "https://api.github.com"
API_VERSION = "2026-03-10"
USER_AGENT = "waittimecanada-collector-dispatcher/1.0"
DEFAULT_STATE_FILE = Path("/var/lib/waittimecanada-dispatcher/dispatch-ledger.json")
HTTP_TIMEOUT_SECONDS = 20
PER_PAGE = 100
MAX_RUNS = 1000
ACTIVE_STATUSES = ("queued", "in_progress", "requested", "waiting", "pending")
RECENT_EVENTS = ("schedule", "workflow_dispatch")
LEDGER_VERSION = 1

EXIT_OK = 0
EXIT_BLOCKED = 1
EXIT_ERROR = 2

ApiRequest = Callable[[str, str, str, Mapping[str, object] | None], tuple[int, object | None]]
Clock = Callable[[], datetime]


@dataclass(frozen=True)
class Result:
    status: str
    reason: str
    slot: str | None
    run_id: int | None = None


class GuardRejectedError(Exception):
    """A preflight result that must prevent dispatch."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class LedgerInvalidError(Exception):
    """The durable ledger cannot safely authorize a new request."""


class LockBusyError(Exception):
    """Another local dispatcher currently owns the lock."""


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Do not forward a bearer token through an HTTP redirect."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


def _slot_for(now: datetime) -> datetime | None:
    if now.tzinfo is None:
        return None
    current = now.astimezone(UTC)
    if not 39 <= current.minute <= 43:
        return None
    return current.replace(minute=29, second=0, microsecond=0)


def _slot_text(slot: datetime) -> str:
    return slot.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _json_request(
    method: str,
    path: str,
    token: str,
    payload: Mapping[str, object] | None = None,
) -> tuple[int, object | None]:
    if not path.startswith("/") or ".." in path.split("/"):
        raise ValueError("invalid fixed API path")
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(  # noqa: S310 - fixed HTTPS API host and path.
        API_ROOT + path,
        data=body,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": API_VERSION,
            **({"Content-Type": "application/json"} if body is not None else {}),
        },
    )
    opener = urllib.request.build_opener(NoRedirectHandler())
    try:
        response = opener.open(request, timeout=HTTP_TIMEOUT_SECONDS)  # noqa: S310
    except urllib.error.HTTPError as exc:
        return exc.code, None
    with response:
        status = response.status
        if status != 200:
            return status, None
        try:
            return status, json.load(response)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return status, None


def _validated_page(payload: object) -> tuple[int, list[Mapping[str, object]]]:
    if not isinstance(payload, dict):
        raise GuardRejectedError("malformed_run_list")
    total = payload.get("total_count")
    runs = payload.get("workflow_runs")
    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise GuardRejectedError("malformed_run_count")
    if not isinstance(runs, list):
        raise GuardRejectedError("malformed_run_list")
    if any(not isinstance(run, dict) for run in runs):
        raise GuardRejectedError("malformed_run_record")
    return total, runs


def _list_recent_runs(
    *, slot: datetime, event: str, token: str, api_request: ApiRequest
) -> list[Mapping[str, object]]:
    created = f">={_slot_text(slot)}"
    results: list[Mapping[str, object]] = []
    total_count: int | None = None
    pages: int | None = None
    for page in range(1, MAX_RUNS // PER_PAGE + 1):
        query = urllib.parse.urlencode(
            {
                "created": created,
                "event": event,
                "per_page": PER_PAGE,
                "page": page,
            }
        )
        status, payload = api_request("GET", f"{WORKFLOW_API_PATH}/runs?{query}", token, None)
        if status != 200:
            raise GuardRejectedError("run_list_unavailable")
        observed_total, runs = _validated_page(payload)
        if observed_total > MAX_RUNS:
            raise GuardRejectedError("run_list_too_large")
        if total_count is None:
            total_count = observed_total
            pages = (observed_total + PER_PAGE - 1) // PER_PAGE
            if pages == 0:
                if runs:
                    raise GuardRejectedError("inconsistent_run_list")
                return []
        elif observed_total != total_count:
            raise GuardRejectedError("run_list_changed")

        if pages is None:
            raise GuardRejectedError("malformed_run_count")
        expected_rows = min(PER_PAGE, total_count - len(results))
        if len(runs) != expected_rows:
            raise GuardRejectedError("incomplete_run_list")
        for run in runs:
            run_id = run.get("id")
            run_event = run.get("event")
            if (
                isinstance(run_id, bool)
                or not isinstance(run_id, int)
                or run_id <= 0
                or run_event != event
            ):
                raise GuardRejectedError("malformed_run_record")
        results.extend(runs)
        if page == pages:
            break
    else:
        raise GuardRejectedError("run_list_page_limit")

    if total_count is None or len(results) != total_count:
        raise GuardRejectedError("incomplete_run_list")
    return results


def _preflight(*, slot: datetime, token: str, api_request: ApiRequest) -> None:
    for status_name in ACTIVE_STATUSES:
        query = urllib.parse.urlencode({"status": status_name, "per_page": 1, "page": 1})
        status, payload = api_request("GET", f"{WORKFLOW_API_PATH}/runs?{query}", token, None)
        if status != 200:
            raise GuardRejectedError("active_run_check_unavailable")
        total, runs = _validated_page(payload)
        if total == 0:
            if runs:
                raise GuardRejectedError("inconsistent_active_run_list")
            continue
        if not runs:
            raise GuardRejectedError("incomplete_active_run_list")
        for run in runs:
            run_status = run.get("status")
            if run_status != status_name:
                raise GuardRejectedError("malformed_active_run_record")
        raise GuardRejectedError("active_workflow_run")

    for event in RECENT_EVENTS:
        runs = _list_recent_runs(slot=slot, event=event, token=token, api_request=api_request)
        if runs:
            raise GuardRejectedError("recent_workflow_run")


def _empty_ledger() -> dict[str, object]:
    return {"version": LEDGER_VERSION, "slots": {}}


def _read_ledger(path: Path) -> dict[str, object]:
    _validate_state_parent(path)
    try:
        file_stat = path.lstat()
    except FileNotFoundError:
        return _empty_ledger()
    except OSError as exc:
        raise LedgerInvalidError from exc
    if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_nlink != 1:
        raise LedgerInvalidError
    if file_stat.st_mode & 0o077:
        raise LedgerInvalidError
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise LedgerInvalidError from exc
    version = parsed.get("version") if isinstance(parsed, dict) else None
    if (
        not isinstance(parsed, dict)
        or isinstance(version, bool)
        or not isinstance(version, int)
        or version != LEDGER_VERSION
    ):
        raise LedgerInvalidError
    slots = parsed.get("slots")
    if not isinstance(slots, dict):
        raise LedgerInvalidError
    for key, entry in slots.items():
        if not isinstance(key, str) or not isinstance(entry, dict):
            raise LedgerInvalidError
        if entry.get("state") not in {"in_flight", "accepted", "ambiguous"}:
            raise LedgerInvalidError
        if not isinstance(entry.get("updated_at"), str):
            raise LedgerInvalidError
        if "run_id" in entry and (
            isinstance(entry["run_id"], bool)
            or not isinstance(entry["run_id"], int)
            or entry["run_id"] <= 0
        ):
            raise LedgerInvalidError
    return parsed


def _write_ledger(path: Path, ledger: Mapping[str, object]) -> None:
    _validate_state_parent(path)
    parent = path.parent
    if not parent.is_dir():
        raise OSError("state directory is unavailable")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=parent
    )
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(ledger, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        directory_fd = os.open(parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        with contextlib.suppress(OSError):
            os.close(descriptor)
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temporary_name)
        raise


@contextlib.contextmanager
def _slot_lock(path: Path) -> Iterator[None]:
    _validate_state_parent(path)
    lock_path = path.with_name(f".{path.name}.lock")
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(lock_path, flags, 0o600)
    except OSError as exc:
        raise LedgerInvalidError from exc
    try:
        lock_stat = os.fstat(descriptor)
        if not stat.S_ISREG(lock_stat.st_mode) or lock_stat.st_uid != os.geteuid():
            raise LedgerInvalidError
        os.fchmod(descriptor, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise LockBusyError from exc
        except OSError as exc:
            raise LedgerInvalidError from exc
        yield
    except LedgerInvalidError:
        raise
    except OSError as exc:
        raise LedgerInvalidError from exc
    finally:
        with contextlib.suppress(OSError):
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _validate_state_parent(path: Path) -> None:
    absolute_parent = path.parent.absolute()
    ancestors = [absolute_parent, *absolute_parent.parents]
    for ancestor in reversed(ancestors):
        try:
            ancestor_stat = ancestor.lstat()
        except OSError as exc:
            raise LedgerInvalidError from exc
        if not stat.S_ISDIR(ancestor_stat.st_mode):
            raise LedgerInvalidError
    parent_stat = absolute_parent.lstat()
    if parent_stat.st_mode & 0o022:
        raise LedgerInvalidError
    if parent_stat.st_uid != os.geteuid():
        raise LedgerInvalidError


def dispatch_once(
    *,
    now: datetime,
    execute: bool,
    enabled: bool,
    token: str | None,
    state_file: Path = DEFAULT_STATE_FILE,
    api_request: ApiRequest = _json_request,
    clock: Clock = lambda: datetime.now(UTC),
) -> Result:
    slot = _slot_for(now)
    if slot is None:
        return Result("blocked", "outside_eligibility_window", None)
    slot_key = _slot_text(slot)
    if not execute:
        return Result("dry_run", "eligible_current_slot_only", slot_key)
    if not enabled:
        return Result("blocked", "execution_disabled", slot_key)
    if not token:
        return Result("blocked", "token_unavailable", slot_key)

    try:
        with _slot_lock(state_file):
            try:
                ledger = _read_ledger(state_file)
            except LedgerInvalidError:
                return Result("blocked", "ledger_unavailable", slot_key)
            slots = ledger["slots"]
            if not isinstance(slots, dict):
                return Result("blocked", "ledger_unavailable", slot_key)
            if slot_key in slots:
                return Result("blocked", "slot_already_attempted", slot_key)

            try:
                _preflight(slot=slot, token=token, api_request=api_request)
            except GuardRejectedError as exc:
                return Result("blocked", exc.reason, slot_key)
            except Exception:
                return Result("blocked", "preflight_unavailable", slot_key)

            if _slot_for(clock()) != slot:
                return Result("blocked", "eligibility_window_elapsed", slot_key)

            attempted_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
            slots[slot_key] = {"state": "in_flight", "updated_at": attempted_at}
            try:
                _write_ledger(state_file, ledger)
            except OSError:
                return Result("error", "intent_persistence_failed", slot_key)

            if _slot_for(clock()) != slot:
                return Result("blocked", "eligibility_window_elapsed", slot_key)

            body: Mapping[str, object] = {
                "ref": "main",
                "inputs": {"refresh_analytics": False},
                "return_run_details": True,
            }
            try:
                status, response = api_request(
                    "POST", f"{WORKFLOW_API_PATH}/dispatches", token, body
                )
            except Exception:
                _mark_ambiguous(state_file, ledger, slots, slot_key)
                return Result("blocked", "dispatch_outcome_ambiguous", slot_key)

            run_id: object = None
            if isinstance(response, dict):
                run_id = response.get("workflow_run_id")
            if (
                status != 200
                or isinstance(run_id, bool)
                or not isinstance(run_id, int)
                or run_id <= 0
            ):
                _mark_ambiguous(state_file, ledger, slots, slot_key)
                return Result("blocked", "dispatch_outcome_ambiguous", slot_key)

            slots[slot_key] = {
                "state": "accepted",
                "updated_at": datetime.now(UTC)
                .isoformat(timespec="seconds")
                .replace("+00:00", "Z"),
                "run_id": run_id,
            }
            try:
                _write_ledger(state_file, ledger)
            except OSError:
                return Result("error", "receipt_persistence_failed", slot_key)
            return Result("accepted", "run_accepted", slot_key, run_id)
    except LockBusyError:
        return Result("blocked", "another_local_dispatcher_active", slot_key)
    except LedgerInvalidError:
        return Result("blocked", "ledger_unavailable", slot_key)
    except OSError:
        return Result("blocked", "local_state_unavailable", slot_key)


def _mark_ambiguous(
    state_file: Path,
    ledger: dict[str, object],
    slots: dict[str, object],
    slot_key: str,
) -> None:
    slots[slot_key] = {
        "state": "ambiguous",
        "updated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
    with contextlib.suppress(OSError):
        _write_ledger(state_file, ledger)


def _emit(result: Result) -> None:
    output: dict[str, object] = {
        "status": result.status,
        "reason": result.reason,
        "slot": result.slot,
    }
    if result.run_id is not None:
        output["run_id"] = result.run_id
    sys.stdout.write(json.dumps(output, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true", help="request the one eligible dispatch")
    mode.add_argument("--dry-run", action="store_true", help="report eligibility without I/O")
    args = parser.parse_args(argv)
    execute = bool(args.execute)
    enabled = False
    token: str | None = None
    if execute:
        enabled = os.environ.get("WTC_GITHUB_DISPATCH_ENABLED") == "1"
        if enabled:
            token = os.environ.get("GITHUB_TOKEN")
    result = dispatch_once(
        now=datetime.now(UTC),
        execute=execute,
        enabled=enabled,
        token=token,
    )
    _emit(result)
    if result.status in {"dry_run", "accepted"}:
        return EXIT_OK
    if result.status == "error":
        return EXIT_ERROR
    return EXIT_BLOCKED


if __name__ == "__main__":
    raise SystemExit(main())
