/* The Vermilion Times: today's date on Central time, and timestamps that stay
   current (fresh stories read "2 hours ago" and carry a New tag). */
(function () {
  var fmt = function (d, opts) {
    try { return new Intl.DateTimeFormat('en-US', Object.assign({ timeZone: 'America/Chicago' }, opts)).format(d); }
    catch (e) { return null; }
  };
  var now = new Date();
  var today = fmt(now, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  ['today', 'today-m'].forEach(function (id) {
    var el = document.getElementById(id); if (el && today) el.textContent = today;
  });
  var yr = document.getElementById('year');
  if (yr) yr.textContent = now.getFullYear();

  function ago(ms) {
    var m = Math.round(ms / 60000);
    if (m < 1) return 'Just now';
    if (m < 60) return m + (m === 1 ? ' minute ago' : ' minutes ago');
    var h = Math.round(m / 60);
    return h + (h === 1 ? ' hour ago' : ' hours ago');
  }
  function tick() {
    var t = Date.now();
    document.querySelectorAll('time.ts[data-pub]').forEach(function (el) {
      var pub = Date.parse(el.getAttribute('data-pub'));
      if (isNaN(pub)) return;
      if (!el.dataset.full) el.dataset.full = el.textContent;
      var age = t - pub;
      el.textContent = (age >= 0 && age < 864e5) ? ago(age) : el.dataset.full;
      el.title = el.dataset.full;
    });
    document.querySelectorAll('.new-tag[data-pub]').forEach(function (el) {
      var age = t - Date.parse(el.getAttribute('data-pub'));
      el.hidden = !(age >= 0 && age < 864e5);
    });
  }
  tick();
  setInterval(tick, 60000);
})();
