"""Conservative parser for simple HTML tables.

Rejects merged cells, nested tables and irregular row widths.
Preserves cell text; does not infer scientific scope or units.
"""
from html.parser import HTMLParser


class SimpleTableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.depth = 0
        self.rows = None
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "table":
            if self.depth:
                raise ValueError("Nested table requires another adapter.")
            self.depth = 1
            self.rows = []
        elif self.depth and tag == "tr":
            if self.row is not None:
                raise ValueError("Unclosed table row.")
            self.row = []
        elif self.depth and tag in ("td", "th"):
            if self.row is None or self.cell is not None:
                raise ValueError("Invalid cell structure.")
            for attribute in ("rowspan", "colspan"):
                if attrs.get(attribute, "1") != "1":
                    raise ValueError("Merged cells require another adapter.")
            self.cell = []
        elif self.cell is not None and tag == "br":
            self.cell.append(" ")

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if not self.depth:
            return
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr":
            if self.cell is not None or self.row is None:
                raise ValueError("Incomplete row.")
            self.rows.append(self.row)
            self.row = None
        elif tag == "table":
            if self.row is not None or self.cell is not None:
                raise ValueError("Incomplete table.")
            self.tables.append(self.rows)
            self.depth = 0
            self.rows = None


def parse_simple_table(html):
    if not isinstance(html, str) or not html.strip():
        raise ValueError("Missing HTML.")
    parser = SimpleTableParser()
    parser.feed(html)
    parser.close()
    if parser.depth or len(parser.tables) != 1:
        raise ValueError("Expected one complete table.")
    rows = parser.tables[0]
    if len(rows) < 2 or len(rows[0]) < 2:
        raise ValueError("Insufficient table structure.")
    if any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("Irregular table width.")

    headers = rows[0][1:]
    labels = [row[0] for row in rows[1:]]
    if (
        any(not item for item in headers + labels)
        or len(set(headers)) != len(headers)
        or len(set(labels)) != len(labels)
    ):
        raise ValueError("Missing or ambiguous row/column labels.")

    return {
        "column_headers": headers,
        "rows": [
            {
                "row_label": row[0],
                "cells": dict(zip(headers, row[1:])),
            }
            for row in rows[1:]
        ],
    }
