const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(require('node:path').join(__dirname, 'index.html'), 'utf8');
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const elements = Object.fromEntries(['nav','filters','eyebrow','title','subtitle','guide','content','table'].map(id => [id, {innerHTML:'',textContent:''}]));
const context = vm.createContext({document:{getElementById:id=>elements[id],createElement:()=>({click(){}})},console,Blob,URL,setTimeout});
for (const script of scripts) vm.runInContext(script, context, {timeout:5000});
for (const page of ['overview','drivers','countries','detail','definitions']) {
  vm.runInContext(`nav('${page}')`, context);
  if (!elements.content.innerHTML.length) throw Error(`Empty page: ${page}`);
  console.log(`${page}: rendered`);
}
vm.runInContext("setFilter('brand','Beko');setFilter('channel','Online');detail('Germany')",context);
if (!elements.content.innerHTML.includes('Germany revenue trend')) throw Error('Country drill-down failed');
const residual = vm.runInContext('(()=>{let r=current(),m=metrics(r),b=bridge(r);return m.a-m.b-b.volume-b.mix-b.price-b.fx})()',context);
if (Math.abs(residual)>0.01) throw Error(`Bridge does not reconcile: ${residual}`);
console.log('Filters and country drill-down: rendered');
console.log(`Bridge reconciliation residual: ${residual}`);
const csv=fs.readFileSync(require('node:path').join(__dirname,'dummy-pnl.csv'),'utf8').trim().split(/\r?\n/);
if(csv.length!==1945)throw Error(`Expected 1944 data rows; got ${csv.length-1}`);
const csvTotal=csv.slice(1).reduce((sum,line)=>{const v=line.split(',');return sum+Number(v[8])*Number(v[12])},0);
const appTotal=vm.runInContext('rows.reduce((s,r)=>s+r.actual_revenue_local*r.actual_fx,0)',context);
if(Math.abs(csvTotal-appTotal)/appTotal>0.0001)throw Error('CSV totals do not match dashboard dataset');
for(const country of ['All','Türkiye','Germany','United Kingdom','France','Poland','Romania'])for(const brand of ['All','Beko','Arçelik','Grundig']){
  const result=vm.runInContext(`state.country=${JSON.stringify(country)};state.brand=${JSON.stringify(brand)};state.channel='All';state.period='2025-12';(()=>{let r=current(),m=metrics(r),b=bridge(r);return m.a-m.b-b.volume-b.mix-b.price-b.fx})()`,context);
  if(Math.abs(result)>0.01)throw Error(`Bridge failed for ${country}/${brand}: ${result}`);
}
vm.runInContext("state.country='All';state.brand='All';state.query='Germany';nav('countries')",context);
if(!elements.content.innerHTML.includes('Germany')||!elements.content.innerHTML.includes('Country detail table'))throw Error('Country search rendering failed');
vm.runInContext("sortBy('a');sortBy('a')",context);
const flags=vm.runInContext("state.query='';table([{name:'Boundary',a:105,variance:.05,ly:100,rate:.3},{name:'Above',a:106,variance:.06,ly:100,rate:.3},{name:'Below',a:94,variance:-.06,ly:100,rate:.3}])",context);
for(const expected of ['Within range','Above +5%','Below −5%'])if(!flags.includes(expected))throw Error(`Missing flag: ${expected}`);
console.log(`Dataset: ${csv.length-1} rows; totals match within CSV rounding`);
console.log('Bridge: 28 country and brand selections reconciled; table search, sorting and flag boundaries executed');
