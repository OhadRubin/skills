#!/usr/bin/env python3
"""
Multi-Skill Initializer - Creates a multi-phase skill from template

Usage:
    init_multi_skill.py <skill-name> --path <path> [--phases N]

Examples:
    init_multi_skill.py gap-finder --path skills/public
    init_multi_skill.py code-reviewer --path skills/private --phases 4
    init_multi_skill.py doc-analyzer --path /custom/location --phases 2
"""

import sys
from pathlib import Path


START_SKILL_TEMPLATE = """---
name: start-{skill_name}
description: {skill_description} Use when user explicitly asks start-{skill_name}.
---

# {skill_title}

{skill_overview}

## Procedure

{procedure_steps}

**IMPORTANT:** Do NOT stop between steps. Output what each step requires, then immediately continue to the next skill. Run all steps {skill_name}-* in a single turn.
"""

PHASE_SKILL_TEMPLATE = """---
name: {skill_name}-{phase_num}
description: Triggered by start-{skill_name}.
---

# {skill_title} - Phase {phase_num}

{phase_description}

## What to do

[TODO: Define the specific task for this phase]

## Rules

1. [TODO: Add rule 1]
2. [TODO: Add rule 2]
3. [TODO: Add rule 3]

## Output format

```
# Step {phase_num}: {phase_output_title}

[TODO: Define output structure]
```

## Anti-patterns

- [TODO: What to avoid]
"""


def title_case_skill_name(skill_name):
    """Convert hyphenated skill name to Title Case for display."""
    return ' '.join(word.capitalize() for word in skill_name.split('-'))


def generate_procedure_steps(skill_name, num_phases):
    """Generate the procedure steps for the start skill."""
    lines = []
    for i in range(1, num_phases + 1):
        if i == 1:
            lines.append(f"{i}. Invoke `{skill_name}-{i}` skill on the document")
        else:
            lines.append(f"{i}. Invoke `{skill_name}-{i}` skill (uses Step {i-1} output from conversation)")
    return '\n'.join(lines)


def get_phase_description(phase_num, num_phases):
    """Generate placeholder description based on phase position."""
    if phase_num == 1:
        return "[TODO: First phase - typically raw identification/collection]"
    elif phase_num == num_phases:
        return "[TODO: Final phase - typically refinement/summary]"
    else:
        return "[TODO: Middle phase - typically filtering/analysis]"


def get_phase_output_title(phase_num, num_phases):
    """Generate placeholder output title based on phase position."""
    if phase_num == 1:
        return "Raw Output"
    elif phase_num == num_phases:
        return "Final Output"
    else:
        return f"Phase {phase_num} Output"


def init_multi_skill(skill_name, path, num_phases=3):
    """
    Initialize a new multi-phase skill directory structure.

    Args:
        skill_name: Name of the skill (e.g., 'gap-finder')
        path: Path where the skill directory should be created
        num_phases: Number of phases (default 3)

    Returns:
        Path to created skill directory, or None if error
    """
    if num_phases < 2:
        print("Error: Multi-skill requires at least 2 phases")
        raise ValueError("Multi-skill requires at least 2 phases")

    # Determine skill directory path
    skill_dir = Path(path).resolve() / skill_name

    # Check if directory already exists
    if skill_dir.exists():
        print(f"Error: Skill directory already exists: {skill_dir}")
        raise FileExistsError(f"Skill directory already exists: {skill_dir}")

    skill_title = title_case_skill_name(skill_name)

    # Create main skill directory
    try:
        skill_dir.mkdir(parents=True, exist_ok=False)
        print(f"Created skill directory: {skill_dir}")
    except Exception as e:
        print(f"Error creating directory: {e}")
        raise

    # Create start-* orchestrator skill
    start_dir = skill_dir / f"start-{skill_name}"
    try:
        start_dir.mkdir(exist_ok=False)
        start_content = START_SKILL_TEMPLATE.format(
            skill_name=skill_name,
            skill_title=skill_title,
            skill_description="[TODO: Brief description of what this multi-phase skill does.]",
            skill_overview="[TODO: 1-2 sentences explaining what this skill enables]\n\nRun {num_phases} steps in sequence. Each step is a separate skill invocation.".format(num_phases=num_phases),
            procedure_steps=generate_procedure_steps(skill_name, num_phases)
        )
        (start_dir / 'SKILL.md').write_text(start_content)
        print(f"Created start-{skill_name}/SKILL.md")
    except Exception as e:
        print(f"Error creating start skill: {e}")
        raise

    # Create phase skills
    for phase_num in range(1, num_phases + 1):
        phase_dir = skill_dir / f"{skill_name}-{phase_num}"
        try:
            phase_dir.mkdir(exist_ok=False)
            phase_content = PHASE_SKILL_TEMPLATE.format(
                skill_name=skill_name,
                skill_title=skill_title,
                phase_num=phase_num,
                phase_description=get_phase_description(phase_num, num_phases),
                phase_output_title=get_phase_output_title(phase_num, num_phases)
            )
            (phase_dir / 'SKILL.md').write_text(phase_content)
            print(f"Created {skill_name}-{phase_num}/SKILL.md")
        except Exception as e:
            print(f"Error creating phase {phase_num} skill: {e}")
            raise

    # Print summary
    print(f"\nSkill '{skill_name}' initialized successfully at {skill_dir}")
    print(f"\nStructure created:")
    print(f"  {skill_name}/")
    print(f"    start-{skill_name}/SKILL.md  (orchestrator)")
    for i in range(1, num_phases + 1):
        print(f"    {skill_name}-{i}/SKILL.md        (phase {i})")
    print(f"\nNext steps:")
    print(f"1. Edit start-{skill_name}/SKILL.md to update description and overview")
    print(f"2. Edit each {skill_name}-N/SKILL.md to define phase-specific tasks")
    print(f"3. Test by invoking: /start-{skill_name}")

    return skill_dir


def main():
    if len(sys.argv) < 4 or sys.argv[2] != '--path':
        print("Usage: init_multi_skill.py <skill-name> --path <path> [--phases N]")
        print("\nCreates a multi-phase skill with:")
        print("  - start-<name>/SKILL.md  (orchestrator that runs all phases)")
        print("  - <name>-1/SKILL.md      (phase 1)")
        print("  - <name>-2/SKILL.md      (phase 2)")
        print("  - ...                    (additional phases)")
        print("\nOptions:")
        print("  --phases N    Number of phases (default: 3, minimum: 2)")
        print("\nExamples:")
        print("  init_multi_skill.py gap-finder --path skills/public")
        print("  init_multi_skill.py code-reviewer --path skills/private --phases 4")
        sys.exit(1)

    skill_name = sys.argv[1]
    path = sys.argv[3]

    # Parse optional --phases argument
    num_phases = 3
    if '--phases' in sys.argv:
        phases_idx = sys.argv.index('--phases')
        if phases_idx + 1 < len(sys.argv):
            try:
                num_phases = int(sys.argv[phases_idx + 1])
            except ValueError:
                print("Error: --phases must be followed by a number")
                sys.exit(1)

    print(f"Initializing multi-skill: {skill_name}")
    print(f"   Location: {path}")
    print(f"   Phases: {num_phases}")
    print()

    try:
        result = init_multi_skill(skill_name, path, num_phases)
        sys.exit(0)
    except Exception as e:
        print(f"\nFailed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
