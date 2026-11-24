/* GeekMcON Web: the same window running entirely in the browser (GitHub Pages), no install.
   Notes live in this browser's IndexedDB; import a folder of .md files and export everything as a .zip
   that opens in the desktop app or Obsidian. Implements the subset of the local app's HTTP API the UI uses.
   Loaded on every page; only used when the page was not served by the desktop app. */
(function () {
  const FOLDERS = ["Inbox", "Projects", "Knowledge", "Archive"];
  const VERSION = "web";
  const notes = new Map();          // path -> {path, text, mtime}
  const extraFolders = new Set(FOLDERS);
  const events = [];
  let db = null, listener = null, ready = null;

  const now = () => Date.now() / 1000;
  const stamp = () => { const d = new Date(), p = n => String(n).padStart(2, "0"); return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`; };
  const today = () => stamp().slice(0, 10);
  const fold = s => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  const slug = t => (t || "Untitled").replace(/[\\/:*?"<>|#^[\]]+/g, " ").replace(/\s+/g, " ").trim().slice(0, 80) || "Untitled";

  /* ---------- storage ---------- */
  function openDB() {
    return new Promise(res => {
      if (!("indexedDB" in window)) return res(null);
      let rq;
      try { rq = indexedDB.open("cekmecon-web", 1); } catch { return res(null); }
      rq.onupgradeneeded = () => rq.result.createObjectStore("notes", { keyPath: "path" });
      rq.onsuccess = () => res(rq.result);
      rq.onerror = rq.onblocked = () => res(null);
    });
  }
  function tx(mode, fn) {
    if (!db) return Promise.resolve();
    return new Promise(res => { try { const t = db.transaction("notes", mode); fn(t.objectStore("notes")); t.oncomplete = t.onerror = t.onabort = () => res(); } catch { res(); } });
  }
  const persist = n => tx("readwrite", s => s.put(n));
  const unpersist = p => tx("readwrite", s => s.delete(p));
  function loadAll() {
    if (!db) return Promise.resolve([]);
    return new Promise(res => { try { const r = db.transaction("notes").objectStore("notes").getAll(); r.onsuccess = () => res(r.result || []); r.onerror = () => res([]); } catch { res([]); } });
  }

  /* ---------- parsing ---------- */
  function parse(path, text) {
    const meta = {}; let body = text;
    const fm = text.match(/^---\n([\s\S]*?)\n---\n?/);
    if (fm) {
      body = text.slice(fm[0].length);
      fm[1].split("\n").forEach(l => { const m = l.match(/^([\w-]+):\s*(.*)$/); if (m) meta[m[1]] = m[2].replace(/^["']|["']$/g, ""); });
    }
    const h = body.match(/^# (.+)$/m);
    const title = meta.title || (h ? h[1].trim() : path.split("/").pop().replace(/\.md$/, ""));
    const parts = path.split("/");
    const project = meta.project || (parts[0] === "Projects" && parts.length > 2 ? parts[1] : "");
    const tags = [...new Set((body.match(/(?:^|\s)#([A-Za-z][\w/-]{1,40})/g) || []).map(t => t.trim().slice(1)))];
    const links = [...new Set([...body.matchAll(/\[\[([^\]|#]+)/g)].map(m => m[1].trim()))];
    return { title, project, kind: meta.kind || "", tags, links, body };
  }
  const info = new Map();
  function index(n) { info.set(n.path, parse(n.path, n.text)); }

  function safe(rel) {
    rel = String(rel || "").replace(/\\/g, "/").replace(/^\/+/, "");
    if (!rel || rel.split("/").some(p => p === ".." || p === "." || p.startsWith("."))) throw new Error("ruta no válida");
    return rel;
  }
  async function put(path, text, mtime) {
    path = safe(path);
    if (!path.endsWith(".md")) throw new Error("solo notas .md");
    const n = { path, text, mtime: mtime || now() };
    notes.set(path, n); index(n);
    path.split("/").slice(0, -1).forEach((_, i, a) => extraFolders.add(a.slice(0, i + 1).join("/")));
    await persist(n);
    return path;
  }
  function emit(kind, text, mood) {
    const ev = { id: Math.random().toString(16).slice(2, 10), t: now(), kind, text, mood: mood || "idle" };
    events.push(ev); if (events.length > 200) events.shift();
    if (listener) listener(ev);
  }

  /* ---------- queries ---------- */
  function tree() {
    return [...notes.values()].sort((a, b) => a.path.localeCompare(b.path)).map(n => {
      const i = info.get(n.path);
      return { path: n.path, title: i.title, mtime: n.mtime, tags: i.tags.join(" "), project: i.project, kind: i.kind, size: n.text.length };
    });
  }
  function byName() {
    const m = new Map();
    for (const [p, i] of info) { m.set(i.title.toLowerCase(), p); m.set(p.split("/").pop().replace(/\.md$/, "").toLowerCase(), p); }
    return m;
  }
  function backlinks(rel) {
    const i = info.get(rel); if (!i) return [];
    const names = new Set([i.title.toLowerCase(), rel.split("/").pop().replace(/\.md$/, "").toLowerCase()]);
    return [...info].filter(([p, x]) => p !== rel && x.links.some(l => names.has(l.toLowerCase()))).map(([p]) => p).sort();
  }
  function graph() {
    const names = byName(), edges = new Set(), open = {};
    tasks(false).forEach(t => { open[t.path] = (open[t.path] || 0) + 1; });
    for (const [p, i] of info) for (const l of i.links) { const t = names.get(l.toLowerCase()); if (t && t !== p) edges.add(p + "\n" + t); }
    return {
      nodes: tree().map(n => ({ id: n.path, title: n.title, project: n.project, kind: n.kind, folder: n.path.includes("/") ? n.path.split("/")[0] : "", mtime: Math.round(n.mtime), size: n.size, tags: n.tags, open: open[n.path] || 0 })),
      edges: [...edges].sort().map(e => { const [source, target] = e.split("\n"); return { source, target }; }),
    };
  }
  function search(q, limit) {
    const terms = fold(q).match(/[\p{L}\p{N}_-]{2,}/gu) || [];
    if (!terms.length) return [];
    const out = [];
    for (const [p, i] of info) {
      const t = fold(i.title), b = fold(i.body);
      let score = 0, first = -1;
      for (const term of terms) {
        let c = 0, k = b.indexOf(term);
        if (k >= 0 && (first < 0 || k < first)) first = k;
        while (k >= 0 && c < 50) { c++; k = b.indexOf(term, k + term.length); }
        if (t.includes(term)) score += 8;
        if (i.tags.some(x => fold(x).includes(term))) score += 4;
        score += c ? 1 + Math.log(c) : 0;
      }
      if (!score) continue;
      let snip = "";
      if (first >= 0) {
        const s = Math.max(0, first - 50), raw = i.body.slice(s, s + 150).replace(/\s+/g, " ");
        snip = (s ? "… " : "") + raw;
        for (const term of terms) snip = snip.replace(new RegExp("(" + term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "i"), "«$1»");
      }
      out.push({ path: p, title: i.title, snippet: snip, project: i.project, score });
    }
    return out.sort((a, b) => b.score - a.score).slice(0, limit || 30);
  }
  function stats() {
    const g = graph(), all = [...notes.values()];
    return { notes: all.length, bytes: all.reduce((a, n) => a + n.text.length, 0), links: g.edges.length,
      projects: [...new Set([...info.values()].map(i => i.project).filter(Boolean))].sort(), fts: false, vault: "Este navegador" };
  }

  /* ---------- writing ---------- */
  async function newNote(title, body, folder, meta) {
    folder = safe(folder || "Inbox");
    let base = `${folder}/${slug(title)}`, p = base + ".md", i = 2;
    while (notes.has(p)) p = `${base} ${i++}.md`;
    const fm = Object.entries(Object.assign({ created: stamp() }, meta || {})).map(([k, v]) => `${k}: ${v}`).join("\n");
    return put(p, `---\n${fm}\n---\n# ${title}\n\n${(body || "").trim()}\n`);
  }
  async function move(rel, dest) {
    rel = safe(rel); dest = safe(dest);
    const n = notes.get(rel); if (!n) throw new Error("no existe " + rel);
    const name = rel.split("/").pop();
    let p = `${dest}/${name}`, i = 2;
    while (notes.has(p) && p !== rel) p = `${dest}/${name.replace(/\.md$/, "")} ${i++}.md`;
    if (p === rel) return rel;
    notes.delete(rel); info.delete(rel); await unpersist(rel);
    return put(p, n.text, n.mtime);
  }
  async function organize() {
    const moved = [];
    for (const [p, i] of [...info]) {
      if (!p.startsWith("Inbox/") || p.startsWith("Inbox/Diario/")) continue;
      if (i.project) moved.push(await move(p, `Projects/${slug(i.project)}`));
      else if (i.tags.length && /^(conocimiento|knowledge|ref|referencia)$/i.test(i.tags[0])) moved.push(await move(p, "Knowledge"));
    }
    return { moved, linked: 0, deduped: 0 };
  }
  async function daily(day) {
    day = day || today();
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) throw new Error("día no válido");
    const p = `Inbox/Diario/${day}.md`;
    if (!notes.has(p)) await put(p, `---\nkind: daily\ncreated: ${stamp()}\n---\n# ${day}\n\n## Notas\n\n- \n\n## Tareas\n\n- [ ] \n`);
    return p;
  }

  async function capture(text) {
    text = String(text || "").split(/\s+/).join(" ").trim();
    if (!text) throw new Error("nota vacía");
    const p = await daily(), lines = notes.get(p).text.split("\n");
    const d = new Date(), entry = `- ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")} ${text.slice(0, 2000)}`;
    let i = lines.findIndex(l => l.trim().toLowerCase() === "## notas");
    if (i < 0) lines.push(entry);
    else {
      i++; while (i < lines.length && !lines[i].startsWith("## ")) i++;
      while (i > 0 && (lines[i - 1].trim() === "" || lines[i - 1].trim() === "-")) { if (lines[i - 1].trim() === "-") lines.splice(i - 1, 1); i--; }
      lines.splice(i, 0, entry);
    }
    await put(p, lines.join("\n").replace(/\n*$/, "\n"));
    return p;
  }
  const TASK = /^(\s*[-*] \[)( |x|X)(\] )(.*)$/;
  function tasks(all) {
    const out = [];
    for (const n of [...notes.values()].sort((a, b) => b.mtime - a.mtime)) {
      if (n.path.startsWith("Archive/")) continue;
      const i = info.get(n.path);
      n.text.split("\n").forEach((l, k) => { const m = l.match(TASK); if (m && m[4].trim() && (all || m[2] === " ")) out.push({ path: n.path, title: i.title, project: i.project, line: k + 1, text: m[4].trim(), done: m[2] !== " " }); });
    }
    return out.sort((a, b) => a.done - b.done).slice(0, 300);
  }
  async function toggleTask(rel, line, expect) {
    const n = notes.get(safe(rel)); if (!n) throw new Error("no existe " + rel);
    const lines = n.text.split("\n"), m = (lines[line - 1] || "").match(TASK);
    if (!m || (expect && m[4].trim() !== String(expect).trim())) throw new Error("esa tarea cambió; recarga");
    const done = m[2] === " ";
    lines[line - 1] = m[1] + (done ? "x" : " ") + m[3] + m[4];
    await put(n.path, lines.join("\n"));
    return { path: n.path, line, done };
  }

  /* ---------- first run: a small sample drawer so the window and Neuronas are not empty ---------- */
  async function seed() {
    const DAY = 86400, t0 = now();
    const S = [
      ["Welcome.md", 0, "# Bienvenida\n\nEsta es la **versión web** de GeekMcON: corre en tu navegador, sin instalar nada.\n\n- Tus notas se guardan en *este* navegador (no salen a ningún servidor).\n- **Exportar** baja un .zip con todo en Markdown; ábrelo con la app de escritorio u Obsidian.\n- **Importar** sube una carpeta de notas .md.\n- Abre **🧠 Neuronas** para ver tu memoria como una red viva.\n\nEmpieza por [[Perfil]] o por el proyecto [[demo]]. #inicio"],
      ["Profile.md", 2, "---\ntitle: Perfil\n---\n# Perfil\n\nCómo me gusta trabajar con Claude:\n\n- Respuestas cortas, en español.\n- Probar antes de decir que algo está listo.\n\nVer [[Bienvenida]]."],
      ["Projects/demo/README.md", 40, "---\nproject: demo\nkind: brief\ntitle: demo\n---\n# demo\n\nApp de ejemplo para ver cómo GeekMcON ordena un proyecto.\n\n- Decisiones: [[Decisions]]\n- Lecciones: [[Lessons]]\n- Tareas: [[Tasks]]\n- Arquitectura: [[Arquitectura]]"],
      ["Projects/demo/Decisions.md", 30, "---\nproject: demo\nkind: decisions\n---\n# Decisions\n\n- 2026-10-02 · SQLite con FTS5 para buscar, sin servidor aparte. Ver [[SQLite FTS5]].\n- 2026-10-20 · Deploy en contenedor único. Ver [[Despliegue]]."],
      ["Projects/demo/Lessons.md", 12, "---\nproject: demo\nkind: lessons\n---\n# Lessons\n\n- Usa pnpm, no npm, en demo.\n- Los tests e2e necesitan `PORT=0`. Ver [[Tests]]."],
      ["Projects/demo/Tasks.md", 3, "---\nproject: demo\nkind: tasks\n---\n# Tasks\n\n- [x] Login con Google\n- [ ] Pagos con [[Stripe]]\n- [ ] Revisar [[Accesibilidad]]"],
      ["Projects/demo/Arquitectura.md", 35, "---\nproject: demo\n---\n# Arquitectura\n\nFrontend estático + API pequeña. Datos en SQLite. Ver [[Decisions]] y [[Despliegue]]."],
      ["Projects/demo/Despliegue.md", 18, "---\nproject: demo\n---\n# Despliegue\n\nUn contenedor, variables en el entorno, healthcheck en `/ping`. Relacionado: [[Arquitectura]]."],
      ["Projects/demo/Tests.md", 9, "---\nproject: demo\n---\n# Tests\n\nUnitarios rápidos y un e2e por flujo crítico. Ver [[Lessons]]."],
      ["Projects/demo/Stripe.md", 5, "---\nproject: demo\n---\n# Stripe\n\nCheckout alojado, webhooks idempotentes. Ver [[Tasks]]."],
      ["Knowledge/SQLite FTS5.md", 90, "# SQLite FTS5\n\nBúsqueda de texto completo con ranking BM25 dentro de SQLite. `remove_diacritics 2` ignora acentos. #knowledge"],
      ["Knowledge/Accesibilidad.md", 60, "# Accesibilidad\n\nFoco visible, contraste AA, `prefers-reduced-motion`. Ver [[Diseño]]. #knowledge"],
      ["Knowledge/Diseño.md", 75, "# Diseño\n\nUna idea por pantalla. Tokens de color con modo oscuro. Ver [[Accesibilidad]]. #knowledge"],
      ["Inbox/Idea suelta.md", 1, "# Idea suelta\n\nVista de calendario para el [[demo]]. #idea"],
    ];
    for (const [p, age, text] of S) await put(p, text, t0 - age * DAY - Math.random() * DAY);
  }

  /* ---------- zip export (store, no compression) ---------- */
  const CRC = (() => { const t = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
  const crc32 = b => { let c = 0xFFFFFFFF; for (let i = 0; i < b.length; i++) c = CRC[(c ^ b[i]) & 255] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; };
  function zip(files) {
    const enc = new TextEncoder(), parts = [], central = []; let off = 0;
    const d = new Date(), dt = ((d.getHours() << 11) | (d.getMinutes() << 5) | (d.getSeconds() >> 1)), dd = (((d.getFullYear() - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate());
    for (const [name, text] of files) {
      const nb = enc.encode(name), data = enc.encode(text), crc = crc32(data);
      const h = new DataView(new ArrayBuffer(30));
      h.setUint32(0, 0x04034b50, true); h.setUint16(4, 20, true); h.setUint16(6, 0x0800, true); h.setUint16(8, 0, true);
      h.setUint16(10, dt, true); h.setUint16(12, dd, true); h.setUint32(14, crc, true); h.setUint32(18, data.length, true); h.setUint32(22, data.length, true);
      h.setUint16(26, nb.length, true); h.setUint16(28, 0, true);
      parts.push(h, nb, data);
      const c = new DataView(new ArrayBuffer(46));
      c.setUint32(0, 0x02014b50, true); c.setUint16(4, 20, true); c.setUint16(6, 20, true); c.setUint16(8, 0x0800, true); c.setUint16(10, 0, true);
      c.setUint16(12, dt, true); c.setUint16(14, dd, true); c.setUint32(16, crc, true); c.setUint32(20, data.length, true); c.setUint32(24, data.length, true);
      c.setUint16(28, nb.length, true); c.setUint32(42, off, true);
      central.push(c, nb);
      off += 30 + nb.length + data.length;
    }
    const size = central.reduce((a, x) => a + x.byteLength, 0), e = new DataView(new ArrayBuffer(22));
    e.setUint32(0, 0x06054b50, true); e.setUint16(8, files.length, true); e.setUint16(10, files.length, true); e.setUint32(12, size, true); e.setUint32(16, off, true);
    return new Blob([...parts, ...central, e], { type: "application/zip" });
  }

  /* ---------- the API the window calls ---------- */
  async function api(path, body) {
    await (ready ||= init());
    const u = new URL(path, "http://x"), q = k => u.searchParams.get(k) || "";
    const p = u.pathname;
    if (body === undefined) {
      if (p === "/api/state") return { tree: tree(), folders: [...extraFolders].sort(), stats: stats(), pending: [], clients: [], events: events.slice(-40), version: VERSION, web: true };
      if (p === "/api/note") { const rel = safe(q("path")), n = notes.get(rel); if (!n) throw new Error("no existe " + rel); return { path: rel, text: n.text, backlinks: backlinks(rel) }; }
      if (p === "/api/resolve") return { path: byName().get(q("title").toLowerCase()) || "" };
      if (p === "/api/search") return { results: search(q("q"), 30) };
      if (p === "/api/graph") return graph();
      if (p === "/api/tasks") return { tasks: tasks(q("all") === "1") };
      throw new Error("not found");
    }
    if (p === "/api/note") { const r = await put(body.path, body.content); emit("save", "Guardado " + r, "write"); return { path: r }; }
    if (p === "/api/note/new") { const r = await newNote(body.title || "Untitled", body.body, body.folder); emit("save", "Nota nueva " + r, "celebrate"); return { path: r }; }
    if (p === "/api/note/move") return { path: await move(body.path, body.folder) };
    if (p === "/api/note/archive") { const r = await move(body.path, "Archive"); emit("save", "Archivada " + r.split("/").pop(), "idle"); return { path: r }; }
    if (p === "/api/daily") { const r = await daily(body.day); emit("save", "Nota del día " + r.split("/").pop().replace(/\.md$/, ""), "write"); return { path: r }; }
    if (p === "/api/capture") { const r = await capture(body.text); emit("save", "Capturado en la nota de hoy", "write"); return { path: r }; }
    if (p === "/api/task/toggle") { const r = await toggleTask(body.path, +body.line, body.text); emit("save", (r.done ? "Tarea hecha ✓ " : "Tarea reabierta ") + r.path.split("/").pop().replace(/\.md$/, ""), r.done ? "celebrate" : "idle"); return r; }
    if (p === "/api/organize") { const r = await organize(); emit("organize", `Ordené el Inbox: ${r.moved.length} movidas`, "celebrate"); return r; }
    if (p === "/api/clients/revoke") return { ok: true };
    throw new Error("not found");
  }

  async function importFiles(fileList) {
    let n = 0;
    for (const f of fileList) {
      if (!/\.(md|markdown)$/i.test(f.name)) continue;
      let rel = (f.webkitRelativePath || f.name).replace(/\\/g, "/");
      const parts = rel.split("/"); if (parts.length > 1) parts.shift(); // drop the picked folder's own name
      rel = parts.join("/").replace(/\.markdown$/i, ".md");
      if (parts.some(x => x.startsWith("."))) continue;
      try { await put(rel.includes("/") ? rel : "Inbox/" + rel, await f.text(), f.lastModified ? f.lastModified / 1000 : now()); n++; } catch { /* skip bad paths */ }
    }
    emit("index", `Importé ${n} nota${n === 1 ? "" : "s"}`, "celebrate");
    return n;
  }
  function exportZip() {
    const files = [...notes.values()].sort((a, b) => a.path.localeCompare(b.path)).map(n => ["Cekmecon/" + n.path, n.text]);
    const url = URL.createObjectURL(zip(files)), a = document.createElement("a");
    a.href = url; a.download = `cekmecon-notas-${today()}.zip`; document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
    emit("save", `Exporté ${files.length} notas en un .zip`, "celebrate");
    return files.length;
  }
  async function reset() {
    for (const p of [...notes.keys()]) await unpersist(p);
    notes.clear(); info.clear(); await seed();
  }

  const init = async () => {
    db = await openDB();
    const all = await loadAll();
    all.forEach(n => { notes.set(n.path, n); index(n); n.path.split("/").slice(0, -1).forEach((_, i, a) => extraFolders.add(a.slice(0, i + 1).join("/"))); });
    if (!all.length) { await seed(); emit("hello", "¡Hola! Esta es la versión web. Te dejé un cajón de ejemplo para que juegues.", "wave"); }
  };

  window.CekmeconWeb = { api, importFiles, exportZip, reset, onEvent(fn) { listener = fn; }, persistent: () => !!db, zip };
})();
