"use strict";
(function () {
  var MINUS = PS.MINUS;
  var state = { series: null, cards: [], status: null, q: "", scale: 10 };
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
      $("headline").textContent = s.state === "stale" ? "The data are too old" : "A newer report is not read yet";
      $("reason").textContent = s.reason;
    }
    var demo = $("demo");
    if (s.history_source === "synthetic") {
      demo.hidden = false;
      demo.textContent = "Demo data: the price history in this build is invented for testing the layout. The estimates are from cards.csv.";
    } else demo.hidden = true;
    PS.footer("Database built " + (s.built_at_utc ? s.built_at_utc.replace("T", " ").replace("+00:00", " UTC") : "unknown") + ".");
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
    facts.appendChild(fact("Colombo vs its usual gap", signed(c.gap_vs_usual_pct) + "%"));
    facts.appendChild(fact("Middle estimate, 3 report days", (c.direction === "down" ? "▼ " : c.direction === "up" ? "▲ " : "") + signed(c.expected_change_pct) + "%"));
    body.appendChild(facts);
    body.appendChild(el("p", "note", "80% range for the change in the Colombo price: " + signed(c.low_pct) + " to " + signed(c.high_pct) + "% (scale " + MINUS + state.scale + "% to +" + state.scale + "%)."));
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
      box.appendChild(PS.lineChart({ width: w, dates: dates, aria: "Line chart of Dambulla wholesale and Colombo prices over the last " + dates.length + " report days",
        series: [{ label: "Dambulla", color: "--dambulla", values: d, fmt: rs }, { label: "Colombo", color: "--colombo", values: c, fmt: rs }] }));
    });
    wrap.appendChild(PS.table("Show the prices as a table", ["Report date", "Dambulla (Rs)", "Colombo (Rs)"],
      dates.map(function (x, i) { return [x, d[i] == null ? "" : d[i].toFixed(0), c[i] == null ? "" : c[i].toFixed(0)]; }).reverse()));
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
