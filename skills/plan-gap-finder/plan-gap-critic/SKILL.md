---
name: plan-gap-critic
description: Phase 2 of plan-gap-finder. Self-critique the raw gaps. Triggered by plan-gap-start.
---

# Plan Gap Critic

Review each gap from Phase 1 output and mark CORE or NOT CORE.

## Decision filters

| Question | If YES → | If NO → |
|----------|----------|---------|
| Number, threshold, or sample size? | NOT CORE | continue |
| Googleable term? | NOT CORE | continue |
| Explained elsewhere in doc? | NOT CORE | continue |
| Competent reader would infer? | NOT CORE | continue |
| Core logic depends on this? | CORE | NOT CORE |

## CORE examples

- Novel term coined by doc, used repeatedly, never defined
- Central concept the approach depends on
- "X enables Y" — mechanism unexplained

## NOT CORE examples

- Numbers (retry counts, thresholds)
- Named algorithms — googleable
- Implementation details

## Output format

```
# Phase 2: Critiqued Gaps

| Gap | Verdict | Reason |
|-----|---------|--------|
| "foo" | CORE | novel term, logic depends on it |
| "bar" | NOT CORE | googleable |
| "3 retries" | NOT CORE | tunable number |
```
