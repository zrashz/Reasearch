"""Structured numerical development checker.

Requires prepared, correctly scoped evidence.
Does not extract facts from prose, tables or images.
A Supported result applies only to the supplied numerical assertion.
"""

from decimal import Decimal, InvalidOperation

SCOPE_FIELDS = ("metric", "unit", "population", "condition")
LABELS = {"Supported", "Refuted", "Insufficient Evidence"}


def number(value):
    if isinstance(value, bool) or value is None:
        raise ValueError("Invalid numerical value.")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ValueError("Invalid numerical value.") from error
    if not result.is_finite():
        raise ValueError("Non-finite numerical value.")
    return result


def insufficient(reason):
    return {"decision": "Insufficient Evidence", "reason": reason}


def check_numeric_assertion(claim, evidence):
    # Invalid evidence is a preparation error.
    if not isinstance(evidence, dict):
        raise ValueError("Evidence must be a dictionary.")

    if not evidence.get("evidence_id"):
        raise ValueError("Evidence identifier is required.")

    scope = evidence.get("scope")
    if not isinstance(scope, dict) or any(
        scope.get(field) in (None, "") for field in SCOPE_FIELDS
    ):
        raise ValueError("Evidence scope is incomplete.")

    values = evidence.get("values")
    if not isinstance(values, dict) or not values:
        raise ValueError("Evidence values are required.")

    source = {}
    for entity, value in values.items():
        if not isinstance(entity, str) or not entity.strip():
            raise ValueError("Invalid evidence entity.")
        source[entity] = number(value)

    if not isinstance(claim, dict):
        return insufficient("Invalid claim structure.")

    claim_scope = claim.get("scope")
    if not isinstance(claim_scope, dict):
        return insufficient("Missing claim scope.")

    if any(
        claim_scope.get(field) in (None, "") for field in SCOPE_FIELDS
    ):
        return insufficient("Incomplete claim scope.")

    if claim_scope != scope:
        return insufficient("Claim and evidence scopes do not match.")

    operation = claim.get("operation")
    arities = {
        "value": 1,
        "difference": 2,
        "ratio": 2,
        "percent_change": 2,
    }
    if operation not in arities:
        return insufficient("Unsupported numerical operation.")

    operands = claim.get("operands")
    if (
        not isinstance(operands, list)
        or len(operands) != arities[operation]
        or any(not isinstance(item, str) for item in operands)
    ):
        return insufficient("Invalid operand identifiers.")

    if any(entity not in source for entity in operands):
        return insufficient("Required source entities are unavailable.")

    try:
        observed = number(claim.get("value"))
    except ValueError:
        return insufficient("Claim value is missing or invalid.")

    selected = [source[entity] for entity in operands]

    if operation == "value":
        expected = selected[0]
        result_unit = scope["unit"]
    elif operation == "difference":
        # Ordered operands: first minus second.
        expected = selected[0] - selected[1]
        result_unit = scope["unit"]
    elif operation == "ratio":
        if selected[1] == 0:
            return insufficient("Ratio denominator is zero.")
        expected = selected[0] / selected[1]
        result_unit = "ratio"
    else:
        # Ordered operands: baseline, new value.
        baseline, new_value = selected
        if baseline <= 0:
            return insufficient(
                "This percentage-change implementation requires "
                "a positive baseline."
            )
        expected = (new_value - baseline) / baseline * 100
        result_unit = "percent"

    if claim.get("result_unit") != result_unit:
        return insufficient("Result unit does not match the operation.")

    # Explicit decimal rounding only; no hidden tolerance.
    places = claim.get("decimal_places")
    if places is not None:
        if (
            isinstance(places, bool)
            or not isinstance(places, int)
            or not 0 <= places <= 8
        ):
            return insufficient("Invalid decimal precision.")
        from decimal import ROUND_HALF_UP
        quantum = Decimal(1).scaleb(-places)
        expected = expected.quantize(quantum, rounding=ROUND_HALF_UP)

    return {
        "decision": "Supported" if observed == expected else "Refuted",
        "reason": "Compared numerical assertion within matched scope.",
        "expected_value": str(expected),
        "claim_value": str(observed),
        "result_unit": result_unit,
        "evidence_id": evidence["evidence_id"],
        "scope": scope,
    }


def aggregate_conjunction(decisions, decomposition_complete=False):
    """Aggregate AND-connected atomic claims only.

    Complete decomposition must be established upstream.
    """
    if (
        not isinstance(decisions, list)
        or not decisions
        or any(label not in LABELS for label in decisions)
    ):
        return insufficient("Missing or invalid atomic decisions.")

    if "Refuted" in decisions:
        return {
            "decision": "Refuted",
            "reason": "At least one conjunct is contradicted.",
        }

    if not decomposition_complete:
        return insufficient("Complete claim decomposition is unconfirmed.")

    if all(label == "Supported" for label in decisions):
        return {
            "decision": "Supported",
            "reason": "Every conjunct is supported.",
        }

    return insufficient("At least one conjunct remains unresolved.")
