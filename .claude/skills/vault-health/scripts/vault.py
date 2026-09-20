"""Shared helpers for reading an Obsidian vault (plain markdown folder). Standard library only (Python 3.9+). Read-only unless a script says otherwise."""
import os, re
from datetime import date, datetime

WIKILINK = re.compile(r"(?<!!)\[\[([^\]\n]+?)\]\]")
TASK = re.compile(r"^\s*[-*]\s+\[( |x|X)\]\s+(.*)$")
DUE = re.compile(r"(?:📅\s*|\[due::\s*|\bdue:\s*)(\d{4}-\d{2}-\d{2})")
DONE = re.compile(r"✅\s*(\d{4}-\d{2}-\d{2})")
SKIP_DIRS = {".obsidian", ".git", ".trash", "node_modules"}

def parse_frontmatter(text):
    """Returns (dict, body). Handles `key: value`, `key: [a, b]` and `- item` lists. Deliberately small; not a full YAML parser."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    block, body = text[3:end].strip("\n"), text[end + 4:].lstrip("\n")
    fm, key = {}, None
    for line in block.split("\n"):
        m = re.match(r"^([A-Za-z0-9_\- ]+):\s*(.*)$", line)
        if m:
            key, val = m.group(1).strip().lower(), m.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                fm[key] = [x.strip().strip("'\"") for x in val[1:-1].split(",") if x.strip()]
            elif val == "":
                fm[key] = []
            else:
                fm[key] = val.strip("'\"")
        elif key and re.match(r"^\s*-\s+", line):
            if not isinstance(fm.get(key), list): fm[key] = []
            fm[key].append(re.sub(r"^\s*-\s+", "", line).strip().strip("'\""))
    return fm, body

def outside_code(body, offset=0):
    """Yield (line_number, line) for lines not inside ``` fences. Pass Note.offset so numbers are FILE line numbers, not body-relative."""
    fenced = False
    for i, line in enumerate(body.split("\n"), start=1 + offset):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            yield i, line

def link_target(raw):
    t = raw.split("|")[0].split("#")[0].split("^")[0].strip()
    return t.split("/")[-1]

class Note:
    def __init__(self, root, path):
        self.path = path; self.rel = os.path.relpath(path, root).replace(os.sep, "/"); self.stem = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8", errors="replace") as f: self.text = f.read()
        self.fm, self.body = parse_frontmatter(self.text)
        self.offset = self.text[:len(self.text) - len(self.body)].count("\n")   # lines consumed by frontmatter, so reported line numbers match the file
        self.mtime = datetime.fromtimestamp(os.path.getmtime(path)).date()
        mod = self.fm.get("modified") or self.fm.get("updated")     # a frontmatter date beats file mtime (mtimes are lost by unzip, git, sync tools)
        if isinstance(mod, str):
            try: self.mtime = date.fromisoformat(mod[:10])
            except ValueError: pass
        self.folder = self.rel.split("/")[0] if "/" in self.rel else ""
        al = self.fm.get("aliases") or self.fm.get("alias") or []
        self.aliases = al if isinstance(al, list) else [al]
    def links(self):
        out = []
        for i, line in outside_code(self.body, self.offset):
            line = re.sub(r"`[^`]*`", "", line)
            for m in WIKILINK.finditer(line):
                t = m.group(1)
                if re.search(r"\.(png|jpe?g|gif|svg|pdf|mp4|webp)$", t.split("|")[0].split("#")[0], re.I): continue
                out.append((i, link_target(t), m.group(0)))
        return out

def load_vault(root, ignore_dirs=()):
    notes = []
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and d not in set(ignore_dirs))
        for f in sorted(files):
            if f.lower().endswith(".md"): notes.append(Note(root, os.path.join(base, f)))
    return notes

def resolver(notes):
    """lower-case name or alias -> list of notes"""
    idx = {}
    for n in notes:
        for key in [n.stem.lower()] + [a.lower() for a in n.aliases]:
            idx.setdefault(key, []).append(n)
    return idx

def parse_day(s):
    return datetime.strptime(s, "%Y-%m-%d").date()

def fail(msg):
    import sys; print(f"ERROR: {msg}", file=sys.stderr); sys.exit(2)
