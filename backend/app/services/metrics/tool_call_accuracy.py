"""Tool-call accuracy: F1 score over the set of expected vs actual tool names."""

from __future__ import annotations


def score_tool_call_accuracy(expected_tools: list[str], actual_tools: list[str]) -> float:
    """Return F1 over tool-name sets (order-independent).

    Confidence: medium — F1 is a standard IR metric; tool names are exact strings.
    """
    if not expected_tools and not actual_tools:
        return 1.0
    if not expected_tools or not actual_tools:
        return 0.0
    exp = set(expected_tools)
    act = set(actual_tools)
    tp = len(exp & act)
    precision = tp / len(act)
    recall = tp / len(exp)
    if precision + recall == 0.0:
        return 0.0
    return round(2.0 * precision * recall / (precision + recall), 4)
