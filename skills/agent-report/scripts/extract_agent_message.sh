#!/bin/bash
# Extract the final message from a Claude agent JSONL file
# Usage: extract_agent_message.sh <agent_id> [output_file]
# Example: extract_agent_message.sh ad42ecb
# Example: extract_agent_message.sh ad42ecb report.md

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <agent_id> [output_file]"
    echo "Example: $0 ad42ecb"
    echo "Example: $0 ad42ecb report.md"
    exit 1
fi

AGENT_ID="$1"
OUTPUT_FILE="${2:-agent-${AGENT_ID}-report.md}"

# Find agent file in Claude projects directory
CLAUDE_DIR="$HOME/.claude/projects"
AGENT_FILE=$(find "$CLAUDE_DIR" -name "agent-${AGENT_ID}.jsonl" 2>/dev/null | head -1)

if [ -z "$AGENT_FILE" ]; then
    echo "Error: Agent file not found for ID: $AGENT_ID"
    echo "Searched in: $CLAUDE_DIR"
    exit 1
fi

echo "Found agent file: $AGENT_FILE"

# Extract metadata and content from the last message
tail -1 "$AGENT_FILE" | jq -r '
{
    agent_id: .agentId,
    slug: .slug,
    timestamp: .timestamp,
    model: .message.model,
    text: (.message.content | map(select(.type == "text") | .text) | join("\n\n"))
} | "# Agent Report: \(.slug // .agent_id)\n\n**Agent ID:** \(.agent_id)\n**Model:** \(.model)\n**Timestamp:** \(.timestamp)\n\n---\n\n\(.text)"
' > "$OUTPUT_FILE"

echo "Written to: $OUTPUT_FILE"
