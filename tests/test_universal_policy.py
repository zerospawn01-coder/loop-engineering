from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "universal" / "universal-policy.json"
EXPECTED_POLICY_ID = "LE-UNIVERSAL-v0"
EXPECTED_LAYER = "UNIVERSAL"
EXPECTED_VERDICTS = ["PASS", "FAIL", "HOLD", "BLOCKED"]
EXPECTED_CONTROLS = {
    "goal_required",
    "current_state_required",
    "primary_hypothesis",
    "scope_control",
    "evidence",
    "no_false_pass",
    "stop_conditions",
    "verdicts",
    "next_issue",
    "human_authority",
}
DOMAIN_SPECIFIC_TERMS = (
    "github",
    "godot",
    "unit test",
    "remote ci",
    "screenshot",
    "video",
    "playtest",
    "sprite",
    "combat",
    "deterministic replay",
)

# ---------------------------------------------------------------------------
# CANONICAL_POLICY
# Closed structural + value representation of the expected Universal Policy.
# Used by gate_03 to perform closed structural schema and exact value equality,
# closing CONFIRMED-01 and CONFIRMED-02 within the frozen 10 gates.
# ---------------------------------------------------------------------------
CANONICAL_POLICY: dict[str, Any] = {
    "policy_id": "LE-UNIVERSAL-v0",
    "layer": "UNIVERSAL",
    "controls": {
        "goal_required": True,
        "current_state_required": True,
        "primary_hypothesis": {"required": True, "cardinality": 1},
        "scope_control": {"required": True},
        "evidence": {"required_for_pass": True},
        "no_false_pass": True,
        "stop_conditions": {"required": True},
        "verdicts": ["PASS", "FAIL", "HOLD", "BLOCKED"],
        "next_issue": {"proposal_only": True, "automatic_execution": False},
        "human_authority": {
            "agent_may_assume": False,
            "agent_may_fabricate_approval": False,
        },
    },
}


# ---------------------------------------------------------------------------
# Mutation helpers (produce in-memory mutated copies of CANONICAL_POLICY)
# ---------------------------------------------------------------------------
def _mutate(keys: list[str], value: Any) -> dict[str, Any]:
    """Return deep copy of CANONICAL_POLICY with nested key path set to value."""
    m = copy.deepcopy(CANONICAL_POLICY)
    obj: Any = m
    for k in keys[:-1]:
        obj = obj[k]
    obj[keys[-1]] = value
    return m


def _mutate_add(keys: list[str], new_key: str, value: Any) -> dict[str, Any]:
    """Return deep copy of CANONICAL_POLICY with extra key inserted at path."""
    m = copy.deepcopy(CANONICAL_POLICY)
    obj: Any = m
    for k in keys:
        obj = obj[k]
    obj[new_key] = value
    return m


