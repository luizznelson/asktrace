// DOM contract tests in Node. No browser or layout simulation is claimed.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class Element{constructor(tag='div'){this.tagName=tag;this.children=[];this.events={};this.dataset={};this.value='';this.hidden=false;this.style={};this.classList={add(){},remove(){}};this.textContent='';}append(...items){this.children.push(...items);}replaceChildren(...items){this.children=items;}addEventListener(name,fn){(this.events[name]??=[]).push(fn);}setAttribute(){}focus(){}scrollIntoView(){}click(){for(const fn of this.events.click||[])fn();}requestSubmit(){return Promise.all((this.events.submit||[]).map(fn=>fn({preventDefault(){}})));}}
const elements=new Map(),get=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
const html=fs.readFileSync('web/index.html','utf8');
for(const match of html.matchAll(/id="([^"]+)"/g))get(match[1]);
get('provider').value='fallback';
const localized=[];for(const match of html.matchAll(/data-i="([^"]+)"/g)){const el=new Element();el.dataset.i=match[1];localized.push(el);}
const store=new Map();
const storage={getItem:key=>store.get(key)||null,setItem:(key,value)=>store.set(key,value),removeItem:key=>store.delete(key)};
const datasets=[{id:'original',coverage:'runs/fixed.json',start:'2026-08-01',end:'2026-10-31',purchases:1081,covered:1080,contracts:125,unknown_awarded:749,excluded:1}];
let requests=[];
const result={question:'Qual é o resumo da cobertura?',provider:'fallback',status:'answered',selected_provider:{model:'qwen/test'},trace:[{step:'plan',plan:{action:'summary'}}],evidence:{question:'summary',coverage:{purchases:1081,covered_purchases:1080,contracts:125,purchases_with_contracts:85,none_returned:995,unknown_awarded_values:749},scope:{uf:'PI',modality:6,date_start:'2026-08-01',date_end:'2026-10-31'},sources:{coverage_report:'runs/fixed.json'},coverage_report_sha256:'a'.repeat(64),result:[]}};
const context={document:{getElementById:get,querySelectorAll:selector=>selector==="[data-i]"?localized:selector.includes("dateShort")?localized.filter(el=>el.dataset.i==="dateShort"):[],querySelector:()=>get('h1'),createElement:tag=>new Element(tag),createTextNode:s=>s,documentElement:{},body:new Element()},fetch:async(url,options)=>{requests.push({url,options});return {ok:true,json:async()=>url==='/api/session'?{token:'test-session-token',datasets,default_dataset:'original'}:structuredClone(result)};},URL:{createObjectURL:()=>'',revokeObjectURL(){}},Blob,matchMedia:()=>({matches:true}),setTimeout:()=>{},Date,console,sessionStorage:storage,Intl};
vm.createContext(context);vm.runInContext(fs.readFileSync('web/app.js','utf8'),context);
(async()=>{await new Promise(resolve=>setImmediate(resolve));
assert.equal(get('discovery').children.length,3);assert.equal(get('submit').disabled,false);
assert.equal(localized.filter(el=>el.textContent===el.dataset.i).length,0,'Every displayed label has a translation');
get('discovery').children[0].click();assert.match(get('question').value,/cobertura/);
await get('ask-form').requestSubmit();assert.equal(requests.filter(r=>r.url==='/api/ask').length,1);
assert.equal(get('asked-question').textContent,result.question);assert.match(get('answer').textContent,/125/);
assert.equal(get('next-questions').children.length,2);assert.equal(get('history').children.length,1);
assert.equal(get('thinking').hidden,true);assert.equal(get('submit').disabled,false);
get('language').click();assert.match(get('answer').textContent,/dataset/);assert.equal(context.document.documentElement.lang,'en');
get('next-questions').children[0].click();assert.match(get('question').value,/municípios/);
get('history').children[0].click();assert.match(get('answer').textContent,/125/);
const saved=JSON.parse(store.get('asktrace.session.v1'));assert.equal(saved.entries.length,1);assert.equal(saved.entries[0].dataset,'original');
const before=requests.length;
vm.runInContext("sessionHistory=[];latest=null;initializeDatasets({datasets:"+JSON.stringify(datasets)+",default_dataset:'original'})",context);
assert.equal(get('history').children.length,1);assert.match(get('answer').textContent,/125/);
assert.equal(requests.length,before,'Restoring history makes no API request');
get('new-session').click();assert.equal(get('question').value,'');assert.equal(get('conversation').hidden,true);
assert.equal(get('history').children[0].textContent,'Your questions will appear here.');
assert.equal(JSON.parse(store.get('asktrace.session.v1')).entries.length,0);
store.set('asktrace.session.v1','not-json');assert.equal(vm.runInContext('readSession()',context),null);
store.set('asktrace.session.v1',JSON.stringify({version:999,entries:[]}));assert.equal(vm.runInContext('readSession()',context),null);
console.log('Assistant session persistence and DOM contract passed: discovery, submit, response, suggestions, history, language, reset, session.');
})().catch(error=>{console.error(error);process.exitCode=1;});
