"use strict";
(function () {
  var $ = window.PS.$;
  PS.initLanguage();
  PS.initTheme();
  PS.footer();
  PS.get("/api/status").then(function (s) {
    var box = $("welcome-live");
    box.className = "welcome-live " + (s.state === "ok" ? "ready" : "withheld");
    box.textContent = "";
    box.appendChild(PS.el("span", "live-dot"));
    if (s.state === "ok") {
      box.appendChild(document.createTextNode(PS.t("latestReady", { date: s.report_date_label })));
    } else {
      box.appendChild(document.createTextNode(PS.t("estimatesHidden", { reason: s.reason })));
    }
  }).catch(function () {
    var box = $("welcome-live");
    box.className = "welcome-live withheld";
    box.textContent = PS.t("latestFailed");
  });
})();
