---
name: onboarding-start
description: Create comprehensive onboarding documentation for a codebase or feature. Use when user asks to "create an onboarding document", "document this codebase for new developers", "write onboarding docs for X", or similar requests for developer onboarding documentation.
---

# Onboarding Document Creator

Orchestrates the creation of onboarding documentation by coordinating the onboarding-analyzer, onboarding-gaps-verifier, and onboarding-writer skills.

## Procedure

1. Copy `create_onboarding_doc.xml` to the working directory with an appropriate name (e.g., `auth_feature_onboarding.xml`)
2. Create a todo list with phases from the XML plan
3. Execute each phase using the appropriate skill:
   - **source-material-gathering** + **key-information-extraction**: Use `onboarding-analyzer`
   - **gaps-pitfalls-identification**: Use `onboarding-gaps-verifier`
   - **document-writing**: Use `onboarding-writer`
   - **verification**: Use `onboarding-gaps-verifier`
4. When a phase is finished:
   - Set `status="completed"` on the phase element in the XML file
   - Mark the corresponding todo item as completed
5. Continue until all phases are done

## Artifacts Produced

Name artifacts appropriately for the feature being documented (e.g., `auth_source_inventory.md`).

| Phase | Artifact | Skill |
|-------|----------|-------|
| 1-2 | `{name}_source_inventory.md`, `{name}_extraction_tables.md` | onboarding-analyzer |
| 3 | `{name}_gaps_pitfalls.md` | onboarding-gaps-verifier |
| 4 | `{name}_onboarding_doc.md` | onboarding-writer |
| 5 | `{name}_verification_log.md` | onboarding-gaps-verifier |
