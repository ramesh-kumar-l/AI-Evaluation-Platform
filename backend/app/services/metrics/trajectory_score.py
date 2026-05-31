"""Trajectory score: Dice-LCS similarity over ordered tool-name sequences."""

from __future__ import annotations


def _lcs_length(a: list[str], b: list[str]) -> int:
    """Longest common subsequence length via DP."""
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[m][n]


def score_trajectory(expected_tools: list[str], actual_tools: list[str]) -> float:
    """Return Dice-LCS: 2·LCS / (|expected| + |actual|).

    Confidence: low — captures ordering but ignores tool argument quality.
    """
    if not expected_tools and not actual_tools:
        return 1.0
    if not expected_tools or not actual_tools:
        return 0.0
    lcs = _lcs_length(expected_tools, actual_tools)
    return round(2.0 * lcs / (len(expected_tools) + len(actual_tools)), 4)
