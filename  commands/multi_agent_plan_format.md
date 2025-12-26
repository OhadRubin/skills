# Prompt: Convert Phased Plan to Multi-Agent Execution Plan

## Background

### Motivation

We want to create training data for multi-agent systems that perform code refactoring. The challenge: writing code that executes refactorings directly is bug-prone and hard to debug. Instead, we decompose refactoring tasks into well-defined subtasks that agents can execute independently.

By requiring explicit write targets in the phased plan, we make dependencies between steps clear. This gives us high-quality training data where:
- Each agent task is atomic and well-scoped
- Dependencies between tasks are clear
- Success/failure is easy to determine
- The execution trace shows clean handoffs between agents

This prompt is part of a pipeline for generating that training data:

```text
┌─────────────────────────────────┐
│  Natural Language Refactoring  │
│            Plan                │
└─────────────────────────────────┘
                │
                │ decompose (with write targets)
                ↓
┌─────────────────────────────────┐
│         Phased Plan            │
│    (phases + write targets)    │
└─────────────────────────────────┘
                │
                │ convert to agents  ← YOU ARE HERE
                ↓
┌─────────────────────────────────┐
│  Multi-Agent Execution Plan    │
│      (Task tool calls)         │
└─────────────────────────────────┘
```

### Why this pipeline?

Writing code that executes refactorings directly is bug-prone. By decomposing the problem into agents with well-defined subtasks, we get:

1. **Dependency Ordering**: Explicit write targets make execution order clear. If phase B writes to what phase A modifies → B depends on A.

2. **Atomic Operations**: Each phase is a well-scoped transformation that either succeeds or fails cleanly.

3. **Composability**: Phases compose cleanly, enabling clear agent handoffs. Each agent has a well-defined input (codebase state) and output (transformed codebase state).

4. **Verifiability**: Write targets make verification easy. Check that expected files/functions were modified.

---

## Your Task

You are given a **phased plan** — a natural language refactoring plan decomposed into ordered phases, with explicit write targets for each phase.

Your task is to convert this into a **multi-agent execution plan** using the `Task` tool to spawn subagents.

Extract the relevant information:
- What phases exist and their ordering
- For each phase: what it does and what files/functions it modifies (write targets)
- Any explicit dependencies between phases

---

## Agent Cost Awareness

Agents have overhead (context loading, coordination, handoffs). Minimize agent count while maintaining parallelism benefits.

**Use direct commands (not agents) for:**
- Deleting a file: `Bash('rm path/to/file.py')`
- Running tests: `Bash('pytest ...')`
- Simple renames: `Bash('mv old.py new.py')`

**Use agents for:**
- Deleting specific functions/tests from files
- Merging/consolidating code
- Refactoring patterns across multiple files
- Anything requiring code comprehension

---

## Output Format: Task Tool Execution Plan

For each phase, produce Task tool invocations. The prompt should be **pure natural language** describing what the agent needs to accomplish — just the intent, not the implementation details.

### Why natural language prompts?

Agent prompts should be natural language describing intent, not implementation details:

1. **Easier to write**: Natural language is simpler than specifying exact commands
2. **More robust**: The agent can adapt to edge cases
3. **Better training signal**: We want agents that understand intent, not agents that blindly execute commands
4. **Composable**: Natural language tasks are easier to combine and modify

```python
# Phase 1: <description>
# Dependencies: none

Task(
    description="<3-5 word description>",
    subagent_type="general-purpose",
    prompt="<Natural language description of what to accomplish>"
)

# Phase 2: <description>
# Dependencies: Phase 1

Task(
    description="<3-5 word description>",
    subagent_type="general-purpose",
    prompt="<Natural language description of what to accomplish>"
)
```

---

## Instructions

1. **Determine Execution Order**: Which Task invocations can run in parallel vs must be sequential?
   - Independent WRITE targets → parallel (multiple Task calls in one message)
   - Same WRITE target (even if different source files) → sequential
   - Pattern A produces what pattern B matches → sequential (wait for TaskOutput)

   ⚠️ "Independent files" means independent WRITE destinations, not just different source files.

2. **Write Agent Prompts**: Each Task prompt should be pure natural language describing the intent. The agent figures out how to execute it.

3. **Handle Dependencies**: Use `run_in_background=True` for parallel agents, then `TaskOutput` to collect results before dependent phases.

---

## Example

### Input: Phased Plan

```text
Phase 1: Rename all instances of `get_data` to `fetch_data`
  - Write targets: all Python files containing get_data calls

Phase 2: Add logging to all `fetch_data` calls
  - Write targets: all Python files containing fetch_data calls
  - Depends on: Phase 1
```

### Output: Task Tool Execution Plan

