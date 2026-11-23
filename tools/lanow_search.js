const {chromium}=require('playwright');
(async()=>{
  const b=await chromium.launch(); const out={};
  for (const q of process.argv.slice(2)) {
    const p=await b.newPage({viewport:{width:1280,height:2400}});
    try {
      const u='https://opportunities.ledfaststart.com/global/en/search-results?keywords='+encodeURIComponent(q);
      await p.goto(u,{waitUntil:'networkidle',timeout:60000}); await p.waitForTimeout(3500);
      const txt=await p.evaluate(()=>document.body.innerText);
      const m=txt.match(/Showing (\d+) results?/); 
      const jobs=await p.evaluate(()=>Array.from(document.querySelectorAll('a')).filter(a=>/\/job\//.test(a.href)).map(a=>{const li=a.closest('li')||a.parentElement; return {href:a.href,t:(li?li.innerText:a.innerText).replace(/\s+/g,' ').slice(0,260)}}));
      const seen=new Set(); const J=jobs.filter(j=>!seen.has(j.href)&&seen.add(j.href));
      console.log('=====',q,'| count',m?m[1]:'?','| listed',J.length);
      J.slice(0,25).forEach(j=>console.log('  -',j.t.replace(/Save job.*$/,'').slice(0,210),'||',j.href.split('/job/')[1]));
    } catch(e){ console.log('ERR',q,String(e).slice(0,160)); }
    await p.close();
  }
  await b.close();
})();
