# /// script
# dependencies = [
#   "claude-agent-sdk",
#   "dicttoxml",
#   "pygments",
# ]
# ///

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    UserMessage,
    SystemMessage,
    ResultMessage,
    PermissionResultAllow,
    ToolPermissionContext,
)
import argparse
import asyncio
import os
import xml.etree.ElementTree as ET
from dataclasses import asdict
from pathlib import Path
from typing import Any, AsyncIterator

import json
from xml.dom.minidom import parseString

import dicttoxml
from pygments import highlight
from pygments.lexers import XmlLexer
from pygments.formatters import TerminalFormatter

"""
deloy haiku models in BFS mode that would help you add additional relevant files 
deploy 1 agent per phase
each agent should read the plan, and suggest additional relevant files per subphase
here are additional directories that might be relevant
/home/ohadr/quick_compose
/home/ohadr/quick_compose_evalbox
/home/ohadr/treebench
enchourage them to search using rg+wc for general terms iterativly and narrow down their search. """



def get_terminal_size() -> tuple[int, int]:
    """Get terminal size (lines, columns)."""
    import shutil
    size = shutil.get_terminal_size()
    return size.lines, size.columns


def truncate_value(value: Any, max_lines: int, wrap_width: int) -> Any:
    """Wrap and truncate a string value if it exceeds max_lines."""
    import textwrap

    if isinstance(value, str):
        # Wrap each line to terminal width
        wrapped_lines = []
        for line in value.splitlines():
            if line.strip():
                wrapped_lines.extend(textwrap.wrap(line, width=wrap_width) or [''])
            else:
                wrapped_lines.append('')

        if len(wrapped_lines) > max_lines:
            truncated = '\n'.join(wrapped_lines[:max_lines])
            return f"{truncated}\n... ({len(wrapped_lines) - max_lines} lines truncated)"
        return '\n'.join(wrapped_lines)
    elif isinstance(value, dict):
        return {k: truncate_value(v, max_lines, wrap_width) for k, v in value.items()}
    elif isinstance(value, list):
        return [truncate_value(item, max_lines, wrap_width) for item in value]
    return value


def filter_null_fields(data: Any) -> Any:
    """Recursively remove None/null fields from a dict."""
    if isinstance(data, dict):
        return {k: filter_null_fields(v) for k, v in data.items() if v is not None}
    elif isinstance(data, list):
        return [filter_null_fields(item) for item in data]
    return data


def safe_asdict(obj, truncate: bool = False) -> dict:
    """Convert dataclass to dict with optional truncation and JSON-safe fallback."""
    d = asdict(obj)

    if truncate:
        lines, cols = get_terminal_size()
        max_lines = max(5, lines // 3)
        wrap_width = max(40, cols - 10)  # Leave margin for XML indentation
        d = truncate_value(d, max_lines, wrap_width)

    # Ensure JSON-serializable by round-tripping with default=str
    return json.loads(json.dumps(d, default=str))


def dict_to_pretty_xml(data: dict) -> str:
    """Convert a dict to pretty-printed XML with syntax highlighting, filtering out null fields."""
    filtered = filter_null_fields(data)
    xml = dicttoxml.dicttoxml(filtered, attr_type=False)
    dom = parseString(xml)
    pretty_xml = dom.toprettyxml(indent='  ')
    return highlight(pretty_xml, XmlLexer(), TerminalFormatter())

def get_pending_subphases(plan_path: str) -> list[str]:
    """Return list of pending subphase IDs from plan XML.

    A subphase is a <phase> nested inside another <phase>.
    Pending means status != "completed".
    """
    plan_file = Path(plan_path)
    if not plan_file.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_path}")

    tree = ET.parse(plan_file)
    root = tree.getroot()

    pending = []
    for subphase in root.findall('.//phase/phase'):
        status = subphase.get('status', 'pending')
        if status != 'completed':
            pending.append(subphase.get('id'))

    return pending


def is_plan_complete(plan_path: str) -> bool:
    """Check if all subphases in plan are completed."""
    pending = get_pending_subphases(plan_path)
    return len(pending) == 0


