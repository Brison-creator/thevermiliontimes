const {chromium}=require('playwright'); const fs=require('fs');
(async()=>{
  const b=await chromium.launch(); const R={};
  for (const id of process.argv.slice(2)) {
    const p=await b.newPage({viewport:{width:1280,height:2400}});
    try {
      await p.goto('https://opportunities.ledfaststart.com/global/en/job/'+id,{waitUntil:'networkidle',timeout:60000}); await p.waitForTimeout(3000);
      const txt=await p.evaluate(()=>document.body.innerText);
      const apply=await p.evaluate(()=>Array.from(document.querySelectorAll('a')).filter(a=>/apply/i.test(a.innerText)).map(a=>a.href));
      R[id]={txt:txt.replace(/\n{2,}/g,'\n'),apply:[...new Set(apply)].slice(0,3),url:p.url()};
    } catch(e){ R[id]={err:String(e).slice(0,160)}; }
    await p.close();
  }
  fs.writeFileSync(process.env.OUT||'/tmp/lanow-jobs.json',JSON.stringify(R,null,1)); await b.close();
})();
