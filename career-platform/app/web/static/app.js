// The only JavaScript in the app: keep the scan banner live while a scan runs.
// Everything else is plain server-rendered forms, which keeps the app easy to
// follow and working with the back button.

(function () {
  var banner = document.getElementById("scan-banner");
  var note = document.getElementById("scan-note");
  if (!banner || banner.hidden) return;

  var misses = 0;

  function poll() {
    fetch("/scan/status")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        misses = 0;
        if (data.status === "running") {
          note.textContent =
            (data.note || "Scanning...") +
            (data.jobs_new ? "  -  " + data.jobs_new + " new so far" : "");
          setTimeout(poll, 3000);
        } else {
          // Reload so the new postings appear without a manual refresh.
          window.location.reload();
        }
      })
      .catch(function () {
        // Tolerate a blip; give up after a few consecutive failures.
        if (++misses < 5) setTimeout(poll, 5000);
        else note.textContent = "Lost contact with the scan. Reload to check.";
      });
  }

  setTimeout(poll, 2000);
})();