```python
# Phase 1: Rename get_data to fetch_data
# Dependencies: none

Task(
    description="Rename get_data to fetch_data",
    subagent_type="general-purpose",
    prompt="Rename all calls to get_data to fetch_data across all Python files."
)

# Phase 2 depends on Phase 1 (pattern matches what Phase 1 produces)

Task(
    description="Add logging to fetch_data",
    subagent_type="general-purpose",
    prompt="Wrap all fetch_data calls with log_call() across all Python files."
)
```

### Parallel Execution Example

If a phase has independent transformations (e.g., different file scopes), run them in parallel:

```python
# These can run in parallel - single message, multiple Task calls

Task(
    description="Rename in module_a",
    subagent_type="general-purpose",
    run_in_background=True,
    prompt="Rename get_data to fetch_data in module_a."
)

Task(
    description="Rename in module_b",
    subagent_type="general-purpose",
    run_in_background=True,
    prompt="Rename get_data to fetch_data in module_b."
)

# Collect results before moving to dependent phases
TaskOutput(task_id="<agent_1_id>")
TaskOutput(task_id="<agent_2_id>")
```

### Anti-Pattern: Parallel Merges to Same Target

When consolidating/merging functions, the SOURCE files may differ but the TARGET is the same. This is a race condition.

**Input:**
```text
Phase 2: Consolidate functions
  2.1: Merge helper_a (from utils_a.py) into main_handler
  2.2: Merge helper_b (from utils_b.py) into main_handler
```

**WRONG (parallel - race condition):**
```python
# ❌ Both write to main_handler!
Task(run_in_background=True, prompt="Merge helper_a into main_handler...")
Task(run_in_background=True, prompt="Merge helper_b into main_handler...")
```

**CORRECT (sequential):**
```python
# ✓ Sequential because same write target
Task(prompt="Merge helper_a into main_handler...")
Task(prompt="Merge helper_b into main_handler...")
```

---

## Now convert the following

<INSERT_PHASED_PLAN>

---

## Process

1. Read both input files
2. Extract: phases, operations per phase, target files, dependencies
3. Group operations by related files (1-3 files per agent)
4. Determine parallelism based on file independence
5. Generate Task invocations with natural language prompts
6. Write output to `<input_dir>/<plan_name>_AGENT_PLAN.md`

## Decomposition Rules

### Grouping

**Optimal agent scope:**
- Each agent handles **2-5 related files** (not 1 file per agent)
- Group by functional domain, not individual file
- All operations on the same file → same agent (mandatory)

**Signs you're over-decomposing:**
- More than 5 agents for a single phase
- Agents handling only 1 file each
- Agents doing trivial operations (single delete, simple rename)

### Parallelism

**Safe to parallelize:**
- Operations with different WRITE targets
- Read-only operations (searches, validations)
- Deletions of unrelated functions

**Must be sequential OR bundled into one agent:**
- Operations that WRITE to the same file
- Operations that WRITE to the same function/class (even if sources are different files)
- Merge operations with the same TARGET (critical!)
- Operations where one produces what another consumes

Both approaches avoid race conditions: sequential agents OR one agent handling all writes to a target.

After parallel batch, collect with `TaskOutput` before next phase.

### Dependencies
- Phase N+1 depends on Phase N completing
- Within a phase: group independent operations for parallel execution
- Operations that modify same function/class → sequential

### Bundling

**Bundle into ONE agent when:**
- Operations are sequential AND on the same file
- Operations are in the same functional domain
- Create-then-use pattern with small scope

**Keep separate when:**
- Create-then-use pattern with large scope

**Create-then-use scope threshold:**
- **Small (bundle):** ≤10 usages across ≤3 files
- **Large (split):** >10 usages OR >3 files

When in doubt, bundle. Splitting creates coordination overhead.

## Output Format

Key points:
- Natural language prompts (WHAT not HOW)
- No implementation details in prompts
- Include execution overview table
- Include compact execution flow summary
- Include expected results table

## Example Decomposition

Input: 15 test deletions across 8 files

Bad (1 agent):
```python
Task(prompt="Delete all 15 tests from 8 files...")  # Too broad
```

Bad (8 agents):
```python
Task(prompt="Delete from file1...")  # Too granular
Task(prompt="Delete from file2...")
# ... 6 more
```

Good (3 agents by ML domain):
```python
Task(prompt="Delete tests from test_data_loader.py, test_preprocessing.py, test_augmentation.py...")  # Data pipeline
Task(prompt="Delete tests from test_model.py, test_layers.py, test_attention.py...")  # Model architecture
Task(prompt="Delete tests from test_training_loop.py, test_metrics.py...")  # Training/evaluation
```

Good (3 agents by ML lifecycle stage):
```python
Task(prompt="Delete tests from test_feature_extraction.py, test_embeddings.py, test_tokenizer.py...")  # Feature engineering
Task(prompt="Delete tests from test_optimizer.py, test_scheduler.py, test_checkpoint.py...")  # Training infrastructure
Task(prompt="Delete tests from test_inference.py, test_batch_predict.py...")  # Serving/inference
```

