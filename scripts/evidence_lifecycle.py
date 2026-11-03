#!/usr/bin/env python3
"""Evidence-aware entity lifecycle and claim provenance helpers.

Stable public IDs and canonical country JSON remain authoritative. This module
adds an explicit review state machine and claim/relationship records so
discovery hits cannot silently become VERIFIED or PUBLISHED.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

LIFECYCLE_STATES = (
    "DISCOVERED",
    "QUALIFIED",
    "FIRST_PARTY_CHECKED",
    "HUMAN_REVIEWED",
    "PUBLISHABLE",
    "PUBLISHED",
    "REJECTED",
    "STALE",
    "DISPUTED",
    "NEEDS_REVIEW",
)

# Allowed forward transitions. Side states can be entered from most active states.
TRANSITIONS: dict[str, set[str]] = {
    "DISCOVERED": {"QUALIFIED", "REJECTED", "DISPUTED", "NEEDS_REVIEW", "STALE"},
    "QUALIFIED": {"FIRST_PARTY_CHECKED", "REJECTED", "DISPUTED", "NEEDS_REVIEW", "STALE"},
    "FIRST_PARTY_CHECKED": {"HUMAN_REVIEWED", "REJECTED", "DISPUTED", "NEEDS_REVIEW", "STALE"},
    "HUMAN_REVIEWED": {"PUBLISHABLE", "REJECTED", "DISPUTED", "NEEDS_REVIEW", "STALE"},
    "PUBLISHABLE": {"PUBLISHED", "REJECTED", "DISPUTED", "NEEDS_REVIEW", "STALE"},
    "PUBLISHED": {"STALE", "DISPUTED", "NEEDS_REVIEW", "REJECTED"},
    "REJECTED": {"DISCOVERED", "NEEDS_REVIEW"},
    "STALE": {"NEEDS_REVIEW", "DISCOVERED", "QUALIFIED"},
    "DISPUTED": {"NEEDS_REVIEW", "REJECTED", "QUALIFIED"},
    "NEEDS_REVIEW": {"QUALIFIED", "FIRST_PARTY_CHECKED", "HUMAN_REVIEWED", "REJECTED", "DISPUTED", "STALE"},
}

RELATIONSHIP_TYPES = (
    "membership",
    "umbrella_member_listed",
    "funding_award",
    "funding_application_unsuccessful",
    "press_mention",
    "calendar_source",
    "institutional_parent",
    "same_as_candidate",
    "operates_in",
)

CLAIM_STRENGTH = ("observed", "corroborated", "first_party", "human_confirmed")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class EvidenceSource:
    url: str
    observedAt: str
    sourceType: str
    label: str | None = None
    retrievalStatus: str = "observed"


@dataclass
class ClaimEvidence:
    claimType: str
    statement: str
    sources: list[EvidenceSource] = field(default_factory=list)
    strength: str = "observed"
    validFrom: str | None = None
    validTo: str | None = None


@dataclass
class RelationshipEdge:
    relationshipType: str
    fromEntityId: str
    toEntityId: str | None = None
    toLabel: str | None = None
    confidence: str = "low"
    evidence: list[ClaimEvidence] = field(default_factory=list)
    validFrom: str | None = None
    validTo: str | None = None


def assert_lifecycle(state: str) -> str:
    if state not in LIFECYCLE_STATES:
        raise ValueError(f"Unknown lifecycle state: {state}")
    return state


def can_transition(current: str, target: str) -> bool:
    assert_lifecycle(current)
    assert_lifecycle(target)
    if current == target:
        return True
    return target in TRANSITIONS[current]


def transition(current: str, target: str, *, reason: str) -> dict[str, str]:
    if not can_transition(current, target):
        raise ValueError(f"Illegal lifecycle transition {current} -> {target}: {reason}")
    return {
        "from": current,
        "to": target,
        "reason": reason,
        "at": utc_now(),
    }


def is_publishable(state: str) -> bool:
    return assert_lifecycle(state) in {"PUBLISHABLE", "PUBLISHED"}


def secondary_mention_alone_blocks_verification(sources: list[dict[str, Any]]) -> bool:
    """A newspaper/directory mention alone must never promote to VERIFIED/PUBLISHED."""
    if not sources:
        return True
    weak = {"secondary", "directory", "press", "wikipedia", "social"}
    return all((s.get("sourceType") or s.get("type") or "").lower() in weak for s in sources)


def grant_is_not_membership(relationship_type: str) -> bool:
    return relationship_type in {"funding_award", "funding_application_unsuccessful"}


def serialize_claim(claim: ClaimEvidence) -> dict[str, Any]:
    payload = asdict(claim)
    if payload["strength"] not in CLAIM_STRENGTH:
        raise ValueError(f"Invalid claim strength: {payload['strength']}")
    return payload


def serialize_relationship(edge: RelationshipEdge) -> dict[str, Any]:
    if edge.relationshipType not in RELATIONSHIP_TYPES:
        raise ValueError(f"Invalid relationship type: {edge.relationshipType}")
    payload = asdict(edge)
    payload["evidence"] = [serialize_claim(ClaimEvidence(**e)) if isinstance(e, dict) else serialize_claim(e) for e in edge.evidence]
    if grant_is_not_membership(edge.relationshipType) and edge.relationshipType == "membership":
        raise ValueError("funding relationships cannot be membership")
    return payload
