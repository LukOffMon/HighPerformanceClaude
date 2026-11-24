/* Neuronas — Çekmecón's memory visualizer. Every note becomes a little cluster of glowing particles;
   links become synapses that fire. Six forms morph into each other: Cerebro, Red, Galaxia, Clústeres, Rueda, Corriente.
   Usage: const nv = Neuronas.mount(el, { data: {nodes, edges}, onOpen: id => …, compact: false });
          nv.setData(data); nv.setForm("red"); nv.destroy();   Neuronas.demo(500) → sample data.
   Node fields: id (path), title, project, folder, kind, mtime (seconds), size (bytes). No dependencies. */
(function () {
  const CSS = `
.nv{position:relative;width:100%;height:100%;box-sizing:border-box;overflow:hidden;background:radial-gradient(ellipse at 50% 40%,#0a1420 0,#03060a 70%);color:#cfe3f1;font:12px/1.4 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;border-radius:16px;min-height:260px;user-select:none;-webkit-user-select:none;touch-action:none}
.nv canvas{position:absolute;inset:0;width:100%;height:100%;display:block;cursor:grab}
.nv canvas.drag{cursor:grabbing}.nv canvas.hot{cursor:pointer}
.nv-panel{position:absolute;left:10px;top:10px;bottom:10px;width:226px;display:flex;flex-direction:column;gap:10px;padding:12px;border-radius:12px;background:rgba(6,10,16,.78);border:1px solid rgba(120,170,210,.14);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);overflow:auto;transition:transform .35s cubic-bezier(.2,.8,.2,1),opacity .35s;z-index:2}
.nv.closed .nv-panel{transform:translateX(-110%);opacity:0;pointer-events:none}
.nv-h{font:600 10px/1 ui-monospace,Menlo,Consolas,monospace;letter-spacing:.16em;text-transform:uppercase;color:#6f8ea6;margin:0 0 6px}
.nv-brand{display:flex;justify-content:space-between;align-items:center;font-weight:700;font-size:13px;color:#e8f6ff}
.nv-brand small{font:500 10px ui-monospace,Menlo,monospace;color:#6f8ea6;letter-spacing:.08em}
.nv-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:4px}
.nv-grid.c2{grid-template-columns:repeat(2,1fr)}
.nv button{font:inherit;color:#b9cfdf;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:7px;padding:5px 4px;cursor:pointer;transition:background .15s,color .15s,border-color .15s}
.nv button:hover{border-color:rgba(120,220,255,.5);color:#fff}
.nv button[aria-pressed="true"]{background:#e8f6ff;color:#04121c;border-color:#e8f6ff;font-weight:600}
.nv button:focus-visible{outline:2px solid #7fe6ff;outline-offset:1px}
.nv-tg{display:flex;justify-content:space-between;align-items:center;padding:2px 0;color:#9db5c7;cursor:pointer}
.nv-tg input{appearance:none;-webkit-appearance:none;width:26px;height:14px;border-radius:9px;background:#22313d;position:relative;cursor:pointer;margin:0;transition:background .2s}
.nv-tg input::after{content:"";position:absolute;top:2px;left:2px;width:10px;height:10px;border-radius:50%;background:#7f97a8;transition:transform .2s,background .2s}
.nv-tg input:checked{background:#1f8fb0}.nv-tg input:checked::after{transform:translateX(12px);background:#fff}
.nv-tg input:focus-visible{outline:2px solid #7fe6ff;outline-offset:2px}
.nv-search{width:100%;box-sizing:border-box;font:inherit;color:#e8f6ff;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:8px;padding:6px 9px;outline:0}
.nv-search:focus{border-color:#4cc9f0}
.nv-legend{display:grid;gap:1px;max-height:none}
.nv-legend button{display:grid;grid-template-columns:10px 1fr auto auto;gap:7px;align-items:center;text-align:left;background:none;border:0;border-radius:6px;padding:3px 4px;color:#b9cfdf}
.nv-legend button:hover{background:rgba(255,255,255,.05)}
.nv-legend button.off{opacity:.35}.nv-legend button[aria-pressed="true"]{background:rgba(255,255,255,.1);color:#fff;font-weight:400}
.nv-legend i{width:9px;height:9px;border-radius:50%;box-shadow:0 0 8px currentColor}
.nv-legend span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.nv-legend em{font:10px ui-monospace,Menlo,monospace;font-style:normal;color:#6f8ea6;text-align:right}
.nv-foot{margin-top:auto;font:10px ui-monospace,Menlo,monospace;color:#5d7a8f;line-height:1.6}
.nv-tip{position:absolute;z-index:3;pointer-events:none;max-width:260px;padding:8px 10px;border-radius:9px;background:rgba(4,8,14,.92);border:1px solid rgba(120,200,240,.25);color:#e8f6ff;font-size:12px;opacity:0;transform:translateY(4px);transition:opacity .15s,transform .15s}
.nv-tip.on{opacity:1;transform:none}
.nv-tip b{display:block;font-size:13px;margin-bottom:2px}.nv-tip small{display:block;color:#8aa6ba;font:11px ui-monospace,Menlo,monospace}
.nv-tools{position:absolute;right:10px;top:10px;display:flex;gap:4px;z-index:2}
.nv-tools button{width:30px;height:30px;padding:0;background:rgba(6,10,16,.7);font-size:14px}
.nv-toggle{position:absolute;left:10px;top:10px;z-index:1;height:30px;padding:0 10px!important;background:rgba(6,10,16,.7)!important}
.nv-bar{position:absolute;left:50%;bottom:10px;transform:translateX(-50%);display:flex;gap:4px;padding:4px;border-radius:99px;background:rgba(6,10,16,.72);border:1px solid rgba(255,255,255,.08);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);z-index:2;max-width:calc(100% - 20px);overflow-x:auto;scrollbar-width:none}
.nv-bar button{border-radius:99px;padding:5px 11px;white-space:nowrap;border:0}
.nv-empty{position:absolute;inset:0;display:grid;place-items:center;text-align:center;color:#6f8ea6;padding:20px;pointer-events:none}
@media (max-width:640px){.nv-panel{width:min(240px,calc(100% - 20px))}}
@media (prefers-reduced-motion:reduce){.nv-panel,.nv-tip{transition:none}}`;

  const PAL = ["#4cc9f0", "#3fd27a", "#a78bfa", "#f472b6", "#fbbf24", "#2dd4bf", "#60a5fa", "#fb7185", "#c084fc", "#a3e635", "#f97316", "#e879f9", "#7d8fa3"];
  const AGE = ["#1d3b8f", "#2563eb", "#22d3ee", "#5eead4", "#d9fbe8"];
  const FORMS = [["cerebro", "Cerebro"], ["red", "Red"], ["galaxia", "Galaxia"], ["clusters", "Clústeres"], ["rueda", "Rueda"], ["corriente", "Corriente"]];
  const COLORS = [["project", "Proyecto"], ["folder", "Carpeta"], ["kind", "Tipo"], ["age", "Edad"]];
  const MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
  const KIND_NAMES = { "": "nota", map: "mapa", brief: "brief", decisions: "decisiones", lessons: "lecciones", tasks: "tareas", log: "registro", daily: "diario" };
  const TAU = Math.PI * 2, GA = Math.PI * (3 - Math.sqrt(5));
  const D3 = new Set(["cerebro", "galaxia"]);
  const LINKED = new Set(["cerebro", "red", "galaxia"]);

  const hash = s => { let h = 2166136261; for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619); return h >>> 0; };
  const rng = seed => { let s = seed >>> 0 || 1; return () => (s = (Math.imul(s, 1664525) + 1013904223) >>> 0) / 4294967296; };
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
  const hex = c => [1, 3, 5].map(i => parseInt(c.slice(i, i + 2), 16));
  const mix = (a, b, t) => { const x = hex(a), y = hex(b); return "#" + x.map((v, i) => Math.round(v + (y[i] - v) * t).toString(16).padStart(2, "0")).join(""); };
  const ageColor = t => { t = clamp(t, 0, 1) * (AGE.length - 1); const i = Math.min(Math.floor(t), AGE.length - 2); return mix(AGE[i], AGE[i + 1], t - i); };
  const fmtDate = s => { const d = new Date(s * 1000); return MONTHS[d.getMonth()] + " " + String(d.getFullYear()).slice(2); };
  const fmtDay = s => new Date(s * 1000).toLocaleDateString("es", { day: "numeric", month: "short", year: "numeric" });

  function injectCSS() {
    if (document.getElementById("nv-css")) return;
    const st = document.createElement("style"); st.id = "nv-css"; st.textContent = CSS; document.head.append(st);
  }

  function sprite(color, size) {
    const c = document.createElement("canvas"); c.width = c.height = size;
    const g = c.getContext("2d"), r = size / 2, grd = g.createRadialGradient(r, r, 0, r, r, r);
    grd.addColorStop(0, "rgba(255,255,255,1)"); grd.addColorStop(.18, color); grd.addColorStop(.45, color + "55"); grd.addColorStop(1, color + "00");
    g.fillStyle = grd; g.fillRect(0, 0, size, size);
    return c;
  }

  function prepare(data) {
    const nodes = (data && data.nodes || []).map(n => {
      const id = String(n.id || n.path || ""), parts = id.split("/");
      return {
        id, title: n.title || parts[parts.length - 1].replace(/\.md$/, ""), project: n.project || "",
        folder: n.folder || (parts.length > 1 ? parts[0] : "Raíz"), kind: KIND_NAMES[n.kind || ""] || n.kind,
        mtime: +n.mtime || 0, size: +n.size || 300, deg: 0, nb: [],
      };
    }).filter(n => n.id);
    const idx = new Map(nodes.map((n, i) => [n.id, i]));
    const edges = [];
    for (const e of (data && data.edges) || []) {
      const a = idx.get(e.source), b = idx.get(e.target);
      if (a === undefined || b === undefined || a === b) continue;
      edges.push([a, b]); nodes[a].deg++; nodes[b].deg++; nodes[a].nb.push(b); nodes[b].nb.push(a);
    }
    return { nodes, edges };
  }

  function mount(host, opts) {
    injectCSS();
    opts = Object.assign({ form: "cerebro", color: "project", compact: false, labels: true, links: true, pulses: true, spin: true, max: 0 }, opts || {});
    const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const root = document.createElement("div");
    root.className = "nv" + (opts.compact ? " compact" : "") + (opts.panel === false || opts.compact ? " closed" : "");
    host.innerHTML = ""; host.append(root);
    const cv = document.createElement("canvas");
    cv.setAttribute("role", "img");
    const tip = document.createElement("div"); tip.className = "nv-tip";
    root.append(cv, tip);
    const ctx = cv.getContext("2d");

    const st = { form: opts.form, color: opts.color, links: opts.links, pulses: opts.pulses && !reduce, labels: opts.labels, spin: opts.spin && !reduce, q: "", focus: null };
    let G = { nodes: [], edges: [] }, groups = [], gIndex = [], nodeColor = [], colorIdx = [];
    let P = 0, pNode, cx, cy, cz, tx, ty, tz, s1, s2, s3, orb, delay, isCore, order, coreOf = [];
    const panelOff = () => !opts.compact && !root.classList.contains("closed") && W > 700 ? 120 : 0;
    let WE = 0, W = 0, H = 0, dpr = 1, R = 100, sprites = [], spriteSize = 32;
    let yaw = 0.4, pitch = 0.18, yawT = 0, pitchT = 0.18, spinV = 0.0016, zoom = 1, panX = 0, panY = 0;
    let orbitAmt = 0, linkAmt = 1, morphT = 0, lastT = 0, hover = -1, hl = null, pulses = [], labels = [], visible = true, raf = 0, alive = true;
    let sx = new Float32Array(0), sy = new Float32Array(0), sd = new Float32Array(0), px = sx, py = sx, ps = sx, forceCache = {};
    let minT = 0, maxT = 1;

    /* ---------- panel ---------- */
    let panel, legendEl, footEl, searchEl, barEl;
    if (!opts.compact) {
      panel = document.createElement("div"); panel.className = "nv-panel";
      panel.innerHTML = `
        <div class="nv-brand"><span>🧠 Neuronas</span><small>${esc(opts.title || "Çekmecón")}</small></div>
        <div><div class="nv-h">Forma</div><div class="nv-grid" data-k="form">${FORMS.map(([k, l]) => `<button type="button" data-v="${k}">${l}</button>`).join("")}</div></div>
        <div><div class="nv-h">Color</div><div class="nv-grid c2" data-k="color">${COLORS.map(([k, l]) => `<button type="button" data-v="${k}">${l}</button>`).join("")}</div></div>
        <div><div class="nv-h">Mostrar</div>
          <label class="nv-tg">Enlaces<input type="checkbox" data-t="links"></label>
          <label class="nv-tg">Sinapsis<input type="checkbox" data-t="pulses"></label>
          <label class="nv-tg">Etiquetas<input type="checkbox" data-t="labels"></label>
          <label class="nv-tg">Girar<input type="checkbox" data-t="spin"></label></div>
        <div><div class="nv-h">Buscar</div><input class="nv-search" type="search" placeholder="Resalta notas…" aria-label="Resaltar notas"></div>
        <div><div class="nv-h">Espacios</div><div class="nv-legend"></div></div>
        <div class="nv-foot"></div>`;
      root.append(panel);
      legendEl = panel.querySelector(".nv-legend"); footEl = panel.querySelector(".nv-foot"); searchEl = panel.querySelector(".nv-search");
      panel.querySelectorAll(".nv-grid").forEach(g => g.addEventListener("click", e => {
        const b = e.target.closest("button"); if (!b) return;
        g.dataset.k === "form" ? api.setForm(b.dataset.v) : setColor(b.dataset.v);
      }));
      panel.querySelectorAll("[data-t]").forEach(i => { i.checked = st[i.dataset.t]; i.onchange = () => { st[i.dataset.t] = i.checked; if (i.dataset.t === "pulses" && !i.checked) pulses = []; }; });
      searchEl.addEventListener("input", () => { st.q = searchEl.value.trim().toLowerCase(); computeHL(); });
      legendEl.addEventListener("click", e => {
        const b = e.target.closest("button"); if (!b) return;
        st.focus = st.focus === +b.dataset.g ? null : +b.dataset.g; renderLegend(); computeHL();
      });
      const tools = document.createElement("div"); tools.className = "nv-tools";
      tools.innerHTML = `<button type="button" data-z="1" title="Acercar" aria-label="Acercar">＋</button><button type="button" data-z="-1" title="Alejar" aria-label="Alejar">−</button><button type="button" data-z="0" title="Centrar" aria-label="Centrar">⟲</button>` +
        (opts.onClose ? `<button type="button" data-x title="Cerrar" aria-label="Cerrar">✕</button>` : "");
      root.append(tools);
      tools.addEventListener("click", e => {
        const b = e.target.closest("button"); if (!b) return;
        if (b.hasAttribute("data-x")) return opts.onClose();
        const z = +b.dataset.z; if (!z) { zoom = 1; panX = panY = 0; } else zoom = clamp(zoom * (z > 0 ? 1.25 : .8), .4, 5);
      });
      const tg = document.createElement("button"); tg.type = "button"; tg.className = "nv-toggle"; tg.textContent = "☰ Ajustes";
      tg.onclick = () => { root.classList.toggle("closed"); resize(); };
      root.append(tg);
      const closeBtn = document.createElement("button"); closeBtn.type = "button"; closeBtn.textContent = "Ocultar panel ‹"; closeBtn.style.marginTop = "4px";
      closeBtn.onclick = () => { root.classList.add("closed"); resize(); };
      panel.append(closeBtn);
      if (opts.panel === false) root.classList.add("closed");
    } else {
      barEl = document.createElement("div"); barEl.className = "nv-bar";
      barEl.innerHTML = FORMS.map(([k, l]) => `<button type="button" data-v="${k}">${l}</button>`).join("");
      barEl.addEventListener("click", e => { const b = e.target.closest("button"); if (b) api.setForm(b.dataset.v); });
      root.append(barEl);
    }
    const empty = document.createElement("div"); empty.className = "nv-empty"; root.append(empty);

    function syncButtons() {
      root.querySelectorAll('[data-k="form"] button, .nv-bar button').forEach(b => b.setAttribute("aria-pressed", String(b.dataset.v === st.form)));
      root.querySelectorAll('[data-k="color"] button').forEach(b => b.setAttribute("aria-pressed", String(b.dataset.v === st.color)));
    }

    /* ---------- data → groups → particles ---------- */
    function groupKey(n) {
      if (st.color === "folder") return n.folder;
      if (st.color === "kind") return n.kind || "nota";
      return n.project || n.folder;
    }
    function regroup() {
      const counts = new Map();
      G.nodes.forEach(n => counts.set(groupKey(n), (counts.get(groupKey(n)) || 0) + 1));
      let list = [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
      const MAXG = 12;
      if (list.length > MAXG) { const rest = list.slice(MAXG - 1).reduce((a, x) => a + x[1], 0); list = list.slice(0, MAXG - 1).concat([["Otros", rest]]); }
      const pos = new Map(list.map(([k], i) => [k, i]));
      const other = pos.get("Otros");
      gIndex = G.nodes.map(n => pos.has(groupKey(n)) ? pos.get(groupKey(n)) : other);
      groups = list.map(([name, count], i) => ({ name, count, links: 0, color: name === "Otros" ? PAL[PAL.length - 1] : PAL[i % (PAL.length - 1)] }));
      G.edges.forEach(([a]) => groups[gIndex[a]] && groups[gIndex[a]].links++);
      recolor();
      renderLegend();
    }
    function recolor() {
      const span = (maxT - minT) || 1;
      nodeColor = G.nodes.map((n, i) => st.color === "age" ? ageColor((n.mtime - minT) / span) : groups[gIndex[i]].color);
      const uniq = [...new Set(nodeColor)];
      sprites = uniq.map(c => sprite(c, spriteSize));
      const ci = new Map(uniq.map((c, i) => [c, i]));
      colorIdx = nodeColor.map(c => ci.get(c));
      if (P) { order = Array.from({ length: P }, (_, i) => i).sort((a, b) => colorIdx[pNode[a]] - colorIdx[pNode[b]]); }
      api.colors = uniq;
    }
    function renderLegend() {
      if (!legendEl) return;
      legendEl.innerHTML = groups.map((g, i) => `<button type="button" data-g="${i}" aria-pressed="${st.focus === i}" class="${st.focus !== null && st.focus !== i ? "off" : ""}"><i style="color:${g.color};background:${g.color}"></i><span title="${esc(g.name)}">${esc(g.name)}</span><em>${g.count}</em><em>${g.links}</em></button>`).join("") || '<span style="color:#5d7a8f">—</span>';
      footEl.innerHTML = `${G.nodes.length} notas · ${G.edges.length} enlaces<br>${P} partículas · ${groups.length} espacios`;
    }
    function computeHL() {
      const q = st.q, f = st.focus;
      if (!q && f === null && hover < 0) { hl = null; return; }
      hl = new Float32Array(G.nodes.length).fill(1);
      G.nodes.forEach((n, i) => {
        let on = true;
        if (q) on = n.title.toLowerCase().includes(q) || n.id.toLowerCase().includes(q);
        if (f !== null) on = on && gIndex[i] === f;
        hl[i] = on ? 1 : .14;
      });
      if (hover >= 0) { hl.fill(.24); hl[hover] = 1; G.nodes[hover].nb.forEach(j => hl[j] = .9); }
    }

    function build() {
      const nodes = G.nodes;
      const times = nodes.map(n => n.mtime).filter(Boolean);
      minT = times.length ? Math.min(...times) : 0; maxT = times.length ? Math.max(...times) : 1;
      const cap = opts.max || (opts.compact ? 5000 : 14000);
      let per = nodes.map(n => 2 + Math.min(14, Math.round(Math.sqrt(n.size) / 5)) + Math.min(n.deg, 10));
      const total = per.reduce((a, b) => a + b, 0) || 1;
      if (total > cap) { const k = cap / total; per = per.map(v => Math.max(1, Math.round(v * k))); }
      else { const floor = opts.compact ? 1400 : 2600; if (total < floor && nodes.length) { const k = Math.min(floor / total, 14); per = per.map(v => Math.round(v * k)); } }
      P = per.reduce((a, b) => a + b, 0);
      const old = { P: cx ? cx.length : 0, cx, cy, cz };
      pNode = new Int32Array(P); isCore = new Uint8Array(P);
      cx = new Float32Array(P); cy = new Float32Array(P); cz = new Float32Array(P);
      tx = new Float32Array(P); ty = new Float32Array(P); tz = new Float32Array(P);
      s1 = new Float32Array(P); s2 = new Float32Array(P); s3 = new Float32Array(P); orb = new Float32Array(P); delay = new Float32Array(P);
      coreOf = new Int32Array(nodes.length);
      let p = 0;
      nodes.forEach((n, i) => {
        const r = rng(hash(n.id));
        for (let k = 0; k < per[i]; k++, p++) {
          pNode[p] = i; s1[p] = r(); s2[p] = r(); s3[p] = r(); delay[p] = r() * .35;
          if (k === 0) { isCore[p] = 1; coreOf[i] = p; }
          orb[p] = k === 0 ? 0 : 3 + Math.sqrt(n.deg) * 2 + s1[p] * 7;
          if (old.P) { const o = p % old.P; cx[p] = old.cx[o]; cy[p] = old.cy[o]; cz[p] = old.cz[o]; }
          else { const a = s1[p] * TAU, rr = s2[p] * 40; cx[p] = Math.cos(a) * rr; cy[p] = Math.sin(a) * rr; cz[p] = 0; }
        }
      });
      sx = new Float32Array(nodes.length); sy = new Float32Array(nodes.length); sd = new Float32Array(nodes.length);
      px = new Float32Array(P); py = new Float32Array(P); ps = new Float32Array(P);
      forceCache = {};
      regroup();
      empty.textContent = nodes.length ? "" : "Aún no hay notas. Cuando Claude o tú escriban, aparecerán aquí como neuronas.";
      cv.setAttribute("aria-label", `Visualización de ${nodes.length} notas y ${G.edges.length} enlaces`);
    }

    /* ---------- layouts (world units: pixels from center) ---------- */
    const g3 = (a, b) => Math.sqrt(-2 * Math.log(a + 1e-6)) * Math.cos(TAU * b); // gaussian from two uniforms
    function tnorm(n) { return maxT > minT ? (n.mtime - minT) / (maxT - minT) : .5; }

    function layout() {
      const nodes = G.nodes, NG = Math.max(groups.length, 1), f = st.form;
      labels = [];
      if (f === "cerebro") {
        const lobes = groups.map((_, k) => {
          const y = -0.95 + 1.5 * (k + .5) / NG, rad = Math.sqrt(Math.max(0, 1 - y * y)), th = k * GA * 1.7;
          return [Math.cos(th) * rad, y, Math.sin(th) * rad];
        });
        const npos = nodes.map((n, i) => {
          const r = rng(hash(n.id) ^ 77), L = lobes[gIndex[i]] || [0, -1, 0];
          let x = L[0] + g3(r(), r()) * .42, y = L[1] + g3(r(), r()) * .42, z = L[2] + g3(r(), r()) * .42;
          const m = Math.hypot(x, y, z) || 1, rr = R * (.6 + .36 * Math.pow(r(), .5));
          x = x / m * rr * 1.2; y = y / m * rr * .86; z = z / m * rr * .95;
          z += Math.sign(z || 1) * R * .05;
          if (y > R * .38) y = R * .38 + (y - R * .38) * .35;
          return [x, y, z];
        });
        for (let p = 0; p < P; p++) {
          const [x, y, z] = npos[pNode[p]];
          if (isCore[p]) { tx[p] = x; ty[p] = y; tz[p] = z; continue; }
          const u = s3[p];
          if (u < .03) { const t = s1[p]; tx[p] = -R * .12 - Math.sin(t * 2.2) * R * .1 + g3(s2[p], u * 33) * R * .035; ty[p] = R * (.3 + t * .95); tz[p] = g3(u * 33, s1[p]) * R * .035; }
          else if (u < .065) { const a = s1[p] * TAU, b = Math.acos(2 * s2[p] - 1), rr = R * .24 * Math.cbrt((u - .03) / .035); tx[p] = -R * .62 + Math.sin(b) * Math.cos(a) * rr * 1.2; ty[p] = R * .45 + Math.cos(b) * rr * .7; tz[p] = Math.sin(b) * Math.sin(a) * rr; }
          else { const sp = R * .055; tx[p] = x + g3(s1[p], s2[p]) * sp; ty[p] = y + g3(s2[p], s3[p]) * sp; tz[p] = z + g3(s3[p], s1[p]) * sp; }
        }
        groups.forEach((g, k) => labels.push({ kind: "group", g: k, text: g.name }));
      } else if (f === "red") {
        const pos = forceLayout();
        for (let p = 0; p < P; p++) { const [x, y] = pos[pNode[p]]; tx[p] = x; ty[p] = y; tz[p] = 0; }
        nodes.map((n, i) => [n.deg, i]).sort((a, b) => b[0] - a[0]).slice(0, 14).forEach(([d, i]) => d && labels.push({ kind: "node", i, text: nodes[i].title }));
      } else if (f === "galaxia") {
        const rank = new Map();
        groups.forEach((_, k) => { const mem = nodes.map((n, i) => [n.mtime, i]).filter(([, i]) => gIndex[i] === k).sort((a, b) => a[0] - b[0]); mem.forEach(([, i], j) => rank.set(i, mem.length > 1 ? j / (mem.length - 1) : .5)); });
        const npos = nodes.map((n, i) => {
          const u = rank.get(i), r = rng(hash(n.id) ^ 9), k = gIndex[i];
          const ang = k / NG * TAU + u * 2.6 + g3(r(), r()) * .1, rr = R * (.14 + .95 * u);
          return [Math.cos(ang) * rr, g3(r(), r()) * R * .03, Math.sin(ang) * rr, u];
        });
        for (let p = 0; p < P; p++) {
          const [x, y, z, u] = npos[pNode[p]];
          if (isCore[p]) { tx[p] = x; ty[p] = y; tz[p] = z; continue; }
          if (s3[p] < .1) { const sp = R * .13; tx[p] = g3(s1[p], s2[p]) * sp; ty[p] = g3(s2[p], s3[p] * 10) * sp * .5; tz[p] = g3(s3[p] * 10, s1[p]) * sp; continue; }
          const sp = R * .028 * (1 + u * 1.5); tx[p] = x + g3(s1[p], s2[p]) * sp; ty[p] = y + g3(s2[p], s3[p]) * sp * .4; tz[p] = z + g3(s3[p], s1[p]) * sp;
        }
        groups.forEach((g, k) => labels.push({ kind: "group", g: k, text: g.name }));
      } else if (f === "clusters") {
        const cnt = groups.map(() => 0); for (let p = 0; p < P; p++) cnt[gIndex[pNode[p]]]++;
        const rad = cnt.map(c => Math.sqrt(c) * 3.2 + 6), circles = [];
        groups.map((_, k) => k).sort((a, b) => rad[b] - rad[a]).forEach(k => {
          for (let s = 0; ; s += .5) {
            const a = s * .55, d = s * 3.2, x = Math.cos(a) * d * 1.35, y = Math.sin(a) * d * .85;
            if (circles.every(c => Math.hypot(c.x - x, c.y - y) > c.r + rad[k] + 22)) { circles[k] = { x, y, r: rad[k] }; break; }
          }
        });
        let bx = 1, by = 1; circles.forEach(c => { bx = Math.max(bx, Math.abs(c.x) + c.r); by = Math.max(by, Math.abs(c.y) + c.r + 16); });
        const sc = Math.min((WE * .5 - 24) / bx, (H * .5 - 24) / by, 2.4);
        const members = groups.map(() => []); nodes.forEach((n, i) => members[gIndex[i]].push(i));
        const npos = new Array(nodes.length);
        members.forEach((m, k) => {
          m.sort((a, b) => nodes[b].deg - nodes[a].deg || nodes[b].size - nodes[a].size);
          const c = circles[k];
          m.forEach((i, j) => { const rr = c.r * .92 * Math.sqrt((j + .5) / m.length), a = j * GA; npos[i] = [(c.x + Math.cos(a) * rr) * sc, (c.y + Math.sin(a) * rr) * sc, c.r * sc / Math.sqrt(m.length + 1)]; });
          labels.push({ kind: "fixed", x: c.x * sc, y: (c.y - c.r) * sc - 8, text: `${groups[k].name} · ${groups[k].count}`, color: groups[k].color });
        });
        for (let p = 0; p < P; p++) {
          const [x, y, sp] = npos[pNode[p]];
          if (isCore[p]) { tx[p] = x; ty[p] = y; tz[p] = 0; continue; }
          const a = s1[p] * TAU, rr = Math.sqrt(s2[p]) * sp * .9; tx[p] = x + Math.cos(a) * rr; ty[p] = y + Math.sin(a) * rr; tz[p] = 0;
        }
      } else if (f === "rueda") {
        const band = R * .7 / NG;
        for (let p = 0; p < P; p++) {
          const i = pNode[p], k = gIndex[i], n = nodes[i];
          const ang = -Math.PI / 2 + TAU * .985 * tnorm(n) + (isCore[p] ? 0 : g3(s1[p], s2[p]) * .012);
          const base = R * .3 + band * (k + .5) + (rng(hash(n.id))() - .5) * band * .7;
          const rr = base + (isCore[p] ? 0 : g3(s2[p], s3[p]) * band * .12);
          tx[p] = Math.cos(ang) * rr; ty[p] = Math.sin(ang) * rr; tz[p] = 0;
        }
        for (let m = 0; m < 12; m++) { const t = minT + (maxT - minT) * m / 12, a = -Math.PI / 2 + TAU * .985 * m / 12; labels.push({ kind: "fixed", x: Math.cos(a) * R * 1.1, y: Math.sin(a) * R * 1.1, text: fmtDate(t), center: true, dim: true }); }
        labels.push({ kind: "rings", band, NG });
      } else if (f === "corriente") {
        const B = 46, w = WE * .84, h = H * .56, x0 = -w / 2;
        const cnt = Array.from({ length: B }, () => new Float32Array(NG));
        const nb = nodes.map(n => Math.min(B - 1, Math.floor(tnorm(n) * B)));
        for (let p = 0; p < P; p++) cnt[nb[pNode[p]]][gIndex[pNode[p]]]++;
        const smooth = cnt.map((_, b) => { const o = new Float32Array(NG); for (let d = -2; d <= 2; d++) { const c = cnt[clamp(b + d, 0, B - 1)], wt = [.1, .2, .4, .2, .1][d + 2]; for (let k = 0; k < NG; k++) o[k] += c[k] * wt; } return o.map(v => Math.pow(v, .62)); });
        const tot = smooth.map(c => c.reduce((a, v) => a + v, 0)), mx = Math.max(...tot, 1), sc = h / mx;
        const bandsY = smooth.map((c, b) => { let y = -tot[b] * sc / 2; return Array.from(c, v => { const y0 = y; y += v * sc; return [y0, y]; }); });
        for (let p = 0; p < P; p++) {
          const i = pNode[p], b = nb[i], k = gIndex[i], [y0, y1] = bandsY[b][k];
          const bx = x0 + (tnorm(nodes[i]) * B) / B * w;
          tx[p] = bx + (isCore[p] ? 0 : (s1[p] - .5) * w / B * 1.6); ty[p] = y0 + (isCore[p] ? .5 : s2[p]) * Math.max(y1 - y0, 1.5); tz[p] = 0;
        }
        for (let m = 0; m <= 6; m++) labels.push({ kind: "fixed", x: x0 + w * m / 6, y: h / 2 + 34, text: fmtDate(minT + (maxT - minT) * m / 6), center: true, dim: true });
        labels.push({ kind: "axis", x0, w, y: h / 2 + 18 });
        groups.forEach((g, k) => { let best = 0, bb = 0; smooth.forEach((c, b) => { if (c[k] > best) { best = c[k]; bb = b; } }); if (best * sc > 12) { const [y0, y1] = bandsY[bb][k]; labels.push({ kind: "fixed", x: x0 + w * (bb + .5) / B, y: (y0 + y1) / 2 + 4, text: g.name, center: true }); } });
      }
      morphT = 0;
    }

    function forceLayout() {
      const key = st.color + "|" + WE + "x" + H;
      if (forceCache[key]) return forceCache[key];
      const nodes = G.nodes, n = nodes.length, NG = Math.max(groups.length, 1);
      const r = rng(1234), x = new Float32Array(n), y = new Float32Array(n), vx = new Float32Array(n), vy = new Float32Array(n);
      const gc = groups.map((_, k) => [Math.cos(k / NG * TAU) * R * .55, Math.sin(k / NG * TAU) * R * .55]);
      nodes.forEach((_, i) => { const c = gc[gIndex[i]]; x[i] = c[0] + g3(r(), r()) * R * .2; y[i] = c[1] + g3(r(), r()) * R * .2; });
      const iters = clamp(Math.round(3e6 / (n * 30 + G.edges.length + 1)), 40, 220), K = Math.min(30, n - 1);
      for (let it = 0; it < iters; it++) {
        const cool = 1 - it / iters;
        for (let i = 0; i < n; i++) {
          for (let s = 0; s < K; s++) {
            const j = (r() * n) | 0; if (j === i) continue;
            const dx = x[i] - x[j], dy = y[i] - y[j], d2 = dx * dx + dy * dy + 4, f = 1400 / d2 * (n / K) * .08;
            vx[i] += dx * f; vy[i] += dy * f;
          }
          const c = gc[gIndex[i]]; vx[i] += (c[0] - x[i]) * .012; vy[i] += (c[1] - y[i]) * .012;
        }
        for (const [a, b] of G.edges) { const dx = x[b] - x[a], dy = y[b] - y[a], d = Math.hypot(dx, dy) + .01, f = (d - 34) / d * .05; vx[a] += dx * f; vy[a] += dy * f; vx[b] -= dx * f; vy[b] -= dy * f; }
        for (let i = 0; i < n; i++) { vx[i] = clamp(vx[i] * .6, -30, 30); vy[i] = clamp(vy[i] * .6, -30, 30); x[i] += vx[i] * cool; y[i] += vy[i] * cool; }
      }
      let bx = 1, by = 1; for (let i = 0; i < n; i++) { bx = Math.max(bx, Math.abs(x[i])); by = Math.max(by, Math.abs(y[i])); }
      const sc = Math.min((WE * .46) / bx, (H * .42) / by, 3);
      return (forceCache[key] = Array.from({ length: n }, (_, i) => [x[i] * sc, y[i] * sc]));
    }

    /* ---------- render ---------- */
    function resize() {
      const b = root.getBoundingClientRect();
      dpr = Math.min(devicePixelRatio || 1, 2); W = Math.max(b.width, 50); H = Math.max(b.height, 50);
      cv.width = W * dpr; cv.height = H * dpr;
      WE = W - 2 * panelOff();
      R = Math.min(WE * (opts.compact ? .4 : .38), H * .4);
      if (G.nodes.length) layout();
    }

    function frame(t) {
      raf = 0;
      if (!alive) return;
      const dt = Math.min(64, t - (lastT || t)); lastT = t;
      const f = st.form, d3 = D3.has(f);
      yawT = d3 ? yawT : 0;
      if (d3 && st.spin && !dragging) yawT += spinV * dt / 16;
      yaw += (yawT - yaw) * (reduce ? 1 : .08);
      pitch += ((f === "galaxia" ? .95 : f === "cerebro" ? .12 : 0) + (d3 ? pitchT - .18 : 0) - pitch) * (reduce ? 1 : .08);
      orbitAmt += ((f === "red" ? 1 : 0) - orbitAmt) * .06;
      linkAmt += ((st.links && LINKED.has(f) ? 1 : 0) - linkAmt) * .08;
      morphT = Math.min(1, morphT + dt / 1400);

      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.globalCompositeOperation = "source-over";
      ctx.clearRect(0, 0, W, H);
      const ox = W / 2 + panX + panelOff(), oy = H / 2 + panY;
      const cyw = Math.cos(yaw), syw = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch), FOC = 900;
      const ease = reduce ? 1 : .075, time = t / 1000;
      for (let p = 0; p < P; p++) {
        const k = clamp((morphT - delay[p]) / (1 - .35), 0, 1);
        if (k > 0 || reduce) { const e = reduce ? 1 : ease * (.4 + k); cx[p] += (tx[p] - cx[p]) * e; cy[p] += (ty[p] - cy[p]) * e; cz[p] += (tz[p] - cz[p]) * e; }
        let x = cx[p], y = cy[p], z = cz[p];
        if (orbitAmt > .01 && orb[p]) { const a = s2[p] * TAU + time * (.4 + s1[p] * .9) * (s3[p] > .5 ? 1 : -1); x += Math.cos(a) * orb[p] * orbitAmt; y += Math.sin(a) * orb[p] * orbitAmt; }
        const x1 = x * cyw + z * syw, z1 = -x * syw + z * cyw;
        const y2 = y * cp - z1 * sp, z2 = y * sp + z1 * cp;
        const s = FOC / (FOC + z2) * zoom;
        px[p] = ox + x1 * s; py[p] = oy + y2 * s; ps[p] = s;
      }
      for (let i = 0; i < G.nodes.length; i++) { const c = coreOf[i]; sx[i] = px[c]; sy[i] = py[c]; sd[i] = ps[c]; }

      ctx.globalCompositeOperation = "lighter";
      if (labels.some(l => l.kind === "rings")) {
        const L = labels.find(l => l.kind === "rings");
        ctx.strokeStyle = "rgba(120,170,210,.08)"; ctx.lineWidth = 1;
        for (let k = 0; k <= L.NG; k++) { ctx.beginPath(); ctx.arc(ox, oy, (R * .3 + L.band * k) * zoom, 0, TAU); ctx.stroke(); }
        for (let m = 0; m < 12; m++) { const a = -Math.PI / 2 + TAU * .985 * m / 12; ctx.beginPath(); ctx.moveTo(ox + Math.cos(a) * R * .28 * zoom, oy + Math.sin(a) * R * .28 * zoom); ctx.lineTo(ox + Math.cos(a) * R * 1.02 * zoom, oy + Math.sin(a) * R * 1.02 * zoom); ctx.stroke(); }
      }
      const axis = labels.find(l => l.kind === "axis");
      if (axis) { ctx.strokeStyle = "rgba(120,170,210,.18)"; ctx.beginPath(); ctx.moveTo(ox + axis.x0 * zoom, oy + axis.y * zoom); ctx.lineTo(ox + (axis.x0 + axis.w) * zoom, oy + axis.y * zoom); ctx.stroke(); }

      // synapses
      if (linkAmt > .02 && G.edges.length) {
        ctx.lineWidth = 1;
        const lim = Math.min(G.edges.length, 5000);
        for (let e = 0; e < lim; e++) {
          const [a, b] = G.edges[e];
          const al = (hover >= 0 ? (a === hover || b === hover ? .55 : .02) : .09 * (hl ? Math.min(hl[a], hl[b]) : 1)) * linkAmt;
          if (al < .01) continue;
          ctx.strokeStyle = nodeColor[a]; ctx.globalAlpha = al;
          const mx = (sx[a] + sx[b]) / 2, my = (sy[a] + sy[b]) / 2, dx = sx[b] - sx[a], dy = sy[b] - sy[a];
          ctx.beginPath(); ctx.moveTo(sx[a], sy[a]); ctx.quadraticCurveTo(mx - dy * .15, my + dx * .15, sx[b], sy[b]); ctx.stroke();
        }
        ctx.globalAlpha = 1;
      }

      // particles, batched by colour
      let cur = -1;
      for (let q = 0; q < P; q++) {
        const p = order[q], i = pNode[p], c = colorIdx[i];
        if (c !== cur) { cur = c; ctx.fillStyle = api.colors[c]; }
        const depth = clamp((ps[p] / zoom - .55) / .9, .15, 1);
        const a = (hl ? hl[i] : 1) * (d3 ? .25 + depth * .75 : .85);
        if (isCore[p]) continue;
        ctx.globalAlpha = a * .8;
        const z = (opts.compact ? 1.1 : 1.3) * (d3 ? .6 + depth * .7 : 1) * Math.min(zoom, 2);
        ctx.fillRect(px[p] - z / 2, py[p] - z / 2, z, z);
      }
      for (let i = 0; i < G.nodes.length; i++) {
        const sz = (6 + Math.min(G.nodes[i].deg, 12) * 1.3) * clamp(sd[i], .5, 2.2) * (i === hover ? 2 : 1);
        ctx.globalAlpha = (hl ? hl[i] : 1) * (d3 ? clamp((sd[i] / zoom - .55) / .9, .2, 1) : 1);
        ctx.drawImage(sprites[colorIdx[i]], sx[i] - sz / 2, sy[i] - sz / 2, sz, sz);
      }

      // pulses travelling along links
      if (st.pulses && linkAmt > .5 && G.edges.length && visible) {
        const want = Math.min(G.edges.length / 25, 5) * dt / 16;
        for (let k = 0; k < want; k++) if (Math.random() < want / Math.ceil(want)) {
          let e;
          if (hover >= 0 && G.nodes[hover].nb.length && Math.random() < .7) { const j = G.nodes[hover].nb[(Math.random() * G.nodes[hover].nb.length) | 0]; e = [hover, j]; }
          else { const ed = G.edges[(Math.random() * G.edges.length) | 0]; e = Math.random() < .5 ? ed : [ed[1], ed[0]]; }
          pulses.push({ a: e[0], b: e[1], t0: t, d: 700 + Math.random() * 900 });
        }
        if (pulses.length > 400) pulses.splice(0, pulses.length - 400);
        pulses = pulses.filter(pu => {
          const k = (t - pu.t0) / pu.d; if (k >= 1) return false;
          const { a, b } = pu, mx = (sx[a] + sx[b]) / 2, my = (sy[a] + sy[b]) / 2, dx = sx[b] - sx[a], dy = sy[b] - sy[a];
          const cxq = mx - dy * .15, cyq = my + dx * .15, u = 1 - k;
          const x = u * u * sx[a] + 2 * u * k * cxq + k * k * sx[b], y = u * u * sy[a] + 2 * u * k * cyq + k * k * sy[b];
          ctx.globalAlpha = Math.sin(k * Math.PI) * (hl ? Math.max(hl[a], hl[b]) : 1);
          ctx.drawImage(sprites[colorIdx[a]], x - 6, y - 6, 12, 12);
          return true;
        });
      } else if (pulses.length) pulses = [];
      ctx.globalAlpha = 1;

      // labels
      ctx.globalCompositeOperation = "source-over";
      if (st.labels && morphT > .5) {
        ctx.font = `${opts.compact ? 10 : 11}px ui-monospace,Menlo,Consolas,monospace`; ctx.textBaseline = "middle";
        const la = clamp((morphT - .5) * 3, 0, 1);
        const gpos = groups.map(() => [0, 0, 0]);
        if (labels.some(l => l.kind === "group")) for (let i = 0; i < G.nodes.length; i++) { const g = gpos[gIndex[i]]; g[0] += sx[i]; g[1] += sy[i]; g[2]++; }
        for (const l of labels) {
          let x, y, text = l.text, color = "rgba(214,234,248,.85)", center = l.center;
          if (l.kind === "group") { const g = gpos[l.g]; if (!g[2] || groups[l.g].count < 2) continue; x = g[0] / g[2]; y = g[1] / g[2]; color = groups[l.g].color; center = true; }
          else if (l.kind === "node") { x = sx[l.i] + 9; y = sy[l.i]; }
          else if (l.kind === "fixed") { x = ox + l.x * zoom; y = oy + l.y * zoom; if (l.color) color = l.color; }
          else continue;
          if (text.length > 26) text = text.slice(0, 25) + "…";
          const w = ctx.measureText(text).width;
          if (center) x -= w / 2;
          ctx.globalAlpha = la * (l.dim ? .55 : 1);
          if (l.kind !== "fixed" || !l.dim) { ctx.fillStyle = "rgba(3,6,10,.62)"; ctx.fillRect(x - 4, y - 8, w + 8, 16); }
          ctx.fillStyle = color; ctx.fillText(text, x, y + .5);
        }
        ctx.globalAlpha = 1;
      }
      schedule();
    }
    function schedule() { if (!raf && alive && visible) raf = requestAnimationFrame(frame); }

    /* ---------- interaction ---------- */
    let dragging = false, dragX = 0, dragY = 0, moved = 0;
    function nearest(x, y) {
      let best = -1, bd = 196;
      for (let i = 0; i < G.nodes.length; i++) { const d = (sx[i] - x) ** 2 + (sy[i] - y) ** 2; if (d < bd && (!hl || hl[i] > .5 || hover >= 0)) { bd = d; best = i; } }
      return best;
    }
    function showTip(i, x, y) {
      if (i < 0) { tip.classList.remove("on"); return; }
      const n = G.nodes[i];
      tip.innerHTML = `<b>${esc(n.title)}</b><small>${esc(groups[gIndex[i]].name)} · ${n.deg} enlace${n.deg === 1 ? "" : "s"}${n.mtime ? " · " + fmtDay(n.mtime) : ""}</small><small>${esc(n.id)}</small>${opts.onOpen ? '<small style="color:#7fe6ff">clic para abrir</small>' : ""}`;
      const tw = tip.offsetWidth, th = tip.offsetHeight;
      tip.style.left = clamp(x + 14, 6, W - tw - 6) + "px"; tip.style.top = clamp(y + 14, 6, H - th - 6) + "px";
      tip.classList.add("on");
    }
    const loc = e => { const b = cv.getBoundingClientRect(); return [e.clientX - b.left, e.clientY - b.top]; };
    cv.addEventListener("pointerdown", e => { dragging = true; moved = 0; [dragX, dragY] = [e.clientX, e.clientY]; cv.classList.add("drag"); cv.setPointerCapture && cv.setPointerCapture(e.pointerId); });
    cv.addEventListener("pointermove", e => {
      const [x, y] = loc(e);
      if (dragging) {
        const dx = e.clientX - dragX, dy = e.clientY - dragY; [dragX, dragY] = [e.clientX, e.clientY]; moved += Math.abs(dx) + Math.abs(dy);
        if (D3.has(st.form)) { yawT += dx * .008; pitchT = clamp(pitchT + dy * .005, -.6, 1.1); } else { panX += dx; panY += dy; }
        return;
      }
      const i = nearest(x, y);
      if (i !== hover) { hover = i; computeHL(); }
      cv.classList.toggle("hot", i >= 0); showTip(i, x, y);
    });
    const endDrag = e => {
      if (!dragging) return; dragging = false; cv.classList.remove("drag");
      if (moved < 6 && e.type === "pointerup") { const [x, y] = loc(e); const i = nearest(x, y); if (i >= 0) { if (opts.onOpen) opts.onOpen(G.nodes[i].id); else { hover = i; computeHL(); showTip(i, x, y); } } }
    };
    cv.addEventListener("pointerup", endDrag); cv.addEventListener("pointercancel", endDrag);
    cv.addEventListener("pointerleave", () => { if (!dragging) { hover = -1; computeHL(); showTip(-1); cv.classList.remove("hot"); } });
    cv.addEventListener("wheel", e => { if (!(e.ctrlKey || e.metaKey) && opts.compact) return; e.preventDefault(); zoom = clamp(zoom * (e.deltaY < 0 ? 1.1 : .9), .4, 5); }, { passive: false });
    cv.tabIndex = 0;
    cv.addEventListener("keydown", e => {
      const i = FORMS.findIndex(([k]) => k === st.form);
      if (e.key === "ArrowRight" || e.key === "ArrowLeft") { e.preventDefault(); api.setForm(FORMS[(i + (e.key === "ArrowRight" ? 1 : FORMS.length - 1)) % FORMS.length][0]); }
      if (e.key === "+" || e.key === "=") zoom = clamp(zoom * 1.2, .4, 5);
      if (e.key === "-") zoom = clamp(zoom / 1.2, .4, 5);
    });

    const ro = new ResizeObserver(() => { resize(); schedule(); });
    ro.observe(root);
    const io = new IntersectionObserver(es => { visible = es.some(e => e.isIntersecting) && !document.hidden; if (visible) { lastT = 0; schedule(); } });
    io.observe(root);
    const onVis = () => { visible = !document.hidden; if (visible) { lastT = 0; schedule(); } };
    document.addEventListener("visibilitychange", onVis);

    function setColor(c) { st.color = c; st.focus = null; forceCache = {}; regroup(); computeHL(); layout(); syncButtons(); if (opts.onChange) opts.onChange({ form: st.form, color: st.color }); }

    const api = {
      colors: [],
      setData(data) { G = prepare(data); hover = -1; hl = null; pulses = []; build(); resize(); computeHL(); syncButtons(); schedule(); return api; },
      setForm(f) { if (!FORMS.some(([k]) => k === f)) return api; st.form = f; zoom = 1; panX = panY = 0; pitchT = .18; layout(); syncButtons(); schedule(); if (opts.onChange) opts.onChange({ form: st.form, color: st.color }); return api; },
      setColor(c) { setColor(c); return api; },
      highlight(q) { st.q = (q || "").toLowerCase(); if (searchEl) searchEl.value = q || ""; computeHL(); return api; },
      get form() { return st.form; },
      get stats() { return { notes: G.nodes.length, links: G.edges.length, particles: P, groups: groups.length }; },
      destroy() { alive = false; ro.disconnect(); io.disconnect(); document.removeEventListener("visibilitychange", onVis); if (raf) cancelAnimationFrame(raf); host.innerHTML = ""; },
    };
    api.setData(opts.data || { nodes: [], edges: [] });
    return api;
  }

  /* sample vault for demos: spaces with their own rhythm over ~2 years, links mostly inside a space */
  function demo(n, seed) {
    const r = rng(seed || 42), now = Date.UTC(2026, 10, 20) / 1000, DAY = 86400;
    const spaces = [
      ["mi-app", "Projects", 0.24, 60, ["Login con Google", "Pagos", "API REST", "Despliegue", "Tests e2e", "Caché", "Onboarding", "Errores 500", "Migración DB", "Notificaciones"]],
      ["tienda", "Projects", 0.16, 300, ["Checkout", "Inventario", "Envíos", "Cupones", "Stripe", "Catálogo", "SEO", "Reseñas"]],
      ["blog", "Projects", 0.1, 420, ["Ideas de posts", "Calendario", "Newsletter", "Analítica", "Borradores"]],
      ["Knowledge", "Knowledge", 0.18, 700, ["Python", "SQLite FTS5", "Diseño de APIs", "Seguridad web", "Accesibilidad", "Rendimiento", "Git", "Docker", "Prompts"]],
      ["Inbox", "Inbox", 0.12, 30, ["Idea suelta", "Pendiente", "Link guardado", "Reunión", "Captura"]],
      ["juego", "Projects", 0.1, 200, ["Física", "Niveles", "Sprites", "Sonido", "Guardado"]],
      ["Archive", "Archive", 0.1, 730, ["Viejo plan", "Prototipo", "Notas 2025"]],
    ];
    const kinds = ["", "", "", "decisions", "lessons", "tasks", "log", "brief"];
    const nodes = [], edges = [];
    spaces.forEach(([name, folder, share, span, topics]) => {
      const count = Math.max(3, Math.round(n * share)), start = nodes.length;
      const burst = r() * span;
      for (let i = 0; i < count; i++) {
        const age = r() < .35 ? Math.abs(burst + (r() - .5) * 40) : r() * span;
        const t = topics[(r() * topics.length) | 0];
        const id = folder === "Projects" ? `Projects/${name}/${t} ${i}.md` : `${folder}/${t} ${i}.md`;
        nodes.push({ id, title: `${t}${i > topics.length ? " " + i : ""}`, project: folder === "Projects" ? name : "", folder, kind: kinds[(r() * kinds.length) | 0], mtime: now - age * DAY - r() * DAY, size: 120 + Math.pow(r(), 2) * 6000 });
      }
      for (let i = start + 1; i < nodes.length; i++) {
        const links = r() < .7 ? 1 + ((r() * 2.4) | 0) : 0;
        for (let k = 0; k < links; k++) { const j = start + ((r() * (i - start)) | 0); if (j !== i) edges.push({ source: nodes[i].id, target: nodes[j].id }); }
      }
    });
    for (let k = 0; k < n * .06; k++) { const a = nodes[(r() * nodes.length) | 0], b = nodes[(r() * nodes.length) | 0]; if (a !== b) edges.push({ source: a.id, target: b.id }); }
    return { nodes, edges };
  }

  window.Neuronas = { mount, demo, FORMS };
})();
