export function renderModelChoices(host,field,models,selected){
host.replaceChildren();field.value=selected||'';
if(!models.length){const p=document.createElement('p');p.textContent='No installed local models found. Restart after checking Ollama.';host.append(p);return;}
for(const row of models){
 const label=document.createElement('label'),radio=document.createElement('input'),text=document.createElement('span'),title=document.createElement('strong'),full=document.createElement('small');
 label.className='n-model-choice';radio.type='radio';radio.name='native-assistant-model';radio.value=row.name;radio.checked=row.name===selected;radio.setAttribute('aria-label',row.name);radio.onchange=()=>{if(radio.checked)field.value=row.name;};
 const parts=row.name.split('/'),base=parts.at(-1);title.textContent=(row.name.includes('HauhauCS')?'HauhauCS · ':'')+(row.family||'Model')+' · '+base;
 full.textContent=row.name;text.append(title,full);label.append(radio,text);host.append(label);
}
}
