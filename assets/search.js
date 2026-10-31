/* Filters search.json in the browser; ?q= in the address pre-fills the box. */
(function () {
  var box = document.getElementById('q'), out = document.getElementById('results'), status = document.getElementById('search-status');
  if (!box) return;
  var items = [];
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function run() {
    var q = box.value.trim().toLowerCase();
    if (!q) { out.innerHTML = ''; status.textContent = items.length + ' stories in the Times.'; return; }
    var words = q.split(/\s+/);
    var hits = items.filter(function (it) {
      var hay = (it.t + ' ' + it.d + ' ' + it.s + ' ' + it.b).toLowerCase();
      return words.every(function (w) { return hay.indexOf(w) !== -1; });
    });
    status.textContent = hits.length + (hits.length === 1 ? ' story' : ' stories') + ' found.';
    out.innerHTML = hits.map(function (it) {
      return '<li><p class="kicker">' + esc(it.s) + '</p><h2 class="h-2"><a href="' + it.u + '">' + esc(it.t) + '</a></h2><p class="summary">' + esc(it.d) + '</p><p class="meta">' + esc(it.p) + '</p></li>';
    }).join('');
  }
  fetch('/search.json').then(function (r) { return r.json(); }).then(function (d) {
    items = d;
    var q = new URLSearchParams(location.search).get('q'); if (q) box.value = q;
    run();
  });
  box.addEventListener('input', run);
})();
