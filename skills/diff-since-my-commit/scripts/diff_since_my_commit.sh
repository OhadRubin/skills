#!/bin/bash
# Show changes to a branch since your last commit, opened in browser
#
# Usage: ./diff_since_my_commit.sh <branch> [email1,email2,...]
# Example: ./diff_since_my_commit.sh origin/backend_refactor
# Example: ./diff_since_my_commit.sh origin/main "me@gmail.com,me@work.com"

set -e

BRANCH="${1:-HEAD}"
DIFF_FILE="/tmp/changes_since_my_commit.diff"

# Get emails - from arg, or default to git config
if [ -n "$2" ]; then
    IFS=',' read -ra EMAILS <<< "$2"
else
    EMAILS=("$(git config user.email)")
fi

if [ -z "${EMAILS[0]}" ]; then
    echo "Error: No email specified and git config user.email is not set"
    exit 1
fi

echo "Looking for your last commit on $BRANCH..."
echo "Emails: ${EMAILS[*]}"

# Fetch latest
git fetch --quiet 2>/dev/null || true

# Find your last commit on the branch (check all emails)
MY_LAST_COMMIT=""
for email in "${EMAILS[@]}"; do
    commit=$(git log "$BRANCH" --author="$email" --format="%H" -1 2>/dev/null || true)
    if [ -n "$commit" ]; then
        # Keep the most recent one
        if [ -z "$MY_LAST_COMMIT" ]; then
            MY_LAST_COMMIT="$commit"
        else
            # Compare timestamps
            ts1=$(git log -1 --format="%ct" "$MY_LAST_COMMIT")
            ts2=$(git log -1 --format="%ct" "$commit")
            if [ "$ts2" -gt "$ts1" ]; then
                MY_LAST_COMMIT="$commit"
            fi
        fi
    fi
done

if [ -z "$MY_LAST_COMMIT" ]; then
    echo "Error: No commits found by ${EMAILS[*]} on $BRANCH"
    exit 1
fi

MY_LAST_COMMIT_SHORT=$(git log -1 --format="%h %s" "$MY_LAST_COMMIT")
echo "Your last commit: $MY_LAST_COMMIT_SHORT"

# Count commits since yours
COMMITS_SINCE=$(git rev-list --count "$MY_LAST_COMMIT..$BRANCH")
echo "Commits since then: $COMMITS_SINCE"

if [ "$COMMITS_SINCE" -eq 0 ]; then
    echo "No changes since your last commit."
    exit 0
fi

# Show who made those commits
echo ""
echo "Authors of changes:"
git log "$MY_LAST_COMMIT..$BRANCH" --format="%an" | sort | uniq -c | sort -rn
echo ""

# Find files YOU touched in your commits on this branch
# (from merge-base with main to your last commit)
MERGE_BASE=$(git merge-base "$BRANCH" origin/main 2>/dev/null || git merge-base "$BRANCH" main 2>/dev/null || echo "")

MY_FILES=""
for email in "${EMAILS[@]}"; do
    if [ -n "$MERGE_BASE" ]; then
        files=$(git log "$MERGE_BASE..$MY_LAST_COMMIT" --author="$email" --name-only --format="" 2>/dev/null | sort -u)
    else
        files=$(git log "$MY_LAST_COMMIT" --author="$email" --name-only --format="" 2>/dev/null | sort -u)
    fi
    MY_FILES="$MY_FILES $files"
done
MY_FILES=$(echo "$MY_FILES" | tr ' ' '\n' | sort -u | grep -v '^$')

if [ -z "$MY_FILES" ]; then
    echo "Error: Could not determine which files you touched"
    exit 1
fi

FILE_COUNT=$(echo "$MY_FILES" | wc -l | tr -d ' ')
echo "Files you touched: $FILE_COUNT"
echo "$MY_FILES" | head -10
[ "$FILE_COUNT" -gt 10 ] && echo "... and $((FILE_COUNT - 10)) more"
echo ""

# Generate diff only for files you touched (and only if modified, not new)
git diff "$MY_LAST_COMMIT..$BRANCH" --diff-filter=M -- $MY_FILES > "$DIFF_FILE"

LINES=$(wc -l < "$DIFF_FILE" | tr -d ' ')
echo "Diff saved to $DIFF_FILE ($LINES lines)"

# Open in browser with diff2html
if command -v diff2html &> /dev/null; then
    echo "Opening in browser..."
    diff2html -i file -s side -o preview -- "$DIFF_FILE"
else
    echo "Install diff2html for browser preview: npm install -g diff2html-cli"
    echo "Or view the diff with: less $DIFF_FILE"
fi
