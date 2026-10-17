"use strict";
(function () {
  var $ = PS.$, el = PS.el;
  var REASONS = [
    ["ok", "Estimate shown", "Data are current and complete, and the model has a clear signal."],
    ["no_clear_signal", "No clear signal", "The expected change is smaller than the model's usual noise. About half of all items fall here by design."],
    ["no_dambulla_price", "No Dambulla price", "The latest report has no Dambulla wholesale price for the item (not listed, or reported as n.a.)."],
    ["no_colombo_price", "No Colombo price", "The latest report has no price for this item in the chosen Colombo market."],
    ["insufficient_data", "Too little history", "Fewer than 40 of the last 60 report days have both prices, so the gap cannot be judged."],
    ["market_closed", "Market closed", "The report says the market was not in operation that day."]
  ];
  PS.start();
  PS.get("/api/summary").then(function (s) {
    var tb = $("why").querySelector("tbody");
    var known = {};
    REASONS.forEach(function (r) {
      known[r[0]] = 1;
      var tr = el("tr"), c = el("td"), tag = el("span", "st" + (r[0] === "ok" ? " ok" : ""), r[1]);
      c.appendChild(tag); tr.appendChild(c);
      tr.appendChild(el("td", null, r[2]));
      tr.appendChild(el("td", null, String(s.by_status[r[0]] || 0)));
      tb.appendChild(tr);
    });
    Object.keys(s.by_status).forEach(function (k) {
      if (known[k]) return;
      var tr = el("tr"); tr.appendChild(el("td", null, k)); tr.appendChild(el("td", null, "Another reason recorded by the guard.")); tr.appendChild(el("td", null, String(s.by_status[k])));
      tb.appendChild(tr);
    });
    $("why-c").textContent = "Counts for the report of " + s.report_date_label + ", " + s.total + " item and Colombo-price pairs in all." +
      (s.state === "ok" ? "" : " Right now every figure is withheld because " + s.reason.charAt(0).toLowerCase() + s.reason.slice(1));
  }).catch(function () { $("why-c").textContent = "The live counts could not be loaded."; });
})();
