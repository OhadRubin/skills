---
name: onboarding-analyzer
description: Gather and analyze source material for onboarding documentation. Creates source_inventory.md and extraction_tables.md. Triggered by onboarding-start during source-material-gathering and key-information-extraction phases.
---

# Onboarding Analyzer

Gather source material and extract key information from a codebase for onboarding documentation.

## Workflow

### Phase 1: Source Material Gathering

Create `source_inventory.md` with three sections:

**1.1 Identify Code Files**
```bash
# Find implementation files
find . -name "*.py" -o -name "*.ts" -o -name "*.js" | head -20
# Or use glob/grep to find specific features
```

Record:
- File paths
- Entry points (main functions, exports)
- Brief 1-line description of each file

**1.2 Identify Existing Docs**
```bash
find . -name "README*" -o -name "*.md" | head -20
```

For each doc:
- Path
- 1-2 sentence summary

**1.3 Identify Plans/Specs**

Locate requirements, specs, or design docs. Note if absent.

### Phase 2: Key Information Extraction

Create `extraction_tables.md` with structured tables:

**2.1 Function Table**

| Function | File:Lines | Purpose |
|----------|-----------|---------|
| `foo()` | `main.py:42-50` | Initializes the config |
| `bar()` | `main.py:52-80` | Processes input data |

**2.2 Dependency Table**

| Dependency | Version/Source | Used By |
|------------|----------------|---------|
| `anthropic` | PyPI | `llm.py` |
| `requests` | PyPI | `api.py` |

**2.3 Data Flow**

Document the "happy path":
1. Entry: `main()` receives request
2. Calls: `validate()` checks input
3. Calls: `process()` does work
4. Returns: result to caller

## Key Questions to Answer

During gathering:
- What feature/phase is being documented?
- Which files are main implementation?
- What existing documentation exists?

During extraction:
- What are the main functions/classes?
- What calls what?
- What external APIs are used?

## Success Criteria

`source_inventory.md`:
- [ ] Code, docs, plans sections present
- [ ] File paths verified to exist
- [ ] At least one entry point identified

`extraction_tables.md`:
- [ ] Function table with accurate line numbers
- [ ] Dependency table with versions
- [ ] Data flow from entry to exit documented
