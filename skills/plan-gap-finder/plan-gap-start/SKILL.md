---
name: plan-gap-start
description: Find conceptual gaps in plan/spec documents. Use when user asks to "find gaps in this plan" or "review this spec for undefined terms".
---

# Plan Gap Finder

Find conceptual gaps by running three phases in sequence. Each phase is a separate skill invocation.

## Procedure

1. Invoke `plan-gap-identifier` skill on the document
2. Invoke `plan-gap-critic` skill (uses Phase 1 output from conversation)
3. Invoke `plan-gap-refiner` skill (uses Phase 2 output from conversation)

Each skill invocation forces a thinking break. Do not combine phases.
