# Skills

Skills are folders of instructions, scripts, and resources that Claude loads dynamically to improve performance on specialized tasks. Skills teach Claude how to complete specific tasks in a repeatable way.

For more information, check out:
- [What are skills?](https://support.claude.com/en/articles/12512176-what-are-skills)
- [Using skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude)
- [How to create custom skills](https://support.claude.com/en/articles/12512198-creating-custom-skills)

# About This Repository

This repository contains Ohad's custom skills for Claude.

# Available Skills

- [python-file-splitter](./skills/python-file-splitter): Split large Python modules into smaller, well-organized files
- [skill-creator](./skills/skill-creator): Create a new skill
- [skill-spec-generator](./skills/skill-spec-generator): Generate structured skill specifications for independent skill creators
- [diff-since-my-commit](./skills/diff-since-my-commit): Show changes to a git branch since your last commit, filtered to only files you touched
- [agent-report](./skills/agent-report): Extract and display the final message from a Claude agent JSONL file

# Try in Claude Code

You can register this repository as a Claude Code Plugin marketplace by running the following command in Claude Code:
```
/plugin marketplace add OhadRubin/skills
```

Then, to install the skill:
1. Select `Browse and install plugins`
2. Select `ohads_skills`
3. Select `python-file-splitter`
4. Select `Install now`

Alternatively, directly install via:
```
/plugin install python-file-splitter@ohads_skills
```
