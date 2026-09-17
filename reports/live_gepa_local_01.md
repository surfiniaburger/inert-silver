# Debate Benchmark Telemetry: `live-gepa-local-01`

## Executive Summary

| Metric | Value |
| :--- | :--- |
| **Run ID** | `live-gepa-local-01` |
| **Total Attempts** | 14 |
| **Accepted Rows** | 6 |
| **Yield Pass Rate** | 42.9% |
| **Total Wall-Clock Time** | 1313.7s |
| **Total Prompt Tokens** | 122,811 |
| **Total Completion Tokens** | 32,497 |
| **Tokens / Accepted Row** | 25,884.67 |
| **Cache Hit Rate** | 0.0% (0 hits / 34 misses) |

## Stage Breakdown

| Stage | Calls | Prompt Tokens | Completion Tokens | Avg | P50 (ms) | P95 (ms) | P99 (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `generator_boundary` | 10 | 32,665 | 10,455 | 29779.5ms | 25389.8ms | 45194.9ms | 48311.5ms |
| `judge_adjudication` | 14 | 67,043 | 13,749 | 65276.9ms | 63923.6ms | 80717.6ms | 85058.7ms |
| `verifier_audit` | 6 | 7,420 | 5,187 | 40818.7ms | 37515.6ms | 57958.0ms | 58972.4ms |
| `generator_refine` | 4 | 15,683 | 3,106 | 25501.1ms | 26007.8ms | 30974.1ms | 31672.2ms |

## Quality Gate Signals

- **Verifier Pass Rate:** 100.0%
- **Verifier Parse OK Rate:** 100.0%
- **Anchor Match Rate:** 100.0%
- **B-Gate Pass Status:** `FAIL`
