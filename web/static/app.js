"use strict";
(function () {
  var MINUS = "−";
  var state = { series: null, cards: [], status: null, q: "", scale: 10 };
  var $ = function (id) { return document.getElementById(id); };
  var NAMES = { "retail Pettah": "Retail, Pettah", "wholesale Pettah": "Wholesale, Pettah", "retail Narahenpita": "Retail, Narahenpita" };

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function signed(v, d) {
    if (v == null) return "";
    var s = Math.abs(v).toFixed(d == null ? 1 : d);
    return (v < 0 ? MINUS : v > 0 ? "+" : "") + s;
  }
  function rs(v) { return v == null ? "" : "Rs " + Math.round(v).toLocaleString("en-US"); }
  function get(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error(url + " returned " + r.status);
      return r.json();
    });
  }

  // ---------- theme ----------
  function applyTheme(t) { if (t) document.documentElement.setAttribute("data-theme", t); else document.documentElement.removeAttribute("data-theme"); }
  try { applyTheme(localStorage.getItem("ps-theme")); } catch (e) { /* storage blocked: follow the OS */ }
  $("theme").addEventListener("click", function () {
    var cur = document.documentElement.getAttribute("data-theme") ||
      (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    var next = cur === "dark" ? "light" : "dark";
    applyTheme(next);
    try { localStorage.setItem("ps-theme", next); } catch (e) { /* ignore */ }
  });

  // ---------- header ----------
  function renderStatus(s) {
    var box = $("status");
    box.setAttribute("data-state", s.state);
    box.setAttribute("aria-busy", "false");
    var n = state.cards.filter(function (c) { return c.status === "ok"; }).length;
    if (s.state === "ok") {
      $("headline").textContent = n ? n + " of " + state.cards.length + " items have an estimate" : "No item has a clear signal today";
      $("reason").textContent = "Based on the CBSL Daily Price Report of " + s.report_date_label + ". Each estimate compares Dambulla wholesale with a Colombo price.";
    } else {
      $("headline").textContent = s.state === "stale" ? "The data are too old" : "A newer report is not read yet";
      $("reason").textContent = s.reason;
    }
    var demo = $("demo");
    if (s.history_source === "synthetic") {
      demo.hidden = false;
      demo.textContent = "Demo data: the price history in this build is invented for testing the layout. The estimates are from cards.csv.";
    } else demo.hidden = true;
    $("foot").textContent = "Source: Statistics Department, Central Bank of Sri Lanka, Daily Price Reports. The Central Bank does not endorse this project or its findings. Database built " +
      (s.built_at_utc ? s.built_at_utc.replace("T", " ").replace("+00:00", " UTC") : "unknown") + ".";
  }

  function renderSeries(s) {
    var box = $("series");
    box.textContent = "";
    s.series.forEach(function (name) {
      var b = el("button", null, NAMES[name] || name);
      b.type = "button";
      b.setAttribute("role", "radio");
      b.setAttribute("aria-checked", String(name === state.series));
      b.addEventListener("click", function () { state.series = name; load(); });
      box.appendChild(b);
    });
  }

  // ---------- rows ----------
  function niceScale(cards) {
    var m = 0;
    cards.forEach(function (c) { if (c.status === "ok") m = Math.max(m, Math.abs(c.low_pct), Math.abs(c.high_pct)); });
    return Math.max(5, Math.ceil(m / 5) * 5);
  }
  function pos(v) { return (50 + (v / state.scale) * 50).toFixed(2) + "%"; }

  function ruler(c, cls) {
    var r = el("span", "ruler" + (cls ? " " + cls : ""));
    r.appendChild(el("span", "zero"));
    var bar = el("span", "bar");
    var lo = Math.min(c.low_pct, c.high_pct), hi = Math.max(c.low_pct, c.high_pct);
    bar.style.left = pos(lo);
    bar.style.width = (((hi - lo) / state.scale) * 50).toFixed(2) + "%";
    var mid = el("span", "mid");
    mid.style.left = pos(c.expected_change_pct);
    r.appendChild(bar); r.appendChild(mid);
    return r;
  }

  function tipText(c) {
    return c.item + ": middle " + signed(c.expected_change_pct) + "%, 80% range " + signed(c.low_pct) + " to " + signed(c.high_pct) + "%";
  }

  function renderRows() {
    var q = state.q.trim().toLowerCase();
    var cards = state.cards.filter(function (c) { return !q || c.item.toLowerCase().indexOf(q) >= 0; });
    var ok = cards.filter(function (c) { return c.status === "ok"; })
      .sort(function (a, b) { return a.expected_change_pct - b.expected_change_pct; });
    var no = cards.filter(function (c) { return c.status !== "ok"; });
    var rows = $("rows");
    rows.textContent = "";
    $("axishead").hidden = ok.length === 0;
    ok.forEach(function (c) {
      var li = el("li", "row");
      var b = el("button");
      b.type = "button";
      var name = el("span", "name", c.item);
      var p = el("span", "prices");
      var pd = el("span", "pr"); pd.appendChild(el("span", "key d")); pd.appendChild(document.createTextNode("Dambulla " + rs(c.dambulla_rs)));
      var pc = el("span", "pr"); pc.appendChild(el("span", "key c")); pc.appendChild(document.createTextNode("Colombo " + rs(c.colombo_rs)));
      p.appendChild(pd); p.appendChild(pc);
      name.appendChild(p);
      var num = el("span", "num");
      num.appendChild(el("b", null, (c.direction === "down" ? "▼ " : c.direction === "up" ? "▲ " : "") + signed(c.expected_change_pct) + "%"));
      num.appendChild(el("small", null, signed(c.low_pct) + " to " + signed(c.high_pct) + (c.signal ? ", " + c.signal + " signal" : "")));
      b.appendChild(name); b.appendChild(ruler(c)); b.appendChild(num);
      b.setAttribute("aria-label", tipText(c) + ". Open details.");
      b.addEventListener("click", function () { openDetail(c); });
      b.addEventListener("pointermove", function (e) { showTip(e.clientX, e.clientY, [tipText(c)]); });
      b.addEventListener("pointerleave", hideTip);
      li.appendChild(b);
      rows.appendChild(li);
    });
    var none = $("none");
    none.hidden = no.length === 0;
    $("none-title").textContent = state.status && state.status.state !== "ok" ? "Items with no figures shown" : "No estimate today";
    var ul = $("none-list");
    ul.textContent = "";
    var all = state.status && state.status.state !== "ok";
    ul.className = all ? "names" : "";
    no.forEach(function (c) {
      var li = el("li");
      li.appendChild(el("b", null, c.item));
      if (!all) li.appendChild(document.createTextNode(c.reason));
      ul.appendChild(li);
    });
  }

  // ---------- tooltip ----------
  var tip = $("tip");
  function showTip(x, y, lines, rowsHtml) {
    tip.textContent = "";
    lines.forEach(function (l) { tip.appendChild(el("div", null, l)); });
    if (rowsHtml) rowsHtml.forEach(function (n) { tip.appendChild(n); });
    tip.hidden = false;
    var w = tip.offsetWidth, h = tip.offsetHeight;
    tip.style.left = Math.min(window.innerWidth - w - 8, Math.max(8, x + 14)) + "px";
    tip.style.top = Math.max(8, Math.min(window.innerHeight - h - 8, y - h - 10)) + "px";
  }
  function hideTip() { tip.hidden = true; }

  // ---------- detail ----------
  function fact(label, value) {
    var f = el("div", "fact");
    f.appendChild(el("span", null, label));
    f.appendChild(el("b", null, value));
    return f;
  }

  function openDetail(c) {
    var d = $("detail");
    $("d-title").textContent = c.item;
    $("d-sub").textContent = (NAMES[state.series] || state.series) + " price compared with Dambulla wholesale. Report of " + state.status.report_date_label + ".";
    var body = $("d-body");
    body.textContent = "";
    var facts = el("div", "facts");
    facts.appendChild(fact("Dambulla wholesale", rs(c.dambulla_rs)));
    facts.appendChild(fact("Colombo price", rs(c.colombo_rs)));
    facts.appendChild(fact("Colombo vs its usual gap", signed(c.gap_vs_usual_pct) + "%"));
    facts.appendChild(fact("Middle estimate, 3 report days", (c.direction === "down" ? "▼ " : c.direction === "up" ? "▲ " : "") + signed(c.expected_change_pct) + "%"));
    body.appendChild(facts);
    body.appendChild(el("p", "note", "80% range for the change in the Colombo price: " + signed(c.low_pct) + " to " + signed(c.high_pct) + "% (scale " + MINUS + state.scale + "% to +" + state.scale + "%)."));
    body.appendChild(ruler(c, "big"));
    var holder = el("div");
    holder.appendChild(el("p", "note", "Loading price history"));
    body.appendChild(holder);
    if (!d.open) d.showModal();
    get("/api/items/" + encodeURIComponent(c.item) + "?series=" + encodeURIComponent(state.series)).then(function (r) {
      holder.textContent = "";
      if (!r.history.length) {
        holder.appendChild(el("p", "note", "No price history is loaded. Put prices_all.csv in the repo root and run: python3 web/build_db.py"));
        return;
      }
      if (r.history_source === "synthetic") holder.appendChild(el("p", "demo", "Demo data: this history is invented to test the chart."));
      holder.appendChild(chart(r.history, state.series));
    }).catch(function (e) { holder.textContent = ""; holder.appendChild(el("p", "note", "Could not load history: " + e.message)); });
  }

  var SVGNS = "http://www.w3.org/2000/svg";
  function s(tag, attrs, text) {
    var e = document.createElementNS(SVGNS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    return e;
  }
  function css(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }

  function chart(hist, seriesName) {
    var wrap = el("div", "chart-wrap");
    var dates = [], byDate = {};
    hist.forEach(function (h) {
      if (!byDate[h.report_date]) { byDate[h.report_date] = {}; dates.push(h.report_date); }
      byDate[h.report_date][h.series] = h.price_rs;
    });
    dates = dates.slice(-120);
    var S = [{ key: "wholesale Dambulla", label: "Dambulla", color: "--dambulla" }, { key: seriesName, label: "Colombo", color: "--colombo" }];
    var vals = [];
    dates.forEach(function (d) { S.forEach(function (x) { if (byDate[d][x.key] != null) vals.push(byDate[d][x.key]); }); });
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
    var pad = (hi - lo) * 0.08 || 1; lo = Math.max(0, lo - pad); hi += pad;
    var W = 640, H = 260, L = 48, R = 112, T = 12, B = 28;
    var X = function (i) { return L + (i / Math.max(1, dates.length - 1)) * (W - L - R); };
    var Y = function (v) { return T + (1 - (v - lo) / (hi - lo)) * (H - T - B); };

    var legend = el("div", "legend");
    S.forEach(function (x) { var i = el("span"); var k = el("i"); k.style.borderTopColor = "var(" + x.color + ")"; i.appendChild(k); i.appendChild(document.createTextNode(x.label)); legend.appendChild(i); });
    wrap.appendChild(legend);

    var svg = s("svg", { viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": "Line chart of Dambulla wholesale and Colombo prices over the last " + dates.length + " report days" });
    for (var t = 0; t <= 4; t++) {
      var v = lo + ((hi - lo) * t) / 4, y = Y(v);
      svg.appendChild(s("line", { x1: L, x2: W - R, y1: y, y2: y, stroke: "var(--line)", "stroke-width": 1 }));
      svg.appendChild(s("text", { x: L - 8, y: y + 4, "text-anchor": "end", "font-size": 11, fill: "var(--ink-3)" }, Math.round(v)));
    }
    [0, Math.floor((dates.length - 1) / 2), dates.length - 1].forEach(function (i) {
      svg.appendChild(s("text", { x: X(i), y: H - 8, "text-anchor": i === 0 ? "start" : i === dates.length - 1 ? "end" : "middle", "font-size": 11, fill: "var(--ink-3)" }, dates[i]));
    });
    var ends = [];
    S.forEach(function (x) {
      var pts = [];
      dates.forEach(function (d, i) { if (byDate[d][x.key] != null) pts.push(X(i).toFixed(1) + "," + Y(byDate[d][x.key]).toFixed(1)); });
      svg.appendChild(s("polyline", { points: pts.join(" "), fill: "none", stroke: "var(" + x.color + ")", "stroke-width": 2, "stroke-linejoin": "round" }));
      var last = dates[dates.length - 1];
      if (byDate[last][x.key] != null) ends.push({ x: x, y: Y(byDate[last][x.key]), v: byDate[last][x.key] });
    });
    if (ends.length === 2 && Math.abs(ends[0].y - ends[1].y) < 15) {
      var up = ends[0].y < ends[1].y ? 0 : 1;
      ends[up].ty = Math.min(ends[0].y, ends[1].y) - 7; ends[1 - up].ty = Math.max(ends[0].y, ends[1].y) + 7;
    }
    ends.forEach(function (e) {
      svg.appendChild(s("circle", { cx: X(dates.length - 1), cy: e.y, r: 4, fill: "var(" + e.x.color + ")", stroke: "var(--surface)", "stroke-width": 2 }));
      svg.appendChild(s("text", { x: W - R + 10, y: (e.ty != null ? e.ty : e.y) + 4, "font-size": 12, fill: "var(--ink)" }, e.x.label + " " + Math.round(e.v)));
    });
    var cross = s("line", { y1: T, y2: H - B, stroke: "var(--ink-3)", "stroke-width": 1, visibility: "hidden" });
    svg.appendChild(cross);
    var dots = S.map(function (x) { var c = s("circle", { r: 4.5, fill: "var(" + x.color + ")", stroke: "var(--surface)", "stroke-width": 2, visibility: "hidden" }); svg.appendChild(c); return c; });
    function at(clientX, clientY) {
      var r = svg.getBoundingClientRect();
      var px = ((clientX - r.left) / r.width) * W;
      var i = Math.round(((px - L) / (W - L - R)) * (dates.length - 1));
      i = Math.max(0, Math.min(dates.length - 1, i));
      var d = dates[i];
      cross.setAttribute("x1", X(i)); cross.setAttribute("x2", X(i)); cross.setAttribute("visibility", "visible");
      var rows = [];
      S.forEach(function (x, k) {
        var v = byDate[d][x.key];
        if (v == null) { dots[k].setAttribute("visibility", "hidden"); return; }
        dots[k].setAttribute("cx", X(i)); dots[k].setAttribute("cy", Y(v)); dots[k].setAttribute("visibility", "visible");
        var row = el("div", "t-row"); var key = el("i"); key.style.borderTopColor = "var(" + x.color + ")";
        row.appendChild(key); row.appendChild(el("b", null, rs(v))); row.appendChild(el("span", null, x.label));
        rows.push(row);
      });
      showTip(clientX, clientY, [], [Object.assign(el("div", "t-d", d))].concat(rows));
    }
    svg.addEventListener("pointermove", function (e) { at(e.clientX, e.clientY); });
    svg.addEventListener("pointerleave", function () { hideTip(); cross.setAttribute("visibility", "hidden"); dots.forEach(function (d) { d.setAttribute("visibility", "hidden"); }); });
    wrap.appendChild(svg);

    var det = el("details", "table");
    det.appendChild(el("summary", null, "Show the prices as a table"));
    var box = el("div", "tbl"), tb = el("table"), thead = el("tr");
    ["Report date", "Dambulla (Rs)", "Colombo (Rs)"].forEach(function (h) { thead.appendChild(el("th", null, h)); });
    tb.appendChild(thead);
    dates.slice().reverse().forEach(function (d) {
      var tr = el("tr");
      tr.appendChild(el("td", null, d));
      S.forEach(function (x) { tr.appendChild(el("td", null, byDate[d][x.key] != null ? byDate[d][x.key].toFixed(0) : "")); });
      tb.appendChild(tr);
    });
    box.appendChild(tb); det.appendChild(box); wrap.appendChild(det);
    return wrap;
  }

  // ---------- load ----------
  function load() {
    return Promise.all([get("/api/status"), get("/api/cards" + (state.series ? "?series=" + encodeURIComponent(state.series) : ""))])
      .then(function (r) {
        state.status = r[0]; state.cards = r[1].cards; state.series = r[1].series;
        state.scale = niceScale(state.cards);
        renderSeries(r[0]); renderStatus(r[0]); renderRows();
      })
      .catch(function (e) {
        $("status").setAttribute("aria-busy", "false");
        $("headline").textContent = "The page could not load the data";
        $("reason").textContent = e.message + ". Is the server running? Start it with: python3 web/server.py";
      });
  }
  $("q").addEventListener("input", function (e) { state.q = e.target.value; renderRows(); });
  $("detail").addEventListener("click", function (e) { if (e.target === this) this.close(); });
  $("detail").addEventListener("close", hideTip);
  load();
})();
