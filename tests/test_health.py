"""Obsidian Second Brain Kit tests. Run: python3 -m unittest discover -s tests -v. Expected values are derived by hand from the planted problems in src/make_sample_vault.py."""
import csv, importlib, os, shutil, subprocess, sys, tempfile, unittest
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "pack") if os.path.isdir(os.path.join(ROOT, "pack")) else ROOT
SV = os.path.join(PACK, "sample-vault"); SK = os.path.join(PACK, ".claude", "skills")
def load(skill, mod):
    p = os.path.join(SK, skill, "scripts")
    if p not in sys.path: sys.path.insert(0, p)
    sys.modules.pop("vault", None); sys.modules.pop(mod, None); return importlib.import_module(mod)
def run(skill, script, *a): return subprocess.run([sys.executable, os.path.join(SK, skill, "scripts", script), *a], capture_output=True, text=True)
def fresh():
    d = tempfile.mkdtemp(); v = os.path.join(d, "vault"); shutil.copytree(SV, v); return d, v
def tree(v): return sorted(os.path.relpath(os.path.join(b, f), v) for b, _, fs in os.walk(v) for f in fs)
D = date(2026, 9, 20)

class TestVault(unittest.TestCase):
    def test_frontmatter(self):
        vt = load("vault-health", "vault")
        fm, body = vt.parse_frontmatter("---\ntype: note\ntags: [a, b]\naliases:\n  - X\n  - Y\n---\nBody")
        self.assertEqual(fm, {"type": "note", "tags": ["a", "b"], "aliases": ["X", "Y"]}); self.assertEqual(body, "Body")
        self.assertEqual(vt.parse_frontmatter("no frontmatter")[0], {})
    def test_link_targets(self):
        vt = load("vault-health", "vault")
        self.assertEqual([vt.link_target(x) for x in ("Note", "Note|alias", "Note#Heading", "Folder/Note^blk")], ["Note"] * 4)
    def test_links_skip_code_and_embeds(self):
        vt = load("vault-health", "vault"); d = tempfile.mkdtemp(); p = os.path.join(d, "a.md")
        open(p, "w").write("See [[Real]] and `[[Inline]]` and ![[pic.png]]\n```\n[[Fenced]]\n```\n"); n = vt.Note(d, p)
        self.assertEqual([t for _, t, _ in n.links()], ["Real"])

class TestHealth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        hc = load("vault-health", "vault_health"); vt = sys.modules["vault"]
        cls.issues = hc.check(vt.load_vault(SV), ("type",), ("Daily", "Templates"), 180, D)
        cls.by = {}
        for note, line, kind, detail in cls.issues: cls.by.setdefault(kind, []).append((note, detail))
    def test_broken_links_exact(self):
        self.assertEqual(sorted((n, d.split(" ")[0]) for n, d in self.by["broken_link"]), [("10-Projects/Podcast launch.md", "[[Guest"), ("10-Projects/Website relaunch.md", "[[Launch")])
    def test_ambiguous_link(self):
        self.assertEqual(sorted(n for n, _ in self.by["ambiguous_link"]), ["10-Projects/Podcast launch.md", "Daily/2026-09-17.md"])   # [[Meeting notes]] and [[Budget draft]] each exist twice
    def test_duplicates(self):
        self.assertEqual(sorted(n for n, _ in self.by["duplicate_name"]), ["00-Inbox/Budget draft.md", "10-Projects/Meeting notes.md", "20-Areas/Finance/Budget draft.md", "20-Areas/Meeting notes.md"])
    def test_missing_property_and_empty(self):
        self.assertEqual(sorted(n for n, _ in self.by["missing_property"]), ["00-Inbox/Article - deep work summary.md", "00-Inbox/Budget draft.md", "00-Inbox/Idea - newsletter topic.md", "00-Inbox/Random thought.md", "30-Resources/Orphan idea.md"])
        self.assertEqual([n for n, _ in self.by["empty_note"]], ["00-Inbox/Random thought.md"])
    def test_stale_excludes_archive(self):
        self.assertEqual([n for n, _ in self.by["stale"]], ["30-Resources/Old reading list.md"])
    def test_orphans(self):
        o = {n for n, _ in self.by["orphan"]}
        self.assertIn("30-Resources/Orphan idea.md", o); self.assertIn("30-Resources/Old reading list.md", o)
        for linked in ("30-Resources/Acme Ltd.md", "30-Resources/Style guide.md", "30-Resources/Deep Work.md", "20-Areas/Health.md", "20-Areas/Career.md", "10-Projects/Website relaunch.md"): self.assertNotIn(linked, o)
        self.assertFalse(any(n.startswith(("Daily/", "Templates/")) for n in o))       # exempt folders
    def test_alias_resolves(self):
        hc = load("vault-health", "vault_health"); vt = sys.modules["vault"]; d = tempfile.mkdtemp()
        open(f"{d}/a.md", "w").write("---\naliases: [Alt Name]\n---\ntext"); open(f"{d}/b.md", "w").write("link [[Alt Name]]")
        self.assertFalse([i for i in hc.check(vt.load_vault(d), (), (), 999, D) if i[2] == "broken_link"])
    def test_readonly_cli(self):
        d, v = fresh(); before = tree(v); mt = {f: os.path.getmtime(os.path.join(v, f)) for f in before}
        r = run("vault-health", "vault_health.py", "--vault", v, "--require", "type", "--today", "2026-09-20", "--out", f"{d}/h.csv"); self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(tree(v), before); self.assertEqual({f: os.path.getmtime(os.path.join(v, f)) for f in before}, mt)
    def test_bad_path(self):
        self.assertEqual(run("vault-health", "vault_health.py", "--vault", "/no/such").returncode, 2)


if __name__ == "__main__":
    unittest.main()
