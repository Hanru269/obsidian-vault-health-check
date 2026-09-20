# Obsidian vault rules

This folder is (or contains) the user's personal knowledge base. Treat it as private and irreplaceable.

## Safety
- Read-only by default. Never edit, move, rename or delete a note without showing the exact change and getting a clear yes first.
- Scripts that can move files (`inbox-triage`) run as a dry run first; apply only what the user approved, and tell them how to undo.
- Suggest a backup or a git commit before any batch change. Never touch `.obsidian/`.
- Notes are private: do not paste their contents anywhere else or send them anywhere.

## Accuracy
- Counts, dates, task buckets and link lists come from the scripts in `.claude/skills/*/scripts/`, not from your own tallying.
- Say which date you used as "today". Quote note names and line numbers so everything is checkable.
- If something is not visible in the vault (why a task slipped, what a note is for), say so instead of guessing.

## Style
- Short, plain, lead with the answer. Suggestions are labelled as suggestions. Reflection prompts are questions, not conclusions.
