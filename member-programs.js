/* Source-verified association program announcements; never convert undated leads to Events. */
(()=>{'use strict';
const widgets=[...document.querySelectorAll('[data-ecosystem-programs]')];
if(!widgets.length)return;
for(const root of widgets){
 const section=root.closest('[data-ecosystem-program-section]');
 const org=root.dataset.organizerId||'';
 const source=root.dataset.source||'';
 if(!org||!source||!section)continue;
 fetch(source,{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('No registry');return r.json()}).then(d=>{
  if(d.schemaVersion!==1||d.sourceRepository!=='880rzz/okoszisztema'||!Array.isArray(d.programCandidates))throw Error('Wrong source');
  const entries=d.programCandidates.filter(p=>p&&p.organizerId===org&&p.status==='date-unverified'&&p.title&&p.sourceUrl);
  if(!entries.length)return;
  const grid=document.createElement('div');grid.className='event-grid';
  for(const p of entries){
   let url;try{url=new URL(p.sourceUrl);if(url.protocol!=='https:')continue;}catch{continue;}
   const article=document.createElement('article');article.className='event';
   const state=document.createElement('div');state.className='date';state.textContent='Időpont ellenőrzés alatt';
   const title=document.createElement('h3');title.textContent=p.title;
   const details=document.createElement('p');details.textContent='A szervezői hivatkozás elérhető, az esemény dátuma és helyszíne még nincs megerősítve.';
   const links=document.createElement('div');links.className='event-links';
   const anchor=document.createElement('a');anchor.href=url.href;anchor.target='_blank';anchor.rel='noopener noreferrer';anchor.textContent='Eredeti szervezői forrás ↗';
   links.append(anchor);article.append(state,title,details,links);grid.append(article);
  }
  if(grid.children.length){root.replaceChildren(grid);section.hidden=false;}
 }).catch(()=>{section.hidden=true;});
}
})();
