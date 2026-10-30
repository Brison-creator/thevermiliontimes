/* Today's date in the masthead, on Central time like the parish. */
(function () {
  var fmt = function (opts) {
    try { return new Intl.DateTimeFormat('en-US', Object.assign({ timeZone: 'America/Chicago' }, opts)).format(new Date()); }
    catch (e) { return null; }
  };
  var day = document.getElementById('today');
  if (day) { var d = fmt({ weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }); if (d) day.textContent = d; }
  var yr = document.getElementById('year');
  if (yr) yr.textContent = new Date().getFullYear();
})();
