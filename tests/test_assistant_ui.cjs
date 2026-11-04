// DOM contract tests in Node. No browser or layout simulation is claimed.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class Element{constructor(tag='div'){this.tagName=tag;this.children=[];this.events={};this.dataset={};this.value='';this.hidden=false;this.style={};this.classList={add(){},remove(){}};this.textContent='';}append(...items){this.children.push(...items);}replaceChildren(...items){this.children=items;}addEventListener(name,fn){(this.events[name]??=[]).push(fn);}setAttribute(){}focus(){}scrollIntoView(){}click(){for(const fn of this.events.click||[])fn();}requestSubmit(){return Promise.all((this.events.submit||[]).map(fn=>fn({preventDefault(){}})));}}
const elements=new Map(),get=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
const html=fs.readFileSync('web/index.html','utf8');
for(const match of html.matchAll(/id="([^"]+)"/g))get(match[1]);
get('provider').value='fallback';
const localized=[];for(const match of html.matchAll(/data-i="([^"]+)"/g)){const el=new Element();el.dataset.i=match[1];localized.push(el);}
let requests=[];
const result={question:'Qual é o resumo da cobertura?',provider:'fallback',status:'answered',selected_provider:{model:'qwen/test'},trace:[{step:'plan',plan:{action:'summary'}}],evidence:{question:'summary',coverage:{purchases:1081,covered_purchases:1080,contracts:125,purchases_with_contracts:85,none_returned:995,unknown_awarded_values:749},scope:{uf:'PI',modality:6,date_start:'2026-08-01',date_end:'2026-10-31'},sources:{coverage_report:'runs/fixed.json'},coverage_report_sha256:'a'.repeat(64),result:[]}};
const context={document:{getElementById:get,querySelectorAll:()=>localized,querySelector:()=>get('h1'),createElement:tag=>new Element(tag),createTextNode:s=>s,documentElement:{},body:new Element()},fetch:async(url,options)=>{requests.push({url,options});return {ok:true,json:async()=>url==='/api/session'?{token:'test-session-token'}:structuredClone(result)};},URL:{createObjectURL:()=>'',revokeObjectURL(){}},Blob,matchMedia:()=>({matches:true}),setTimeout:()=>{},Date,console};
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
get('new-session').click();assert.equal(get('question').value,'');assert.equal(get('conversation').hidden,true);
assert.equal(get('history').children[0].textContent,'Your questions will appear here.');
console.log('Assistant DOM contract passed: discovery, submit, response, suggestions, history, language, reset, session.');
})().catch(error=>{console.error(error);process.exitCode=1;});
