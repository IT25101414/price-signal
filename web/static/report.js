"use strict";
(function () {
  var $ = PS.$, el = PS.el;
  var SERIES = ["retail Pettah", "wholesale Pettah", "retail Narahenpita"];
  var state = { series: SERIES[0] };
  var data = null;
  var seq = 0;

  function message(text) { var m = $("msg"); m.hidden = !text; m.textContent = text || ""; $("out").hidden = !!text; }
  function mean(a) { var v = a.filter(function (x) { return x != null; }); return v.length ? v.reduce(function (p, q) { return p + q; }, 0) / v.length : null; }

  function drawSeries() {
    var box = $("series");
    box.textContent = "";
    SERIES.forEach(function (s) {
      var b = el("button", null, PS.NAMES[s]);
      b.type = "button"; b.setAttribute("aria-pressed", String(s === state.series));
      b.addEventListener("click", function () { state.series = s; drawSeries(); load(); });
      box.appendChild(b);
    });
  }

  function movers(items, name) {
    var rows = items.filter(function (r) { return r.dambulla.change_pct != null && r.colombo.change_pct != null; })
      .sort(function (a, b) { return b.dambulla.change_pct - a.dambulla.change_pct; });
    var box = $("movers");
    PS.responsive(box, function (W) {
      var phone = W < 520, L = phone ? 122 : 150, R = 44, rowH = 30, T = 8, B = 26, H = T + rows.length * rowH + B;
      var m = 0;
      rows.forEach(function (r) { m = Math.max(m, Math.abs(r.dambulla.change_pct), Math.abs(r.colombo.change_pct)); });
      var ticks = PS.ticks(-m * 1.05, m * 1.05, 4), step = ticks.length > 1 ? ticks[1] - ticks[0] : 10;
      while (ticks[ticks.length - 1] < m * 1.05) ticks.push(+(ticks[ticks.length - 1] + step).toFixed(6));   // cover the biggest bar
      var lo = ticks[0], hi = ticks[ticks.length - 1];
      var X = function (v) { return L + (v - lo) / (hi - lo) * (W - L - R); };
      box.appendChild(PS.legend([{ label: "Dambulla wholesale", color: "--dambulla" }, { label: name, color: "--colombo" }]));
      var svg = PS.s("svg", { width: W, height: H, viewBox: "0 0 " + W + " " + H, role: "img",
        "aria-label": "Bar chart of the change in average price, this week against last week, for each item, Dambulla and " + name });
      ticks.forEach(function (v) {
        svg.appendChild(PS.s("line", { x1: X(v), x2: X(v), y1: T, y2: H - B, stroke: v === 0 ? "var(--ink-3)" : "var(--line)", "stroke-width": v === 0 ? 1.5 : 1 }));
        svg.appendChild(PS.s("text", { x: X(v), y: H - 8, "text-anchor": "middle", "font-size": 11, fill: "var(--ink-3)" }, PS.signed(v, 0) + "%"));
      });
      rows.forEach(function (r, i) {
        var y = T + i * rowH;
        svg.appendChild(PS.s("text", { x: L - 8, y: y + rowH / 2 + 4, "text-anchor": "end", "font-size": phone ? 11 : 12, fill: "var(--ink)" }, r.item));
        [[r.dambulla, "--dambulla", 4], [r.colombo, "--colombo", 15]].forEach(function (p) {
          var v = p[0].change_pct, x0 = X(0), x1 = X(v);
          svg.appendChild(PS.s("rect", { x: Math.min(x0, x1), y: y + p[2], width: Math.max(1, Math.abs(x1 - x0)), height: 10, rx: 3, fill: "var(" + p[1] + ")" }));
          var neg = v < 0;
          svg.appendChild(PS.s("text", { x: neg ? x1 - 5 : x1 + 5, y: y + p[2] + 9, "text-anchor": neg ? "end" : "start", "font-size": 10.5, fill: "var(--ink-2)" }, PS.signed(v, 1)));
        });
        var hit = PS.s("rect", { x: 0, y: y, width: W, height: rowH, fill: "transparent" });
        hit.addEventListener("pointermove", function (e) {
          PS.tip(e.clientX, e.clientY, [PS.el("div", "t-d", r.item),
            PS.tipRow("--dambulla", PS.arrow(r.dambulla.change_pct) + PS.signed(r.dambulla.change_pct) + "%", "Dambulla " + PS.rs(r.dambulla.last) + " to " + PS.rs(r.dambulla.this)),
            PS.tipRow("--colombo", PS.arrow(r.colombo.change_pct) + PS.signed(r.colombo.change_pct) + "%", name + " " + PS.rs(r.colombo.last) + " to " + PS.rs(r.colombo.this))]);
        });
        hit.addEventListener("pointerleave", PS.hideTip);
        svg.appendChild(hit);
      });
      box.appendChild(svg);
    });
  }

  function multiples(items, name) {
    var top = items.filter(function (r) { return r.dambulla.change_pct != null && r.colombo.change_pct != null; })
      .sort(function (a, b) { return Math.abs(b.dambulla.change_pct) - Math.abs(a.dambulla.change_pct); }).slice(0, 6);
    var box = $("multi");
    box.textContent = "";
    top.forEach(function (r) {
      var idx = function (a) { var f = null; a.forEach(function (v) { if (f == null && v != null) f = v; }); return a.map(function (v) { return v == null || !f ? null : 100 * v / f; }); };
      var card = el("div", "sm");
      card.appendChild(el("h3", null, r.item));
      var vals = el("div", "vals");
      vals.appendChild(el("span", null, "Dambulla " + PS.arrow(r.dambulla.change_pct) + PS.signed(r.dambulla.change_pct) + "%"));
      vals.appendChild(el("span", null, "Colombo " + PS.arrow(r.colombo.change_pct) + PS.signed(r.colombo.change_pct) + "%"));
      card.appendChild(vals);
      card.appendChild(PS.spark(240, 72, [{ values: idx(r.dambulla.spark), color: "--dambulla" }, { values: idx(r.colombo.spark), color: "--colombo" }], 5));
      var key = el("div", "vals");
      var a = el("span"), b = el("span");
      a.appendChild(el("span", "key d")); a.appendChild(document.createTextNode("Dambulla"));
      b.appendChild(el("span", "key c")); b.appendChild(document.createTextNode(name));
      key.appendChild(a); key.appendChild(b);
      card.appendChild(key);
      box.appendChild(card);
    });
  }

  function table(items, name) {
    var host = $("table");
    host.textContent = "";
    var t = el("table", "data"), th = el("thead"), tr = el("tr");
    ["Item", "Dambulla last week", "Dambulla this week", "Change", name + " last week", name + " this week", "Change"].forEach(function (h) { tr.appendChild(el("th", null, h)); });
    th.appendChild(tr); t.appendChild(th);
    var tb = el("tbody");
    items.forEach(function (r) {
      var row = el("tr");
      var cell = function (v) { row.appendChild(el("td", null, v)); };
      cell(r.item);
      cell(PS.rs(r.dambulla.last)); cell(PS.rs(r.dambulla.this)); cell(r.dambulla.change_pct == null ? "" : PS.arrow(r.dambulla.change_pct) + PS.signed(r.dambulla.change_pct) + "%");
      cell(PS.rs(r.colombo.last)); cell(PS.rs(r.colombo.this)); cell(r.colombo.change_pct == null ? "" : PS.arrow(r.colombo.change_pct) + PS.signed(r.colombo.change_pct) + "%");
      tb.appendChild(row);
    });
    t.appendChild(tb); host.appendChild(t);
  }

  function render(w) {
    var name = PS.NAMES[w.series], items = w.items;
    var span = function (a) { return PS.date(a[0]) + " to " + PS.date(a[1], true); };
    $("h1").textContent = "Weekly report: " + name;
    var dComplete = items.filter(function (r) { return r.dambulla.change_pct != null; });
    var cComplete = items.filter(function (r) { return r.colombo.change_pct != null; });
    var dm = mean(dComplete.map(function (r) { return r.dambulla.change_pct; })), cm = mean(cComplete.map(function (r) { return r.colombo.change_pct; }));
    var up = items.filter(function (r) { return r.colombo.change_pct > 0; }).length, down = items.filter(function (r) { return r.colombo.change_pct < 0; }).length;
    $("lede").textContent = "This week is the five report days " + span(w.this_week) + "; last week is " + span(w.last_week) + ". Using only items with all five prices in both weeks, Dambulla wholesale moved " +
      PS.signed(dm) + "% across " + dComplete.length + " items and " + name + " moved " + PS.signed(cm) + "% across " + cComplete.length + " (" + up + " higher, " + down + " lower in Colombo).";
    $("print-note").textContent = "Price Signal weekly report, " + name + ", report of " + PS.date(w.report_date, true) + ". Source: Statistics Department, Central Bank of Sri Lanka, Daily Price Reports. Not advice.";
    $("movers-c").textContent = "Change in the five-report-day average, this week against last week. A blank means at least one daily price needed for the comparison was unavailable. Items are sorted by the Dambulla move.";
    $("multi-c").textContent = "To compare the shapes, both markets start at 100 on the first day of last week. A value of 110 means 10% above that starting price. The shaded part is this week.";
    movers(items, name); multiples(items, name); table(items, name);
  }

  function load() {
    var my = ++seq;
    var csv = $("csv");
    $("print").disabled = false;
    csv.href = "/api/weekly.csv?series=" + encodeURIComponent(state.series);
    PS.get("/api/weekly?series=" + encodeURIComponent(state.series)).then(function (w) {
      if (my !== seq) return;
      data = w;
      if (w.state !== "ok") { message("The weekly report is not shown. " + w.reason); csv.hidden = true; $("print").hidden = true; $("h1").textContent = "Weekly report"; $("lede").textContent = ""; return; }
      csv.hidden = false; $("print").hidden = false;
      if (!w.items.length) { message("No price history is loaded in this copy of the site. Put prices_all.csv in the repository folder and run: python3 web/build_db.py"); csv.hidden = true; $("print").hidden = true; return; }
      message(""); render(w);
    }).catch(function (e) { if (my === seq) message("Could not load the report: " + e.message + ". Is the server running? Start it with: python3 web/server.py"); });
  }

  PS.start();
  $("print").addEventListener("click", function () { window.print(); });
  drawSeries(); load();
})();
