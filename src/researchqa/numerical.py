"""Development percentage checker for explicitly structured claims.

Not a free-text extractor, general scientific verifier, or calibrated model.
"""

from decimal import Decimal, InvalidOperation


SCOPE_FIELDS = (
    "outcome",
    "population",
    "duration_operator",
    "duration_days",
    "duration_unit",
    "value_unit",
)


def _number(value):
    if isinstance(value, bool):
        raise ValueError("Boolean is not a numerical measurement.")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError("Invalid numerical value.") from error
    if not parsed.is_finite():
        raise ValueError("Non-finite numerical value.")
    return parsed


def check_percentage_claim(claim, evidence):
    required = SCOPE_FIELDS + (
        "group", "numerator", "denominator", "value"
    )

    missing = [
        field for field in required
        if field not in claim or claim[field] is None
    ]
    if missing:
        return {
            "decision": "Insufficient Evidence",
            "reason": "Missing claim attributes.",
            "fields": missing,
        }

    mismatched_scope = [
        field for field in SCOPE_FIELDS
        if claim[field] != evidence[field]
    ]
    if mismatched_scope:
        return {
            "decision": "Insufficient Evidence",
            "reason": "Evidence row does not match the claim scope.",
            "fields": mismatched_scope,
        }

    if not isinstance(claim["group"], str):
        return {
            "decision": "Insufficient Evidence",
            "reason": "Invalid group identifier.",
        }

    group = evidence["groups"].get(claim["group"])
    if group is None:
        return {
            "decision": "Insufficient Evidence",
            "reason": "Group is not represented in this evidence row.",
        }

    # Invalid evidence is a preparation error, not a scientific decision.
    expected = {
        "numerator": _number(group["numerator"]),
        "denominator": _number(group["denominator"]),
        "value": _number(group["reported_percentage"]),
    }

    if not (
        expected["denominator"] > 0
        and 0 <= expected["numerator"] <= expected["denominator"]
        and 0 <= expected["value"] <= 100
    ):
        raise ValueError("Invalid source percentage evidence.")

    try:
        observed = {
            field: _number(claim[field])
            for field in expected
        }
    except ValueError:
        return {
            "decision": "Insufficient Evidence",
            "reason": "Claim numbers could not be parsed reliably.",
        }

    mismatches = [
        field for field in expected
        if observed[field] != expected[field]
    ]

    return {
        "decision": "Refuted" if mismatches else "Supported",
        "reason": (
            "Numerical mismatch within matched scope."
            if mismatches else
            "Scope and reported numerical attributes match."
        ),
        "mismatched_numeric_fields": mismatches,
        "evidence_id": evidence["evidence_id"],
    }
