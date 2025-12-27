# Adding a New Skill to this repo

1. Ask the user where the skill is located. It may be a folder with a `SKILL.md` or a `.skill` file (a zip archive).
2. If `.skill` file, unzip it to `skills/<skill-name>/`
3. Add an entry to `.claude-plugin/marketplace.json` in the `plugins` array
4. Add an entry to `README.md` in the "Available Skills" section
5. Push to the repository
6. Provide the user with
 ```
 /plugin marketplace update ohads_skills
 /plugin install <skillname>@ohads_skills
 ```
 so he could copy paste and quickly install it

