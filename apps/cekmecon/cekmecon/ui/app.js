/* Çekmecón window. Vanilla JS, no build step. */
(() => {
  const KEY = document.querySelector('meta[name="cekmecon-ui"]').content;
  const $ = s => document.querySelector(s);
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const S = { tree: [], folders: [], stats: {}, current: null, text: "", dirty: false, mode: localGet("mode") || "read", pending: [], shownPair: null };

  function localGet(k) { try { return localStorage.getItem("cek." + k); } catch { return null; } }
  function localSet(k, v) { try { localStorage.setItem("cek." + k, v); } catch { } }
  async function api(path, body) {
    const r = await fetch(path, body === undefined ? { headers: { "X-Cekmecon-UI": KEY } }
      : { method: "POST", headers: { "X-Cekmecon-UI": KEY, "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || r.status);
    return j;
  }
  function toast(t) { const el = $("#toast"); el.textContent = t; el.classList.remove("hidden"); clearTimeout(toast.t); toast.t = setTimeout(() => el.classList.add("hidden"), 2400); }

  /* ---------- assistant ---------- */
  const bubble = $("#bubble"), bubbleText = $("#bubbleText");
  const buddy = Rollito.mount($("#buddyMount"), { size: 84 });
  let quietTimer;
  function say(text, mood, ms) {
    bubbleText.textContent = text;
    bubble.classList.remove("quiet");
    buddy.mood(mood || "idle", ms);
    clearTimeout(quietTimer);
    quietTimer = setTimeout(() => bubble.classList.add("quiet"), 7000);
  }
  $("#buddy").addEventListener("click", () => {
    const tips = ["Ctrl+K busca en todo tu cajón.", "Escribe [[Título]] para enlazar notas.", "«Organizar» manda el Inbox al cajón correcto.",
      "Claude guarda decisiones y lecciones aquí, así no relee todo.", "Tus notas son Markdown normal: también se abren en Obsidian."];
    say(tips[Math.floor(Math.random() * tips.length)], "wave");
  });

  /* ---------- state ---------- */
  async function load() {
    const st = await api("/api/state");
    Object.assign(S, { tree: st.tree, folders: st.folders, stats: st.stats, pending: st.pending });
    $("#clientCount").textContent = st.clients.length;
    S.clients = st.clients;
    renderTree(); renderStats();
    if (!S.current) renderHome();
    $("#activity").innerHTML = "";
    st.events.forEach(addEvent);
    if (st.pending.length) showPair(st.pending[0]);
  }
  function renderStats() {
    const s = S.stats;
    $("#stats").innerHTML = `${s.notes} notas · ${s.links} enlaces · ${s.projects.length} proyectos<br><span title="${esc(s.vault)}">📁 ${esc(s.vault)}</span>`;
  }

  /* ---------- tree ---------- */
  function renderTree() {
    const root = { dirs: {}, notes: [] };
    for (const f of S.folders) { let n = root; for (const part of f.split("/")) n = n.dirs[part] ||= { dirs: {}, notes: [] }; }
    for (const note of S.tree) {
      const parts = note.path.split("/"); parts.pop();
      let n = root; for (const p of parts) n = n.dirs[p] ||= { dirs: {}, notes: [] };
      n.notes.push(note);
    }
    const open = new Set(JSON.parse(localGet("open") || '["Inbox","Projects"]'));
    const icon = { Inbox: "📥", Projects: "🗂", Knowledge: "📚", Archive: "🗄" };
    const count = n => n.notes.length + Object.values(n.dirs).reduce((a, d) => a + count(d), 0);
    const html = (n, prefix) => {
      let out = "";
      const order = ["Inbox", "Projects", "Knowledge", "Archive"];
      const names = Object.keys(n.dirs).sort((a, b) => ((order.indexOf(a) + 1) || 99) - ((order.indexOf(b) + 1) || 99) || a.localeCompare(b));
      for (const name of names) {
        const path = prefix ? prefix + "/" + name : name;
        out += `<details class="folder" data-path="${esc(path)}" ${open.has(path) ? "open" : ""}><summary>${icon[name] || (prefix === "Projects" ? "🧻" : "📁")} ${esc(name)}<span class="count">${count(n.dirs[name])}</span></summary>${html(n.dirs[name], path)}</details>`;
      }
      for (const note of n.notes.sort((a, b) => a.title.localeCompare(b.title)))
        out += `<button class="note ${note.kind === "map" ? "auto" : ""} ${S.current === note.path ? "on" : ""}" data-path="${esc(note.path)}" title="${esc(note.path)}">${esc(note.title)}</button>`;
      return out;
    };
    $("#tree").innerHTML = html(root, "");
    $("#tree").querySelectorAll("details").forEach(d => d.addEventListener("toggle", () => {
      d.open ? open.add(d.dataset.path) : open.delete(d.dataset.path); localSet("open", JSON.stringify([...open]));
    }));
  }
  $("#tree").addEventListener("click", e => { const b = e.target.closest(".note"); if (b) openNote(b.dataset.path); });

  /* ---------- home ---------- */
  function renderHome() {
    $("#editor").classList.add("hidden"); $("#home").classList.remove("hidden");
    const s = S.stats, proj = s.projects;
    $("#home").innerHTML = `
      <div class="hero"><div id="heroBuddy"></div><div><h1>Tu cajón está listo</h1>
      <p>Claude guarda aquí lo que aprende de tus proyectos y te devuelve solo lo necesario. Menos tokens, cero releer.</p></div></div>
      <div class="cards">
        <div class="card"><b>${s.notes}</b><span>notas</span></div><div class="card"><b>${proj.length}</b><span>cajones de proyecto</span></div>
        <div class="card"><b>${s.links}</b><span>enlaces</span></div><div class="card"><b>${S.clients ? S.clients.length : 0}</b><span>conexiones de Claude</span></div></div>
      <h3>Proyectos</h3>
      <div class="projects">${proj.map(p => `<button class="proj" data-path="Projects/${esc(p)}/README.md"><b>🧻 ${esc(p)}</b><small>brief · mapa · decisiones · lecciones</small></button>`).join("") || '<p class="muted">Aún no hay proyectos. Se crean solos la primera vez que Claude trabaja en uno.</p>'}</div>
      <h3>Conectar con Claude</h3>
      <ol class="steps"><li>En una terminal: <code>cekmecon connect</code> (solo una vez).</li>
      <li>Abre Claude Code en tu proyecto, en esta computadora, y pídele cualquier cosa.</li>
      <li>Aparecerá un aviso aquí: pulsa <b>Permitir siempre</b>. Desde entonces Claude entra solo.</li></ol>`;
    Rollito.mount($("#heroBuddy"), { size: 92, sleepAfter: 0 }).mood("wave", 0);
    $("#home").querySelectorAll(".proj").forEach(b => b.onclick = () => openNote(b.dataset.path));
  }

  /* ---------- editor ---------- */
  async function openNote(path) {
    if (S.dirty) await save();
    try {
      const n = await api("/api/note?path=" + encodeURIComponent(path));
      S.current = path; S.text = n.text; S.dirty = false;
      const open = new Set(JSON.parse(localGet("open") || '["Inbox","Projects"]'));
      path.split("/").slice(0, -1).forEach((_, i, a) => open.add(a.slice(0, i + 1).join("/")));
      localSet("open", JSON.stringify([...open]));
      $("#home").classList.add("hidden"); $("#editor").classList.remove("hidden");
      $("#src").value = n.text;
      const parts = path.split("/");
      $("#crumbs").innerHTML = parts.slice(0, -1).map(esc).join(" / ") + (parts.length > 1 ? " / " : "") + `<b>${esc(parts.at(-1))}</b>`;
      $("#saveState").textContent = "";
      setMode(S.mode); renderPreview();
      $("#backlinks").innerHTML = n.backlinks.length ? n.backlinks.map(b => `<a data-path="${esc(b)}">← ${esc(b.split("/").pop().replace(/\.md$/, ""))}</a>`).join("") : '<span class="muted">Nadie enlaza aquí todavía.</span>';
      renderTree();
    } catch (e) { toast("No se pudo abrir: " + e.message); }
  }
  function setMode(m) {
    S.mode = m; localSet("mode", m);
    $("#edBody").className = "ed-body mode-" + m;
    document.querySelectorAll(".seg button").forEach(b => b.classList.toggle("on", b.dataset.mode === m));
    if (m !== "read") $("#src").focus();
  }
  document.querySelectorAll(".seg button").forEach(b => b.onclick = () => setMode(b.dataset.mode));
  let saveTimer;
  $("#src").addEventListener("input", () => {
    S.text = $("#src").value; S.dirty = true; $("#saveState").textContent = "editando…";
    renderPreview(); clearTimeout(saveTimer); saveTimer = setTimeout(save, 900);
  });
  async function save() {
    if (!S.dirty || !S.current) return;
    S.dirty = false;
    try { await api("/api/note", { path: S.current, content: S.text }); $("#saveState").textContent = "guardado ✓"; }
    catch (e) { S.dirty = true; $("#saveState").textContent = "error al guardar"; toast(e.message); }
  }
  $("#archiveBtn").onclick = async () => {
    if (!S.current || !confirm("¿Archivar esta nota? (se mueve a Archive/, no se borra)")) return;
    await api("/api/note/archive", { path: S.current }); S.current = null; await load();
  };

  /* ---------- markdown ---------- */
  const titles = () => new Map(S.tree.flatMap(n => [[n.title.toLowerCase(), n.path], [n.path.split("/").pop().replace(/\.md$/, "").toLowerCase(), n.path]]));
  function inline(s, map) {
    s = esc(s);
    s = s.replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]/g, (_, t, alias) => {
        const p = map.get(t.trim().toLowerCase());
        return `<a class="wiki ${p ? "" : "missing"}" data-path="${esc(p || "")}" data-title="${esc(t.trim())}">${esc(alias || t)}</a>`;
      })
      .replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>").replace(/(^|[^*])\*([^*\s][^*]*)\*/g, "$1<i>$2</i>")
      .replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
      .replace(/(^|\s)#([A-Za-z][\w/-]{1,40})/g, '$1<span class="tag">#$2</span>');
    return s;
  }
  function md(text) {
    const map = titles();
    let out = "", list = null, code = null, para = [];
    const flush = () => { if (para.length) { out += `<p>${inline(para.join(" "), map)}</p>`; para = []; } };
    const close = () => { if (list) { out += `</${list}>`; list = null; } };
    let lines = text.split("\n");
    const fm = text.match(/^---\n([\s\S]*?)\n---\n?/);
    if (fm) { out += `<div class="front">${esc(fm[1]).replace(/\n/g, " · ")}</div>`; lines = text.slice(fm[0].length).split("\n"); }
    const heads = [];
    for (const line of lines) {
      if (code !== null) { if (line.startsWith("```")) { out += `<pre><code>${esc(code)}</code></pre>`; code = null; } else code += line + "\n"; continue; }
      if (line.startsWith("```")) { flush(); close(); code = ""; continue; }
      let m;
      if ((m = line.match(/^(#{1,4}) (.+)/))) { flush(); close(); const id = "h" + heads.length; heads.push([m[1].length, m[2], id]); out += `<h${m[1].length} id="${id}">${inline(m[2], map)}</h${m[1].length}>`; continue; }
      if ((m = line.match(/^\s*[-*] \[( |x)\] (.*)/i))) { flush(); if (list !== "ul") { close(); out += "<ul>"; list = "ul"; } out += `<li class="task"><input type="checkbox" disabled ${m[1] !== " " ? "checked" : ""}>${inline(m[2], map)}</li>`; continue; }
      if ((m = line.match(/^\s*[-*] (.*)/))) { flush(); if (list !== "ul") { close(); out += "<ul>"; list = "ul"; } out += `<li>${inline(m[1], map)}</li>`; continue; }
      if ((m = line.match(/^\s*\d+\. (.*)/))) { flush(); if (list !== "ol") { close(); out += "<ol>"; list = "ol"; } out += `<li>${inline(m[1], map)}</li>`; continue; }
      if ((m = line.match(/^> ?(.*)/))) { flush(); close(); out += `<blockquote>${inline(m[1], map)}</blockquote>`; continue; }
      if (!line.trim()) { flush(); close(); continue; }
      para.push(line);
    }
    flush(); close();
    if (code !== null) out += `<pre><code>${esc(code)}</code></pre>`;
    return { html: out, heads };
  }
  function renderPreview() {
    const r = md(S.text);
    $("#preview").innerHTML = r.html;
    $("#outline").innerHTML = r.heads.length ? r.heads.map(([l, t, id]) => `<a class="h${l}" data-anchor="${id}">${esc(t)}</a>`).join("") : '<span class="muted">—</span>';
  }
  document.addEventListener("click", async e => {
    const a = e.target.closest("a.wiki, .list a[data-path]");
    if (a) {
      e.preventDefault();
      if (a.dataset.path) return openNote(a.dataset.path);
      if (a.dataset.title && confirm(`Crear la nota «${a.dataset.title}»?`)) {
        const folder = S.current ? S.current.split("/").slice(0, -1).join("/") || "Inbox" : "Inbox";
        const r = await api("/api/note/new", { title: a.dataset.title, folder }); await load(); openNote(r.path);
      }
    }
    const o = e.target.closest("[data-anchor]");
    if (o) document.getElementById(o.dataset.anchor)?.scrollIntoView({ behavior: "smooth" });
    if (e.target.closest("[data-close]")) e.target.closest(".overlay").classList.add("hidden");
  });

  /* ---------- actions ---------- */
  $("#newBtn").onclick = async () => {
    const title = prompt("Título de la nota:"); if (!title) return;
    const r = await api("/api/note/new", { title, folder: "Inbox" }); await load(); await openNote(r.path); setMode("edit");
  };
  $("#organizeBtn").onclick = async () => {
    say("Ordenando cajones…", "work", 0);
    try { const r = await api("/api/organize", {}); await load(); say(`Listo: ${r.moved.length} movidas, ${r.linked} enlazadas, ${r.deduped} duplicados fuera.`, "celebrate"); }
    catch (e) { say("Uy: " + e.message, "alert"); }
  };
  $("#reloadBtn").onclick = load;
  $("#clientsBtn").onclick = () => {
    $("#clientList").innerHTML = (S.clients || []).map(c => `<div class="client"><div><b>${esc(c.name)}</b><br><small class="muted">${esc(c.host)} · desde ${esc(c.created)}${c.last_seen ? " · visto " + esc(c.last_seen) : ""}</small></div><button data-revoke="${esc(c.id)}">Revocar</button></div>`).join("") || '<p class="muted">Ninguna conexión todavía.</p>';
    $("#clients").classList.remove("hidden");
  };
  $("#clientList").addEventListener("click", async e => {
    const b = e.target.closest("[data-revoke]"); if (!b) return;
    await api("/api/clients/revoke", { id: b.dataset.revoke }); await load(); $("#clientsBtn").onclick();
  });

  /* ---------- palette ---------- */
  let hits = [], sel = 0, searchTimer;
  function openPalette() { $("#palette").classList.remove("hidden"); $("#palInput").value = ""; $("#palInput").focus(); renderHits(S.tree.slice(-8).reverse().map(n => ({ ...n, snippet: n.path }))); }
  function renderHits(list) {
    hits = list; sel = 0;
    $("#palResults").innerHTML = list.map((h, i) => `<button class="hit ${i ? "" : "on"}" data-i="${i}"><b>${esc(h.title)}</b><small>${esc(h.snippet || "").replace(/«/g, "<em>").replace(/»/g, "</em>")}</small></button>`).join("") || '<div class="hit muted">Sin resultados</div>';
  }
  $("#searchBtn").onclick = openPalette;
  $("#palInput").addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(async () => { const q = $("#palInput").value.trim(); if (q) renderHits((await api("/api/search?q=" + encodeURIComponent(q))).results); }, 120);
  });
  $("#palInput").addEventListener("keydown", e => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); sel = (sel + (e.key === "ArrowDown" ? 1 : -1) + hits.length) % Math.max(hits.length, 1); document.querySelectorAll(".hit").forEach((h, i) => h.classList.toggle("on", i === sel)); }
    if (e.key === "Enter" && hits[sel]) { $("#palette").classList.add("hidden"); openNote(hits[sel].path); }
  });
  $("#palResults").addEventListener("click", e => { const b = e.target.closest(".hit[data-i]"); if (b) { $("#palette").classList.add("hidden"); openNote(hits[+b.dataset.i].path); } });
  $("#palette").addEventListener("click", e => { if (e.target.id === "palette") $("#palette").classList.add("hidden"); });
  document.addEventListener("keydown", e => {
    const mod = e.ctrlKey || e.metaKey;
    if (mod && e.key.toLowerCase() === "k") { e.preventDefault(); openPalette(); }
    if (mod && e.key.toLowerCase() === "s") { e.preventDefault(); save(); }
    if (mod && e.key.toLowerCase() === "n") { e.preventDefault(); $("#newBtn").onclick(); }
    if (e.key === "Escape") document.querySelectorAll(".overlay:not(#pair)").forEach(o => o.classList.add("hidden"));
  });

  /* ---------- graph ---------- */
  $("#graphBtn").onclick = async () => { $("#graph").classList.remove("hidden"); drawGraph(await api("/api/graph")); };
  function drawGraph(g) {
    const cv = $("#graphCanvas"), dpr = devicePixelRatio || 1, W = cv.clientWidth, H = cv.clientHeight;
    cv.width = W * dpr; cv.height = H * dpr;
    const ctx = cv.getContext("2d"); ctx.scale(dpr, dpr);
    const css = getComputedStyle(document.documentElement);
    const col = { ink: css.getPropertyValue("--ink"), line: css.getPropertyValue("--line"), acc: css.getPropertyValue("--accent"), muted: css.getPropertyValue("--muted") };
    const projects = [...new Set(g.nodes.map(n => n.project).filter(Boolean))];
    const hue = p => p ? 95 + (projects.indexOf(p) * 47) % 120 : 150;
    const nodes = g.nodes.map((n, i) => ({ ...n, x: W / 2 + Math.cos(i) * (80 + i * 3), y: H / 2 + Math.sin(i) * (80 + i * 3), vx: 0, vy: 0, deg: 0 }));
    const idx = new Map(nodes.map((n, i) => [n.id, i]));
    const edges = g.edges.map(e => [idx.get(e.source), idx.get(e.target)]).filter(([a, b]) => a !== undefined && b !== undefined);
    edges.forEach(([a, b]) => { nodes[a].deg++; nodes[b].deg++; });
    let frame = 0, hover = null;
    function step() {
      for (let i = 0; i < nodes.length; i++) for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i], b = nodes[j]; let dx = a.x - b.x, dy = a.y - b.y, d2 = dx * dx + dy * dy + .01;
        const f = 900 / d2; a.vx += dx * f; a.vy += dy * f; b.vx -= dx * f; b.vy -= dy * f;
      }
      for (const [i, j] of edges) { const a = nodes[i], b = nodes[j], dx = b.x - a.x, dy = b.y - a.y; a.vx += dx * .012; a.vy += dy * .012; b.vx -= dx * .012; b.vy -= dy * .012; }
      for (const n of nodes) { n.vx += (W / 2 - n.x) * .004; n.vy += (H / 2 - n.y) * .004; n.x += n.vx *= .82; n.y += n.vy *= .82; }
    }
    function draw() {
      ctx.clearRect(0, 0, W, H);
      ctx.strokeStyle = col.line; ctx.lineWidth = 1.2;
      for (const [i, j] of edges) { ctx.beginPath(); ctx.moveTo(nodes[i].x, nodes[i].y); ctx.lineTo(nodes[j].x, nodes[j].y); ctx.stroke(); }
      for (const n of nodes) {
        const r = 4 + Math.min(n.deg, 10) * 1.2;
        ctx.fillStyle = n === hover ? col.acc : `hsl(${hue(n.project)} 55% 45%)`;
        ctx.beginPath(); ctx.arc(n.x, n.y, r, 0, 7); ctx.fill();
        if (n === hover || n.deg > 2 || nodes.length < 40) { ctx.fillStyle = col.ink; ctx.font = "12px system-ui"; ctx.fillText(n.title, n.x + r + 3, n.y + 4); }
      }
    }
    (function loop() { if (frame++ < 260) step(); draw(); if (!$("#graph").classList.contains("hidden")) requestAnimationFrame(loop); })();
    const pick = e => { const r = cv.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top; return nodes.find(n => (n.x - x) ** 2 + (n.y - y) ** 2 < 140); };
    cv.onmousemove = e => { hover = pick(e); cv.style.cursor = hover ? "pointer" : "default"; };
    cv.onclick = e => { const n = pick(e); if (n) { $("#graph").classList.add("hidden"); openNote(n.id); } };
  }

  /* ---------- pairing ---------- */
  let pairBuddy;
  function showPair(req) {
    if (S.shownPair === req.id) return;
    S.shownPair = req.id;
    $("#pairClient").textContent = req.client;
    $("#pairWhere").textContent = `${req.host ? "En " + req.host : ""}${req.cwd ? " · carpeta " + req.cwd : ""}`;
    if (!pairBuddy) pairBuddy = Rollito.mount($("#pairMascot"), { size: 88, sleepAfter: 0 });
    pairBuddy.mood("alert", 0);
    $("#pair").classList.remove("hidden");
    say(`${req.client} pide permiso para entrar. ¿Lo dejas?`, "alert", 0);
    const answer = async (allow, always) => {
      $("#pair").classList.add("hidden");
      try { await api(`/api/pair/${req.id}/answer`, { allow, always }); } catch (e) { toast(e.message); }
      S.shownPair = null; load();
    };
    $("#pairAlways").onclick = () => answer(true, true);
    $("#pairOnce").onclick = () => answer(true, false);
    $("#pairDeny").onclick = () => answer(false, false);
  }

  /* ---------- live activity ---------- */
  function addEvent(ev) {
    const el = document.createElement("div");
    el.className = "ev " + ev.kind;
    el.innerHTML = `<time>${new Date(ev.t * 1000).toLocaleTimeString()}</time>${esc(ev.text)}`;
    $("#activity").prepend(el);
    while ($("#activity").children.length > 80) $("#activity").lastChild.remove();
  }
  let refreshTimer;
  function connectEvents() {
    const es = new EventSource("/api/events?k=" + encodeURIComponent(KEY));
    es.onmessage = m => {
      const ev = JSON.parse(m.data);
      addEvent(ev);
      say(ev.text, ev.mood);
      if (ev.kind === "pair" && ev.request) showPair(ev.request);
      clearTimeout(refreshTimer);
      refreshTimer = setTimeout(async () => { const cur = S.current; await load(); if (cur && !S.dirty && ev.kind !== "pair") { const n = await api("/api/note?path=" + encodeURIComponent(cur)).catch(() => null); if (n && n.text !== S.text) { S.text = n.text; $("#src").value = n.text; renderPreview(); } } }, 500);
    };
    es.onerror = () => { buddy.mood("sleep", 0); bubbleText.textContent = "Perdí la conexión con la app. Reintentando…"; bubble.classList.remove("quiet"); };
  }
  window.addEventListener("beforeunload", () => { if (S.dirty) save(); });

  load().then(() => { connectEvents(); say("¡Hola! Soy Rollito. Te aviso de todo lo que Claude haga en tu cajón.", "wave"); })
    .catch(e => say("No pude cargar el cajón: " + e.message, "alert", 0));
})();
