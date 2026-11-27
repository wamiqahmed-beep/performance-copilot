const {spawn}=require('node:child_process'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const profile=fs.mkdtempSync(path.join(os.tmpdir(),'copilot-phase2-'));
const browser=spawn('C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',['--headless=new','--disable-gpu','--no-first-run','--remote-debugging-port=9238',`--user-data-dir=${profile}`,pathToFileURL(path.join(__dirname,'index.html')).href],{stdio:'ignore',windowsHide:true});
async function main(){
 let targets;for(let i=0;i<50;i++){try{targets=await(await fetch('http://127.0.0.1:9238/json')).json();if(targets.some(t=>t.type==='page'))break;}catch{}await new Promise(r=>setTimeout(r,300));}
 if(!targets)throw Error('Edge did not start');
 const socket=new WebSocket(targets.find(t=>t.type==='page').webSocketDebuggerUrl);await new Promise((yes,no)=>{socket.onopen=yes;socket.onerror=no});
 let id=0;const pending=new Map(),errors=[];
 socket.onmessage=e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.text);if(pending.has(m.id)){pending.get(m.id)(m);pending.delete(m.id)}};
 const send=(method,params={})=>new Promise(resolve=>{const n=++id;pending.set(n,resolve);socket.send(JSON.stringify({id:n,method,params}))});
 const evaluate=async expression=>{const m=await send('Runtime.evaluate',{expression,returnByValue:true});if(m.result.exceptionDetails)throw Error(JSON.stringify(m.result.exceptionDetails));return m.result.result.value};
 try{
  await send('Runtime.enable');await send('Page.enable');await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
  for(let i=0;i<40;i++){if(await evaluate("typeof ml !== 'undefined' && !!document.getElementById('forecast-table')"))break;await new Promise(r=>setTimeout(r,250));}
  for(const page of ['overview','countries','detail','segments','model','definitions','drivers']){
   const r=await evaluate(`nav('${page}');({title:document.querySelector('h1').textContent,body:document.getElementById('content').textContent.length,overflow:document.documentElement.scrollWidth>innerWidth})`);
   if(r.body<100||r.overflow)throw Error('Page failure '+JSON.stringify(r));console.log(page,JSON.stringify(r));
  }
  await evaluate("nav('segments')");const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});fs.writeFileSync(path.join(__dirname,'phase2-preview.png'),Buffer.from(shot.result.data,'base64'));
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  for(const page of ['overview','segments','model']){if(await evaluate(`nav('${page}');document.documentElement.scrollWidth>innerWidth`))throw Error('Mobile overflow '+page);}
  await send('Page.navigate',{url:pathToFileURL(path.join(__dirname,'model-note.html')).href});
  for(let i=0;i<40;i++){if(await evaluate("!!document.getElementById('scores') && document.getElementById('scores').children.length===3"))break;await new Promise(r=>setTimeout(r,250));}
  await send('Emulation.setDeviceMetricsOverride',{width:1000,height:1200,deviceScaleFactor:1,mobile:false});
  const pdf=await send('Page.printToPDF',{printBackground:true,preferCSSPageSize:true});fs.writeFileSync(path.join(__dirname,'model-note.pdf'),Buffer.from(pdf.result.data,'base64'));
  if(errors.length)throw Error(errors.join('; '));console.log('Offline browser checks passed; printable PDF generated.');
 }finally{socket.close();}
}
main().catch(e=>{console.error(e);process.exitCode=1}).finally(()=>browser.kill());
