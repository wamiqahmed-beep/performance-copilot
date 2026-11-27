const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const path=require('node:path');
const elements={};
for(const id of ['nav','filters','eyebrow','title','subtitle','guide','content','table','forecast-table','foot'])elements[id]={innerHTML:'',textContent:'',insertAdjacentHTML(position,html){this.innerHTML=position==='afterbegin'?html+this.innerHTML:this.innerHTML+html}};
const context=vm.createContext({window:{},document:{getElementById:id=>elements[id],querySelector:()=>elements.foot},console,Blob,URL,setTimeout});
const html=fs.readFileSync(path.join(__dirname,'index.html'),'utf8');
for(const match of html.matchAll(/<script(?: src="([^"]+)")?>([\s\S]*?)<\/script>/g))vm.runInContext(match[1]?fs.readFileSync(path.join(__dirname,match[1]),'utf8'):match[2],context);
for(const page of ['overview','drivers','countries','detail','definitions','segments','model']){
 vm.runInContext(`nav('${page}')`,context);assert.ok(elements.content.innerHTML.length);assert.ok(!elements.content.innerHTML.includes('undefined'));console.log(page+': rendered');
}
assert.equal(vm.runInContext('rows.length',context),3888);
for(const [v,label] of [[.05,'Within range'],[-.05,'Within range'],[.050001,'Above +5%'],[-.050001,'Below -5%']])assert.equal(vm.runInContext(`flagText(${v})`,context),label);
vm.runInContext("nav('countries');forecastQuery='Germany'",context);assert.ok(vm.runInContext('forecastTable()',context).includes('Germany'));assert.ok(!vm.runInContext('forecastTable()',context).includes('Romania'));
vm.runInContext("forecastQuery='';state.country='Germany';nav('overview')",context);assert.ok(!vm.runInContext('forecastTable()',context).includes('Romania'));
vm.runInContext("state.country='All';forecastSortBy('prediction');forecastSortBy('prediction');state.brand='Beko';state.channel='Online';nav('overview')",context);
assert.ok(elements.content.innerHTML.includes('country totals, all brands/channels'));
vm.runInContext("detail('Germany')",context);assert.ok(vm.runInContext('forecastTable()',context).includes('Germany'));assert.ok(!vm.runInContext('forecastTable()',context).includes('Romania'));
const data=context.window.MODEL_DATA;
assert.equal(data.evaluation.rows.length,36);assert.equal(data.forecasts.length,6);
assert.equal(data.segments.reduce((n,s)=>n+s.size,0),6);
for(const r of data.forecasts)assert.ok(Math.abs(r.predicted_gap-(r.prediction/r.budget-1))<1e-8);
for(const r of data.evaluation.rows)assert.ok(Math.abs(r.error-(r.prediction-r.revenue))<1e-7);
console.log('Phase 2: flags, scope, sorting, search, drill-down and exported reconciliations passed.');
