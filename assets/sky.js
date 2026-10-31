/* Tonight's sky over Pecan Island: sun, moon, planets, close passes ("alignments"),
   eclipses and meteor showers, computed in the browser with Astronomy Engine. */
(function(){
  var box=document.getElementById('lv-sky'); if(!box) return;
  function run(){
    var A=window.Astronomy; if(!A){ setTimeout(run,300); return; }
    try{ draw(A); }catch(e){ ['lv-sunmoon','lv-planets','lv-events'].forEach(function(id){var el=document.getElementById(id); if(el) el.innerHTML='<li>Sky data is unavailable right now.</li>';}); }
  }
  var MONTHS=['Jan.','Feb.','March','April','May','June','July','Aug.','Sept.','Oct.','Nov.','Dec.'];
  var DAYS=['Sun.','Mon.','Tue.','Wed.','Thu.','Fri.','Sat.'];
  function ct(d){
    var o={}; new Intl.DateTimeFormat('en-US',{timeZone:'America/Chicago',weekday:'short',year:'numeric',month:'numeric',day:'numeric',hour:'numeric',minute:'2-digit',hour12:false})
      .formatToParts(d).forEach(function(p){o[p.type]=p.value;});
    return {wd:DAYS[['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].indexOf(o.weekday)],m:+o.month-1,d:+o.day,y:+o.year,h:+o.hour%24,min:+o.minute};
  }
  function time(d){var t=ct(d),h=t.h%12||12; return h+(t.min?':'+(t.min<10?'0':'')+t.min:'')+' '+(t.h<12?'a.m.':'p.m.');}
  function day(d,withYear){var t=ct(d); return t.wd+' '+MONTHS[t.m]+' '+t.d+(withYear&&t.y!==ct(new Date()).y?', '+t.y:'');}
  function esc(s){return String(s).replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c];});}
  function compass(az){return ['north','northeast','east','southeast','south','southwest','west','northwest'][Math.round(az/45)%8];}
  function height(alt){return alt<15?'low in the':alt<45?'partway up in the':'high in the';}

  function draw(A){
    var lat=+box.getAttribute('data-lat'), lon=+box.getAttribute('data-lon');
    var obs=new A.Observer(lat,lon,1), now=new Date(), H=3600e3;
    function rs(body,dir,start,days){var t=A.SearchRiseSet(body,obs,dir,start,days||2); return t?t.date:null;}
    function horiz(body,d){var eq=A.Equator(body,d,obs,true,true); return A.Horizon(d,obs,eq.ra,eq.dec,'normal');}

    // ---------- Sun and Moon
    var sunset=rs('Sun',-1,new Date(now.getTime()-2*H)), sunrise=rs('Sun',+1,sunset||now);
    var phase=A.MoonPhase(now), lit=Math.round(A.Illumination('Moon',now).phase_fraction*100);
    var pname=phase<6||phase>354?'New moon':phase<84?'Waxing crescent':phase<96?'First quarter':phase<174?'Waxing gibbous':phase<186?'Full moon':phase<264?'Waning gibbous':phase<276?'Last quarter':'Waning crescent';
    var mrise=rs('Moon',+1,now), mset=rs('Moon',-1,now);
    var q=A.SearchMoonQuarter(now), full=null, nw=null;
    for(var i=0;i<4&&(!full||!nw);i++){ if(q.quarter===2&&!full) full=q.time.date; if(q.quarter===0&&!nw) nw=q.time.date; q=A.NextMoonQuarter(q); }
    var sm=[];
    if(sunset) sm.push('<li><b>Sunset</b> '+time(sunset)+(sunrise?' &middot; <b>Sunrise</b> '+time(sunrise):'')+'</li>');
    sm.push('<li><b>Moon:</b> '+pname+', '+lit+'% lit</li>');
    if(mrise||mset) sm.push('<li>'+(mrise?'Moonrise '+day(mrise)+', '+time(mrise):'')+(mrise&&mset?' &middot; ':'')+(mset?'Moonset '+day(mset)+', '+time(mset):'')+'</li>');
    if(full) sm.push('<li>Next full moon: '+day(full)+'</li>');
    if(nw) sm.push('<li>Next new moon (darkest skies): '+day(nw)+'</li>');
    document.getElementById('lv-sunmoon').innerHTML=sm.join('');

    // ---------- Planets tonight
    var PL=['Mercury','Venus','Mars','Jupiter','Saturn'];
    var eve=sunset?new Date(sunset.getTime()+75*60e3):new Date(now.getTime()+H), morn=sunrise?new Date(sunrise.getTime()-75*60e3):new Date(eve.getTime()+10*H);
    var upEve=[], upMorn=[], rows=[];
    PL.forEach(function(p){
      var he=horiz(p,eve), hm=horiz(p,morn), mag=A.Illumination(p,eve).mag;
      var bright=mag<-1?'very bright':mag<1.5?'bright':'faint';
      var parts=[];
      if(he.altitude>5){ upEve.push(p); parts.push('After sunset: '+height(he.altitude)+' '+compass(he.azimuth)); }
      if(hm.altitude>5){ upMorn.push(p); parts.push('Before dawn: '+height(hm.altitude)+' '+compass(hm.azimuth)); }
      if(!parts.length) parts.push(A.AngleFromSun(p,now)<15?'Too close to the Sun to see':'Not well placed tonight');
      rows.push('<li><b>'+p+'</b> <span class="meta">('+bright+')</span><br>'+parts.join('<br>')+'</li>');
    });
    var lead='';
    if(upEve.length>=2) lead+='<li class="lv-hl">'+upEve.length+' planets in the evening sky: '+upEve.join(', ')+'</li>';
    if(upMorn.length>=2) lead+='<li class="lv-hl">'+upMorn.length+' planets before dawn: '+upMorn.join(', ')+'</li>';
    document.getElementById('lv-planets').innerHTML=lead+rows.join('');

    // ---------- Coming up
    var ev=[];
    // Close passes ("alignments"): Moon or planet pairs within a few degrees, next 60 days
    var bodies=['Moon'].concat(PL), STEP=2*H, N=30*24/2*2, prev=[], prev2=[];
    for(var k=0;k<=N;k++){
      var d=new Date(now.getTime()+k*STEP), v={};
      bodies.forEach(function(b){v[b]=A.GeoVector(b,d,true);});
      var seps=[], idx=0;
      for(var a=0;a<bodies.length;a++) for(var b=a+1;b<bodies.length;b++){
        var s=A.AngleBetween(v[bodies[a]],v[bodies[b]]);
        if(k>=2&&prev[idx]<prev2[idx]&&prev[idx]<=s){
          var lim=bodies[a]==='Moon'?4:3;
          if(prev[idx]<lim) ev.push({t:new Date(d.getTime()-STEP),pair:[bodies[a],bodies[b]],sep:prev[idx],kind:'pass'});
        }
        seps.push(s); idx++;
      }
      prev2=prev; prev=seps;
    }
    ev=ev.filter(function(e){
      var p=e.pair[1]; if(A.AngleFromSun(p,e.t)<15) return false;
      // visible that evening or the following morning from Pecan Island?
      var ss=rs('Sun',-1,new Date(e.t.getTime()-14*H)), sr=ss&&rs('Sun',+1,ss);
      var okE=ss&&horiz(p,new Date(ss.getTime()+75*60e3)).altitude>8, okM=sr&&horiz(p,new Date(sr.getTime()-75*60e3)).altitude>8;
      if(!okE&&!okM) return false;
      e.when=okE?'after sunset':'before dawn'; e.date=okE?ss:sr; return true;
    }).map(function(e){
      return {t:e.date,html:'<b>'+e.pair[0]+' and '+e.pair[1]+'</b> about '+Math.max(1,Math.round(e.sep))+'&deg; apart, '+e.when};
    });
    // Oppositions: outer planets at their biggest and brightest, next 12 months
    ['Mars','Jupiter','Saturn'].forEach(function(p){
      var t=A.SearchRelativeLongitude(p,0,now); if(t&&t.date-now<366*24*H) ev.push({t:t.date,html:'<b>'+p+' at opposition:</b> up all night and at its brightest'});
    });
    // Mercury and Venus at greatest elongation, next 6 months
    ['Mercury','Venus'].forEach(function(p){
      var e=A.SearchMaxElongation(p,now); if(e&&e.time.date-now<183*24*H) ev.push({t:e.time.date,html:'<b>'+p+' farthest from the Sun</b> ('+Math.round(e.elongation)+'&deg;), best seen '+(e.visibility==='evening'?'after sunset':'before dawn')});
    });
    // Eclipses
    var le=A.SearchLunarEclipse(now);
    for(var j=0;j<4&&le;j++){
      if(le.peak.date-now>3*366*24*H) break;
      if(horiz('Moon',le.peak.date).altitude>0){ ev.push({t:le.peak.date,html:'<b>'+le.kind.charAt(0).toUpperCase()+le.kind.slice(1)+' lunar eclipse</b>, visible from Pecan Island, peak '+time(le.peak.date)}); break; }
      le=A.NextLunarEclipse(le.peak);
    }
    var se=A.SearchLocalSolarEclipse(now,obs);
    if(se&&se.peak.time.date-now<4*366*24*H&&se.peak.altitude>0) ev.push({t:se.peak.time.date,html:'<b>'+se.kind.charAt(0).toUpperCase()+se.kind.slice(1)+' solar eclipse</b> seen from Pecan Island, peak '+time(se.peak.time.date)+'. Never look at the Sun without eclipse glasses.'});
    // Meteor showers (approximate peak nights)
    [['Quadrantid',0,3],['Lyrid',3,22],['Eta Aquariid',4,5],['Perseid',7,12],['Orionid',9,21],['Leonid',10,17],['Geminid',11,14]].forEach(function(m){
      var y=ct(now).y, t=new Date(Date.UTC(y,m[1],m[2],8));
      if(t<now-24*H) t=new Date(Date.UTC(y+1,m[1],m[2],8));
      if(t-now<75*24*H) ev.push({t:t,html:'<b>'+m[0]+' meteor shower</b> peaks around this night; best after midnight away from town lights'});
    });
    ev.sort(function(a,b){return a.t-b.t;});
    var seen={}; ev=ev.filter(function(e){var k=e.html; if(seen[k]) return false; seen[k]=1; return true;}).slice(0,9);
    document.getElementById('lv-events').innerHTML=ev.map(function(e){return '<li><span class="lv-date">'+day(e.t,true)+'</span>'+e.html+'</li>';}).join('')||'<li>No major sky events in the next few weeks.</li>';
  }
  if(document.readyState==='complete') run(); else window.addEventListener('load',run);
})();