# ---------------------------------------------------------------------------
# Mutation regression cases (MUT-01..MUT-20)
# Each entry is (label, mutated_policy, expected_failing_gate_id).
# gate_10 is strictly excluded from mutation evaluation to ensure the
# designated gate itself catches the violation without relying on disk diff.
# ---------------------------------------------------------------------------
MUTATIONS: list[tuple[str, dict[str, Any], str]] = [
    # --- Value mutations (CONFIRMED-01 regression) ---
    ("MUT-01 goal_required=false",
        _mutate(["controls", "goal_required"], False),
        "LE-U-GATE-03"),
    ("MUT-02 current_state_required=false",
        _mutate(["controls", "current_state_required"], False),
        "LE-U-GATE-03"),
    ("MUT-03 primary_hypothesis.required=false",
        _mutate(["controls", "primary_hypothesis", "required"], False),
        "LE-U-GATE-04"),
    ("MUT-04 primary_hypothesis.cardinality=2",
        _mutate(["controls", "primary_hypothesis", "cardinality"], 2),
        "LE-U-GATE-04"),
    ("MUT-05 scope_control.required=false",
        _mutate(["controls", "scope_control", "required"], False),
        "LE-U-GATE-03"),
    ("MUT-06 evidence.required_for_pass=false",
        _mutate(["controls", "evidence", "required_for_pass"], False),
        "LE-U-GATE-05"),
    ("MUT-07 no_false_pass=false",
        _mutate(["controls", "no_false_pass"], False),
        "LE-U-GATE-03"),
    ("MUT-08 stop_conditions.required=false",
        _mutate(["controls", "stop_conditions", "required"], False),
        "LE-U-GATE-03"),
    ("MUT-09 verdicts add UNKNOWN",
        _mutate(["controls", "verdicts"],
                ["PASS", "FAIL", "HOLD", "BLOCKED", "UNKNOWN"]),
        "LE-U-GATE-06"),
    ("MUT-10 next_issue.proposal_only=false",
        _mutate(["controls", "next_issue", "proposal_only"], False),
        "LE-U-GATE-07"),
    ("MUT-11 next_issue.automatic_execution=true",
        _mutate(["controls", "next_issue", "automatic_execution"], True),
        "LE-U-GATE-07"),
    ("MUT-12 human_authority.agent_may_assume=true",
        _mutate(["controls", "human_authority", "agent_may_assume"], True),
        "LE-U-GATE-08"),
    ("MUT-13 human_authority.agent_may_fabricate_approval=true",
        _mutate(["controls", "human_authority", "agent_may_fabricate_approval"], True),
        "LE-U-GATE-08"),
    # --- Closed-structure bypass mutations (CONFIRMED-02 regression) ---
    ("MUT-14 scope_control.engine=unity",
        _mutate_add(["controls", "scope_control"], "engine", "unity"),
        "LE-U-GATE-03"),
    ("MUT-15 scope_control.project=foo",
        _mutate_add(["controls", "scope_control"], "project", "foo"),
        "LE-U-GATE-03"),
    ("MUT-16 scope_control.domain=game",
        _mutate_add(["controls", "scope_control"], "domain", "game"),
        "LE-U-GATE-03"),
    ("MUT-17 scope_control.inheritance={}",
        _mutate_add(["controls", "scope_control"],
                    "inheritance", {"mode": "override"}),
        "LE-U-GATE-03"),
    ("MUT-18 unknown top-level field",
        _mutate_add([], "unknown_field", "injected"),
        "LE-U-GATE-03"),
    ("MUT-19 unknown control key",
        _mutate_add(["controls"], "unknown_control", True),
        "LE-U-GATE-03"),
    ("MUT-20 unknown nested field in human_authority",
        _mutate_add(["controls", "human_authority"], "extra_flag", True),
        "LE-U-GATE-03"),
]


# ---------------------------------------------------------------------------
# Policy loading
# ---------------------------------------------------------------------------
def load_policy() -> dict[str, Any]:
    with POLICY_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise AssertionError("Universal Policy root must be a JSON object")
    return data


# ---------------------------------------------------------------------------
# LE-U-GATE-01..10 — Canonical Gate Suite (exactly 10 gates)
# ---------------------------------------------------------------------------
def gate_01(policy: dict[str, Any]) -> None:
    assert isinstance(policy, dict)


def gate_02(policy: dict[str, Any]) -> None:
    assert policy.get("policy_id") == EXPECTED_POLICY_ID
    assert policy.get("layer") == EXPECTED_LAYER


def gate_03(policy: dict[str, Any]) -> None:
    # Closed structural schema + value equality check against CANONICAL_POLICY
    controls = policy.get("controls")
    assert isinstance(controls, dict)
    assert set(controls) == EXPECTED_CONTROLS
    assert policy == CANONICAL_POLICY, (
        "Policy structure/value mismatch from CANONICAL_POLICY.\n"
        f"  Expected: {json.dumps(CANONICAL_POLICY, sort_keys=True)}\n"
        f"  Actual:   {json.dumps(policy, sort_keys=True)}"
    )


