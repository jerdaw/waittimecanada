"""Conservative source-name to hospital-ID matching shared by the scrapers.

A hospital ID must only ever receive values from the one facility it names.
The helpers here enforce that:

* provincial or other aggregate rows are never treated as hospitals;
* only an exact match (after trivial normalization of case, whitespace,
  apostrophes and dashes) resolves to a mapped hospital ID;
* a source name that merely contains, or is contained in, a mapped name (for
  example a campus of a multi-site corporation) is *ambiguous* and must be
  skipped rather than guessed;
* within one run, an ID claimed by more than one source row is ambiguous and
  every row claiming it is dropped.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal

MatchStatus = Literal["exact", "unmapped", "aggregate", "ambiguous"]

# Normalized (see normalize_source_name) names that denote a province-wide or
# otherwise aggregated row rather than a facility.
AGGREGATE_NAMES: frozenset[str] = frozenset(
    {
        "ontario",
        "province of ontario",
        "ontario average",
        "ontario provincial average",
        "ontario total",
        "all ontario",
        "quebec",
        "province of quebec",
        "quebec average",
        "quebec total",
        "ensemble du quebec",
        "moyenne du quebec",
        "province",
        "provincial",
        "provincial average",
        "provincial total",
        "moyenne provinciale",
        "moyenne",
        "average",
        "total",
        "all hospitals",
        "all facilities",
        "all emergency departments",
    }
)

_APOSTROPHES = str.maketrans({"’": "'", "‘": "'", "ʼ": "'", "`": "'"})
_DASHES = str.maketrans({"‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-"})


def normalize_source_name(name: str) -> str:
    """Normalize a source facility name for exact comparison only.

    Case, surrounding/repeated whitespace, apostrophe and dash variants are
    unified. Accents and word content are preserved so that distinct
    facilities stay distinct.
    """
    text = unicodedata.normalize("NFKC", name).translate(_APOSTROPHES).translate(_DASHES)
    return re.sub(r"\s+", " ", text).strip().casefold()


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def is_aggregate_name(name: str) -> bool:
    """Return True when a source row name is a provincial/aggregate row."""
    normalized = _strip_accents(normalize_source_name(name))
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized).strip()
    return normalized in AGGREGATE_NAMES


@dataclass(frozen=True)
class MatchOutcome:
    """Result of matching one source name against a known-hospital mapping."""

    status: MatchStatus
    hospital_id: str | None = None
    candidates: tuple[str, ...] = ()


def match_source_name(name: str, mapping: Mapping[str, str]) -> MatchOutcome:
    """Match a source name to a mapped hospital ID without guessing.

    Returns:
        ``exact`` with the hospital ID when the name equals one mapping key (after
        normalization); ``aggregate`` for provincial rows; ``ambiguous`` (with the
        candidate IDs) when the name only partially overlaps mapping keys; and
        ``unmapped`` when it has no relationship to any mapping key.
    """
    if is_aggregate_name(name):
        return MatchOutcome(status="aggregate")

    target = normalize_source_name(name)
    if not target:
        return MatchOutcome(status="unmapped")

    exact_ids = {
        hospital_id for key, hospital_id in mapping.items() if normalize_source_name(key) == target
    }
    if len(exact_ids) == 1:
        return MatchOutcome(status="exact", hospital_id=next(iter(exact_ids)))
    if len(exact_ids) > 1:
        return MatchOutcome(status="ambiguous", candidates=tuple(sorted(exact_ids)))

    related_ids: set[str] = set()
    for key, hospital_id in mapping.items():
        key_norm = normalize_source_name(key)
        if key_norm and (key_norm in target or target in key_norm):
            related_ids.add(hospital_id)
    if related_ids:
        return MatchOutcome(status="ambiguous", candidates=tuple(sorted(related_ids)))

    return MatchOutcome(status="unmapped")


@dataclass
class MatchReport:
    """What a scraper did with each source row in the most recent parse."""

    mapped: list[tuple[str, str]] = field(default_factory=list)  # (source name, hospital id)
    generated: list[tuple[str, str]] = field(default_factory=list)  # unmapped names given a slug id
    skipped: list[tuple[str, str]] = field(default_factory=list)  # (source name, reason)

    def clear(self) -> None:
        self.mapped.clear()
        self.generated.clear()
        self.skipped.clear()


def find_colliding_ids(rows: Sequence[tuple[str, str]]) -> dict[str, list[str]]:
    """Find hospital IDs claimed by more than one source row.

    Args:
        rows: ``(source_name, hospital_id)`` pairs, one per source row.

    Returns:
        Mapping of each contested hospital ID to the source names that claimed it.
    """
    claims: dict[str, list[str]] = defaultdict(list)
    for source_name, hospital_id in rows:
        claims[hospital_id].append(source_name)
    return {hid: names for hid, names in claims.items() if len(names) > 1}
