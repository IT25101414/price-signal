"use strict";
(function () {
  var $ = PS.$, el = PS.el;
  var RANGE_NAMES = { 5: "1 week", 22: "1 month", 65: "3 months", 130: "6 months", 250: "1 year" };
  var state = { items: [], series: "retail Pettah", item: null, days: 22, mode: "rs", ranges: [5, 22, 65, 130, 250], seriesList: [] };
  var seq = 0;

  function seg(boxId, options, current, onPick) {
    var box = $(boxId);
    box.textContent = "";
    options.forEach(function (o) {
      var b = el("button", null, o[1]);
      b.type = "button";
      b.setAttribute("role", "radio");
      b.setAttribute("aria-checked", String(o[0] === current));
      b.addEventListener("click", function () { onPick(o[0]); });
      box.appendChild(b);
    });
  }
  function message(html, text) {
    var m = $("msg");
    m.hidden = !text;
    m.textContent = text || "";
    $("out").hidden = !!text;
  }
  function itemsFor(series) { return state.items.filter(function (i) { return i.history[series]; }); }

  function drawControls() {
    seg("series", state.seriesList.map(function (s) { return [s, PS.NAMES[s] || s]; }), state.series, function (v) {
      state.series = v; fixItem(); drawControls(); load();
    });
    seg("range", state.ranges.map(function (d) { return [d, RANGE_NAMES[d] || d + " days"]; }), state.days, function (v) { state.days = v; drawControls(); load(); });
    seg("mode", [["rs", "Rupees"], ["index", "Indexed to 100"]], state.mode, function (v) { state.mode = v; drawControls(); load(); });
    var sel = $("item");
    sel.textContent = "";
    itemsFor(state.series).forEach(function (i) {
      var o = el("option", null, i.item); o.value = i.item; if (i.item === state.item) o.selected = true; sel.appendChild(o);
    });
  }
  function fixItem() {
    var ok = itemsFor(state.series);
    if (!ok.some(function (i) { return i.item === state.item; })) state.item = ok.length ? ok[0].item : null;
  }

  function fact(label, value, sub) {
    var f = el("div", "fact");
    f.appendChild(el("span", null, label));
    f.appendChild(el("b", null, value));
    if (sub) f.appendChild(el("span", null, sub));
    return f;
  }
  function first(a) { for (var i = 0; i < a.length; i++) if (a[i] != null) return a[i]; return null; }
  function last(a) { for (var i = a.length - 1; i >= 0; i--) if (a[i] != null) return a[i]; return null; }

  function render(h) {
    var dates = h.dates, d = h.dambulla, c = h.colombo;
    if (first(d) == null || first(c) == null) {
      message(null, "There are no " + (first(d) == null ? "Dambulla" : (PS.NAMES[state.series] || state.series)) + " prices for " + h.item + " in this period.");
      return;
    }
    var base = state.mode === "index";
    var d0 = first(d), c0 = first(c);
    var dv = base ? d.map(function (v) { return v == null ? null : 100 * v / d0; }) : d;
    var cv = base ? c.map(function (v) { return v == null ? null : 100 * v / c0; }) : c;
    var gap = d.map(function (v, i) { return v != null && c[i] != null ? 100 * (c[i] / v - 1) : null; });
    var gv = gap.filter(function (v) { return v != null; });
    var gavg = gv.length ? gv.reduce(function (a, b) { return a + b; }, 0) / gv.length : null;
    var name = PS.NAMES[state.series] || state.series;
    var chD = d0 ? 100 * (last(d) / d0 - 1) : null, chC = c0 ? 100 * (last(c) / c0 - 1) : null;

    var f = $("facts");
    f.textContent = "";
    f.appendChild(fact("Dambulla wholesale", PS.rs(last(d)), PS.arrow(chD) + PS.signed(chD) + "% over the period"));
    f.appendChild(fact(name, PS.rs(last(c)), PS.arrow(chC) + PS.signed(chC) + "% over the period"));
    f.appendChild(fact("Average gap", PS.signed(gavg, 0) + "%", "Colombo above Dambulla, " + dates.length + " report days"));

    $("c1-t").textContent = h.item + ": Dambulla and " + name;
    $("c1-c").textContent = base ? "Both prices set to 100 on the first day, so you can compare how they moved, not what they cost." : "Price per kg in rupees, as reported.";
    var box = $("c1");
    PS.responsive(box, function (w) {
      box.appendChild(PS.legend([{ label: "Dambulla wholesale", color: "--dambulla" }, { label: name, color: "--colombo" }]));
      box.appendChild(PS.lineChart({
        floorZero: true, width: w, dates: dates, aria: "Line chart of " + h.item + " prices, Dambulla and " + name + ", last " + dates.length + " report days",
        axisFmt: base ? function (v) { return v.toFixed(0); } : function (v) { return Math.round(v).toLocaleString("en-US"); },
        series: [{ label: "Dambulla", color: "--dambulla", values: dv, fmt: base ? function (v) { return v.toFixed(1); } : PS.rs },
                 { label: "Colombo", color: "--colombo", values: cv, fmt: base ? function (v) { return v.toFixed(1); } : PS.rs }]
      }));
      box.appendChild(PS.table("Show the prices as a table", ["Report date", "Dambulla (Rs)", name + " (Rs)", "Gap (%)"],
        dates.map(function (x, i) { return [x, d[i] == null ? "" : d[i].toFixed(0), c[i] == null ? "" : c[i].toFixed(0), gap[i] == null ? "" : PS.signed(gap[i], 0)]; }).reverse()));
    });
    var b2 = $("c2");
    PS.responsive(b2, function (w) {
      b2.appendChild(PS.legend([{ label: "Gap", color: "--accent" }, { label: "Average " + PS.signed(gavg, 0) + "%", color: "--ink-3", dash: true }]));
      b2.appendChild(PS.lineChart({
        width: w, height: 200, dates: dates, aria: "Line chart of the gap between the Colombo and Dambulla prices of " + h.item,
        axisFmt: function (v) { return PS.signed(v, 0) + "%"; },
        ref: gavg == null ? null : { value: gavg },
        series: [{ label: "Gap", color: "--accent", values: gap, fmt: function (v) { return PS.signed(v, 1) + "%"; } }]
      }));
    });
  }

  function load() {
    var my = ++seq;
    if (!state.item) { message(null, "No item has price history for this Colombo price right now."); return; }
    PS.get("/api/history?item=" + encodeURIComponent(state.item) + "&series=" + encodeURIComponent(state.series) + "&days=" + state.days).then(function (h) {
      if (my !== seq) return;
      if (h.state !== "ok") { message(null, "Past prices are not shown. " + h.reason); return; }
      if (!h.dates.length) { message(null, "No price history is loaded in this copy of the site. Put prices_all.csv in the repository folder and run: python3 web/build_db.py"); return; }
      message(null, "");
      render(h);
    }).catch(function (e) { message(null, "Could not load the prices: " + e.message); });
  }

  PS.start();
  $("item").addEventListener("change", function (e) { state.item = e.target.value; load(); });
  PS.get("/api/items").then(function (r) {
    state.items = r.items; state.ranges = r.ranges; state.seriesList = r.series;
    if (r.state !== "ok") { drawControls(); message(null, "Past prices are not shown. " + r.reason); return; }
    var q = new URLSearchParams(location.search);
    if (q.get("series") && r.series.indexOf(q.get("series")) >= 0) state.series = q.get("series");
    if (q.get("item")) state.item = q.get("item");
    fixItem(); drawControls(); load();
  }).catch(function (e) { message(null, "Could not load the item list: " + e.message + ". Is the server running? Start it with: python3 web/server.py"); });
})();
