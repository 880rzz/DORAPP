(() => {
  const root = document.body;
  const iso = (root.dataset.country || "").toLowerCase();
  if (!iso) return;

  const $ = (s) => document.querySelector(s);
  const $$ = (s) => [...document.querySelectorAll(s)];
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, m => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[m]));
  const norm = (v) => String(v ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLocaleLowerCase("hu").trim();
  const collator = new Intl.Collator("hu",{sensitivity:"base"});
  const uniq = (a) => [...new Set(a.filter(Boolean).map(x=>String(x).trim()).filter(Boolean))].sort(collator.compare);

  let orgs=[], education=[], events=[], activeRegion="";
  let regionNames={};

  const regionOf = (x) => String(x?.region || x?.state || (x?.scope==="national" ? "Országos" : "") || "Régió nélkül");
  const regionLabel = (x) => regionNames[x] || x;

  function activitiesOf(o){
    return [...(o.activities||[]), ...(o.categories||[]), ...(o.activityCategories||[])].filter(Boolean);
  }
  function socialLinks(o){
    const rows = [];
    if(o.website) rows.push(["Weboldal",o.website]);
    if(o.facebook) rows.push(["Facebook",o.facebook]);
    if(o.instagram) rows.push(["Instagram",o.instagram]);
    if(o.youtube) rows.push(["YouTube",o.youtube]);
    if(o.linkedin) rows.push(["LinkedIn",o.linkedin]);
    for(const c of (o.publicChannels||[])){
      if(c?.url && !rows.some(x=>x[1]===c.url)) rows.push([c.label||c.platform||"Közösségi oldal",c.url]);
    }
    return rows;
  }
  function calendarSummary(o){
    const sources=(o.calendarSources||[]).filter(x=>x?.url);
    if(!sources.length) return "";
    const ingest=sources.filter(x=>x.ingestEvents).length;
    return ingest ? `${sources.length} programforrás · ${ingest} automatikus` : `${sources.length} programforrás`;
  }

  function card(o){
    const region=regionLabel(regionOf(o));
    const socials=socialLinks(o).slice(0,3).map(([l,u])=>`<a href="${esc(u)}" target="_blank" rel="noopener external">${esc(l)} ↗</a>`).join("");
    const cal=calendarSummary(o);
    return `<article class="card country-org-card" data-org-id="${esc(o.id)}" data-region="${esc(regionOf(o))}">
      <div class="meta">${esc(region)} · ${esc(o.city||"országos")} · ${esc(o.type||"szervezet")}</div>
      <h3>${esc(o.name)}</h3>
      <p>${esc(o.summary||o.intro||"Ellenőrzött magyar diaszpóra-szervezet.")}</p>
      ${cal?`<p class="site-status"><strong>Programok:</strong> ${esc(cal)}</p>`:""}
      <div class="links"><a href="organizations/${encodeURIComponent(o.id)}.html">Teljes adatlap →</a>${socials}</div>
    </article>`;
  }

  function buildOptions(){
    const regionSel=$("#countryRegion"), citySel=$("#countryCity"), orgSel=$("#countryOrganization"), actSel=$("#countryActivity"), progSel=$("#countryProgram");
    const currentRegion=regionSel?.value||"";
    const regions=uniq([...orgs.map(regionOf),...education.map(regionOf),...events.map(regionOf)].filter(x=>x&&x!=="Régió nélkül"));
    if(regionSel) regionSel.innerHTML='<option value="">Minden tartomány / régió</option>'+regions.map(x=>`<option value="${esc(x)}">${esc(regionLabel(x))}</option>`).join("");
    if(regionSel && regions.includes(currentRegion)) regionSel.value=currentRegion;

    const chosenRegion=regionSel?.value||activeRegion||"";
    const scope = x => !chosenRegion || regionOf(x)===chosenRegion;
    const cities=uniq([...orgs.filter(scope).map(x=>x.city),...education.filter(scope).map(x=>x.city),...events.filter(scope).map(x=>x.city)]);
    if(citySel) citySel.innerHTML='<option value="">Minden város</option>'+cities.map(x=>`<option>${esc(x)}</option>`).join("");
    if(orgSel) orgSel.innerHTML='<option value="">Minden szervezet</option>'+orgs.filter(scope).filter(x=>x.entityClass!=="activity").sort((a,b)=>collator.compare(a.name||"",b.name||"")).map(x=>`<option value="${esc(x.id)}">${esc(x.name)}</option>`).join("");
    const acts=uniq(orgs.filter(scope).flatMap(activitiesOf));
    if(actSel) actSel.innerHTML='<option value="">Minden tevékenység</option>'+acts.map(x=>`<option>${esc(x)}</option>`).join("");
    if(progSel) progSel.innerHTML='<option value="">Minden program</option>'+events.filter(scope).sort((a,b)=>String(a.startDate||"").localeCompare(String(b.startDate||""))).map(x=>`<option value="${esc(x.id)}">${esc(x.name||x.title)}</option>`).join("");
  }

  function filters(){
    return {
      region: $("#countryRegion")?.value || activeRegion || "",
      city: $("#countryCity")?.value || "",
      org: $("#countryOrganization")?.value || "",
      activity: $("#countryActivity")?.value || "",
      program: $("#countryProgram")?.value || "",
      contact: norm($("#countryContact")?.value||""),
      address: norm($("#countryAddress")?.value||""),
      query: norm($("#countryQuery")?.value||"")
    };
  }

  function matchingOrg(o,f){
    if(o.entityClass==="activity") return false;
    if(f.region && regionOf(o)!==f.region) return false;
    if(f.city && o.city!==f.city) return false;
    if(f.org && o.id!==f.org) return false;
    if(f.activity && !activitiesOf(o).some(x=>x===f.activity)) return false;
    if(f.contact && !norm([o.contactName,o.email,o.phone].filter(Boolean).join(" ")).includes(f.contact)) return false;
    if(f.address && !norm([o.address,o.city,o.region,o.state,...(o.serviceLocations||[]).flatMap(x=>[x.address,x.city,x.label])].filter(Boolean).join(" ")).includes(f.address)) return false;
    if(f.program && !events.some(e=>(e.organizerId===o.id||e.organizationId===o.id)&&e.id===f.program)) return false;
    if(f.query){
      const hay=norm([o.name,o.city,o.region,o.state,o.type,o.intro,o.summary,o.email,o.phone,o.address,...activitiesOf(o),...(o.targetGroups||[])].filter(Boolean).join(" "));
      if(!f.query.split(/\s+/).every(t=>hay.includes(t))) return false;
    }
    return true;
  }

  function renderOrganizations(){
    const f=filters();
    const list=orgs.filter(o=>matchingOrg(o,f)).sort((a,b)=>collator.compare(a.name||"",b.name||""));
    const grid=$("#countryOrgGrid"), count=$("#countryOrgCount"), empty=$("#countryOrgEmpty");
    if(count) count.textContent=`${list.length} találat`;
    if(grid) grid.innerHTML=list.map(card).join("");
    if(empty) empty.hidden=!!list.length;
    updateRegionMap(list);
  }

  function matchingEducation(x,f){
    if(f.region && regionOf(x)!==f.region) return false;
    if(f.city && x.city!==f.city) return false;
    if(f.address && !norm([x.venue,x.address,x.city,x.region,x.state].filter(Boolean).join(" ")).includes(f.address)) return false;
    if(f.query && !norm([x.name,x.city,x.region,x.type,x.intro,x.summary,x.venue].filter(Boolean).join(" ")).includes(f.query)) return false;
    return true;
  }
  function renderEducation(){
    const f=filters();
    const list=education.filter(x=>matchingEducation(x,f)).sort((a,b)=>collator.compare(a.name||"",b.name||""));
    const grid=$("#countryEducationGrid"), count=$("#countryEducationCount"), empty=$("#countryEducationEmpty");
    if(count) count.textContent=`${list.length} találat`;
    if(grid) grid.innerHTML=list.map(x=>`<article class="card"><div class="meta">${esc(regionLabel(regionOf(x)))} · ${esc(x.city||"")}</div><h3>${esc(x.name)}</h3><p>${esc(x.summary||x.intro||x.type||"Magyar oktatási lehetőség")}</p><div class="links"><a href="education/${encodeURIComponent(x.id)}.html">Teljes adatlap →</a>${x.website?`<a href="${esc(x.website)}" target="_blank" rel="noopener external">Weboldal ↗</a>`:""}</div></article>`).join("");
    if(empty) empty.hidden=!!list.length;
  }
  function renderEvents(){
    const f=filters(), now=new Date();
    const list=events.filter(e=>{
      if(e.endDate && new Date(e.endDate)<now) return false;
      if(f.region && regionOf(e)!==f.region) return false;
      if(f.city && e.city!==f.city) return false;
      if(f.program && e.id!==f.program) return false;
      if(f.org && !(e.organizerId===f.org||e.organizationId===f.org)) return false;
      if(f.address && !norm([e.address,e.venue,e.city,e.region].filter(Boolean).join(" ")).includes(f.address)) return false;
      if(f.query && !norm([e.name,e.title,e.organizer,e.city,e.region,e.venue,e.description,...(e.categories||[])].filter(Boolean).join(" ")).includes(f.query)) return false;
      return true;
    }).sort((a,b)=>String(a.startDate||a.date||"").localeCompare(String(b.startDate||b.date||"")));
    const grid=$("#countryEventGrid"), count=$("#countryEventCount"), empty=$("#countryEventEmpty");
    if(count) count.textContent=`${list.length} közelgő program`;
    if(grid) grid.innerHTML=list.map(e=>`<article class="event"><div class="date">${esc(e.startDate||e.date||"")}</div><h3>${esc(e.name||e.title)}</h3><p>${esc([e.organizer,e.city,e.venue].filter(Boolean).join(" · "))}</p><div class="event-links"><a href="events/${encodeURIComponent(e.id)}.html">Program részletei →</a>${e.sourceUrl?`<a href="${esc(e.sourceUrl)}" target="_blank" rel="noopener external">Eredeti forrás ↗</a>`:""}</div></article>`).join("");
    if(empty) empty.hidden=!!list.length;
  }

  function renderDirectoryResults(){
    const f=filters();
    const orgList=orgs.filter(o=>matchingOrg(o,f)).slice(0,12);
    const eduList=education.filter(x=>matchingEducation(x,f)).slice(0,8);
    const eventList=events.filter(e=>{
      if(f.region && regionOf(e)!==f.region) return false;
      if(f.city && e.city!==f.city) return false;
      if(f.program && e.id!==f.program) return false;
      if(f.org && !(e.organizerId===f.org||e.organizationId===f.org)) return false;
      if(f.query && !norm([e.name,e.title,e.city,e.venue,e.organizer,e.description].filter(Boolean).join(" ")).includes(f.query)) return false;
      return true;
    }).slice(0,8);
    const root=$("#countryDirectoryResults"), count=$("#countryDirectoryCount");
    const total=orgList.length+eduList.length+eventList.length;
    if(count) count.textContent=`${total} közvetlen találat az aktuális szűrésben`;
    if(!root) return;
    root.innerHTML=[
      ...orgList.map(o=>`<a class="directory-result" href="organizations/${encodeURIComponent(o.id)}.html"><span>Szervezet · ${esc(regionLabel(regionOf(o)))}</span><strong>${esc(o.name)}</strong><small>${esc([o.city,o.type].filter(Boolean).join(" · "))}</small></a>`),
      ...eduList.map(x=>`<a class="directory-result" href="education/${encodeURIComponent(x.id)}.html"><span>Oktatás · ${esc(regionLabel(regionOf(x)))}</span><strong>${esc(x.name)}</strong><small>${esc([x.city,x.type].filter(Boolean).join(" · "))}</small></a>`),
      ...eventList.map(e=>`<a class="directory-result" href="events/${encodeURIComponent(e.id)}.html"><span>Program · ${esc(regionLabel(regionOf(e)))}</span><strong>${esc(e.name||e.title)}</strong><small>${esc([e.startDate||e.date,e.city].filter(Boolean).join(" · "))}</small></a>`)
    ].join("");
  }

  function apply(){
    renderDirectoryResults();
    renderOrganizations();
    renderEducation();
    renderEvents();
  }

  function regionCounts(){
    const m={};
    for(const o of orgs){
      if(o.entityClass==="activity") continue;
      const r=regionOf(o);
      if(r && r!=="Régió nélkül") m[r]=(m[r]||0)+1;
    }
    return m;
  }
  function updateRegionMap(filtered){
    const counts=regionCounts();
    const filteredCounts={};
    for(const o of (filtered||orgs)){
      if(o.entityClass==="activity") continue;
      const r=regionOf(o); if(r) filteredCounts[r]=(filteredCounts[r]||0)+1;
    }
    $$(".country-region-button").forEach(b=>{
      const r=b.dataset.region;
      const n=counts[r]||0;
      const filteredN=filteredCounts[r]||0;
      b.classList.toggle("active",r===activeRegion);
      b.classList.toggle("muted-by-filter",filtered && filteredN===0);
      const c=b.querySelector(".map-count"); if(c)c.textContent=n;
      b.title=`${regionLabel(r)} – ${n} ellenőrzött magyar szervezet`;
      b.setAttribute("aria-label",b.title);
    });
    const s=$("#countryMapSummary");
    if(s) s.textContent=activeRegion ? `${regionLabel(activeRegion)}: ${counts[activeRegion]||0} ellenőrzött magyar szervezet` : `${Object.values(counts).reduce((a,b)=>a+b,0)} ellenőrzött szervezet a területi bontásban`;
  }

  function bindCountryMapController(obj, doc){
    const viewport=obj.closest(".country-map-viewport");
    if(!viewport || !doc?.documentElement) return;
    const surface=doc.documentElement;
    const toolbar=viewport.parentElement?.querySelector(".country-map-toolbar");
    const zoomIn=toolbar?.querySelector("[data-country-map-zoom-in]");
    const zoomOut=toolbar?.querySelector("[data-country-map-zoom-out]");
    const resetBtn=toolbar?.querySelector("[data-country-map-reset]");
    const status=toolbar?.querySelector("[data-country-map-status]");
    const pointers=new Map();
    let scale=1, x=0, y=0, dragStart=null, pinchStart=null, moved=false;
    const MIN=1, MAX=3, STEP=.5;
    function clamp(){
      const rect=viewport.getBoundingClientRect();
      const maxX=Math.max(0,rect.width*(scale-1)/2);
      const maxY=Math.max(0,rect.height*(scale-1)/2);
      x=Math.max(-maxX,Math.min(maxX,x)); y=Math.max(-maxY,Math.min(maxY,y));
      if(scale<=1){x=0;y=0;}
    }
    function render(){
      clamp();
      obj.style.transform=`translate3d(${x}px,${y}px,0) scale(${scale})`;
      viewport.classList.toggle("is-zoomed",scale>1);
      if(status) status.textContent=`${Math.round(scale*100)}%`;
      if(zoomOut) zoomOut.disabled=scale<=MIN;
      if(zoomIn) zoomIn.disabled=scale>=MAX;
    }
    function setScale(next, clientX, clientY){
      const old=scale; scale=Math.max(MIN,Math.min(MAX,next));
      if(clientX!=null && clientY!=null && old!==scale){
        const r=viewport.getBoundingClientRect(), dx=clientX-(r.left+r.width/2), dy=clientY-(r.top+r.height/2), ratio=scale/old;
        x=dx-(dx-x)*ratio; y=dy-(dy-y)*ratio;
      }
      render();
    }
    function reset(){scale=1;x=0;y=0;pointers.clear();dragStart=null;pinchStart=null;render();}
    zoomIn?.addEventListener("click",()=>setScale(scale+STEP));
    zoomOut?.addEventListener("click",()=>setScale(scale-STEP));
    resetBtn?.addEventListener("click",reset);
    const point=e=>({x:e.clientX,y:e.clientY});
    surface.style.touchAction="none";
    surface.addEventListener("pointerdown",e=>{
      pointers.set(e.pointerId,point(e)); moved=false;
      try{surface.setPointerCapture(e.pointerId);}catch(_){}
      if(pointers.size===1 && scale>1){dragStart={px:e.clientX,py:e.clientY,x,y};viewport.classList.add("is-dragging");}
      else if(pointers.size===2){const p=[...pointers.values()];pinchStart={distance:Math.hypot(p[1].x-p[0].x,p[1].y-p[0].y),scale};dragStart=null;viewport.classList.add("is-dragging");}
    });
    surface.addEventListener("pointermove",e=>{
      if(!pointers.has(e.pointerId)) return;
      pointers.set(e.pointerId,point(e));
      if(pointers.size===2){
        const p=[...pointers.values()], distance=Math.hypot(p[1].x-p[0].x,p[1].y-p[0].y), cx=(p[0].x+p[1].x)/2, cy=(p[0].y+p[1].y)/2;
        if(pinchStart?.distance){setScale(pinchStart.scale*distance/pinchStart.distance,cx,cy);moved=true;e.preventDefault();}
      }else if(dragStart && scale>1){
        const dx=e.clientX-dragStart.px, dy=e.clientY-dragStart.py;
        if(Math.abs(dx)+Math.abs(dy)>4)moved=true;
        x=dragStart.x+dx;y=dragStart.y+dy;render();e.preventDefault();
      }
    },{passive:false});
    function endPointer(e){pointers.delete(e.pointerId);try{surface.releasePointerCapture(e.pointerId);}catch(_){}if(pointers.size<2)pinchStart=null;if(!pointers.size){dragStart=null;viewport.classList.remove("is-dragging");}}
    surface.addEventListener("pointerup",endPointer);
    surface.addEventListener("pointercancel",endPointer);
    surface.addEventListener("click",e=>{if(moved){e.preventDefault();e.stopPropagation();moved=false;}},true);
    surface.addEventListener("wheel",e=>{if(!(e.ctrlKey||e.metaKey||scale>1))return;e.preventDefault();setScale(scale+(e.deltaY<0?STEP:-STEP),e.clientX,e.clientY);},{passive:false});
    window.addEventListener("resize",render,{passive:true});
    window.addEventListener("orientationchange",render,{passive:true});
    render();
  }

  function bindSubdivisionSvg(){
    const obj=$("#countrySubdivisionMap");
    if(!obj) return;
    obj.addEventListener("load",()=>{
      const doc=obj.contentDocument;
      if(!doc) return;
      bindCountryMapController(obj,doc);
      const buttons=$(".country-region-button");
      const byMapName=new Map(buttons.map(b=>[norm(b.dataset.mapRegion||b.querySelector("span")?.textContent||""),b]));
      const ns="http://www.w3.org/2000/svg";
      doc.querySelectorAll("[data-region]").forEach(path=>{
        const mapName=path.getAttribute("data-region")||"";
        const button=byMapName.get(norm(mapName));
        const count=Number(button?.querySelector(".map-count")?.textContent||0);
        path.style.fill=count>0?"#7b1d24":"#e2e3e5";
        path.style.stroke="#fff";
        path.style.strokeWidth="1.5";
        path.style.transition="fill .14s ease";
        if(!button) return;
        path.style.cursor="pointer";
        path.setAttribute("tabindex","0");
        path.setAttribute("role","button");
        path.setAttribute("aria-label",(button.querySelector("span")?.textContent||mapName)+": "+count+" ellenőrzött magyar szervezet");
        const activate=()=>button.click();
        path.addEventListener("click",activate);
        path.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();activate();}});
        path.addEventListener("mouseenter",()=>{path.style.fill="#111";});
        path.addEventListener("mouseleave",()=>{path.style.fill=count>0?"#7b1d24":"#e2e3e5";});
        try{
          const box=path.getBBox();
          if(box.width>8 && box.height>8){
            const t=doc.createElementNS(ns,"text");
            t.setAttribute("x",String(box.x+box.width/2));
            t.setAttribute("y",String(box.y+box.height/2));
            t.setAttribute("text-anchor","middle");
            t.setAttribute("dominant-baseline","central");
            t.setAttribute("font-family","Arial, sans-serif");
            t.setAttribute("font-weight","800");
            t.setAttribute("font-size",String(Math.max(8,Math.min(18,Math.min(box.width,box.height)*.28))));
            t.setAttribute("fill",count>0?"#fff":"#555");
            t.setAttribute("stroke",count>0?"#7b1d24":"#e2e3e5");
            t.setAttribute("stroke-width","2.5");
            t.setAttribute("paint-order","stroke");
            t.setAttribute("pointer-events","none");
            t.setAttribute("aria-hidden","true");
            t.textContent=String(count);
            path.parentNode.appendChild(t);
          }
        }catch(_){}
      });
    });
  }

  function bindRegionMap(){
    $(".country-region-button").forEach(b=>b.addEventListener("click",()=>{
      const r=b.dataset.region;
      activeRegion=activeRegion===r?"":r;
      const sel=$("#countryRegion"); if(sel)sel.value=activeRegion;
      buildOptions(); apply();
      $("#countryOrgGrid")?.scrollIntoView({behavior:"smooth",block:"start"});
    }));
    $("#countryAllRegions")?.addEventListener("click",()=>{activeRegion="";if($("#countryRegion"))$("#countryRegion").value="";buildOptions();apply();});
  }

  function bindFilters(){
    const ids=["#countryRegion","#countryCity","#countryOrganization","#countryActivity","#countryProgram","#countryContact","#countryAddress","#countryQuery"];
    ids.forEach(id=>$(id)?.addEventListener(id.includes("Region")||id.includes("City")||id.includes("Organization")||id.includes("Activity")||id.includes("Program")?"change":"input",()=>{
      if(id==="#countryRegion") activeRegion=$("#countryRegion").value;
      if(id==="#countryRegion"){ buildOptions(); }
      apply();
    }));
    $("#countryReset")?.addEventListener("click",()=>{
      activeRegion="";
      ids.forEach(id=>{const el=$(id);if(el)el.value="";});
      buildOptions(); apply();
    });
  }

  async function init(){
    const base=`../../data/countries/${iso}`;
    const [o,e,v]=await Promise.all([
      fetch(base+"/organizations.json",{cache:"no-store"}).then(r=>r.ok?r.json():({organizations:[]})).catch(()=>({organizations:[]})),
      fetch(base+"/education.json",{cache:"no-store"}).then(r=>r.ok?r.json():({institutions:[]})).catch(()=>({institutions:[]})),
      fetch(base+"/events.json",{cache:"no-store"}).then(r=>r.ok?r.json():({events:[]})).catch(()=>({events:[]}))
    ]);
    orgs=o.organizations||o.items||[];
    education=e.institutions||e.education||e.items||[];
    events=v.events||v.items||[];
    regionNames=Object.fromEntries((o.states||o.regions||[]).filter(x=>x?.id).map(x=>[x.id,x.name||x.label||x.id]));
    buildOptions();
    bindRegionMap();
    bindSubdivisionSvg();
    bindFilters();
    apply();
  }
  init();
})();