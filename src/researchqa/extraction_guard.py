"""Narrow development guard; not complete semantic verification."""

import copy
import re

POPULATION_PATTERNS = {
    "all_trial_participants": (
        r"\ball trial participants\b",
        r"\ball randomi[sz]ed participants\b",
    ),
    "Table3_NICU_duration_subgroup": (
        r"\btable\s*3\s+nicu[- ]duration subgroup\b",
    ),
}

def guard_attributes(claim_text, attributes):
    if not isinstance(claim_text, str):
        raise TypeError("Claim text must be a string.")
    if not isinstance(attributes, dict):
        raise TypeError("Attributes must be a dictionary.")

    guarded = copy.deepcopy(attributes)
    flags = []

    fraction_present = bool(
        re.search(r"\b\d+\s*/\s*\d+\b", claim_text)
    )

    if not fraction_present:
        for field in ("numerator", "denominator"):
            if guarded.get(field) is not None:
                flags.append({
                    "field": field,
                    "raw_value": guarded[field],
                    "reason": "No recognised explicit count fraction.",
                })
            guarded[field] = None

    population = guarded.get("population")

    if population is not None:
        patterns = POPULATION_PATTERNS.get(population, ())
        explicit = any(
            re.search(pattern, claim_text.lower())
            for pattern in patterns
        )

        if not explicit:
            flags.append({
                "field": "population",
                "raw_value": population,
                "reason": "No recognised explicit population phrase.",
            })
            guarded["population"] = None

    return guarded, flags
