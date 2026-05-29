"""Failure-mode classifier for NL2GeoSQL evaluation records.

Bins a failed evaluation row into one of {pass, catalog, dialect, golden,
safety, unknown}. Self-contained — extracted from the evaluation orchestrator
so the offline reproduction toolchain has no LLM-API dependency.
"""
from __future__ import annotations


def classify_failure(rec: dict) -> str:
    """Bin a failed row into one of {catalog, dialect, golden, safety, unknown}.

    Passing rows return 'pass'. Robust (safety/refusal) rows return 'safety'
    regardless of pass/fail because the failure attribution for those is
    categorical, not error-string-driven.
    """
    if rec["ex"] == 1:
        return "pass"
    reason = (rec.get("reason") or "").lower()
    perr = (rec.get("pred_error") or "").lower()
    gerr = (rec.get("gold_error") or "").lower()
    pred = (rec.get("pred_sql") or "").lower()
    if rec.get("is_robust"):
        return "safety"
    # Golden execution problems take precedence (shouldn't happen post P0-b).
    if gerr and "no gold" not in gerr:
        return "golden"
    # Dialect signatures.
    if "round(double precision, integer)" in perr:
        return "dialect"
    if "operator does not exist" in perr:
        return "dialect"
    if "function" in perr and "does not exist" in perr:
        return "dialect"
    # Schema-level issues — column not found means catalog needs aliases.
    if "column" in perr and "does not exist" in perr:
        return "catalog"
    if "relation" in perr and "does not exist" in perr:
        return "catalog"
    # Empty SQL = generation gave up.
    if not pred:
        return "unknown"
    # Row-count / value mismatch likely indicates filter logic error rooted
    # in unmapped business term → catalog.
    if "row count" in reason or "rowset mismatch" in reason or "value:" in reason:
        return "catalog"
    return "unknown"
