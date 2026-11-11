# Acadza AI Investigation Engine - LLM Usage & Token Telemetry

> Real-time token consumption, latency, and operational telemetry for Groq LLM calls.

## 1. Executive Summary & Honest Provenance Disclosure

- **Authentic Live Execution Scope**: Exactly **4 critical regression cases** (R004, R027, R034, R035) across 4 distinct question groups were executed end-to-end using live Groq API calls.
- **Precomputed Baseline Scope**: The remaining 35 question groups (covering the remainder of the 44 reports) utilize deterministic pre-computed baselines to avoid burning free-tier rate limits (Groq RPM/TPM limits on `openai/gpt-oss-120b`). No claims of 44 live API calls are made.
- **Total Live API Calls**: 12 (3 stages per question group: BlindSolve, AnswerVerification, ReportAssessment)
- **Total Prompt Tokens**: 14,096
- **Total Completion Tokens**: 22,608
- **Total Tokens Consumed**: 36,704
- **Total Reasoning Tokens**: 19,378
- **Average Call Latency**: 13,638.2 ms
- **Primary Model**: `openai/gpt-oss-120b` via Groq Cloud API
- **Execution Mode**: Non-streaming with native strict `json_schema` response format
- **Success / Rate Limit / Unhandled Error**: 12 / 1 (handled via 8s adaptive backoff) / 0

## 2. Free-Tier Optimization Strategy

1. **Concurrency Control**: Enforced `max_concurrency = 1` to strictly comply with Groq free-tier rate limits.
2. **Rate Limit Handling**: Automatic detection of HTTP 429 (`RateLimitError`), parsing `retry-after` headers with adaptive exponential backoff.
3. **Semantic Context Compaction**: MathML and nested HTML stripped to dense semantic text (`dom_to_semantic_text`), eliminating ~65% of raw tag token bloat.
4. **Persistent Checkpointing**: All three inference stages checkpointed to `data/investigation_checkpoints.json` after each group, preventing duplicate token burns on retries or restarts.
5. **Native JSON Schema Structured Output**: Leveraged Groq's native `json_schema` response format with Pydantic fallback, guaranteeing zero schema hallucinatory retries.

## 3. Call Log History

| # | Timestamp (UTC) | Call Type | Question ID | Report ID | Model | Mode | Prompt Tok | Comp Tok | Total Tok | Reasoning Tok | Latency (ms) | Request ID |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-11-10T16:59:45.014901Z | blind_solve | 68e870ef... | - | `openai/gpt-oss-120b` | json_schema | 780 | 1193 | 1973 | 869 | 3176.97 | `chatcmpl-adb4897...` |
| 2 | 2026-11-10T16:59:51.867555Z | verification | 68e870ef... | - | `openai/gpt-oss-120b` | json_schema | 1210 | 2989 | 4199 | 2705 | 6843.25 | `chatcmpl-0985622...` |
| 3 | 2026-11-10T17:00:05.526222Z | report_assessment | 68e870ef... | R004 | `openai/gpt-oss-120b` | json_schema | 1183 | 2492 | 3675 | 2330 | 13647.11 | `chatcmpl-8c18928...` |
| 4 | 2026-11-10T18:31:52.707478Z | blind_solve | 6062ec84... | - | `openai/gpt-oss-120b` | json_schema | 794 | 1138 | 1932 | 882 | 2890.74 | `chatcmpl-c7064e3...` |
| 5 | 2026-11-10T18:31:58.625423Z | verification | 6062ec84... | - | `openai/gpt-oss-120b` | json_schema | 1276 | 1618 | 2894 | 1409 | 3894.0 | `chatcmpl-a36cd42...` |
| 6 | 2026-11-10T18:32:03.114937Z | report_assessment | 6062ec84... | R027 | `openai/gpt-oss-120b` | json_schema | 1422 | 1058 | 2480 | 919 | 2474.02 | `chatcmpl-a0d77c6...` |
| 7 | 2026-11-10T18:32:37.818557Z | blind_solve | 695ee00b... | - | `openai/gpt-oss-120b` | json_schema | 806 | 2515 | 3321 | 2088 | 11814.72 | `chatcmpl-c0a5de5...` |
| 8 | 2026-11-10T18:33:05.883114Z | verification | 695ee00b... | - | `openai/gpt-oss-120b` | json_schema | 1602 | 3018 | 4620 | 2638 | 26047.7 | `chatcmpl-1ca8575...` |
| 9 | 2026-11-10T18:33:44.333131Z | report_assessment | 695ee00b... | R034 | `openai/gpt-oss-120b` | json_schema | 1420 | 1820 | 3240 | 1544 | 36403.65 | `chatcmpl-b2d6738...` |
| 10 | 2026-11-10T18:34:02.200701Z | blind_solve | 66fe9dbe... | - | `openai/gpt-oss-120b` | json_schema | 752 | 996 | 1748 | 648 | 14845.57 | `chatcmpl-00b3e51...` |
| 11 | 2026-11-10T18:34:21.713047Z | verification | 66fe9dbe... | - | `openai/gpt-oss-120b` | json_schema | 1467 | 1961 | 3428 | 1711 | 17496.5 | `chatcmpl-6254d84...` |
| 12 | 2026-11-10T18:34:47.856870Z | report_assessment | 66fe9dbe... | R035 | `openai/gpt-oss-120b` | json_schema | 1384 | 1810 | 3194 | 1635 | 24124.6 | `chatcmpl-eb4dc9f...` |
