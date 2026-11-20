"""Narrow latency binding adapter.

Supports explicit '<entity>'s <number> seconds' wording and
a unique '<integer>-hop' table column.
Returns binding candidates, not full scientific decisions.
"""
import re


def bind_latency_mentions(claim, rows, caption):
    unresolved = []
    bindings = []

    if not isinstance(caption, str) or not re.search(
        r"\blatency\b", caption, re.IGNORECASE
    ):
        return {
            "bindings": [],
            "unresolved": ["Latency table context not established."],
        }

    conditions = list(re.finditer(r"\b\d+-hop\b", claim))
    if len(conditions) != 1:
        return {
            "bindings": [],
            "unresolved": ["A unique explicit hop condition is required."],
        }

    condition = conditions[0].group(0)
    if len(rows) < 2:
        return {"bindings": [], "unresolved": ["Missing table rows."]}

    width = len(rows[0])
    if any(len(row) != width for row in rows):
        return {"bindings": [], "unresolved": ["Irregular table width."]}

    columns = [
        i for i, cell in enumerate(rows[0])
        if cell["text"].strip() == condition
    ]
    if len(columns) != 1:
        return {
            "bindings": [],
            "unresolved": ["Condition column is missing or ambiguous."],
        }

    column = columns[0]
    entity_rows = {}
    for row in rows[1:]:
        entity = row[0]["text"].strip().rstrip("♠♢").strip()
        if entity and not entity.startswith("\\"):
            entity_rows.setdefault(entity.casefold(), []).append((entity, row))

    for entries in entity_rows.values():
        entity = entries[0][0]
        pattern = (
            rf"(?<!\w){re.escape(entity)}[’']s\s+"
            rf"(?P<value>\d+(?:\.\d+)?)\s+seconds\b"
        )
        mentions = list(re.finditer(pattern, claim, re.IGNORECASE))
        if not mentions:
            continue

        if len(entries) != 1 or len(mentions) != 1:
            unresolved.append("Ambiguous entity or claim mention: " + entity)
            continue

        _, row = entries[0]
        source_text = row[column]["text"].strip()
        if not re.fullmatch(r"[+-]?\d+(?:\.\d+)?", source_text):
            unresolved.append("Source value is not a plain number: " + entity)
            continue

        mention = mentions[0]
        bindings.append({
            "entity": entity,
            "condition": condition,
            "claim_quote": mention.group(0),
            "claim_offsets": [mention.start(), mention.end()],
            "claim_value": mention.group("value"),
            "source_value": source_text,
            "source_cell_id": row[column]["cell_id"],
            "entity_cell_id": row[0]["cell_id"],
            "condition_cell_id": rows[0][column]["cell_id"],
        })

    if not bindings:
        unresolved.append("No supported entity-value wording matched.")

    unresolved.append(
        "Other claim components and complete scientific scope remain unchecked."
    )
    return {"bindings": bindings, "unresolved": unresolved}
