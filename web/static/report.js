"use strict";
(function () {
  var $ = PS.$, el = PS.el;
  var SERIES = ["retail Pettah", "wholesale Pettah", "retail Narahenpita"];
  var PERIODS = ["daily", "weekly", "monthly", "annual"];
  var LABELS = { daily: "Daily", weekly: "Weekly", monthly: "Monthly", annual: "Annual" };
  var state = { series: SERIES[0], period: "weekly" };
  var seq = 0;

  function message(text) { var m = $("msg"); m.hidden = !text; m.textContent = text || ""; $("out").hidden = !!text; }
  function mean(a) { var v = a.filter(function (x) { return x != null; }); return v.length ? v.reduce(function (p, q) { return p + q; }, 0) / v.length : null; }
  function span(a) { return a[0] === a[1] ? PS.date(a[0], true) : PS.date(a[0]) + " to " + PS.date(a[1], true); }

  function drawChoices(id, values, current, label, change) {
    var box = $(id); box.textContent = "";
    values.forEach(function (value) {
      var b = el("button", null, label(value));
      b.type = "button"; b.setAttribute("aria-pressed", String(value === current));
      b.addEventListener("click", function () { change(value); });
      box.appendChild(b);
    });
  }

  function drawControls() {
    drawChoices("period", PERIODS, state.period, function (p) { return LABELS[p]; }, function (p) {
      state.period = p; drawControls(); load();
    });
    drawChoices("series", SERIES, state.series, function (s) { return PS.NAMES[s]; }, function (s) {
      state.series = s; drawControls(); load();
    });
  }

  function movers(items, name, periodLabel) {
    var rows = items.filter(function (r) { return r.dambulla.change_pct != null && r.colombo.change_pct != null; })
      .sort(function (a, b) { return Math.abs(b.dambulla.change_pct) - Math.abs(a.dambulla.change_pct); });
    var box = $("movers"); box.textContent = "";
    PS.responsive(box, function (W) {
      var phone = W < 520, L = phone ? 122 : 150, R = 44, rowH = 30, T = 8, B = 26, H = T + rows.length * rowH + B;
      var m = 0;
      rows.forEach(function (r) { m = Math.max(m, Math.abs(r.dambulla.change_pct), Math.abs(r.colombo.change_pct)); });
      var edge = Math.max(m * 1.05, 1), ticks = PS.ticks(-edge, edge, 4), step = ticks.length > 1 ? ticks[1] - ticks[0] : 1;
      while (ticks[ticks.length - 1] < edge) ticks.push(+(ticks[ticks.length - 1] + step).toFixed(6));
      var lo = ticks[0], hi = ticks[ticks.length - 1];
      var X = function (v) { return L + (v - lo) / (hi - lo) * (W - L - R); };
      box.appendChild(PS.legend([{ label: "Dambulla wholesale", color: "--dambulla" }, { label: name, color: "--colombo" }]));
      var svg = PS.s("svg", { width: W, height: H, viewBox: "0 0 " + W + " " + H, role: "img",
        "aria-label": "Bar chart of " + periodLabel.toLowerCase() + " price changes for Dambulla and " + name });
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
          svg.appendChild(PS.s("text", { x: v < 0 ? x1 - 5 : x1 + 5, y: y + p[2] + 9, "text-anchor": v < 0 ? "end" : "start", "font-size": 10.5, fill: "var(--ink-2)" }, PS.signed(v, 1)));
        });
        var hit = PS.s("rect", { x: 0, y: y, width: W, height: rowH, fill: "transparent" });
        hit.addEventListener("pointermove", function (e) {
          PS.tip(e.clientX, e.clientY, [PS.el("div", "t-d", r.item),
            PS.tipRow("--dambulla", PS.arrow(r.dambulla.change_pct) + PS.signed(r.dambulla.change_pct) + "%", "Dambulla " + PS.rs(r.dambulla.last) + " to " + PS.rs(r.dambulla.this)),
            PS.tipRow("--colombo", PS.arrow(r.colombo.change_pct) + PS.signed(r.colombo.change_pct) + "%", name + " " + PS.rs(r.colombo.last) + " to " + PS.rs(r.colombo.this))]);
        });
        hit.addEventListener("pointerleave", PS.hideTip); svg.appendChild(hit);
      });
      box.appendChild(svg);
    });
  }

  function multiples(items, name, windowDays) {
    var top = items.filter(function (r) { return r.dambulla.change_pct != null && r.colombo.change_pct != null; })
      .sort(function (a, b) { return Math.abs(b.dambulla.change_pct) - Math.abs(a.dambulla.change_pct); }).slice(0, 6);
    var box = $("multi"); box.textContent = "";
    top.forEach(function (r) {
      var idx = function (a) { var f = null; a.forEach(function (v) { if (f == null && v != null) f = v; }); return a.map(function (v) { return v == null || !f ? null : 100 * v / f; }); };
      var card = el("div", "sm"); card.appendChild(el("h3", null, r.item));
      var vals = el("div", "vals");
      vals.appendChild(el("span", null, "Dambulla " + PS.arrow(r.dambulla.change_pct) + PS.signed(r.dambulla.change_pct) + "%"));
      vals.appendChild(el("span", null, "Colombo " + PS.arrow(r.colombo.change_pct) + PS.signed(r.colombo.change_pct) + "%"));
      card.appendChild(vals);
      card.appendChild(PS.spark(240, 72, [{ values: idx(r.dambulla.spark), color: "--dambulla" }, { values: idx(r.colombo.spark), color: "--colombo" }], windowDays));
      var key = el("div", "vals"), a = el("span"), b = el("span");
      a.appendChild(el("span", "key d")); a.appendChild(document.createTextNode("Dambulla"));
      b.appendChild(el("span", "key c")); b.appendChild(document.createTextNode(name));
      key.appendChild(a); key.appendChild(b); card.appendChild(key); box.appendChild(card);
    });
  }

  function table(items, name, previousLabel, currentLabel) {
    var host = $("table"); host.textContent = "";
    var t = el("table", "data"), th = el("thead"), tr = el("tr");
    ["Item", "Dambulla " + previousLabel, "Dambulla " + currentLabel, "Change", name + " " + previousLabel, name + " " + currentLabel, "Change"].forEach(function (h) { tr.appendChild(el("th", null, h)); });
    th.appendChild(tr); t.appendChild(th);
    var tb = el("tbody");
    items.forEach(function (r) {
      var row = el("tr"), cell = function (v) { row.appendChild(el("td", null, v)); };
      cell(r.item); cell(PS.rs(r.dambulla.last)); cell(PS.rs(r.dambulla.this));
      cell(r.dambulla.change_pct == null ? "" : PS.arrow(r.dambulla.change_pct) + PS.signed(r.dambulla.change_pct) + "%");
      cell(PS.rs(r.colombo.last)); cell(PS.rs(r.colombo.this));
      cell(r.colombo.change_pct == null ? "" : PS.arrow(r.colombo.change_pct) + PS.signed(r.colombo.change_pct) + "%");
      tb.appendChild(row);
    });
    t.appendChild(tb); host.appendChild(t);
  }

  function wording(w) {
    if (w.period === "daily") return { previous: "previous day", current: "latest day", unit: "daily prices",
      intro: "The latest report day is " + span(w.current_period) + "; the previous report day is " + span(w.previous_period) + "." };
    if (w.period === "weekly") return { previous: "previous week", current: "current week", unit: "five daily prices in each week",
      intro: "The current five-report-day period is " + span(w.current_period) + "; the previous period is " + span(w.previous_period) + "." };
    if (w.period === "monthly") return { previous: "previous month", current: "current month", unit: "22 daily prices in each period",
      intro: "The current 22-report-day period is " + span(w.current_period) + "; the previous 22-report-day period is " + span(w.previous_period) + "." };
    return { previous: "earliest period", current: "recent period", unit: "22 daily prices in each period",
      intro: "The recent 22-report-day average (" + span(w.current_period) + ") is compared with the earliest 22-report-day average in the available one-year history (" + span(w.previous_period) + ", " + w.history_days + " report days available)." };
  }

  function render(w) {
    var name = PS.NAMES[w.series], items = w.items, label = LABELS[w.period], copy = wording(w);
    $("h1").textContent = label + " report: " + name;
    var dComplete = items.filter(function (r) { return r.dambulla.change_pct != null; });
    var cComplete = items.filter(function (r) { return r.colombo.change_pct != null; });
    var dm = mean(dComplete.map(function (r) { return r.dambulla.change_pct; }));
    var cm = mean(cComplete.map(function (r) { return r.colombo.change_pct; }));
    var up = items.filter(function (r) { return r.colombo.change_pct > 0; }).length;
    var down = items.filter(function (r) { return r.colombo.change_pct < 0; }).length;
    var unchanged = items.filter(function (r) { return r.colombo.change_pct === 0; }).length;
    $("lede").textContent = copy.intro + " Using only complete comparisons, Dambulla wholesale moved " + PS.signed(dm) + "% across " + dComplete.length + " items and " + name + " moved " + PS.signed(cm) + "% across " + cComplete.length + " (" + up + " higher, " + down + " lower, " + unchanged + " unchanged in Colombo).";
    $("print-note").textContent = "Price Signal " + label.toLowerCase() + " report, " + name + ", latest source report " + PS.date(w.report_date, true) + ". Source: Statistics Department, Central Bank of Sri Lanka, Daily Price Reports. Not advice.";
    $("movers-c").textContent = "Percentage change from the earlier comparison period to the later one. A blank means at least one required daily price was unavailable. Items are ordered by the size of the Dambulla movement.";
    $("multi-c").textContent = "Both markets start at 100 on the first available day shown, making their movement easier to compare. The shaded area marks the later comparison period.";
    $("table-c").textContent = "A value appears only when all " + copy.unit + " are available. This strict rule prevents partial periods from looking complete.";
    movers(items, name, label); multiples(items, name, w.window_days); table(items, name, copy.previous, copy.current);
  }

  function load() {
    var my = ++seq, csv = $("csv"), query = "series=" + encodeURIComponent(state.series) + "&period=" + state.period;
    $("print").disabled = false; csv.href = "/api/report.csv?" + query;
    PS.get("/api/report?" + query).then(function (w) {
      if (my !== seq) return;
      if (w.state !== "ok") { message("The report is not shown. " + w.reason); csv.hidden = true; $("print").hidden = true; $("h1").textContent = "Price reports"; $("lede").textContent = ""; return; }
      csv.hidden = false; $("print").hidden = false;
      if (!w.current_period || !w.items.length) { message("There is not enough complete price history for this report period yet."); csv.hidden = true; $("print").hidden = true; return; }
      message(""); render(w);
    }).catch(function (e) { if (my === seq) message("Could not load the report: " + e.message + ". Is the server running? Start it with: python3 web/server.py"); });
  }

  PS.start();
  $("print").addEventListener("click", function () { window.print(); });
  drawControls(); load();
})();
