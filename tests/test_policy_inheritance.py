from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from inheritance.policy_inheritance import (  # noqa: E402
    PolicyInheritanceViolation,
    resolve_policy_inheritance,
)


UPPER = {
    "additive": {
        "evidence": ["upper-evidence"],
        "gates": ["upper-gate"],
        "constraints": ["upper-constraint"],
    },
    "restrictive": {
        "scope": ["src", "tests"],
        "allowed_actions": ["read", "write", "test"],
        "agent_authority": ["analyze", "implement", "propose"],
    },
    "fixed": {
        "no_false_pass": True,
        "verdict_semantics": ["PASS", "FAIL", "HOLD", "BLOCKED"],
        "human_authority_boundary": {
            "agent_may_assume_human_authority": False
        },
        "upper_stop_conditions": ["required-gate-failure", "human-hold"],
    },
}


def expect_violation(upper: dict, lower: dict) -> None:
    try:
        resolve_policy_inheritance(upper, lower)
    except PolicyInheritanceViolation:
        return
    raise AssertionError("Expected PolicyInheritanceViolation")


def gate_01() -> None:
    resolved = resolve_policy_inheritance(UPPER, {})
    assert resolved["fixed"]["no_false_pass"] is True


def gate_02() -> None:
    lower = {"additive": {"evidence": ["lower-evidence"]}}
    resolved = resolve_policy_inheritance(UPPER, lower)
    assert resolved["additive"]["evidence"] == [
        "upper-evidence",
        "lower-evidence",
    ]


def gate_03() -> None:
    lower = {
        "additive": {
            "gates": ["lower-gate"],
            "constraints": ["lower-constraint"],
        }
    }
    resolved = resolve_policy_inheritance(UPPER, lower)
    assert "upper-gate" in resolved["additive"]["gates"]
    assert "lower-gate" in resolved["additive"]["gates"]
    assert "upper-constraint" in resolved["additive"]["constraints"]
    assert "lower-constraint" in resolved["additive"]["constraints"]


def gate_04() -> None:
    lower = {
        "restrictive": {
            "scope": ["src"],
            "allowed_actions": ["read", "test"],
            "agent_authority": ["analyze", "propose"],
        }
    }
    resolved = resolve_policy_inheritance(UPPER, lower)
    assert resolved["restrictive"] == lower["restrictive"]

    frozen_upper = {
        **UPPER,
        "restrictive": {
            **UPPER["restrictive"],
            "scope": ["scripts/aether/**"],
        },
    }
    frozen_lower = {
        "restrictive": {
            "scope": ["scripts/aether/biosynthesis/**"],
        }
    }
    resolved = resolve_policy_inheritance(frozen_upper, frozen_lower)
    assert resolved["restrictive"]["scope"] == [
        "scripts/aether/biosynthesis/**"
    ]


def gate_05() -> None:
    lower = {"restrictive": {"scope": ["src", "tests", "secrets"]}}
    expect_violation(UPPER, lower)

    frozen_upper = {
        **UPPER,
        "restrictive": {
            **UPPER["restrictive"],
            "scope": ["scripts/aether/biosynthesis/**"],
        },
    }
    frozen_expansion = {
        "restrictive": {
            "scope": ["scripts/**"],
        }
    }
    expect_violation(frozen_upper, frozen_expansion)

    escape_upper = {
        **UPPER,
        "restrictive": {
            **UPPER["restrictive"],
            "scope": ["scripts/aether/**"],
        },
    }
    for escape_scope in (
        "scripts/aether/../secrets/**",
        "scripts/aether/biosynthesis/../../secrets/**",
    ):
        expect_violation(
            escape_upper,
            {"restrictive": {"scope": [escape_scope]}},
        )


def gate_06() -> None:
    lower = {"restrictive": {"agent_authority": ["analyze", "merge"]}}
    expect_violation(UPPER, lower)


def gate_07() -> None:
    lower = {"fixed": {"no_false_pass": False}}
    expect_violation(UPPER, lower)


def gate_08() -> None:
    lower = {"fixed": {"verdict_semantics": ["PASS", "FAIL"]}}
    expect_violation(UPPER, lower)


def gate_09() -> None:
    lower = {
        "fixed": {
            "human_authority_boundary": {
                "agent_may_assume_human_authority": True
            }
        }
    }
    expect_violation(UPPER, lower)


def gate_10() -> None:
    lower = {
        "additive": {"evidence": ["lower-evidence"], "gates": ["lower-gate"]},
        "restrictive": {"scope": ["src"]},
    }
    first = resolve_policy_inheritance(UPPER, lower)
    second = resolve_policy_inheritance(UPPER, lower)
    assert first == second
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


GATES = (
    ("LE-I-GATE-01", gate_01),
    ("LE-I-GATE-02", gate_02),
    ("LE-I-GATE-03", gate_03),
    ("LE-I-GATE-04", gate_04),
    ("LE-I-GATE-05", gate_05),
    ("LE-I-GATE-06", gate_06),
    ("LE-I-GATE-07", gate_07),
    ("LE-I-GATE-08", gate_08),
    ("LE-I-GATE-09", gate_09),
    ("LE-I-GATE-10", gate_10),
)


def main() -> int:
    failures = 0
    for gate_id, gate in GATES:
        try:
            gate()
        except Exception as exc:
            failures += 1
            print(f"{gate_id} FAIL: {exc}")
        else:
            print(f"{gate_id} PASS")

    print(f"LE-v0-02 RESULT: {len(GATES) - failures}/{len(GATES)} PASS")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
