/*
  Keeps the "local time" on the About page ticking without a reload.
  The server already printed the right time, so the page is correct even without this script.
*/
(function () {
  "use strict";

  var clocks = document.querySelectorAll("[data-clock]");
  if (!clocks.length) return;

  function tick() {
    clocks.forEach(function (el) {
      try {
        el.textContent = new Intl.DateTimeFormat("en-GB", {
          hour: "2-digit",
          minute: "2-digit",
          hourCycle: "h23",
          timeZone: el.dataset.tz,
        }).format(new Date());
      } catch (error) {
        // Unknown zone in this browser: keep the time the server printed.
      }
    });
  }

  tick();
  setInterval(tick, 20000);
})();