Good (3 agents by model components):
```python
Task(prompt="Delete tests from test_encoder.py, test_decoder.py...")  # Core architecture
Task(prompt="Delete tests from test_loss_functions.py, test_regularization.py, test_dropout.py...")  # Training mechanics
Task(prompt="Delete tests from test_model_export.py, test_onnx_conversion.py, test_quantization.py...")  # Model deployment
```

### Example: Trivial Operation (Use Bash)

Bad (agent for trivial op):
```python
Task(prompt="Delete file X...")  # Overkill
```

Good (direct command):
```python
Bash('rm path/to/file.py')
```

### Example: Same-File Bundling

Bad (2 agents for same file):
```python
Task(prompt="Do operation A in file.py...")
Task(prompt="Do operation B in file.py...")
```

Good (1 agent):
```python
Task(prompt="In file.py: do operation A, then do operation B.")
```

### Example: Create-Then-Use (Scope Dependent)

**Small scope → bundle:**
```python
Task(prompt="Create helper X in utils.py, then update the 3 usages in module.py.")
```

**Large scope → split:**
```python
Task(prompt="Create helper X in utils.py...")
TaskOutput(task_id="<helper_id>")

Task(run_in_background=True, prompt="Update module_a.py to use helper X...")
Task(run_in_background=True, prompt="Update module_b.py to use helper X...")
Task(run_in_background=True, prompt="Update module_c.py to use helper X...")
```

# Output Format Reference

## Structure

```markdown
# Multi-Agent Execution Plan: <Title>

This plan uses natural language prompts that describe intent, letting agents determine implementation details.

---

## Execution Overview

| Phase | Description | Dependencies | Parallelizable |
|-------|-------------|--------------|----------------|
| 1 | ... | None | Yes (N agents) |
| 2 | ... | Phase 1 | Yes (N agents), then M sequential |
| ... | ... | ... | ... |

## Write Target Analysis

| Task | Source(s) | Write Target | Can Parallel With |
|------|-----------|--------------|-------------------|
| 1.1 | file_a.py | target_1.py | 1.2 |
| 1.2 | file_b.py | target_2.py | 1.1 |
| 2.1 | file_c.py | target_3.py:func | 2.2 |
| 2.2 | file_d.py | target_3.py:func | ❌ (same target as 2.1) |

---

## Phase 1: <Description> (Parallel)

```python
# Phase 1.1: <task>
# Dependencies: none

Task(
    description="<3-5 words>",
    subagent_type="general-purpose",
    run_in_background=True,
    prompt="<Natural language intent>"
)

# Phase 1.2: <task>
# Dependencies: none

Task(
    description="<3-5 words>",
    subagent_type="general-purpose",
    run_in_background=True,
    prompt="<Natural language intent>"
)

# Collect Phase 1 results
TaskOutput(task_id="<phase_1.1_id>")
TaskOutput(task_id="<phase_1.2_id>")
```

---

## Phase N: <Description>

```python
# Phase N.1: <task>
# Dependencies: Phase N-1

Task(
    description="<3-5 words>",
    subagent_type="general-purpose",
    prompt="<Natural language intent>"
)
```

---

## Complete Execution Flow

```python
# === PHASE 1: ... ===
Task(description="...", subagent_type="general-purpose", run_in_background=True, prompt="...")
Task(description="...", subagent_type="general-purpose", run_in_background=True, prompt="...")

TaskOutput(task_id="<1.1_id>")
TaskOutput(task_id="<1.2_id>")

# === PHASE 2: ... ===
...
```

---

## Expected Results

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| ... | ... | ... | ... |
```

## Task Properties

- `description`: 3-5 word summary
- `subagent_type`: Always "general-purpose"
- `run_in_background`: True for parallel tasks, omit for sequential
- `prompt`: Natural language describing WHAT to do, not HOW

## Prompt Style

Bad (implementation details):
```python
prompt="""Run ast-grep --pattern 'def foo($$$): $$$' --rewrite '' -U"""
```

Good (natural language intent):
```python
prompt="""Delete the function foo from utils.py."""
```

## Decision Tree: Should This Be Its Own Agent?

```
Operation to perform
        │
        ▼
┌─────────────────────┐
│ Is it trivial?      │──Yes──► Direct command (Bash)
│ (rm, mv, pytest)    │
└─────────────────────┘
        │ No
        ▼
┌─────────────────────┐
│ Same file as        │──Yes──► Bundle with that agent
│ another operation?  │
└─────────────────────┘
        │ No
        ▼
┌─────────────────────┐
│ Create-then-use     │──Small scope──► Single agent does both
│ dependency?         │──Large scope──► Split (create first, then parallel consumers)
└─────────────────────┘
        │ No
        ▼
┌─────────────────────┐
│ Same domain as      │──Yes──► Bundle into domain agent
│ other operations?   │
└─────────────────────┘
        │ No
        ▼
    Own agent ✅
```