def get_prompt(plan_path: str) -> str:
    return f"""Your goal is to implement the next **subphase** in {plan_path}. READ THE ENTIRE FILE.
1. Look for the next **subphase** in {plan_path} that has status!="completed".
    1.1. If you feel the subphase is trivial, you may attempt to do several subphases in one go. (NOT RECOMMENDED). At this point you should focus on single subphase. Do not ask me if you are not sure, (I have my responses set to always auto-approve)
        Examples for trivial subphases:
        - write a test
        - run a command
        - verify something works 
2. Go into plan mode, and explore the repo as you normally do in plan mode, using Explore agents (in BFS mode).
 2.1. Include a list of files you are sure are relevant to the subphase (you might have missed some)
 2.2. As a backup to identify files you might have missed and are relevant, give them a list of general terms to rg and explore these files)
 2.3. Give them a questions to answer that would help you come up with a plan.
3. Write your plan.
4. Exit plan mode.
5. Again, deploy Explore agents (in DFS mode). This time, use the things you learned from the other agents to fine-tune your understanding of the codebase (same methodology as above), do this in order to gain exact line-numbers and file paths, so you wouldn't have to read so much. Your context length is more valuable than the Explore agents.
6. Implement the plan using the information the Explore agents provided you.
7. Set status="completed", and add tags explaining what you did in {plan_path} (2 lines max).
8. Commit and push (or merge into the target branch, depending on the subphase instructions)."""

TEST_PROMPT = """Go into plan mode, write "create 'Hello there' in a new file", exit plan mode and do what the plan says."""


async def auto_approve(
    tool_name: str, tool_input: dict[str, Any], context: ToolPermissionContext
) -> PermissionResultAllow:
    """Auto-approve all tool requests."""
    return PermissionResultAllow()


async def prompt_stream(prompt: str) -> AsyncIterator[dict[str, Any]]:
    """Wrap prompt as async iterable."""
    yield {"type": "user", "message": {"role": "user", "content": prompt}}


def handle_message(message):
    """Handle a single message from the agent - XML output."""
    truncate = isinstance(message, UserMessage)
    d = {"type": type(message).__name__, **safe_asdict(message, truncate=truncate)}
    print(dict_to_pretty_xml(d))


async def run_single_iteration(prompt: str):
    """Run a single agent iteration."""
    options = ClaudeAgentOptions(
        can_use_tool=auto_approve,
        system_prompt={"type": "preset", "preset": "claude_code"},
        add_dirs=[os.path.expanduser("~/treebench")],
    )

    async with ClaudeSDKClient(options) as client:
        await client.query(prompt_stream(prompt))
        async for message in client.receive_response():
            handle_message(message)


async def run_agent(prompt: str, plan_path: str, max_iterations: int | None = None):
    """Run agent with prompt.

    Args:
        prompt: The prompt to send to the agent
        plan_path: Path to plan XML for termination check
        max_iterations: Max iterations to run (None = infinite)
    """
    iteration = 0
    while max_iterations is None or iteration < max_iterations:
        # Check termination condition
        pending = get_pending_subphases(plan_path)
        if not pending:
            print("All subphases completed! Plan is done.")
            break

        iteration += 1
        print(f"[Iteration {iteration}] {len(pending)} subphases remaining: {pending[0]}, ...")

        await run_single_iteration(prompt)
        await asyncio.sleep(1)


async def main():
    parser = argparse.ArgumentParser(description="Run Claude agent to implement plan")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test prompt (create Hello there file) once instead of plan loop",
    )
    parser.add_argument(
        "--max-iterations", "-n",
        type=int,
        default=None,
        help="Max iterations to run (default: infinite)",
    )
    parser.add_argument(
        "plan_path",
        type=str,
        help="Path to plan XML file",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show plan status (pending subphases) and exit",
    )
    args = parser.parse_args()

    if args.status:
        pending = get_pending_subphases(args.plan_path)
        total = len(ET.parse(args.plan_path).findall('.//phase/phase'))
        completed = total - len(pending)
        print(f"Plan: {args.plan_path}")
        print(f"Progress: {completed}/{total} subphases completed")
        if pending:
            print(f"\nPending ({len(pending)}):")
            for p in pending:
                print(f"  - {p}")
        else:
            print("\nAll subphases completed!")
        return

    if args.test:
        await run_agent(TEST_PROMPT, args.plan_path, max_iterations=1)
    else:
        await run_agent(get_prompt(args.plan_path), args.plan_path, max_iterations=args.max_iterations)


if __name__ == "__main__":
    asyncio.run(main())
