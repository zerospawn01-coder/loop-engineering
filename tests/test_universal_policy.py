from __future__ import annotations

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


def load_policy() -> dict[str, Any]:
    with POLICY_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise AssertionError("Universal Policy root must be a JSON object")
    return data


def gate_01(policy: dict[str, Any]) -> None:
    assert isinstance(policy, dict)


def gate_02(policy: dict[str, Any]) -> None:
    assert policy.get("policy_id") == EXPECTED_POLICY_ID
    assert policy.get("layer") == EXPECTED_LAYER


def gate_03(policy: dict[str, Any]) -> None:
    controls = policy.get("controls")
    assert isinstance(controls, dict)
    assert set(controls) == EXPECTED_CONTROLS


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
        assert term not in serialized, f"Domain-specific term found in Universal Policy: {term}"


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


def main() -> int:
    try:
        policy = load_policy()
    except Exception as exc:
        print(f"LE-U-GATE-01 FAIL: {exc}")
        return 1

    failures = 0
    for gate_id, gate in GATES:
        try:
            gate(policy)
        except Exception as exc:
            failures += 1
            print(f"{gate_id} FAIL: {exc}")
        else:
            print(f"{gate_id} PASS")

    print(f"LE-v0-01 RESULT: {len(GATES) - failures}/{len(GATES)} PASS")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
