"use strict";
/* Shared helpers for every page: DOM, number formats, theme, menu, tooltip and the small SVG charts. No libraries. */
(function () {
  var MINUS = "−";
  var SVGNS = "http://www.w3.org/2000/svg";
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var PAGES = [["/", "Today"], ["/explore", "Explore"], ["/report", "Weekly report"], ["/method", "Method"], ["/help", "Help"]];
  var PS = window.PS = {};

  PS.MINUS = MINUS;
  PS.NAMES = { "retail Pettah": "Retail, Pettah", "wholesale Pettah": "Wholesale, Pettah", "retail Narahenpita": "Retail, Narahenpita" };

  PS.el = function (tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  };
  PS.s = function (tag, attrs, text) {
    var e = document.createElementNS(SVGNS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    return e;
  };
  PS.$ = function (id) { return document.getElementById(id); };
  PS.signed = function (v, d) {
    if (v == null || isNaN(v)) return "";
    var s = Math.abs(v).toFixed(d == null ? 1 : d);
    return (v < 0 ? MINUS : v > 0 ? "+" : "") + s;
  };
  PS.arrow = function (v) { return v == null ? "" : v < 0 ? "▼ " : v > 0 ? "▲ " : ""; };
  PS.rs = function (v) { return v == null ? "" : "Rs " + Math.round(v).toLocaleString("en-US"); };
  PS.date = function (iso, year) {
    var p = iso.split("-");
    return parseInt(p[2], 10) + " " + MONTHS[parseInt(p[1], 10) - 1] + (year ? " " + p[0] : "");
  };
  PS.get = function (url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error(url + " returned " + r.status);
      return r.json();
    });
  };

  // ---------- theme ----------
  function applyTheme(t) { if (t) document.documentElement.setAttribute("data-theme", t); else document.documentElement.removeAttribute("data-theme"); }
  try { applyTheme(localStorage.getItem("ps-theme")); } catch (e) { /* storage blocked: follow the OS */ }
  PS.initTheme = function () {
    var b = PS.$("theme");
    if (!b) return;
    b.addEventListener("click", function () {
      var cur = document.documentElement.getAttribute("data-theme") ||
        (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
      var next = cur === "dark" ? "light" : "dark";
      applyTheme(next);
      try { localStorage.setItem("ps-theme", next); } catch (e) { /* ignore */ }
      window.dispatchEvent(new Event("resize"));
    });
  };

  // ---------- menu and footer ----------
  PS.menu = function () {
    var nav = PS.$("nav");
    if (!nav) return;
    var here = location.pathname.replace(/\/+$/, "") || "/";
    PAGES.forEach(function (p) {
      var a = PS.el("a", null, p[1]);
      a.href = p[0];
      if (p[0] === here) a.setAttribute("aria-current", "page");
      nav.appendChild(a);
    });
  };
  PS.footer = function (extra) {
    var f = PS.$("foot");
    if (!f) return;
    f.textContent = "";
    var links = PS.el("p", "foot-links");
    PAGES.forEach(function (p) { var a = PS.el("a", null, p[1]); a.href = p[0]; links.appendChild(a); });
    var g = PS.el("a", null, "Source code"); g.href = "https://github.com/IT25101414/price-signal"; links.appendChild(g);
    f.appendChild(links);
    f.appendChild(PS.el("p", null, "Source: Statistics Department, Central Bank of Sri Lanka, Daily Price Reports. The Central Bank does not endorse this project or its findings. " +
      "Estimates are statistical, not advice." + (extra ? " " + extra : "")));
  };
  // Every page says so when the price history is invented (demo builds), so made-up prices are never mistaken for real ones.
  PS.demoNotice = function () {
    if (PS.$("demo")) return;                       // the Today page has its own notice
    fetch("/api/status").then(function (r) { return r.json(); }).then(function (s) {
      if (s.history_source !== "synthetic") return;
      var main = document.querySelector("main");
      if (!main) return;
      var p = PS.el("p", "demo", "Demo data: the price history on this page is invented for testing the layout, not Central Bank prices.");
      p.setAttribute("role", "note");
      main.insertBefore(p, main.firstChild);
    }).catch(function () {});
  };
  PS.start = function (extra) { PS.initTheme(); PS.menu(); PS.footer(extra); PS.demoNotice(); };

  // ---------- tooltip ----------
  var tip;
  PS.tip = function (x, y, nodes) {
    tip = tip || PS.$("tip");
    if (!tip) { tip = PS.el("div", "tip"); tip.id = "tip"; tip.setAttribute("role", "status"); document.body.appendChild(tip); }
    tip.textContent = "";
    nodes.forEach(function (n) { tip.appendChild(typeof n === "string" ? PS.el("div", null, n) : n); });
    tip.hidden = false;
    var w = tip.offsetWidth, h = tip.offsetHeight;
    tip.style.left = Math.min(window.innerWidth - w - 8, Math.max(8, x + 14)) + "px";
    tip.style.top = Math.max(8, Math.min(window.innerHeight - h - 8, y - h - 10)) + "px";
  };
  PS.hideTip = function () { tip = tip || PS.$("tip"); if (tip) tip.hidden = true; };
  PS.tipRow = function (color, value, label) {
    var row = PS.el("div", "t-row"), k = PS.el("i");
    k.style.borderTopColor = "var(" + color + ")";
    row.appendChild(k); row.appendChild(PS.el("b", null, value)); row.appendChild(PS.el("span", null, label));
    return row;
  };

  // ---------- chart helpers ----------
  function niceStep(raw) {
    var p = Math.pow(10, Math.floor(Math.log(raw) / Math.LN10)), f = raw / p;
    return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 6.5 ? 5 : 10) * p;
  }
  PS.ticks = function (lo, hi, n) {
    if (hi === lo) { hi = lo + 1; }
    var step = niceStep((hi - lo) / (n || 4)), a = Math.floor(lo / step) * step, out = [];
    for (var v = a; v <= hi + step * 0.001; v += step) out.push(+v.toFixed(6));
    return out;
  };
  /* Draw into box now and again whenever its width changes, so text stays readable on a phone. */
  PS.responsive = function (box, draw) {
    var last = -1;
    function go() {
      var w = Math.floor(box.clientWidth);
      if (w === last || w < 60) return;
      last = w; box.textContent = ""; draw(w);
    }
    go();
    if (window.ResizeObserver) new ResizeObserver(go).observe(box); else window.addEventListener("resize", go);
    window.addEventListener("resize", function () { last = -1; go(); });
  };
  PS.legend = function (items) {
    var l = PS.el("div", "legend");
    items.forEach(function (x) {
      var i = PS.el("span"), k = PS.el("i");
      k.style.borderTopColor = "var(" + x.color + ")";
      if (x.dash) k.style.borderTopStyle = "dashed";
      i.appendChild(k); i.appendChild(document.createTextNode(x.label)); l.appendChild(i);
    });
    return l;
  };
  PS.table = function (summary, headers, rows) {
    var det = PS.el("details", "table");
    det.appendChild(PS.el("summary", null, summary));
    var box = PS.el("div", "tbl"), tb = PS.el("table"), tr = PS.el("tr");
    headers.forEach(function (h) { tr.appendChild(PS.el("th", null, h)); });
    tb.appendChild(tr);
    rows.forEach(function (r) {
      var t = PS.el("tr");
      r.forEach(function (c) { t.appendChild(PS.el("td", null, c)); });
      tb.appendChild(t);
    });
    box.appendChild(tb); det.appendChild(box);
    return det;
  };

  /* Line chart. o: {dates, series:[{label,color,values,fmt,dash}], width, height, axisFmt, ref:{value,label}, aria} */
  PS.lineChart = function (o) {
    var W = o.width, H = o.height || 260, L = 52, R = W < 520 ? 12 : 118, T = 12, B = 28, dates = o.dates;
    var vals = [];
    o.series.forEach(function (s) { s.values.forEach(function (v) { if (v != null) vals.push(v); }); });
    if (o.ref) vals.push(o.ref.value);
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals), pad = (hi - lo) * 0.08 || 1;
    lo -= pad; hi += pad;
    if (o.floorZero && lo < 0) lo = 0;
    var ticks = PS.ticks(lo, hi, 4); lo = Math.min(lo, ticks[0]); hi = Math.max(hi, ticks[ticks.length - 1]);
    var X = function (i) { return L + (i / Math.max(1, dates.length - 1)) * (W - L - R); };
    var Y = function (v) { return T + (1 - (v - lo) / (hi - lo)) * (H - T - B); };
    var afmt = o.axisFmt || function (v) { return String(Math.round(v)); };
    var svg = PS.s("svg", { width: W, height: H, viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": o.aria || "Line chart" });
    ticks.forEach(function (v) {
      var y = Y(v);
      svg.appendChild(PS.s("line", { x1: L, x2: W - R, y1: y, y2: y, stroke: "var(--line)", "stroke-width": 1 }));
      svg.appendChild(PS.s("text", { x: L - 8, y: y + 4, "text-anchor": "end", "font-size": 11, fill: "var(--ink-3)" }, afmt(v)));
    });
    var yr = dates.length > 150;
    [0, Math.floor((dates.length - 1) / 2), dates.length - 1].forEach(function (i, k) {
      svg.appendChild(PS.s("text", { x: X(i), y: H - 8, "text-anchor": k === 0 ? "start" : k === 2 ? "end" : "middle", "font-size": 11, fill: "var(--ink-3)" }, PS.date(dates[i], yr)));
    });
    if (o.ref) {
      var ry = Y(o.ref.value);
      svg.appendChild(PS.s("line", { x1: L, x2: W - R, y1: ry, y2: ry, stroke: "var(--ink-3)", "stroke-width": 1.5, "stroke-dasharray": "5 4" }));
      if (o.ref.label) svg.appendChild(PS.s("text", { x: W - R + 8, y: ry + 4, "font-size": 12, fill: "var(--ink-2)" }, o.ref.label));
    }
    var ends = [];
    o.series.forEach(function (s) {
      var pts = [], run = [];
      s.values.forEach(function (v, i) {
        if (v == null) { if (run.length) pts.push(run); run = []; return; }
        run.push(X(i).toFixed(1) + "," + Y(v).toFixed(1));
      });
      if (run.length) pts.push(run);
      pts.forEach(function (seg) {
        svg.appendChild(PS.s("polyline", { points: seg.join(" "), fill: "none", stroke: "var(" + s.color + ")", "stroke-width": 2, "stroke-linejoin": "round", "stroke-dasharray": s.dash || "none" }));
      });
      var li = -1;
      s.values.forEach(function (v, i) { if (v != null) li = i; });
      if (li >= 0) ends.push({ s: s, i: li, y: Y(s.values[li]), v: s.values[li] });
    });
    if (R > 60) {
      ends.sort(function (a, b) { return a.y - b.y; });
      for (var k = 1; k < ends.length; k++) if (ends[k].y - (ends[k - 1].ty != null ? ends[k - 1].ty : ends[k - 1].y) < 15) ends[k].ty = (ends[k - 1].ty != null ? ends[k - 1].ty : ends[k - 1].y) + 15;
    }
    ends.forEach(function (e) {
      svg.appendChild(PS.s("circle", { cx: X(e.i), cy: e.y, r: 4, fill: "var(" + e.s.color + ")", stroke: "var(--surface)", "stroke-width": 2 }));
      if (R > 60) svg.appendChild(PS.s("text", { x: W - R + 10, y: (e.ty != null ? e.ty : e.y) + 4, "font-size": 12, fill: "var(--ink)" }, e.s.label + " " + (e.s.fmt || afmt)(e.v)));
    });
    var cross = PS.s("line", { y1: T, y2: H - B, stroke: "var(--ink-3)", "stroke-width": 1, visibility: "hidden" });
    svg.appendChild(cross);
    var dots = o.series.map(function (s) { var c = PS.s("circle", { r: 4.5, fill: "var(" + s.color + ")", stroke: "var(--surface)", "stroke-width": 2, visibility: "hidden" }); svg.appendChild(c); return c; });
    function at(cx, cy) {
      var r = svg.getBoundingClientRect(), px = ((cx - r.left) / r.width) * W;
      var i = Math.max(0, Math.min(dates.length - 1, Math.round(((px - L) / (W - L - R)) * (dates.length - 1))));
      cross.setAttribute("x1", X(i)); cross.setAttribute("x2", X(i)); cross.setAttribute("visibility", "visible");
      var rows = [PS.el("div", "t-d", PS.date(dates[i], true))];
      o.series.forEach(function (s, j) {
        var v = s.values[i];
        if (v == null) { dots[j].setAttribute("visibility", "hidden"); return; }
        dots[j].setAttribute("cx", X(i)); dots[j].setAttribute("cy", Y(v)); dots[j].setAttribute("visibility", "visible");
        rows.push(PS.tipRow(s.color, (s.fmt || afmt)(v), s.label));
      });
      PS.tip(cx, cy, rows);
    }
    svg.addEventListener("pointermove", function (e) { at(e.clientX, e.clientY); });
    svg.addEventListener("pointerleave", function () { PS.hideTip(); cross.setAttribute("visibility", "hidden"); dots.forEach(function (d) { d.setAttribute("visibility", "hidden"); }); });
    return svg;
  };

  /* Tiny two-line chart for small multiples. values arrays share one x axis; band marks the last n points. */
  PS.spark = function (w, h, series, band) {
    var all = [];
    series.forEach(function (s) { s.values.forEach(function (v) { if (v != null) all.push(v); }); });
    var lo = Math.min.apply(null, all), hi = Math.max.apply(null, all), pad = (hi - lo) * 0.12 || 1; lo -= pad; hi += pad;
    var n = series[0].values.length, X = function (i) { return 4 + (i / (n - 1)) * (w - 8); }, Y = function (v) { return 4 + (1 - (v - lo) / (hi - lo)) * (h - 8); };
    var svg = PS.s("svg", { width: w, height: h, viewBox: "0 0 " + w + " " + h, "aria-hidden": "true" });
    if (band) svg.appendChild(PS.s("rect", { x: X(n - band), y: 0, width: w - X(n - band), height: h, fill: "var(--accent-soft)", opacity: 0.55 }));
    series.forEach(function (s) {
      var pts = [];
      s.values.forEach(function (v, i) { if (v != null) pts.push(X(i).toFixed(1) + "," + Y(v).toFixed(1)); });
      svg.appendChild(PS.s("polyline", { points: pts.join(" "), fill: "none", stroke: "var(" + s.color + ")", "stroke-width": 2, "stroke-linejoin": "round" }));
    });
    return svg;
  };
})();