def gate_04(policy: dict[str, Any]) -> None:
    hypothesis = policy["controls"]["primary_hypothesis"]
    assert hypothesis == {"required": True, "cardinality": 1}


def gate_05(policy: dict[str, Any]) -> None:
    assert policy["controls"]["evidence"]["required_for_pass"] is True


def gate_06(policy: dict[str, Any]) -> None:
    verdicts = policy["controls"]["verdicts"]
    assert verdicts == EXPECTED_VERDICTS
    assert len(verdicts) == len(set(verdicts)) == 4


def gate_07(policy: dict[str, Any]) -> None:
    next_issue = policy["controls"]["next_issue"]
    assert next_issue["proposal_only"] is True
    assert next_issue["automatic_execution"] is False


def gate_08(policy: dict[str, Any]) -> None:
    human_authority = policy["controls"]["human_authority"]
    assert human_authority["agent_may_assume"] is False
    assert human_authority["agent_may_fabricate_approval"] is False


def gate_09(policy: dict[str, Any]) -> None:
    serialized = json.dumps(policy, ensure_ascii=False).lower()
    for term in DOMAIN_SPECIFIC_TERMS:
        assert term not in serialized, (
            f"Domain-specific term found in Universal Policy: {term}"
        )


def gate_10(policy: dict[str, Any]) -> None:
    second_read = load_policy()
    assert policy == second_read
    first_canonical = json.dumps(policy, sort_keys=True, separators=(",", ":"))
    second_canonical = json.dumps(second_read, sort_keys=True, separators=(",", ":"))
    assert first_canonical == second_canonical


GATES = (
    ("LE-U-GATE-01", gate_01),
    ("LE-U-GATE-02", gate_02),
    ("LE-U-GATE-03", gate_03),
    ("LE-U-GATE-04", gate_04),
    ("LE-U-GATE-05", gate_05),
    ("LE-U-GATE-06", gate_06),
    ("LE-U-GATE-07", gate_07),
    ("LE-U-GATE-08", gate_08),
    ("LE-U-GATE-09", gate_09),
    ("LE-U-GATE-10", gate_10),
)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    total_failures = 0

    # --- BASE-01: Canonical on-disk policy verification ---
    try:
        policy = load_policy()
    except Exception as exc:
        print(f"LE-U-GATE-01 FAIL: {exc}")
        return 1

    gate_failures = 0
    for gate_id, gate in GATES:
        try:
            gate(policy)
        except Exception as exc:
            gate_failures += 1
            print(f"{gate_id} FAIL: {exc}")
        else:
            print(f"{gate_id} PASS")

    gate_count = len(GATES)
    print(f"LE-v0-01 RESULT: {gate_count - gate_failures}/{gate_count} PASS")
    total_failures += gate_failures

    # --- MUT-01..MUT-20: Designated gate mutation regression ---
    # gate_10 is strictly excluded; each mutation is tested directly against its designated gate.
    print()
    print(f"MUTATION REGRESSION: {len(MUTATIONS)} cases")
    gate_dict = dict(GATES)
    mut_failures = 0

    for mut_name, mutated_policy, expected_gate_id in MUTATIONS:
        target_gate = gate_dict[expected_gate_id]
        rejected = False
        try:
            target_gate(mutated_policy)
        except Exception:
            rejected = True

        if rejected:
            print(f"  REJECTED     {mut_name}  (by designated: {expected_gate_id})")
        else:
            mut_failures += 1
            print(f"  NOT-REJECTED {mut_name}  ** FAILED TO BE REJECTED BY {expected_gate_id} **")

    rejected_count = len(MUTATIONS) - mut_failures
    print(f"MUTATION RESULT: {rejected_count}/{len(MUTATIONS)} REJECTED (by designated gates)")
    total_failures += mut_failures

    print()
    print(f"OVERALL RESULT: {'PASS' if total_failures == 0 else 'FAIL'}")
    return 0 if total_failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
