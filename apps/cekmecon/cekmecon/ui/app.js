/* GeekMcON window. Vanilla JS, no build step.
   Served by the desktop app (127.0.0.1, real UI key) it talks to the local API; opened anywhere else
   (GitHub Pages, a file) it runs on CekmeconWeb, the in-browser store in webstore.js. */
(() => {
  const KEY = (document.querySelector('meta[name="cekmecon-ui"]') || {}).content || "";
  const WEB = !KEY || KEY === "__UI_" + "KEY__" || !window.EventSource;
  document.documentElement.classList.add(WEB ? "is-web" : "is-local");
  const $ = s => document.querySelector(s);
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const S = { tree: [], folders: [], stats: {}, current: null, text: "", dirty: false, mode: localGet("mode") || "read", pending: [], shownPair: null };

  function localGet(k) { try { return localStorage.getItem("cek." + k); } catch { return null; } }
  function localSet(k, v) { try { localStorage.setItem("cek." + k, v); } catch { } }
  async function api(path, body) {
    if (WEB) return CekmeconWeb.api(path, body);
    const r = await fetch(path, body === undefined ? { headers: { "X-Cekmecon-UI": KEY } }
      : { method: "POST", headers: { "X-Cekmecon-UI": KEY, "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || r.status);
    return j;
  }
  /* ---------- theme, sidebar, connection ---------- */
  const THEMES = ["", "light", "dark"], THEME_NAMES = { "": "automático", light: "claro", dark: "oscuro" };
  function applyTheme(t) { if (t) document.documentElement.dataset.theme = t; else delete document.documentElement.dataset.theme; $("#themeBtn").title = "Tema: " + THEME_NAMES[t]; }
  applyTheme(localGet("theme") || "");
  $("#themeBtn").onclick = () => { const t = THEMES[(THEMES.indexOf(localGet("theme") || "") + 1) % 3]; localSet("theme", t); applyTheme(t); toast("Tema " + THEME_NAMES[t]); };
  $("#sideBtn").onclick = () => { const o = $("#side").classList.toggle("open"); $("#sideBtn").setAttribute("aria-expanded", String(o)); };
  function netStatus() {
    const on = navigator.onLine !== false;
    $("#netDot").className = "net " + (on ? "on" : "off");
    $("#netDot").title = WEB ? (on ? "En línea · versión web (tus notas viven en este navegador)" : "Sin conexión · sigue funcionando offline")
      : (on ? "App local · con internet" : "App local · sin internet (todo sigue funcionando)");
  }
  addEventListener("online", () => { netStatus(); say("Volvió la conexión a internet.", "celebrate"); });
  addEventListener("offline", () => { netStatus(); say(WEB ? "Sin internet: sigo funcionando, todo se guarda aquí." : "Sin internet: no pasa nada, todo vive en tu PC.", "think"); });

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
    if (!S.current) renderHome(); else renderTasks();
    $("#activity").innerHTML = "";
    st.events.forEach(addEvent);
    if (st.pending.length) showPair(st.pending[0]);
    return st;
  }
  function renderStats() {
    const s = S.stats;
    $("#stats").innerHTML = `${s.notes} notas · ${s.links} enlaces · ${s.projects.length} proyectos<br><span title="${esc(s.vault)}">${WEB ? "🌐" : "📁"} ${esc(s.vault)}</span>`;
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
      if (!prefix && n.notes.length) out += '<div class="tree-sep">Raíz</div>';
      for (const note of n.notes.sort((a, b) => a.title.localeCompare(b.title)))
        out += `<button class="note ${note.kind === "map" ? "auto" : ""} ${S.current === note.path ? "on" : ""}" data-path="${esc(note.path)}" title="${esc(note.path)}">${esc(note.title)}</button>`;
      return out;
    };
    $("#tree").innerHTML = html(root, "");
    $("#tree").querySelectorAll("details").forEach(d => d.addEventListener("toggle", () => {
      d.open ? open.add(d.dataset.path) : open.delete(d.dataset.path); localSet("open", JSON.stringify([...open]));
    }));
  }
  $("#tree").addEventListener("click", e => { const b = e.target.closest(".note"); if (b) { openNote(b.dataset.path); $("#side").classList.remove("open"); } });

  /* ---------- home ---------- */
  /* ---------- review: what you wrote a week / month / year ago, and a random note ---------- */
  function reviewHTML() {
    const now = Date.now() / 1000, D = 86400, out = [];
    for (const [label, days] of [["Hace una semana", 7], ["Hace un mes", 30], ["Hace un año", 365]]) {
      const t = now - days * D, n = S.tree.filter(x => Math.abs(x.mtime - t) < 3 * D).sort((a, b) => Math.abs(a.mtime - t) - Math.abs(b.mtime - t))[0];
      if (n) out.push(`<button data-path="${esc(n.path)}"><small>${label}</small>${esc(n.title)}</button>`);
    }
    return out.join("") || '<span class="muted">Cuando tengas notas de hace una semana, un mes o un año, aparecen aquí para repasarlas.</span>';
  }
  function randomNote() {
    const pool = S.tree.filter(n => !n.path.startsWith("Archive/")); if (!pool.length) return;
    const n = pool[Math.floor(Math.random() * pool.length)];
    openNote(n.path); say(`Al azar: «${n.title}». A veces lo olvidado es lo que más sirve.`, "think");
  }

  /* ---------- open tasks across the whole vault ---------- */
  async function renderTasks() {
    let list = [];
    try { list = (await api("/api/tasks")).tasks; } catch { return; }
    const row = t => `<label class="task-row ${t.done ? "done" : ""}"><input type="checkbox" ${t.done ? "checked" : ""} data-path="${esc(t.path)}" data-line="${t.line}" data-text="${esc(t.text)}"><span><a data-open="${esc(t.path)}">${esc(t.text)}</a><small>${esc(t.title)}${t.project ? " · " + esc(t.project) : ""}</small></span></label>`;
    const empty = '<span class="muted">Nada pendiente. Escribe <code>- [ ] algo</code> en cualquier nota y aparece aquí.</span>';
    $("#taskCount").textContent = list.length;
    $("#sideTasks").innerHTML = list.slice(0, 40).map(row).join("") || empty;
    const ht = $("#homeTasks"); if (ht) { ht.innerHTML = list.slice(0, 8).map(row).join("") || empty; $("#homeTaskCount").textContent = list.length; }
  }
  document.addEventListener("change", async e => {
    const c = e.target.closest(".task-row input"); if (!c) return;
    try { const r = await api("/api/task/toggle", { path: c.dataset.path, line: +c.dataset.line, text: c.dataset.text }); if (r.done) say("¡Tarea hecha! Una menos.", "celebrate"); }
    catch (err) { toast(err.message); }
    setTimeout(renderTasks, 250);
    if (S.current === c.dataset.path && !S.dirty) { const n = await api("/api/note?path=" + encodeURIComponent(S.current)).catch(() => null); if (n) { S.text = n.text; $("#src").value = n.text; renderPreview(); } }
  });
  document.addEventListener("click", e => { const a = e.target.closest(".task-row a[data-open]"); if (a) { e.preventDefault(); openNote(a.dataset.open); } });

  let homeNv = null;
  function renderHome() {
    $("#editor").classList.add("hidden"); $("#home").classList.remove("hidden");
    const s = S.stats, proj = s.projects;
    if (homeNv) { homeNv.destroy(); homeNv = null; }
    const recent = [...S.tree].sort((a, b) => b.mtime - a.mtime).slice(0, 6);
    const ago = t => { const d = (Date.now() / 1000 - t) / 60; return d < 1 ? "ahora" : d < 60 ? `hace ${d | 0} min` : d < 1440 ? `hace ${d / 60 | 0} h` : `hace ${d / 1440 | 0} d`; };
    $("#home").innerHTML = `
      <div class="hero"><div id="heroBuddy"></div><div><h1>${WEB ? "GeekMcON en tu navegador" : "Tu cajón está listo"}</h1>
      <p>${WEB ? "Sin instalar nada. Tus notas viven en este navegador y funcionan sin conexión. Exporta un .zip cuando quieras llevarlas a la app de escritorio u Obsidian."
        : "Claude guarda aquí lo que aprende de tus proyectos y te devuelve solo lo necesario. Menos tokens, cero releer."}</p></div></div>
      <div class="neuro-card"><div class="neuro-mini" id="homeNeuro"></div>
        <div class="neuro-cta"><small>Neuronas</small><b>Tu memoria, viva</b><span class="muted">Cada nota es un racimo de partículas; cada enlace, una sinapsis que se enciende. Nueve formas: cerebro, neurona, red, galaxia, clústeres, matriz, rueda, calendario y corriente.</span>
        <button class="primary" id="homeNeuroBtn">🧠 Abrir Neuronas</button></div></div>
      ${recent.length ? `<h3>Recientes</h3><div class="recent">${recent.map(n => `<button class="rec" data-path="${esc(n.path)}"><b>${esc(n.title)}</b><small>${esc(n.path.split("/").slice(0, -1).join(" / ") || "raíz")} · ${ago(n.mtime)}</small></button>`).join("")}</div>` : ""}
      <div class="home-grid">
        <div class="panel-card"><h3>Pendientes <span class="pill" id="homeTaskCount">…</span></h3><div class="tasks" id="homeTasks"><span class="muted">Cargando…</span></div></div>
        <div class="panel-card"><h3>Repasar <button class="ghost" id="randomBtn" title="Nota al azar (Alt+R)">🎲 Al azar</button></h3><div class="review">${reviewHTML()}</div></div>
      </div>
      <div class="cards">
        <div class="card"><b>${s.notes}</b><span>notas</span></div><div class="card"><b>${proj.length}</b><span>cajones de proyecto</span></div>
        <div class="card"><b>${s.links}</b><span>enlaces</span></div><div class="card local-only"><b>${S.clients ? S.clients.length : 0}</b><span>conexiones de Claude</span></div></div>
      <h3>Proyectos</h3>
      <div class="projects">${proj.map(p => `<button class="proj" data-path="Projects/${esc(p)}/README.md"><b>🧻 ${esc(p)}</b><small>brief · mapa · decisiones · lecciones</small></button>`).join("") || '<p class="muted">Aún no hay proyectos. Se crean solos la primera vez que Claude trabaja en uno.</p>'}</div>
      ${WEB ? `<h3>Llévalo a tu PC</h3>
      <ol class="steps"><li><b>⬇ Exportar</b> baja todas tus notas en un .zip de Markdown.</li>
      <li>Instala la <a href="https://lukoffmon.github.io/HighPerformanceClaude/cekmecon/#instalar" target="_blank" rel="noopener">app de escritorio</a> (Windows, macOS o Linux) y descomprime el .zip en tu carpeta <code>Cekmecon</code>.</li>
      <li>La app de escritorio es la que se conecta con Claude Code. Esta versión web es para leer, escribir y explorar desde cualquier lado.</li></ol>
      <p class="muted small-print">Guardado: ${CekmeconWeb.persistent() ? "en este navegador (IndexedDB)" : "solo en memoria: este navegador bloquea el almacenamiento, exporta antes de cerrar"} · <button class="linkish" id="resetWeb">Restablecer el cajón de ejemplo</button></p>`
      : `<h3>Conectar con Claude</h3>
      <ol class="steps"><li>En una terminal: <code>cekmecon connect</code> (solo una vez).</li>
      <li>Abre Claude Code en tu proyecto, en esta computadora, y pídele cualquier cosa.</li>
      <li>Aparecerá un aviso aquí: pulsa <b>Permitir siempre</b>. Desde entonces Claude entra solo.</li></ol>
      <p class="muted small-print">¿Lejos de tu PC? Abre la <a href="https://lukoffmon.github.io/HighPerformanceClaude/cekmecon/app/" target="_blank" rel="noopener">versión web</a> (necesita internet la primera vez; luego funciona offline).</p>`}`;
    Rollito.mount($("#heroBuddy"), { size: 92, sleepAfter: 0 }).mood("wave", 0);
    $("#home").querySelectorAll(".proj, .rec, .review [data-path]").forEach(b => b.onclick = () => openNote(b.dataset.path));
    $("#randomBtn").onclick = randomNote;
    renderTasks();
    $("#homeNeuroBtn").onclick = () => openNeuronas();
    const rs = $("#resetWeb");
    if (rs) rs.onclick = async () => { if (confirm("¿Borrar las notas de este navegador y volver al cajón de ejemplo? (Exporta antes si quieres guardarlas)")) { await CekmeconWeb.reset(); S.current = null; await load(); } };
    api("/api/graph").then(g => { if (!$("#homeNeuro")) return; homeNv = Neuronas.mount($("#homeNeuro"), { data: g, compact: true, form: "cerebro", onOpen: openNote }); }).catch(() => { });
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
      if (homeNv) { homeNv.destroy(); homeNv = null; }
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
  $("#dailyBtn").onclick = async () => {
    try { const r = await api("/api/daily", {}); await load(); await openNote(r.path); setMode("split"); say("Tu nota de hoy está lista. Escribe lo que quieras recordar.", "write"); }
    catch (e) { toast(e.message); }
  };
  $("#importBtn").onclick = () => $("#importInput").click();
  $("#importInput").onchange = async e => {
    const n = await CekmeconWeb.importFiles(e.target.files); e.target.value = "";
    await load(); toast(`Importé ${n} nota${n === 1 ? "" : "s"}`);
  };
  $("#exportBtn").onclick = () => { const n = CekmeconWeb.exportZip(); toast(`Exportando ${n} notas…`); };
  /* quick capture into today's note */
  $("#captureForm").addEventListener("submit", async e => {
    e.preventDefault();
    const text = $("#captureInput").value.trim(); if (!text) return $("#captureInput").focus();
    try {
      const r = await api("/api/capture", { text }); $("#captureInput").value = "";
      say("Guardado en la nota de hoy ✓", "write");
      if (S.current === r.path) { const n = await api("/api/note?path=" + encodeURIComponent(r.path)); S.text = n.text; $("#src").value = n.text; renderPreview(); }
      load();
    } catch (err) { toast(err.message); }
  });
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  let rec = null;
  if (SR) {
    $("#micBtn").classList.remove("hidden");
    $("#micBtn").onclick = () => {
      if (rec) { rec.stop(); return; }
      if (navigator.onLine === false) return toast("Dictar necesita internet en la mayoría de navegadores");
      rec = new SR(); rec.lang = document.documentElement.lang === "es" ? "es-ES" : navigator.language; rec.interimResults = true; rec.continuous = false;
      const base = $("#captureInput").value ? $("#captureInput").value.trim() + " " : "";
      rec.onresult = ev => { $("#captureInput").value = base + [...ev.results].map(r => r[0].transcript).join(""); };
      rec.onend = () => { rec = null; $("#micBtn").setAttribute("aria-pressed", "false"); $("#captureInput").focus(); say("Listo. Revisa el texto y pulsa Enter para guardarlo.", "idle"); };
      rec.onerror = ev => toast("Dictado: " + (ev.error === "not-allowed" ? "permite el micrófono" : ev.error));
      $("#micBtn").setAttribute("aria-pressed", "true"); say("Te escucho… habla y luego pulsa Enter.", "read", 0);
      try { rec.start(); } catch { rec = null; }
    };
  }
  /* read the open note aloud */
  if (!("speechSynthesis" in window)) $("#speakBtn").classList.add("hidden");
  $("#speakBtn").onclick = () => {
    if (speechSynthesis.speaking) { speechSynthesis.cancel(); $("#speakBtn").setAttribute("aria-pressed", "false"); return; }
    const u = new SpeechSynthesisUtterance($("#preview").innerText.slice(0, 20000)); u.lang = "es-ES"; u.rate = 1.02;
    u.onend = u.onerror = () => $("#speakBtn").setAttribute("aria-pressed", "false");
    $("#speakBtn").setAttribute("aria-pressed", "true"); speechSynthesis.speak(u); say("Leyendo en voz alta. Pulsa 🔊 otra vez para parar.", "read");
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

  /* ---------- palette: search, or ">" for commands ---------- */
  let hits = [], sel = 0, searchTimer;
  const closePal = () => $("#palette").classList.add("hidden");
  function commands() {
    const c = [
      ["Nota nueva", "Ctrl+N", () => $("#newBtn").onclick()], ["Nota de hoy", "Alt+D", () => $("#dailyBtn").onclick()],
      ["Captura rápida", "Alt+C", () => $("#captureInput").focus()], ["Nota al azar", "Alt+R", randomNote],
      ["Neuronas", "Alt+G", () => openNeuronas()], ...Neuronas.FORMS.map(([k, l]) => [`Neuronas: ${l}`, "", () => openNeuronas(k)]),
      ["Organizar el Inbox", "", () => $("#organizeBtn").onclick()], ["Cambiar tema", "", () => $("#themeBtn").onclick()],
      ["Leer la nota en voz alta", "", () => $("#speakBtn").onclick()], ["Ir al inicio", "", () => { S.current = null; renderHome(); renderTree(); }],
      ["Atajos de teclado", "?", () => $("#help").classList.remove("hidden")],
    ];
    if (WEB) c.push(["Exportar todo (.zip)", "", () => $("#exportBtn").onclick()], ["Importar carpeta de notas", "", () => $("#importBtn").onclick()]);
    else c.push(["Conexiones con Claude", "", () => $("#clientsBtn").onclick()]);
    return c.map(([title, key, run]) => ({ title, snippet: key ? "atajo " + key : "comando", run, cmd: true }));
  }
  function openPalette(prefix) {
    $("#palette").classList.remove("hidden"); $("#palInput").value = prefix || ""; $("#palInput").focus();
    if (prefix) return showCommands("");
    renderHits([...S.tree].sort((a, b) => b.mtime - a.mtime).slice(0, 8).map(n => ({ ...n, snippet: n.path })), "Recientes · escribe para buscar · empieza con > para comandos");
  }
  function showCommands(q) { const f = q.toLowerCase(); renderHits(commands().filter(c => c.title.toLowerCase().includes(f))); }
  function renderHits(list, hint) {
    hits = list; sel = 0;
    $("#palResults").innerHTML = (hint ? `<div class="hit muted" style="font-size:12px">${esc(hint)}</div>` : "") + (list.map((h, i) => `<button class="hit ${h.cmd ? "cmd" : ""} ${i ? "" : "on"}" data-i="${i}"><b>${esc(h.title)}</b><small>${esc(h.snippet || "").replace(/«/g, "<em>").replace(/»/g, "</em>")}</small></button>`).join("") || '<div class="hit muted">Sin resultados</div>');
  }
  function pick(h) { closePal(); if (h.cmd) h.run(); else openNote(h.path); }
  $("#searchBtn").onclick = () => openPalette();
  $("#palInput").addEventListener("input", () => {
    clearTimeout(searchTimer);
    const q = $("#palInput").value.trim();
    if (q.startsWith(">")) return showCommands(q.slice(1).trim());
    searchTimer = setTimeout(async () => { if (q) renderHits((await api("/api/search?q=" + encodeURIComponent(q))).results); }, 120);
  });
  $("#palInput").addEventListener("keydown", e => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); sel = (sel + (e.key === "ArrowDown" ? 1 : -1) + hits.length) % Math.max(hits.length, 1); document.querySelectorAll(".hit[data-i]").forEach((h, i) => h.classList.toggle("on", i === sel)); }
    if (e.key === "Enter" && hits[sel]) pick(hits[sel]);
  });
  $("#palResults").addEventListener("click", e => { const b = e.target.closest(".hit[data-i]"); if (b) pick(hits[+b.dataset.i]); });
  $("#palette").addEventListener("click", e => { if (e.target.id === "palette") closePal(); });
  const typing = e => /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) || e.target.isContentEditable;
  document.addEventListener("keydown", e => {
    const mod = e.ctrlKey || e.metaKey;
    if (mod && e.key.toLowerCase() === "k") { e.preventDefault(); openPalette(); }
    if (mod && e.shiftKey && e.key.toLowerCase() === "p") { e.preventDefault(); openPalette(">"); }
    if (mod && e.key.toLowerCase() === "s") { e.preventDefault(); save(); }
    if (mod && e.key.toLowerCase() === "n") { e.preventDefault(); $("#newBtn").onclick(); }
    if (e.altKey && e.code === "KeyD") { e.preventDefault(); $("#dailyBtn").onclick(); }
    if (e.altKey && e.code === "KeyG") { e.preventDefault(); openNeuronas(); }
    if (e.altKey && e.code === "KeyC") { e.preventDefault(); $("#captureInput").focus(); }
    if (e.altKey && e.code === "KeyR") { e.preventDefault(); randomNote(); }
    if (e.key === "?" && !typing(e) && !mod) { e.preventDefault(); $("#help").classList.remove("hidden"); }
    if (e.key === "Escape") document.querySelectorAll(".overlay:not(#pair)").forEach(o => o.classList.add("hidden"));
  });

  /* ---------- neuronas ---------- */
  let nv = null;
  async function openNeuronas(form) {
    $("#graph").classList.remove("hidden");
    const g = await api("/api/graph");
    const close = () => $("#graph").classList.add("hidden");
    if (!nv) nv = Neuronas.mount($("#neuroMount"), { data: g, form: localGet("nvform") || "cerebro", color: localGet("nvcolor") || "project", title: WEB ? "web" : "local",
      onOpen: id => { close(); openNote(id); }, onClose: close, onChange: st => { localSet("nvform", st.form); localSet("nvcolor", st.color); } });
    else nv.setData(g);
    if (typeof form === "string") nv.setForm(form);
    say(`Tu memoria: ${g.nodes.length} notas y ${g.edges.length} enlaces. Arrastra para girar, clic en una neurona para abrirla.`, "think");
  }
  $("#graphBtn").onclick = () => openNeuronas();
  $("#graph").addEventListener("click", e => { if (e.target.id === "graph") $("#graph").classList.add("hidden"); });

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
    if (WEB) {
      CekmeconWeb.onEvent(ev => { addEvent(ev); say(ev.text, ev.mood); });
      if ("serviceWorker" in navigator && window.isSecureContext && location.protocol !== "file:") navigator.serviceWorker.register("sw.js").catch(() => { });
      return;
    }
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

  /* desktop app + internet: tell the user once a day when a newer version exists (fails silently offline) */
  function checkUpdate(version) {
    if (WEB || navigator.onLine === false || !/^\d+\.\d+\.\d+$/.test(version || "")) return;
    const last = +localGet("updcheck") || 0; if (Date.now() - last < 864e5) return;
    localSet("updcheck", String(Date.now()));
    fetch("https://api.github.com/repos/LukOffMon/HighPerformanceClaude/releases/latest", { headers: { Accept: "application/vnd.github+json" } })
      .then(r => r.ok ? r.json() : null).then(j => {
        const m = j && String(j.tag_name || "").match(/(\d+)\.(\d+)\.(\d+)/); if (!m) return;
        const a = m.slice(1).map(Number), b = version.split(".").map(Number);
        if (a[0] > b[0] || (a[0] === b[0] && (a[1] > b[1] || (a[1] === b[1] && a[2] > b[2]))))
          say(`Hay una versión nueva de GeekMcON (${m.slice(1).join(".")}). Para actualizar, en PowerShell: irm https://raw.githubusercontent.com/LukOffMon/HighPerformanceClaude/main/apps/cekmecon/update.ps1 | iex  (o en la terminal: cekmecon update)`, "celebrate");
      }).catch(() => { });
  }

  netStatus();
  load().then(st => { connectEvents(); say(WEB ? "¡Hola! Soy Rollito. Esta es la versión web: todo se guarda en este navegador." : "¡Hola! Soy Rollito. Te aviso de todo lo que Claude haga en tu cajón.", "wave"); checkUpdate(st && st.version); })
    .catch(e => say("No pude cargar el cajón: " + e.message, "alert", 0));
})();
