const {spawn} = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const profile=fs.mkdtempSync(path.join(os.tmpdir(),'copilot-qa-'));
const browser=spawn('C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',['--headless=new','--disable-gpu','--no-first-run','--remote-debugging-port=9227',`--user-data-dir=${profile}`,'http://127.0.0.1:4174/'],{stdio:'ignore',windowsHide:true});
async function main(){
 let targets; for(let i=0;i<30;i++){try{targets=await (await fetch('http://127.0.0.1:9227/json')).json();break}catch{await new Promise(r=>setTimeout(r,300))}} if(!targets)throw Error('Browser did not start');
 const socket=new WebSocket(targets.find(t=>t.type==='page').webSocketDebuggerUrl); await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject});
 let id=0,pending=new Map(),errors=[];socket.onmessage=e=>{let m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.text);if(m.id&&pending.has(m.id)){pending.get(m.id)(m);pending.delete(m.id)}};
 const send=(method,params={})=>new Promise(resolve=>{let n=++id;pending.set(n,resolve);socket.send(JSON.stringify({id:n,method,params}))});
 await send('Runtime.enable');await send('Page.enable');await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
 await new Promise(r=>setTimeout(r,1500));await send('Runtime.evaluate',{expression:"nav('drivers')"});await new Promise(r=>setTimeout(r,800));
 let data=await send('Runtime.evaluate',{expression:"({title:document.querySelector('h1').textContent,hero:document.querySelector('.variance-hero h2').textContent,drivers:document.querySelectorAll('.driver-item').length,overflow:document.documentElement.scrollWidth>innerWidth})",returnByValue:true});if(!data.result.result.value||data.result.result.value.drivers!==4||data.result.result.value.overflow)throw Error('Variance page did not render correctly');console.log(JSON.stringify(data.result.result.value));
 let image=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});fs.writeFileSync(path.join(__dirname,'qa-variance.png'),Buffer.from(image.result.data,'base64'));
 await send('Runtime.evaluate',{expression:"setFilter('brand','Beko');setFilter('channel','Online');nav('countries');detail('Germany')"});let check=await send('Runtime.evaluate',{expression:"document.querySelector('#content').textContent.includes('Germany revenue trend')",returnByValue:true});console.log('Country drill-down:',check.result.result.value,'Browser errors:',errors.length);if(errors.length||!check.result.result.value)throw Error('Browser QA failed');socket.close();
}
main().catch(e=>{console.error(e);process.exitCode=1}).finally(()=>browser.kill());
