---
name: onboarding-gaps-verifier
description: Identify documentation gaps, pitfalls, and verify onboarding documents. Creates gaps_pitfalls.md and verification_log.md. Triggered by onboarding-start during gaps-pitfalls-identification and verification phases.
---

# Onboarding Gaps Verifier

Identify gaps and pitfalls in code understanding, and verify onboarding documents.

## Workflow

### Phase 1: Gaps & Pitfalls Identification

Create `gaps_pitfalls.md` with three sections:

**1.1 Non-Obvious Requirements**

Review extracted info and source code for:
- Implicit assumptions in the code
- Required environment setup not mentioned
- Magic values or conventions
- Domain knowledge requirements

Example format:
```markdown
## Non-Obvious Requirements

1. **Environment**: Requires `ANTHROPIC_API_KEY` env var (not documented)
2. **Convention**: All handler functions must return dict with `status` key
3. **Assumption**: Input files must be UTF-8 encoded
```

**1.2 Ordering Dependencies**

Document what must happen in what order:
- Initialization sequences
- Setup before use
- Teardown requirements
- Circular dependencies (if any)

Example format:
```markdown
## Ordering Requirements

1. Initialize config before calling any API functions
2. Register handlers before starting the server
3. Close database connection after all queries complete
```

**1.3 Common Errors**

Based on code analysis, identify likely errors:
- Error messages that are misleading
- Edge cases that fail silently
- Common misconfigurations

Example format:
```markdown
## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `KeyError: 'data'` | Missing response field | Check API version |
| Silent failure | Empty input list | Validate input length |
```

### Phase 2: Document Verification

Create `verification_log.md` with verification results:

**2.1 Accuracy Check**

Spot-check at least 3 line number references:
```markdown
## Accuracy Verification

| Reference | Verified | Notes |
|-----------|----------|-------|
| `main.py:42` | Yes | Correct |
| `api.py:100` | No | Now at line 105 |
```

Verify all file paths exist.

**2.2 Completeness Checklist**

- [ ] Can someone implement using only this doc?
- [ ] Are file paths and line numbers accurate?
- [ ] Is it high-level (minimal code snippets)?
- [ ] Are all steps in dependency order?

**2.3 Style Compliance**

- [ ] Tables over prose for structured data
- [ ] Minimal code snippets (max 3 lines)
- [ ] Clear dependency ordering
- [ ] No placeholder text remains

## Key Questions

For gaps analysis:
- What requires domain knowledge?
- What breaks if done out of order?
- What error messages are misleading?

For verification:
- Can someone implement using only this doc?
- Are all file paths and line numbers current?

## Success Criteria

`gaps_pitfalls.md`:
- [ ] At least 3 non-obvious items (or explicit "none found")
- [ ] All ordering dependencies documented
- [ ] At least 3 common errors with solutions (or explicit "none found")

`verification_log.md`:
- [ ] 3+ line numbers verified
- [ ] All 4 completeness checklist items pass
- [ ] All style compliance items pass
