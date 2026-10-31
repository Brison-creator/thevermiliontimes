/* Starbase Watch: refreshes launches, Pecan Island jobs and weather in the
   browser. The page is built with a snapshot, so it still works if a feed is down. */
(function(){
  var root=document.getElementById('live'); if(!root) return;
  var MONTHS=['Jan.','Feb.','March','April','May','June','July','Aug.','Sept.','Oct.','Nov.','Dec.'];
  var FULL=['January','February','March','April','May','June','July','August','September','October','November','December'];
  var DAYS=['Sun.','Mon.','Tue.','Wed.','Thu.','Fri.','Sat.'];
  var FEEDS={
    launches:'https://ll.thespacedevs.com/2.3.0/launches/upcoming/?lsp__name=SpaceX&limit=12&mode=normal',
    jobs:'https://boards-api.greenhouse.io/v1/boards/spacex/jobs',
    weather:'https://api.weather.gov/gridpoints/LCH/89,69/forecast',
    alerts:'https://api.weather.gov/alerts/active?point=29.6466,-92.4532',
    recent:'https://ll.thespacedevs.com/2.3.0/launches/previous/?lsp__name=SpaceX&limit=5&mode=normal&net__gte='+new Date().getFullYear()+'-01-01'
  };
  var TTL={launches:30*60e3, recent:60*60e3, jobs:60*60e3, weather:30*60e3, alerts:5*60e3}; // Launch Library allows ~15 calls/hour per visitor
  function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
  function ct(d){ // parts of a date in Central time
    var f=new Intl.DateTimeFormat('en-US',{timeZone:'America/Chicago',weekday:'short',year:'numeric',month:'numeric',day:'numeric',hour:'numeric',minute:'2-digit',hour12:false});
    var o={}; f.formatToParts(d).forEach(function(p){o[p.type]=p.value;});
    var h=+o.hour%24; return {wd:DAYS[['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].indexOf(o.weekday)],m:+o.month-1,d:+o.day,y:+o.year,h:h,min:+o.minute};
  }
  function ap(t){var h=t.h%12||12; return h+(t.min?':'+(t.min<10?'0':'')+t.min:'')+' '+(t.h<12?'a.m.':'p.m.');}
  function when(l){
    var d=new Date(l.net), p=(l.precision||'').toLowerCase(), t=ct(d);
    if(p.indexOf('year')>-1) return 'Sometime in '+d.getUTCFullYear();
    if(p.indexOf('quarter')>-1||p.indexOf('half')>-1) return (l.precision||'').replace('Quarter ','Q')+' '+d.getUTCFullYear();
    if(p.indexOf('month')>-1) return 'No earlier than '+FULL[d.getUTCMonth()]+' '+d.getUTCFullYear();
    if(p==='day'||p.indexOf('week')>-1) return 'No earlier than '+MONTHS[d.getUTCMonth()]+' '+d.getUTCDate();
    return t.wd+' '+MONTHS[t.m]+' '+t.d+', '+(p.indexOf('hour')>-1?'about ':'')+ap(t)+' CT';
  }
  function badge(st){var c={'Go':'go','TBC':'tbc','TBD':'tbd','Success':'ok','Hold':'hold','In Flight':'go','Failure':'hold','Partial Failure':'tbc'}[st]||'tbd'; return '<span class="lv-badge '+c+'">'+esc(st)+'</span>';}
  function precise(p){p=(p||'').toLowerCase(); return p==='second'||p==='minute';}

  function launch(l){return {name:l.name,net:l.net,precision:(l.net_precision||{}).name||'',status:l.status.abbrev,
      rocket:l.rocket.configuration.name,pad:l.pad.name,site:l.pad.location.name,mission:((l.mission||{}).description||'').slice(0,240),
      orbit:((l.mission||{}).orbit||{}).abbrev||'',wstart:l.window_start||'',wend:l.window_end||'',prob:l.probability,webcast:!!l.webcast_live};}
  var shrink={
    launches:function(raw){return (raw.results||[]).map(launch);},
    recent:function(raw){return {count:raw.count||0,items:(raw.results||[]).map(launch)};},
    jobs:function(raw){return (raw.jobs||[]).filter(function(j){return /pecan island/i.test(j.location.name)||/louisiana/i.test(j.title);})
      .map(function(j){return {title:j.title.trim(),url:j.absolute_url};});},
    weather:function(raw){return raw.properties.periods.slice(0,6).map(function(p){return {name:p.name,temp:p.temperature,unit:p.temperatureUnit,short:p.shortForecast,wind:p.windSpeed+' '+p.windDirection};});},
    alerts:function(raw){return (raw.features||[]).map(function(a){var p=a.properties;return {event:p.event,headline:p.headline||'',url:p['@id']||a.id||''};});}
  };
  function windowTxt(l){
    if(!precise(l.precision)||!l.wstart||!l.wend||l.wstart===l.wend) return '';
    return 'Window '+ap(ct(new Date(l.wstart)))+' to '+ap(ct(new Date(l.wend)));
  }
  function row(l,count){
    var bits=[windowTxt(l), l.orbit?'Orbit: '+l.orbit:'', (l.prob!=null)?'Weather '+l.prob+'% go':''].filter(Boolean);
    return '<li'+(count&&precise(l.precision)?' data-net="'+esc(l.net)+'"':'')+'><span class="lv-date">'+esc(when(l))+'</span><span class="lv-name">'+esc(l.name)+'</span><span class="lv-site">'+esc(l.site)+'</span>'+badge(l.status)+
      (count&&bits.length?'<span class="lv-extra">'+esc(bits.join(' \u00b7 '))+'</span>':'')+
      (l.webcast?'<a class="lv-watchlive" href="https://www.spacex.com/launches/" rel="noopener">Live now: watch at SpaceX.com</a>':'')+(count?'<span class="lv-countdown"></span>':'')+'</li>';
  }
  function cached(k){try{var c=JSON.parse(localStorage.getItem('vt-live-'+k)); if(c&&Date.now()-c.t<TTL[k]) return c.items;}catch(e){} return null;}
  function store(k,items){try{localStorage.setItem('vt-live-'+k,JSON.stringify({t:Date.now(),items:items}));}catch(e){}}
  function get(k){
    var c=cached(k); if(c) return Promise.resolve(c);
    return fetch(FEEDS[k],{headers:{'Accept':'application/json'}}).then(function(r){if(!r.ok) throw r.status; return r.json();})
      .then(function(raw){var items=shrink[k](raw); store(k,items); return items;});
  }
  function upcoming(L){var cut=Date.now()-3*3600e3; return L.filter(function(l){return new Date(l.net).getTime()>cut&&l.status!=='Success';});}

  var R={
    launches:function(L){
      var up=upcoming(L), el=document.getElementById('lv-launches');
      if(el) el.innerHTML=up.slice(0,8).map(function(l){return row(l,true);}).join('')||'<li>No launches on the public schedule.</li>';
      var s=up.filter(function(l){return /starship/i.test(l.rocket+' '+l.name);})[0], card=root.querySelector('.lv-ship');
      if(card&&s){
        card.setAttribute('data-net',s.net); card.setAttribute('data-precision',s.precision||'');
        card.innerHTML='<p class="label">Next Starship Flight</p><h3 class="h-1">'+esc(s.name)+'</h3><p class="lv-when">'+esc(when(s))+' '+badge(s.status)+'</p>'+
          '<p class="lv-countdown"></p><p class="meta">'+esc(s.pad)+', '+esc(s.site)+'</p>'+(s.mission?'<p class="summary">'+esc(s.mission)+'</p>':'')+
          (s.webcast?'<p><a class="btn" href="https://www.spacex.com/launches/" rel="noopener">Live now: watch at SpaceX.com</a></p>':'');
      }
    },
    recent:function(P){
      var n=document.getElementById('lv-yearcount'), el=document.getElementById('lv-recent');
      if(n) n.textContent=P.count; if(el) el.innerHTML=P.items.map(function(l){return row(l,false);}).join('');
    },
    alerts:function(A){
      var box=document.getElementById('lv-alerts'); if(!box) return;
      box.hidden=!A.length;
      box.querySelector('ul').innerHTML=A.map(function(a){return '<li><a href="'+esc(a.url)+'" rel="noopener"><b>'+esc(a.event)+'</b></a> '+esc(a.headline)+'</li>';}).join('');
    },
    jobs:function(J){
      var el=document.getElementById('lv-jobs'), n=document.getElementById('lv-jobcount');
      if(n) n.textContent=J.length;
      if(el) el.innerHTML=J.map(function(j){return '<li><a href="'+esc(j.url)+'" rel="noopener">'+esc(j.title)+'</a></li>';}).join('')||'<li>No Louisiana openings listed right now.</li>';
    },
    weather:function(W){
      var el=document.getElementById('lv-wx');
      if(el) el.innerHTML=W.slice(0,4).map(function(w){return '<li><b>'+esc(w.name)+'</b><span class="lv-temp">'+esc(w.temp)+'&deg;'+esc(w.unit)+'</span><span>'+esc(w.short)+'</span><span class="meta">Wind '+esc(w.wind)+'</span></li>';}).join('');
    }
  };
  var fresh=0;
  Object.keys(FEEDS).forEach(function(k){
    get(k).then(function(items){
      R[k](items); fresh++;
      var f=document.getElementById('lv-fetched'), t=ct(new Date());
      if(f) f.textContent=MONTHS[t.m]+' '+t.d+', '+ap(t)+' CT (live)';
      tick();
    }).catch(function(){ /* keep the snapshot already on the page */ });
  });

  function pad(n){return (n<10?'0':'')+n;}
  function tick(){
    var now=Date.now();
    [].forEach.call(root.querySelectorAll('[data-net]'),function(el){
      var out=el.querySelector('.lv-countdown'); if(!out) return;
      var p=el.getAttribute('data-precision'); if(p!==null&&!precise(p)){out.textContent='';return;}
      var ms=new Date(el.getAttribute('data-net')).getTime()-now;
      if(ms<=0){out.textContent=ms>-3*3600e3?'Launch window open':'';return;}
      var s=Math.floor(ms/1000), d=Math.floor(s/86400), h=Math.floor(s%86400/3600), m=Math.floor(s%3600/60);
      out.textContent='T− '+(d?d+'d ':'')+pad(h)+':'+pad(m)+':'+pad(s%60);
    });
  }
  tick(); setInterval(tick,1000);
})();
