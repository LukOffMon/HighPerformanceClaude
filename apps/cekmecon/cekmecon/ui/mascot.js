/* Rollito — Çekmecón's pixel assistant: a little green bamboo-paper roll that tells you what is happening.
   Usage: const r = Rollito.mount(element, {size: 96}); r.say("Hello", "wave");
   Moods: idle, wave, work, think, read, write, celebrate, alert, sleep. No dependencies. */
(function () {
  const PAL = { D: "#145c34", G: "#2fae5f", L: "#8ee6a8", H: "#0b3a20", W: "#c8f7d4", E: "#06210f", K: "#3fd27a" };
  const LAYERS = {
    leaf: [".....GK..KG.....", "......GKKG......"],
    body: [
      "................", "................",
      "....LLLLLLLL....", "...LLLHHHHLLL...", "...DLLLLLLLLD...",
      "...GGWGGGGGGG...", "...GGWGGGGGGG...", "...GGWGGGGGGG...", "...GGGGGGGGGG...",
      "...GGGGGGGGGG...", "...GGGGGGGGGG...", "...DGGGGGGGGD...", "....DDDDDDDD...."],
    eyes: ["", "", "", "", "", "", "", "......E..E......", "......E..E......"],
    armL: ["", "", "", "", "", "", "", "", ".GG.............", ".G.............."],
    armR: ["", "", "", "", "", "", "", "", ".............GG.", "..............G."],
    legL: ["", "", "", "", "", "", "", "", "", "", "", "", "", ".....DD.........", ".....DD........."],
    legR: ["", "", "", "", "", "", "", "", "", "", "", "", "", ".........DD.....", ".........DD....."],
  };
  const CSS = `
.rb{position:relative;display:inline-block;line-height:0;user-select:none;-webkit-user-select:none}
.rb svg{width:100%;height:100%;overflow:visible;shape-rendering:crispEdges;image-rendering:pixelated}
.rb g{transform-box:fill-box}
.rb .rb-all{animation:rb-bob 2.4s steps(2,jump-none) infinite}
.rb .rb-eyes{transform-origin:center;animation:rb-blink 4.2s infinite}
.rb .rb-armL{transform-origin:100% 0}.rb .rb-armR{transform-origin:0 0}
.rb .rb-leaf{transform-origin:50% 100%;animation:rb-sway 3.6s ease-in-out infinite}
.rb-fx{position:absolute;inset:-14% -14% auto auto;font:700 14px/1 ui-monospace,Menlo,Consolas,monospace;color:#3fd27a;pointer-events:none;text-shadow:0 1px 0 #06210f}
.rb.wave .rb-armR{animation:rb-wave .5s steps(2,jump-none) infinite}
.rb.work .rb-armL{animation:rb-pump .32s steps(2,jump-none) infinite}.rb.work .rb-armR{animation:rb-pump .32s steps(2,jump-none) infinite reverse}
.rb.work .rb-legL{animation:rb-step .32s steps(2,jump-none) infinite}.rb.work .rb-legR{animation:rb-step .32s steps(2,jump-none) infinite .16s}
.rb.write .rb-armL,.rb.write .rb-armR{animation:rb-type .18s steps(2,jump-none) infinite}.rb.write .rb-armR{animation-delay:.09s}
.rb.read .rb-eyes{animation:rb-read 1.6s steps(2,jump-none) infinite}
.rb.think .rb-eyes{transform:translate(-1px,-1px);animation:none}
.rb.celebrate .rb-all{animation:rb-jump .5s steps(3,jump-none) infinite}.rb.celebrate .rb-armL{transform:rotate(60deg)}.rb.celebrate .rb-armR{transform:rotate(-60deg)}
.rb.alert .rb-all{animation:rb-shake .25s steps(2,jump-none) infinite}
.rb.sleep .rb-eyes{transform:scaleY(.15);animation:none}.rb.sleep .rb-all{animation:rb-bob 4s steps(2,jump-none) infinite}
@keyframes rb-bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-.5px)}}
@keyframes rb-blink{0%,92%,100%{transform:scaleY(1)}95%{transform:scaleY(.1)}}
@keyframes rb-sway{0%,100%{transform:rotate(-6deg)}50%{transform:rotate(6deg)}}
@keyframes rb-wave{0%,100%{transform:rotate(0)}50%{transform:rotate(-55deg)}}
@keyframes rb-pump{0%,100%{transform:translateY(0)}50%{transform:translateY(-1px)}}
@keyframes rb-step{0%,100%{transform:translateY(0)}50%{transform:translateY(-1px)}}
@keyframes rb-type{0%,100%{transform:translateY(0)}50%{transform:translateY(1px)}}
@keyframes rb-read{0%,100%{transform:translateX(-1px)}50%{transform:translateX(1px)}}
@keyframes rb-jump{0%,100%{transform:translateY(0)}50%{transform:translateY(-2px)}}
@keyframes rb-shake{0%,100%{transform:translateX(-.5px)}50%{transform:translateX(.5px)}}
@media (prefers-reduced-motion: reduce){.rb *{animation:none!important}}`;
  const FX = { think: "…", alert: "!", sleep: "z z", celebrate: "✦ ✧", write: "✎", read: "", work: "⚙", wave: "", idle: "" };

  function layer(name, rows) {
    let out = `<g class="rb-${name}">`;
    rows.forEach((row, y) => [...row].forEach((c, x) => {
      if (PAL[c]) out += `<rect x="${x}" y="${y}" width="1.02" height="1.02" fill="${PAL[c]}"/>`;
    }));
    return out + "</g>";
  }
  function svg() {
    return `<svg viewBox="0 0 16 16" aria-hidden="true"><g class="rb-all">${
      ["legL", "legR", "armL", "armR", "body", "leaf", "eyes"].map(n => layer(n, LAYERS[n])).join("")}</g></svg>`;
  }
  function injectCss() {
    if (document.getElementById("rb-css")) return;
    const s = document.createElement("style");
    s.id = "rb-css"; s.textContent = CSS; document.head.appendChild(s);
  }
  function mount(el, opts = {}) {
    injectCss();
    const size = opts.size || 96;
    const wrap = document.createElement("div");
    wrap.className = "rb idle";
    wrap.style.width = wrap.style.height = size + "px";
    wrap.innerHTML = svg() + '<span class="rb-fx"></span>';
    el.appendChild(wrap);
    const fx = wrap.querySelector(".rb-fx");
    let timer = null, sleepTimer = null;
    function mood(m, ms) {
      wrap.className = "rb " + (m || "idle");
      fx.textContent = FX[m] || "";
      clearTimeout(timer); clearTimeout(sleepTimer);
      if (m !== "idle" && m !== "sleep" && ms !== 0) timer = setTimeout(() => mood("idle"), ms || 3200);
      if (m === "idle" && opts.sleepAfter !== 0) sleepTimer = setTimeout(() => mood("sleep", 0), opts.sleepAfter || 90000);
    }
    mood("idle");
    return { el: wrap, mood, say(text, m, ms) { mood(m || "idle", ms); if (opts.onSay) opts.onSay(text, m); } };
  }
  window.Rollito = { mount };
})();
