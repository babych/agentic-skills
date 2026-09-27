---
name: skill-creator
description: Comprehensive framework, architectural guidelines, and automation tools for designing, structuring, testing, and publishing production-grade Antigravity skills.
---

# Antigravity Skill Creator: The Ultimate Engineering Guide

Skills extend the agent's intelligence, workflows, and tool capabilities for specialized domains. A well-designed skill transforms complex manual procedures into reproducible, autonomous AI workflows.

---

## 1. 🏗️ Skill Directory Anatomy

Every skill resides in its own directory (e.g. `.agents/skills/<skill-name>/` or `~/.gemini/antigravity/skills/<skill-name>/`) with the following standardized structure:

```
my-awesome-skill/
├── SKILL.md                 # REQUIRED: Frontmatter + core agent instructions
├── scripts/                 # OPTIONAL: Helper CLI tools, automation scripts (Python/Bash/PowerShell)
│   ├── run_task.py
│   └── test_env.sh
├── examples/                # OPTIONAL: Code samples, reference inputs/outputs
│   ├── sample_input.json
│   └── expected_output.md
├── references/              # OPTIONAL: Deep API documentation, hardware specs, cheat sheets
│   └── architecture_notes.md
└── resources/               # OPTIONAL: Assets, model weights, config templates
    └── template_config.yaml
```

---

## 2. 📝 Writing the Perfect `SKILL.md`

### Frontmatter Standard (YAML)
```yaml
---
name: my-awesome-skill
description: 1-2 sentence precise summary of what the skill does and when the agent should activate it.
---
```

### Core Content Sections
1. **Overview & Goal:** High-level summary of the problem domain.
2. **Prerequisites & Tooling:** Environment variables, required packages, hardware targets.
3. **Execution Pipeline:** Step-by-step instructions with code blocks.
4. **Edge Cases & Failure Modes:** Common pitfalls and how the agent should self-heal.
5. **Quality Verification:** Concrete checklist to verify task completion.

---

## 3. 🎯 Best Practices for Agentic Skills

* **Declarative & Actionable:** Write instructions as clear operational directives rather than conversational prose.
* **Idempotence:** Scripts and commands should be safely re-runnable without breaking existing states.
* **Deterministic Paths:** Always use relative workspace paths or standard environment variables (`$HOME`, `$env:USERPROFILE`).
* **Tool First Philosophy:** Instruct the agent to prioritize native tools (`view_file`, `replace_file_content`) over shell commands when possible.

---

## 4. 🚀 Publishing & Distributing Skills

1. **Workspace Level:** Place in `<workspace_root>/.agents/skills/` (shared with the project repo).
2. **User Global Level:** Place in `~/.gemini/antigravity/skills/` (available across all workspaces).
3. **Git Hub Distribution:** Share via an open skills repository like `Babych/antigravity-skills`.
