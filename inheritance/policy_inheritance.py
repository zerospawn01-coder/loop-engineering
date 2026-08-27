from __future__ import annotations

from copy import deepcopy
from typing import Any


ADDITIVE_FIELDS = ("evidence", "gates", "constraints")
RESTRICTIVE_FIELDS = ("scope", "allowed_actions", "agent_authority")
FIXED_FIELDS = (
    "no_false_pass",
    "verdict_semantics",
    "human_authority_boundary",
    "upper_stop_conditions",
)
SECTIONS = ("additive", "restrictive", "fixed")


class PolicyInheritanceViolation(ValueError):
    """Raised when a lower policy weakens or expands beyond an upper policy."""


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PolicyInheritanceViolation(f"{label} must be an object")
    return value


def _require_string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise PolicyInheritanceViolation(f"{label} must be a list of strings")
    if len(value) != len(set(value)):
        raise PolicyInheritanceViolation(f"{label} must not contain duplicates")
    return value


def _validate_known_fields(policy: dict[str, Any], label: str) -> None:
    unknown_sections = set(policy) - set(SECTIONS)
    if unknown_sections:
        raise PolicyInheritanceViolation(
            f"{label} contains unknown sections: {sorted(unknown_sections)}"
        )

    known_by_section = {
        "additive": set(ADDITIVE_FIELDS),
        "restrictive": set(RESTRICTIVE_FIELDS),
        "fixed": set(FIXED_FIELDS),
    }
    for section, known_fields in known_by_section.items():
        content = policy.get(section, {})
        _require_mapping(content, f"{label}.{section}")
        unknown_fields = set(content) - known_fields
        if unknown_fields:
            raise PolicyInheritanceViolation(
                f"{label}.{section} contains unknown fields: {sorted(unknown_fields)}"
            )


def _merge_additive(
    upper: dict[str, Any], lower: dict[str, Any]
) -> dict[str, list[str]]:
    resolved: dict[str, list[str]] = {}
    for field in ADDITIVE_FIELDS:
        upper_values = _require_string_list(
            upper.get(field, []), f"upper.additive.{field}"
        )
        lower_values = _require_string_list(
            lower.get(field, []), f"lower.additive.{field}"
        )
        merged = list(upper_values)
        for value in lower_values:
            if value not in merged:
                merged.append(value)
        resolved[field] = merged
    return resolved


def _validate_scope_entry(value: str, label: str) -> None:
    if any(segment in (".", "..") for segment in value.split("/")):
        raise PolicyInheritanceViolation(
            f"{label} contains forbidden dot segment: {value}"
        )

    wildcard_chars = ("*", "?", "[", "]")
    if not any(char in value for char in wildcard_chars):
        return
    if value.endswith("/**") and not any(
        char in value[:-3] for char in wildcard_chars
    ):
        return
    raise PolicyInheritanceViolation(
        f"{label} uses unsupported scope pattern: {value}"
    )


def _scope_entry_within(lower: str, upper: str) -> bool:
    if lower == upper:
        return True
    if upper.endswith("/**"):
        upper_base = upper[:-3].rstrip("/")
        return lower == upper_base or lower.startswith(f"{upper_base}/")
    return False


def _merge_scope(upper: dict[str, Any], lower: dict[str, Any]) -> list[str]:
    upper_values = _require_string_list(
        upper.get("scope", []), "upper.restrictive.scope"
    )
    for value in upper_values:
        _validate_scope_entry(value, "upper.restrictive.scope")

    if "scope" not in lower:
        return list(upper_values)

    lower_values = _require_string_list(
        lower["scope"], "lower.restrictive.scope"
    )
    for value in lower_values:
        _validate_scope_entry(value, "lower.restrictive.scope")

    outside = [
        value
        for value in lower_values
        if not any(
            _scope_entry_within(value, upper_value) for upper_value in upper_values
        )
    ]
    if outside:
        raise PolicyInheritanceViolation(
            f"lower.restrictive.scope expands upper policy: {sorted(outside)}"
        )
    return list(lower_values)


def _merge_restrictive(
    upper: dict[str, Any], lower: dict[str, Any]
) -> dict[str, list[str]]:
    resolved: dict[str, list[str]] = {"scope": _merge_scope(upper, lower)}
    for field in ("allowed_actions", "agent_authority"):
        upper_values = _require_string_list(
            upper.get(field, []), f"upper.restrictive.{field}"
        )
        if field not in lower:
            resolved[field] = list(upper_values)
            continue

        lower_values = _require_string_list(
            lower[field], f"lower.restrictive.{field}"
        )
        expansion = set(lower_values) - set(upper_values)
        if expansion:
            raise PolicyInheritanceViolation(
                f"lower.restrictive.{field} expands upper policy: {sorted(expansion)}"
            )
        resolved[field] = list(lower_values)
    return resolved


def _merge_fixed(upper: dict[str, Any], lower: dict[str, Any]) -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    for field in FIXED_FIELDS:
        if field not in upper:
            raise PolicyInheritanceViolation(f"upper.fixed.{field} is required")
        upper_value = upper[field]
        if field in lower and lower[field] != upper_value:
            raise PolicyInheritanceViolation(
                f"lower.fixed.{field} attempts to override a non-overridable value"
            )
        resolved[field] = deepcopy(upper_value)
    return resolved


def resolve_policy_inheritance(
    upper_policy: dict[str, Any], lower_policy: dict[str, Any]
) -> dict[str, Any]:
    """Resolve one upper/lower policy pair using the frozen LE-v0 inheritance rules."""

    upper = _require_mapping(upper_policy, "upper")
    lower = _require_mapping(lower_policy, "lower")
    _validate_known_fields(upper, "upper")
    _validate_known_fields(lower, "lower")

    upper_additive = _require_mapping(upper.get("additive", {}), "upper.additive")
    lower_additive = _require_mapping(lower.get("additive", {}), "lower.additive")
    upper_restrictive = _require_mapping(
        upper.get("restrictive", {}), "upper.restrictive"
    )
    lower_restrictive = _require_mapping(
        lower.get("restrictive", {}), "lower.restrictive"
    )
    upper_fixed = _require_mapping(upper.get("fixed", {}), "upper.fixed")
    lower_fixed = _require_mapping(lower.get("fixed", {}), "lower.fixed")

    return {
        "additive": _merge_additive(upper_additive, lower_additive),
        "restrictive": _merge_restrictive(upper_restrictive, lower_restrictive),
        "fixed": _merge_fixed(upper_fixed, lower_fixed),
    }
