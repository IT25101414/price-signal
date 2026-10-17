"use strict";
(function () {
  var MINUS = PS.MINUS;
  var state = { series: null, cards: [], status: null, q: "", direction: "all", signal: "all", sort: "expected", scale: 10 };
  var seq = 0;
  var $ = PS.$, el = PS.el, signed = PS.signed, rs = PS.rs, get = PS.get, NAMES = PS.NAMES;
  PS.initTheme();
  PS.menu();

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
      $("headline").textContent = s.state === "stale" ? "The data are too old" :
        (s.state === "source_unavailable" ? "The source could not be checked" : "A newer report is not read yet");
      $("reason").textContent = s.reason;
    }
    var demo = $("demo");
    if (s.history_source === "synthetic") {
      demo.hidden = false;
      demo.textContent = "Demo data: the price history in this build is invented for testing the layout. The estimates are from cards.csv.";
    } else demo.hidden = true;
    var meta = $("status-meta");
    meta.textContent = "";
    [
      ["Price data " + s.report_date_label, "neutral"],
      [s.state === "ok" ? "Source verified" : "Source withheld", s.state === "ok" ? "ok" : "warn"],
      [s.age_working_days + " working day" + (s.age_working_days === 1 ? "" : "s") + " old", s.age_working_days <= s.max_age_working_days ? "ok" : "warn"],
      [NAMES[state.series] || state.series || "Loading market", "neutral"],
      [s.history_source === "synthetic" ? "Synthetic history" : "Observed history", s.history_source === "synthetic" ? "warn" : "neutral"]
    ].forEach(function (x) {
      var chip = el("span", "meta-chip " + x[1], x[0]);
      meta.appendChild(chip);
    });
    PS.footer("Database built " + (s.built_at_utc ? s.built_at_utc.replace("T", " ").replace("+00:00", " UTC") : "unknown") + ".");
  }

  function renderSeries(s) {
    var box = $("series");
    box.textContent = "";
    s.series.forEach(function (name) {
      var b = el("button", null, NAMES[name] || name);
      b.type = "button";
      b.setAttribute("aria-pressed", String(name === state.series));
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

  function intervalWidth(c) { return c.high_pct - c.low_pct; }
  function signalLabel(v) { return v === "strong" ? "stronger signal" : v === "weak" ? "early signal" : "signal"; }

  function filteredCards() {
    var q = state.q.trim().toLowerCase();
    return state.cards.filter(function (c) {
      if (q && c.item.toLowerCase().indexOf(q) < 0) return false;
      if (state.direction !== "all" && c.direction !== state.direction) return false;
      if (state.signal !== "all" && c.signal !== state.signal) return false;
      return true;
    });
  }

  function kpi(label, value, note, tone) {
    var a = el("article", "kpi" + (tone ? " " + tone : ""));
    a.appendChild(el("p", "kpi-label", label));
    a.appendChild(el("strong", "kpi-value", value));
    a.appendChild(el("p", "kpi-note", note));
    return a;
  }

  function renderOverview() {
    var box = $("overview"), kpis = $("kpis");
    box.hidden = false;
    kpis.textContent = "";
    var ok = state.cards.filter(function (c) { return c.status === "ok"; });
    var strong = ok.filter(function (c) { return c.signal === "strong"; });
    var rises = ok.filter(function (c) { return c.direction === "up"; }).length;
    var falls = ok.filter(function (c) { return c.direction === "down"; }).length;
    var avgWidth = ok.length ? ok.reduce(function (n, c) { return n + intervalWidth(c); }, 0) / ok.length : null;
    var safe = state.status.state === "ok";
    kpis.appendChild(kpi("Items with estimates", safe ? ok.length + " / " + state.cards.length : "—", "Items with enough current information", "accent"));
    kpis.appendChild(kpi("Stronger signals", safe ? String(strong.length) : "—", "Items with the clearest signal today", "strong-tone"));
    kpis.appendChild(kpi("Expected direction", safe ? rises + " rise · " + falls + " fall" : "—", "A guide, not a recommendation"));
    kpis.appendChild(kpi("Average uncertainty", safe && avgWidth != null ? avgWidth.toFixed(1) + " points" : "—", "A smaller range means less uncertainty"));
    renderSignalMap(safe ? ok : []);
    renderWatchlist(safe ? ok : []);
    renderOps();
  }

  function renderSignalMap(cards) {
    var host = $("signal-map");
    host.textContent = "";
    if (!cards.length) {
      host.appendChild(el("p", "empty-panel", "No active estimates are available for the map."));
      return;
    }
    var W = 760, H = 310, L = 56, R = 18, T = 20, B = 44;
    var xAbs = Math.max(5, Math.ceil(Math.max.apply(null, cards.map(function (c) { return Math.abs(c.expected_change_pct); })) / 5) * 5);
    var maxU = Math.ceil(Math.max.apply(null, cards.map(intervalWidth)) / 10) * 10 || 10;
    var X = function (v) { return L + ((v + xAbs) / (2 * xAbs)) * (W - L - R); };
    var Y = function (v) { return H - B - (v / maxU) * (H - T - B); };
    var svg = PS.s("svg", { viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": "Chart comparing the expected price change and uncertainty for each item" });
    [-xAbs, -xAbs / 2, 0, xAbs / 2, xAbs].forEach(function (v) {
      var x = X(v);
      svg.appendChild(PS.s("line", { x1: x, x2: x, y1: T, y2: H - B, stroke: "var(--line)", "stroke-width": v === 0 ? 2 : 1 }));
      svg.appendChild(PS.s("text", { x: x, y: H - 16, "text-anchor": "middle", "font-size": 11, fill: "var(--ink-3)" }, signed(v, 0) + "%"));
    });
    [0, maxU / 2, maxU].forEach(function (v) {
      var y = Y(v);
      svg.appendChild(PS.s("line", { x1: L, x2: W - R, y1: y, y2: y, stroke: "var(--line)", "stroke-width": 1 }));
      svg.appendChild(PS.s("text", { x: L - 8, y: y + 4, "text-anchor": "end", "font-size": 11, fill: "var(--ink-3)" }, Math.round(v) + " pp"));
    });
    svg.appendChild(PS.s("text", { x: (L + W - R) / 2, y: H - 2, "text-anchor": "middle", "font-size": 12, fill: "var(--ink-2)" }, "Middle estimate: expected Colombo change"));
    cards.forEach(function (c) {
      var g = PS.s("g", { tabindex: "0", role: "button", "aria-label": tipText(c) + ". Uncertainty width " + intervalWidth(c).toFixed(1) + " percentage points. Open details." });
      var dot = PS.s("circle", { cx: X(c.expected_change_pct), cy: Y(intervalWidth(c)), r: c.signal === "strong" ? 8 : 6,
        fill: c.signal === "strong" ? "var(--accent)" : "var(--colombo)", opacity: c.signal === "strong" ? .95 : .72,
        stroke: "var(--surface)", "stroke-width": 2 });
      g.appendChild(dot);
      function show(e) { showTip(e.clientX || 40, e.clientY || 80, [tipText(c), "Uncertainty " + intervalWidth(c).toFixed(1) + " percentage points"]); }
      g.addEventListener("pointermove", show);
      g.addEventListener("pointerleave", hideTip);
      g.addEventListener("focus", function () { showTip(window.innerWidth / 2, 160, [tipText(c), "Uncertainty " + intervalWidth(c).toFixed(1) + " percentage points"]); });
      g.addEventListener("blur", hideTip);
      g.addEventListener("click", function () { openDetail(c); });
      g.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openDetail(c); } });
      svg.appendChild(g);
    });
    host.appendChild(svg);
  }

  function renderWatchlist(cards) {
    var list = $("watchlist");
    list.textContent = "";
    var ranked = cards.slice().sort(function (a, b) {
      var evidence = (b.signal === "strong") - (a.signal === "strong");
      return evidence || Math.abs(b.expected_change_pct) - Math.abs(a.expected_change_pct) || intervalWidth(a) - intervalWidth(b);
    }).slice(0, 5);
    $("watch-count").textContent = ranked.length + " shown";
    if (!ranked.length) {
      list.appendChild(el("li", "empty-panel", "No signals are available."));
      return;
    }
    ranked.forEach(function (c, i) {
      var li = el("li");
      var b = el("button"); b.type = "button";
      b.appendChild(el("span", "watch-rank", String(i + 1).padStart(2, "0")));
      var words = el("span", "watch-words");
      words.appendChild(el("b", null, c.item));
      words.appendChild(el("small", null, signalLabel(c.signal) + " · uncertainty " + intervalWidth(c).toFixed(1) + " points"));
      b.appendChild(words);
      b.appendChild(el("strong", "watch-value " + (c.direction || "flat"), PS.arrow(c.expected_change_pct) + signed(c.expected_change_pct) + "%"));
      b.addEventListener("click", function () { openDetail(c); });
      li.appendChild(b); list.appendChild(li);
    });
  }

  function renderOps() {
    var s = state.status, grid = $("ops-grid"), chip = $("ops-state");
    grid.textContent = "";
    var ok = s.state === "ok";
    chip.className = "status-chip " + (ok ? "ok" : "warn");
    chip.textContent = ok ? "All checks passed" : "Estimates are hidden";
    var checks = [
      ["Source website", ok ? "Latest listing checked" : "Needs attention", ok],
      ["Data freshness", s.age_working_days + " of " + s.max_age_working_days + " allowed working days", s.age_working_days <= s.max_age_working_days],
      ["Items checked", state.cards.length + " items for this market", state.cards.length > 0],
      ["Price history", s.history_source === "synthetic" ? "Made-up demonstration data" : "Observed source data", s.history_source !== "synthetic"],
      ["Website updated", s.built_at_utc ? s.built_at_utc.replace("T", " ").replace("+00:00", " UTC") : "Unknown", !!s.built_at_utc]
    ];
    checks.forEach(function (x) {
      var item = el("div", "op-item");
      item.appendChild(el("span", "op-icon " + (x[2] ? "pass" : "attention"), x[2] ? "✓" : "!"));
      var words = el("span"); words.appendChild(el("b", null, x[0])); words.appendChild(el("small", null, x[1])); item.appendChild(words);
      grid.appendChild(item);
    });
  }

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
    return c.item + ": best estimate " + signed(c.expected_change_pct) + "%, possible range " + signed(c.low_pct) + " to " + signed(c.high_pct) + "%";
  }

  function renderRows() {
    var cards = filteredCards();
    var ok = cards.filter(function (c) { return c.status === "ok"; });
    ok.sort(function (a, b) {
      if (state.sort === "name") return a.item.localeCompare(b.item);
      if (state.sort === "uncertainty") return intervalWidth(a) - intervalWidth(b);
      return a.expected_change_pct - b.expected_change_pct;
    });
    var no = cards.filter(function (c) { return c.status !== "ok"; });
    var rows = $("rows");
    rows.textContent = "";
    $("axishead").hidden = ok.length === 0;
    $("view-count").textContent = ok.length + " with estimates · " + no.length + " without estimates";
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
      num.appendChild(el("small", null, "Possible range " + signed(c.low_pct) + " to " + signed(c.high_pct) + (c.signal ? ", " + signalLabel(c.signal) : "")));
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

  function csvCell(v) {
    if (v == null) return "";
    var s = String(v);
    return /[\",\n]/.test(s) ? '"' + s.replaceAll('"', '""') + '"' : s;
  }

  function exportView() {
    if (!state.status || state.status.state !== "ok") return;
    var cards = filteredCards().filter(function (c) { return c.status === "ok"; });
    var fields = ["report_date", "item", "series", "signal", "direction", "expected_change_pct", "low_pct", "high_pct", "dambulla_rs", "colombo_rs", "gap_vs_usual_pct"];
    var lines = [fields.join(",")];
    cards.forEach(function (c) { lines.push(fields.map(function (f) { return csvCell(f === "series" ? state.series : (f === "report_date" ? state.status.report_date : c[f])); }).join(",")); });
    var blob = new Blob([lines.join("\n") + "\n"], { type: "text/csv;charset=utf-8" });
    var url = URL.createObjectURL(blob), a = document.createElement("a");
    a.href = url; a.download = "price-signal-" + state.series.replaceAll(" ", "-") + "-" + state.status.report_date + ".csv";
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  }

  function showTip(x, y, lines) { PS.tip(x, y, lines); }
  var hideTip = PS.hideTip;

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
    facts.appendChild(fact("Current gap compared with usual", signed(c.gap_vs_usual_pct) + "%"));
    facts.appendChild(fact("Best estimate for the following 3 report days", (c.direction === "down" ? "▼ " : c.direction === "up" ? "▲ " : "") + signed(c.expected_change_pct) + "%"));
    body.appendChild(facts);
    body.appendChild(el("p", "note", "Possible range for the Colombo price change: " + signed(c.low_pct) + " to " + signed(c.high_pct) + "%. In past testing, the real change fell inside a range like this about 8 times in 10. It is not a guaranteed best- or worst-case price. Chart scale: " + MINUS + state.scale + "% to +" + state.scale + "%."));
    body.appendChild(ruler(c, "big"));
    var holder = el("div");
    holder.appendChild(el("p", "note", "Loading price history"));
    body.appendChild(holder);
    var more = el("p", "note");
    var link = el("a", null, "Explore older prices of " + c.item);
    link.href = "/explore?item=" + encodeURIComponent(c.item) + "&series=" + encodeURIComponent(state.series);
    more.appendChild(link);
    body.appendChild(more);
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

  function chart(hist, seriesName) {
    var wrap = el("div", "chart-wrap");
    var dates = [], byDate = {};
    hist.forEach(function (h) {
      if (!byDate[h.report_date]) { byDate[h.report_date] = {}; dates.push(h.report_date); }
      byDate[h.report_date][h.series] = h.price_rs;
    });
    dates = dates.slice(-120);
    var d = dates.map(function (x) { return byDate[x]["wholesale Dambulla"]; }), c = dates.map(function (x) { return byDate[x][seriesName]; });
    var box = el("div", "chart-box");
    wrap.appendChild(box);
    PS.responsive(box, function (w) {
      box.appendChild(PS.legend([{ label: "Dambulla", color: "--dambulla" }, { label: "Colombo", color: "--colombo" }]));
      box.appendChild(PS.lineChart({ floorZero: true, width: w, dates: dates, aria: "Line chart of Dambulla wholesale and Colombo prices over the last " + dates.length + " report days",
        series: [{ label: "Dambulla", color: "--dambulla", values: d, fmt: rs }, { label: "Colombo", color: "--colombo", values: c, fmt: rs }] }));
    });
    wrap.appendChild(PS.table("Show the prices as a table", ["Report date", "Dambulla (Rs)", "Colombo (Rs)"],
      dates.map(function (x, i) { return [x, d[i] == null ? "" : d[i].toFixed(0), c[i] == null ? "" : c[i].toFixed(0)]; }).reverse()));
    return wrap;
  }

  // ---------- load ----------
  function load() {
    var my = ++seq;
    return Promise.all([get("/api/status"), get("/api/cards" + (state.series ? "?series=" + encodeURIComponent(state.series) : ""))])
      .then(function (r) {
        if (my !== seq) return;
        state.status = r[0]; state.cards = r[1].cards; state.series = r[1].series;
        state.scale = niceScale(state.cards);
        renderSeries(r[0]); renderStatus(r[0]); renderOverview(); renderRows();
        $("export").disabled = state.status.state !== "ok" || !state.cards.some(function (c) { return c.status === "ok"; });
      })
      .catch(function (e) {
        if (my !== seq) return;
        $("status").setAttribute("aria-busy", "false");
        $("headline").textContent = "The page could not load the data";
        $("reason").textContent = e.message + ". Is the server running? Start it with: python3 web/server.py";
      });
  }
  $("q").addEventListener("input", function (e) { state.q = e.target.value; renderRows(); });
  $("direction").addEventListener("change", function (e) { state.direction = e.target.value; renderRows(); });
  $("signal").addEventListener("change", function (e) { state.signal = e.target.value; renderRows(); });
  $("sort").addEventListener("change", function (e) { state.sort = e.target.value; renderRows(); });
  $("export").addEventListener("click", exportView);
  $("detail").addEventListener("click", function (e) { if (e.target === this) this.close(); });
  $("detail").addEventListener("close", hideTip);
  load();
})();
