# Factory Relay Inspect Agent-Runtime Eval

Model: `openai-api/deepseek/deepseek-v4-pro`

| condition | status | score | log |
| --- | --- | ---: | --- |
| `no_skills` | success | 1.0000 | `/tmp/ai4ss-factory-relay-logs/2026-07-04T17-56-45-00-00_factory-relay_QJTZPBKcmkMcsLvYpYuNHx.eval` |
| `single_skill` | success | 1.0000 | `/tmp/ai4ss-factory-relay-logs/2026-07-04T18-01-18-00-00_factory-relay_PdxwK7S2pVhmpiTn2iUBwm.eval` |
| `full_skills` | success | 0.9818 | `/tmp/ai4ss-factory-relay-logs/2026-07-04T18-05-09-00-00_factory-relay_WPFFbsF7sspX7qRwqYwA7J.eval` |
| `broken_handoff` | success | 1.0000 | `/tmp/ai4ss-factory-relay-logs/2026-07-04T18-10-32-00-00_factory-relay_cBWSGQ9zXkVANP5sMi2ZSQ.eval` |
| `shuffled_order` | success | 0.9300 | `/tmp/ai4ss-factory-relay-logs/2026-07-04T18-12-44-00-00_factory-relay_dypqv7WFWE6w6rZGpqatp6.eval` |

## Audit Findings

| condition | audit_ok | error codes |
| --- | --- | --- |
| `no_skills` | True | - |
| `single_skill` | True | - |
| `full_skills` | False | invalid_next_skill_route |
| `broken_handoff` | True | - |
| `shuffled_order` | False | data_repair_misrouted, status_route_mismatch |

## Marginal Gain

- `full_vs_no_skills`: -0.0182
- `full_vs_single_skill`: -0.0182
- `broken_handoff_vs_no_skills`: 0.0000
- `shuffled_order_vs_no_skills`: -0.0700
- `full_skills_score`: 0.9818
- `no_skills_score`: 1.0000
- `single_skill_score`: 1.0000
- `broken_handoff_score`: 1.0000
- `shuffled_order_score`: 0.9300
