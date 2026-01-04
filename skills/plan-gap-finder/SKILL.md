---
name: plan-gap-finder
description: Use this skill only when the user explicitly requests it.
---

Review the provided document and list conceptual gaps that prevent self-containment.

Do this in THREE PHASES:


stop and think after each phase, like so:
- read the document
- think about phase 1 (not visible)
- write a visible message for phase 1 (visible, in requested output format)
- read the first line of the document (AGAIN)
- think about phase 2 (not visible)
- write a visible message for phase 2 (visible, in requested output format)
- read the first line of the document (AGAIN)
- think about phase 3 (not visible)
- write a visible message for phase 3 (visible, in requested output format)


YOU MUST FOLLOW THE FORMAT ABOVE IN ORDER TO TRIGGER THE THINKING PHASE
---
# Phase 1: Identify
Generate a raw list of potential gaps. Don't filter yet.

## What I'm looking for

Terms or claims that are used but never defined/justified — things that would block a reader from understanding the plan's intent.

Good: "'X' - undefined"
Bad: "Why do we need X? What problem does it solve? Alternatives?"

Good: "'Y' - unexplained"
Bad: "Y's relationship to Z is unclear, causal mechanism not established"

## Rules

1. **One line per gap** — no sub-bullets, no elaboration
2. **Question the why, not the how** — approach-level, not implementation-level
3. **Flag, don't fix** — just name the undefined term, don't speculate what it might mean
4. **Only flag CORE gaps** — ask: "can a reader follow the document's logic without this?" If yes, skip it.
   - **Core:** novel term coined by the document, used repeatedly, never defined
   - **Core:** central concept the whole approach depends on
   - **Core:** relationship between two concepts that drives the logic ("X enables Y" — how?)
   - **Core:** a claim presented as obvious but isn't ("this predicts that" — why?)
   - **Not core:** specific numbers (retry counts, thresholds, sample sizes) — tunable
   - **Not core:** named methods/algorithms — googleable
   - **Not core:** standard industry terms
   - **Not core:** implementation details (data structures, file paths, function names)
   - **Not core:** edge cases or error handling specifics
5. **Max 15 items** — forces you to prioritize the real blockers

## Output format

```
- [Line 42] "foo" - undefined — why core: used 10+ times, logic depends on it
- [Line 87] "X enables Y" - asserted — why core: central claim of the approach
```

Each flag MUST include "why core:" explaining why this blocks understanding the document's logic. If you can't justify it, don't include it.

## Examples of good vs bad questions

| Bad (too analytical) | Good (just flag it) |
|----------------------|---------------------|
| "'foo' is circular, relies on 'bar' which uses 'foo'" | "'foo' - undefined" |
| "Why X instead of Y or Z?" | "'X' - unexplained" |
| "Threshold not justified, alternatives not discussed" | "'threshold' - unjustified" |
| "Causal mechanism between A and B unexplained" | "'A → B' - asserted" |
| "How system achieves X without Y is unclear" | "'X' - unclear" |
| "Line 50 contradicts line 80 regarding..." | "'X' - inconsistent" |
| "Why X is Y, not explained" | "'X is Y' - unjustified" |

## What I DON'T want

- **Analysis** — don't explain WHY something is a gap, just name it
- **Comparisons** — don't suggest alternatives or ask "why not X?"
- **Diagnosis** — don't say "circular definition" or "causal mechanism unexplained"
- **Elaboration** — if you can say it in 3 words, don't use 15
- **Cross-references** — don't say "vs. line X" or "contradicts line Y"
- **"Why X" framing** — don't write "why X is Y, not explained" — just write "'X' - unexplained"

Your job is to POINT, not to EXPLAIN. Imagine you're putting sticky notes on a document — each sticky note has 3-5 words max.

## Anti-patterns to avoid

- Exploding one concept into multiple sub-questions
- Asking about parameter choices (that's implementation)
- Questioning standard industry terms
- Listing things the document explicitly explains elsewhere
- Comparing to alternatives ("why X not Y")
- Analyzing the nature of the gap ("circular", "causal", "conflates")
- **No question marks** — you're flagging, not asking
- **No "vs" between lines** — don't write "X vs Y", flag each separately if both matter



# Phase 2: Self-critique

For each gap from Phase 1, run through these filters:

| Question | If YES → | If NO → |
|----------|----------|---------|
| Is this a number, threshold, or sample size? | NOT CORE | continue |
| Can the reader google this term? | NOT CORE | continue |
| Is this explained elsewhere in the document? | NOT CORE | continue |
| Would a competent reader infer this from context? | NOT CORE | continue |
| Does the document's core logic depend on this? | CORE | NOT CORE |

Output a table:
```
| Gap | Verdict | Reason |
|-----|---------|--------|
| "foo" | CORE | logic depends on it, used 10x |
| "bar" | NOT CORE | googleable standard term |
```

# Phase 3: Refine
Output only the CORE items in the final format.
