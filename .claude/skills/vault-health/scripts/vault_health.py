#!/usr/bin/env python3
"""Read-only health check for an Obsidian vault: broken wikilinks, orphans, duplicate note names, missing frontmatter, empty and stale notes.

Usage: python3 vault_health.py --vault ~/Vault [--require type,created] [--ignore-folders Daily,Templates] [--stale-days 180] [--today 2026-09-20] [--out health.csv]
Orphan = no other note links to it (ignored folders are exempt). Stale = not modified for N days and not in an Archive folder. Nothing is modified.
"""
import argparse, csv, os
from datetime import date
from vault import fail, load_vault, parse_day, resolver

def check(notes, require=(), exempt=(), stale_days=180, today=None):
    today = today or date.today(); idx = resolver(notes); issues = []; inbound = {n.rel: 0 for n in notes}
    for n in notes:
        for line, tgt, raw in n.links():
            hits = idx.get(tgt.lower(), [])
            if not hits: issues.append((n.rel, line, "broken_link", f"{raw} matches no note"))
            elif len(hits) > 1: issues.append((n.rel, line, "ambiguous_link", f"{raw} matches {len(hits)} notes: " + ", ".join(h.rel for h in hits)))
            for h in hits:
                if h.rel != n.rel: inbound[h.rel] += 1
    names = {}
    for n in notes: names.setdefault(n.stem.lower(), []).append(n)
    for k, ns in names.items():
        if len(ns) > 1: issues += [(n.rel, 0, "duplicate_name", "same name as " + ", ".join(m.rel for m in ns if m is not n)) for n in ns]
    for n in notes:
        for r in require:
            if not n.fm.get(r.lower()): issues.append((n.rel, 0, "missing_property", f"no '{r}' in frontmatter"))
        if not n.body.strip(): issues.append((n.rel, 0, "empty_note", "no content"))
        if n.folder not in exempt and inbound[n.rel] == 0: issues.append((n.rel, 0, "orphan", "no other note links here"))
        if (today - n.mtime).days >= stale_days and "archive" not in n.rel.lower() and n.folder not in exempt:
            issues.append((n.rel, 0, "stale", f"not modified for {(today - n.mtime).days} days"))
    return sorted(issues, key=lambda i: (i[2], i[0], i[1]))

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", required=True); ap.add_argument("--require", default=""); ap.add_argument("--ignore-folders", default="Daily,Templates")
    ap.add_argument("--stale-days", type=int, default=180); ap.add_argument("--today"); ap.add_argument("--out", default="vault_health.csv")
    a = ap.parse_args()
    if not os.path.isdir(a.vault): fail(f"not a folder: {a.vault}")
    notes = load_vault(a.vault); ex = tuple(x for x in a.ignore_folders.split(",") if x)
    iss = check(notes, tuple(x for x in a.require.split(",") if x), ex, a.stale_days, parse_day(a.today) if a.today else None)
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["note", "line", "issue", "detail"]); w.writerows(iss)
    counts = {}
    for i in iss: counts[i[2]] = counts.get(i[2], 0) + 1
    print(f"{len(notes)} notes scanned, {len(iss)} issues: " + (", ".join(f"{k} {v}" for k, v in sorted(counts.items())) or "none"))
    for note, line, kind, detail in iss[:40]: print(f"  {kind:<16} {note}{':' + str(line) if line else ''}  {detail}")
    print(f"Wrote {a.out} (vault untouched)")

if __name__ == "__main__":
    main()
