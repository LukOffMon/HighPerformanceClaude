"""End-to-end tests: vault, organizer, HTTP app with pairing, and the MCP bridge over stdio.

Run: python3 -m unittest discover -s apps/cekmecon/tests   (standard library only)
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TMP = tempfile.mkdtemp(prefix="cek-")
os.environ.update(CEKMECON_HOME=f"{TMP}/state", CEKMECON_VAULT=f"{TMP}/vault", CEKMECON_NO_WINDOW="1", CEKMECON_NO_AUTOSTART="1", CEKMECON_NO_AUTOCONNECT="1")
sys.path.insert(0, str(ROOT))

from cekmecon import paths  # noqa: E402
from cekmecon.organizer import Organizer, scan_project  # noqa: E402
from cekmecon.store import Vault  # noqa: E402


def req(method, port, path, body=None, headers=None):
    r = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method=method,
                               data=json.dumps(body).encode() if body is not None else None,
                               headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(r, timeout=10) as res:
            return res.status, res.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


class VaultTests(unittest.TestCase):
    def test_layout_search_links_and_safety(self):
        v = Vault(Path(TMP) / "v1", Path(TMP) / "i1.sqlite")
        self.assertTrue((v.root / "Profile.md").exists())
        a = v.new_note("Auth with Google", "We use [[Session cookies]] and #auth", "Knowledge")
        v.new_note("Session cookies", "httpOnly, SameSite=Lax", "Knowledge")
        hits = v.search("google auth")
        self.assertEqual(hits[0]["path"], a)
        self.assertIn("Knowledge/Auth with Google.md", v.backlinks("Knowledge/Session cookies.md"))
        g = v.graph()
        self.assertEqual(len(g["edges"]), 1)
        node = next(n for n in g["nodes"] if n["id"] == a)  # fields Neuronas draws with
        self.assertEqual(node["folder"], "Knowledge")
        self.assertGreater(node["mtime"], 0)
        self.assertGreater(node["size"], 0)
        self.assertIn("auth", node["tags"])
        d = v.daily("2026-01-02")
        self.assertEqual(d, "Inbox/Diario/2026-01-02.md")
        v.write(d, v.read(d) + "\nescrito a mano\n")
        self.assertEqual(v.daily("2026-01-02"), d)  # never overwrites an existing day
        self.assertIn("escrito a mano", v.read(d))
        with self.assertRaises(ValueError):
            v.daily("../../x")
        c = v.capture("llamar a Ana sobre [[Session cookies]]", "2026-01-02")
        body = v.read(c)
        self.assertIn("llamar a Ana", body)
        self.assertLess(body.index("llamar a Ana"), body.index("## Tareas"))  # lands under ## Notas
        self.assertNotIn("\n- \n", body)  # the empty placeholder bullet is replaced
        with self.assertRaises(ValueError):
            v.capture("   ")
        t = v.new_note("Plan", "- [ ] escribir tests\n- [x] hecho\n* [ ] revisar", "Inbox")
        open_tasks = [x for x in v.tasks() if x["path"] == t]
        self.assertEqual([x["text"] for x in open_tasks], ["escribir tests", "revisar"])
        first = open_tasks[0]
        self.assertTrue(v.toggle_task(t, first["line"], first["text"])["done"])
        self.assertIn("- [x] escribir tests", v.read(t))
        self.assertFalse(any(x["text"] == "escribir tests" for x in v.tasks()))
        self.assertEqual(next(n for n in v.graph()["nodes"] if n["id"] == t)["open"], 1)  # Neuronas' axon
        with self.assertRaises(ValueError):
            v.toggle_task(t, first["line"], "otra cosa")  # file changed under us
        with self.assertRaises(ValueError):
            v.write("../evil.md", "x")
        with self.assertRaises(ValueError):
            v.write("Inbox/x.sh", "x")

    def test_organizer_project_remember_context(self):
        v = Vault(Path(TMP) / "v2", Path(TMP) / "i2.sqlite")
        org = Organizer(v)
        proj = Path(TMP) / "my-app"
        proj.mkdir()
        (proj / "package.json").write_text(json.dumps({"scripts": {"test": "vitest", "dev": "next dev"}}))
        (proj / "README.md").write_text("# my-app\n\nA tiny shop for bamboo paper.\n")
        info = scan_project(proj)
        self.assertIn("Node.js", info["stack"])
        res = org.open_project(str(proj))
        self.assertEqual(res["project"], "my-app")
        self.assertTrue((v.root / "Projects/my-app/Map.md").exists())
        org.remember("lesson", "Use pnpm, not npm", "my-app")
        org.remember("lesson", "use pnpm,  not npm!", "my-app")  # duplicate
        self.assertEqual((v.root / "Projects/my-app/Lessons.md").read_text().count("pnpm"), 1)
        org.remember("task", "Add checkout tests", "my-app")
        v.new_note("Idea for my-app checkout", "my-app needs Stripe later", "Inbox")
        out = org.organize()
        self.assertTrue(any("Projects/my-app" in m for m in out["moved"]))
        ctx = org.context("my-app", "checkout", budget=600)
        self.assertLessEqual(ctx["tokens"], 650)
        self.assertIn("Add checkout tests", ctx["text"])
        self.assertIn("bamboo paper", ctx["text"])


class AppAndBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from cekmecon import server
        cls.server = server
        cls.thread = threading.Thread(target=server.serve, kwargs={"port": 47317, "window": False}, daemon=True)
        cls.thread.start()
        for _ in range(300):
            if paths.read_json(paths.running_file(), {}).get("port"):
                break
            time.sleep(0.1)
        cls.port = paths.read_json(paths.running_file(), {})["port"]
        page = urllib.request.urlopen(f"http://127.0.0.1:{cls.port}/").read().decode()
        cls.key = page.split('name="cekmecon-ui" content="')[1].split('"')[0]

    def ui(self, method, path, body=None):
        code, data = req(method, self.port, path, body, {"X-Cekmecon-UI": self.key})
        return code, json.loads(data)

    def test_security_guards(self):
        self.assertEqual(req("GET", self.port, "/api/state")[0], 401)  # no UI key
        self.assertEqual(req("GET", self.port, "/api/state", headers={"Host": "evil.com:80", "X-Cekmecon-UI": self.key})[0], 403)
        self.assertEqual(req("POST", self.port, "/api/pair", {}, {"Origin": "https://evil.example"})[0], 403)
        self.assertEqual(req("POST", self.port, "/api/claude/status", {})[0], 401)  # not paired

    def test_ui_crud(self):
        code, r = self.ui("POST", "/api/note/new", {"title": "Hola", "folder": "Inbox"})
        self.assertEqual(code, 200)
        code, n = self.ui("GET", "/api/note?path=" + urllib.request.quote(r["path"]))
        self.assertIn("# Hola", n["text"])
        code, st = self.ui("GET", "/api/state")
        self.assertTrue(any(t["path"] == r["path"] for t in st["tree"]))
        code, d = self.ui("POST", "/api/daily", {})
        self.assertEqual(code, 200)
        self.assertTrue(d["path"].startswith("Inbox/Diario/"))
        code, g = self.ui("GET", "/api/graph")
        self.assertTrue(any(n["id"] == d["path"] and n["kind"] == "daily" for n in g["nodes"]))
        code, c = self.ui("POST", "/api/capture", {"text": "idea rápida"})
        self.assertEqual(c["path"], d["path"])
        code, tk = self.ui("GET", "/api/tasks")
        self.assertEqual(code, 200)
        self.assertIsInstance(tk["tasks"], list)
        for asset in ("neurons.js", "webstore.js", "app.js"):
            self.assertEqual(req("GET", self.port, "/ui/" + asset)[0], 200)

    def test_mcp_bridge_pairs_once_then_is_automatic(self):
        env = {**os.environ, "PYTHONPATH": str(ROOT), "CEKMECON_PAIR_WAIT": "20"}
        token_file = Path(os.environ["CEKMECON_HOME"]) / "token.json"
        if token_file.exists():
            token_file.unlink()

        def approve():  # the user clicking "Permitir siempre" in the window
            for _ in range(100):
                code, st = self.ui("GET", "/api/state")
                if st["pending"]:
                    self.ui("POST", f"/api/pair/{st['pending'][0]['id']}/answer", {"allow": True, "always": True})
                    return
                time.sleep(0.1)

        def run_bridge(calls):
            msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
                    {"jsonrpc": "2.0", "method": "notifications/initialized"},
                    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}]
            msgs += [{"jsonrpc": "2.0", "id": 10 + i, "method": "tools/call", "params": {"name": n, "arguments": a}} for i, (n, a) in enumerate(calls)]
            p = subprocess.run([sys.executable, "-m", "cekmecon", "mcp"], input="\n".join(json.dumps(m) for m in msgs) + "\n",
                               capture_output=True, text=True, env=env, cwd=str(ROOT), timeout=60)
            return [json.loads(l) for l in p.stdout.splitlines() if l.strip()]

        t = threading.Thread(target=approve)
        t.start()
        out = run_bridge([("cekmecon_open_project", {"path": str(ROOT), "query": "vault"}),
                          ("cekmecon_remember", {"kind": "decision", "text": "Stdlib only", "project": "cekmecon"})])
        t.join()
        self.assertEqual(out[0]["result"]["serverInfo"]["name"], "cekmecon")
        self.assertEqual(len(out[1]["result"]["tools"]), 8)
        self.assertFalse(out[2]["result"]["isError"], out[2])
        self.assertIn("Project drawer", out[2]["result"]["content"][0]["text"])
        self.assertIn("Saved to", out[3]["result"]["content"][0]["text"])
        self.assertTrue(token_file.exists())
        # second session: no approval needed
        out2 = run_bridge([("cekmecon_search", {"query": "Stdlib"})])
        self.assertFalse(out2[2]["result"]["isError"], out2[2])
        self.assertIn("Decisions", out2[2]["result"]["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
