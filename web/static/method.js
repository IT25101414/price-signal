"use strict";
(function () {
  var $ = PS.$, el = PS.el;
  var HNAME = { 1: "1 day", 3: "3 days", 5: "5 days" };
  var ORDER = ["wholesale Pettah", "retail Pettah", "retail Narahenpita"];

  /* Rows grouped by series. kind "dot": a dot with an optional interval. kind "bar": a bar from zero. */
  function rowsChart(box, o) {
    PS.responsive(box, function (W) {
      var phone = W < 520, L = phone ? 84 : 120, R = phone ? 96 : 190, gh = 24, rh = 24, T = 6, B = 26;
      var groups = o.groups, n = groups.length, rows = 0;
      groups.forEach(function (g) { rows += g.rows.length; });
      var H = T + n * gh + rows * rh + B;
      var lo = o.min, hi = o.max;
      var ticks = PS.ticks(lo, hi, 5);
      var X = function (v) { return L + (v - lo) / (hi - lo) * (W - L - R); };
      if (o.legend) box.appendChild(PS.legend(o.legend));
      var svg = PS.s("svg", { width: W, height: H, viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": o.aria });
      if (o.band) svg.appendChild(PS.s("rect", { x: X(o.band[0]), y: T, width: X(o.band[1]) - X(o.band[0]), height: H - T - B, fill: "var(--accent-soft)", opacity: 0.55 }));
      ticks.forEach(function (v) {
        svg.appendChild(PS.s("line", { x1: X(v), x2: X(v), y1: T, y2: H - B, stroke: v === 0 && o.zero ? "var(--ink-3)" : "var(--line)", "stroke-width": v === 0 && o.zero ? 1.5 : 1 }));
        svg.appendChild(PS.s("text", { x: X(v), y: H - 8, "text-anchor": "middle", "font-size": 11, fill: "var(--ink-3)" }, o.fmt(v)));
      });
      if (o.ref != null) svg.appendChild(PS.s("line", { x1: X(o.ref), x2: X(o.ref), y1: T, y2: H - B, stroke: "var(--ink-3)", "stroke-width": 1.5, "stroke-dasharray": "5 4" }));
      var y = T;
      groups.forEach(function (g) {
        svg.appendChild(PS.s("text", { x: 0, y: y + 16, "font-size": 13, "font-weight": 700, fill: "var(--ink)" }, g.title));
        y += gh;
        g.rows.forEach(function (r) {
          var cy = y + rh / 2;
          svg.appendChild(PS.s("text", { x: L - 8, y: cy + 4, "text-anchor": "end", "font-size": 12, fill: "var(--ink-2)" }, r.label));
          if (o.kind === "dot") {
            if (r.lo != null) svg.appendChild(PS.s("line", { x1: X(r.lo), x2: X(r.hi), y1: cy, y2: cy, stroke: "var(--accent)", "stroke-width": 2.5, "stroke-linecap": "round" }));
            svg.appendChild(PS.s("circle", { cx: X(r.v), cy: cy, r: 5, fill: "var(--accent)", stroke: "var(--surface)", "stroke-width": 2 }));
            svg.appendChild(PS.s("text", { x: Math.max(X(r.hi != null ? r.hi : r.v), X(r.v)) + 10, y: cy + 4, "font-size": 12, fill: "var(--ink)" }, r.text));
          } else {
            var x0 = X(0), x1 = X(r.v), a = { x: Math.min(x0, x1), y: cy - 7, width: Math.max(1, Math.abs(x1 - x0)), height: 14, rx: 3 };
            if (r.style === "ceiling") { a.fill = "none"; a.stroke = "var(--ink-3)"; a["stroke-width"] = 1.5; a["stroke-dasharray"] = "4 3"; }
            else a.fill = r.style === "own" ? "var(--ink-3)" : "var(--accent)";
            svg.appendChild(PS.s("rect", a));
            svg.appendChild(PS.s("text", { x: r.v < 0 ? x1 - 6 : x1 + 6, y: cy + 4, "text-anchor": r.v < 0 ? "end" : "start", "font-size": 12, fill: "var(--ink)" }, r.text));
          }
          var hit = PS.s("rect", { x: 0, y: y, width: W, height: rh, fill: "transparent" });
          hit.addEventListener("pointermove", function (e) { PS.tip(e.clientX, e.clientY, [g.title + ", " + r.label, r.tip]); });
          hit.addEventListener("pointerleave", PS.hideTip);
          svg.appendChild(hit);
          y += rh;
        });
      });
      box.appendChild(svg);
    });
  }

  function bySeries(list) { return ORDER.map(function (s) { return [s, list.filter(function (r) { return r.series === s; })]; }).filter(function (p) { return p[1].length; }); }
  function pct(v, d) { return PS.signed(v, d == null ? 1 : d) + "%"; }

  function gain(list) {
    if (!list.length) return;
    var groups = bySeries(list).map(function (p) {
      return { title: PS.NAMES[p[0]], rows: p[1].map(function (r) {
        return { label: HNAME[r.h] || r.h + " days", v: r.gain, lo: r.lo, hi: r.hi, text: PS.signed(r.gain) + "  (" + PS.signed(r.lo) + " to " + PS.signed(r.hi) + ")",
                 tip: "Gain " + PS.signed(r.gain) + " points, 95% interval " + PS.signed(r.lo) + " to " + PS.signed(r.hi) + "; placebo " + PS.signed(r.placebo) + "; " + r.items_positive + " of " + r.items + " items gain." };
      }) };
    });
    var lo = Math.min.apply(null, list.map(function (r) { return r.lo; })), hi = Math.max.apply(null, list.map(function (r) { return r.hi; }));
    rowsChart($("g-chart"), { kind: "dot", groups: groups, min: Math.min(-1, Math.floor(lo - 1)), max: Math.ceil(hi + 1), zero: true, fmt: function (v) { return PS.signed(v, 0); },
      aria: "Gain from adding the Dambulla price, by Colombo series and forecast horizon, with 95% intervals" });
    $("g-table").appendChild(PS.table("Show the numbers as a table", ["Colombo price", "Horizon", "Gain (points)", "95% interval", "Placebo", "Items with a gain", "Verdict"],
      list.map(function (r) { return [PS.NAMES[r.series], HNAME[r.h], PS.signed(r.gain), PS.signed(r.lo) + " to " + PS.signed(r.hi), PS.signed(r.placebo), r.items_positive + " of " + r.items, r.verdict]; })));
    var above = list.filter(function (r) { return r.lo > 0; }).length, plc = Math.max.apply(null, list.map(function (r) { return Math.abs(r.placebo); }));
    var weak = list.filter(function (r) { return r.verdict.indexOf("partly") === 0; });
    $("g-read").textContent = "In " + above + " of " + list.length + " cases the interval sits above zero. A placebo that swaps in another item's Dambulla price gives at most " + plc.toFixed(1) +
      " points, so the gain is specific to the item." + (weak.length ? " One case is only partly supported: " + weak.map(function (r) { return PS.NAMES[r.series] + " at " + HNAME[r.h]; }).join(", ") + ", where the gain fell in 2026 and fewer items gain." : "");
  }

  function calib(list) {
    if (!list.length) return;
    var groups = bySeries(list).map(function (p) {
      return { title: PS.NAMES[p[0]], rows: p[1].map(function (r) {
        return { label: HNAME[r.h] || r.h + " days", v: r.inside, text: r.inside.toFixed(1) + "% inside",
                 tip: r.inside.toFixed(1) + "% of " + r.tests.toLocaleString("en-US") + " outcomes inside the range. By year: " + Object.keys(r.by_year).map(function (y) { return y + " " + r.by_year[y] + "%"; }).join(", ") };
      }) };
    });
    rowsChart($("k-chart"), { kind: "dot", groups: groups, min: 70, max: 90, band: [75, 85], ref: 80, fmt: function (v) { return v + "%"; },
      aria: "Share of outcomes inside the stated 80 percent range, by Colombo series and horizon" });
    $("k-table").appendChild(PS.table("Show the numbers as a table", ["Colombo price", "Horizon", "Test cases", "Inside the range", "By year", "Average half-width"],
      list.map(function (r) { return [PS.NAMES[r.series], HNAME[r.h], r.tests.toLocaleString("en-US"), r.inside.toFixed(1) + "%", Object.keys(r.by_year).map(function (y) { return y + ": " + r.by_year[y] + "%"; }).join("  "), r.half_width.toFixed(1) + "%"]; })));
    var v = list.map(function (r) { return r.inside; }), out = [];
    list.forEach(function (r) { Object.keys(r.by_year).forEach(function (y) { if (r.by_year[y] < 75 || r.by_year[y] > 85) out.push(PS.NAMES[r.series] + " at " + HNAME[r.h] + " in " + y + " (" + r.by_year[y] + "%)"); }); });
    $("k-read").textContent = "Overall the range held between " + Math.min.apply(null, v).toFixed(1) + "% and " + Math.max.apply(null, v).toFixed(1) + "% of the time." +
      (out.length ? " One year is outside the band: " + out.join(", ") + "; we report it rather than hide it." : " Every year is inside the band.");
  }

  function decide(list) {
    if (!list.length) return;
    var groups = list.map(function (r) {
      return { title: PS.NAMES[r.series], rows: [
        { label: "Dambulla model", style: "model", v: r.d_all.pct, text: pct(r.d_all.pct, 2), tip: "Cost against always buying today: " + pct(r.d_all.pct, 2) + ". Right about the direction " + r.d_all.hit + "% of the time (" + r.d_top25.hit + "% for the strongest 25% of calls)." },
        { label: "Own-history model", style: "own", v: r.c_all.pct, text: pct(r.c_all.pct, 2), tip: "A model that uses only the price's own history." },
        { label: "Hindsight ceiling", style: "ceiling", v: r.hindsight_pct, text: pct(r.hindsight_pct, 2), tip: "What perfect foresight would save. No real buyer can reach it." }] };
    });
    var lo = Math.min.apply(null, list.map(function (r) { return r.hindsight_pct; }));
    rowsChart($("d-chart"), { kind: "bar", groups: groups, min: Math.floor(lo - 2), max: 1, zero: true, fmt: function (v) { return PS.signed(v, 0) + "%"; },
      legend: [{ label: "Dambulla model", color: "--accent" }, { label: "Own-history model", color: "--ink-3" }, { label: "Hindsight ceiling", color: "--ink-3", dash: true }],
      aria: "Cost of following each model against always buying today, as a share of the purchase value, by Colombo series" });
    $("d-table").appendChild(PS.table("Show the numbers as a table", ["Colombo price", "Dambulla model", "Own-history model", "Hindsight ceiling", "Dambulla vs own history (95% interval)", "Direction right: all / strongest 25%"],
      list.map(function (r) { return [PS.NAMES[r.series], pct(r.d_all.pct, 2), pct(r.c_all.pct, 2), pct(r.hindsight_pct, 2), PS.signed(r.d_vs_c_pts, 2) + " points (" + PS.signed(r.d_vs_c_lo, 2) + " to " + PS.signed(r.d_vs_c_hi, 2) + ")", r.d_all.hit + "% / " + r.d_top25.hit + "%"]; })));
    var d = list.map(function (r) { return Math.abs(r.d_all.pct); });
    var share = list.map(function (r) { return 100 * r.d_all.pct / r.hindsight_pct; });
    $("d-read").textContent = "Following the Dambulla model cost " + Math.min.apply(null, d).toFixed(1) + " to " + Math.max.apply(null, d).toFixed(1) + "% less than always buying today and captured roughly " + Math.round(Math.min.apply(null, share)) + " to " + Math.round(Math.max.apply(null, share)) +
      "% of what perfect hindsight could save. The source uses different units for different foods, so no mixed-unit rupee total is claimed. The saving is a simulation, not observed savings.";
  }

  PS.start();
  PS.get("/api/evidence").then(function (e) {
    var any = e.gain.length + e.calibration.length + e.decision.length;
    if (!any) {
      var m = $("msg"); m.hidden = false;
      m.textContent = "The result files are not in this copy of the site, so no charts are shown. They are saved in the repository as results_*.txt.";
      return;
    }
    $("out").hidden = false;
    gain(e.gain); calib(e.calibration); decide(e.decision);
  }).catch(function (e) { var m = $("msg"); m.hidden = false; m.textContent = "Could not load the evidence: " + e.message; });
})();
