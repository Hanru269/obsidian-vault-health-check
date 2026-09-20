---
name: vault-health
description: Audit an Obsidian vault for broken and ambiguous wikilinks, orphan notes, duplicate note names, missing properties, empty notes and stale notes. Use when the user asks to check, clean up, or audit their vault or notes.
---

# Vault health

Read-only. Never edit, move or delete notes in this skill.
1. Confirm the vault path (usually `.` when Claude Code runs inside the vault) and which properties every note should have (ask; e.g. `type,created`). Suggest they have a backup.
2. Run: `python3 .claude/skills/vault-health/scripts/vault_health.py --vault . --require type,created --ignore-folders Daily,Templates --today YYYY-MM-DD --out reports/vault-health.csv`
3. Summarise by issue type with counts, then the most useful fixes first: broken links (say what the likely target is if a similar note name exists), ambiguous links (name the duplicate notes), duplicates, missing properties, orphans, stale.
4. For orphans and stale notes, do not recommend deleting: suggest linking, archiving or ignoring, and let the user decide. Say that "orphan" means nothing links to it, which is normal for inbox and reference notes.
5. Offer to draft fixes as a list of exact edits (file, line, change) for the user to approve. Apply nothing until they say so.
