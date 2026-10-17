const READY = new Set(["reviewed","verified-zero"]);
const TYPE_LABELS = {
  country: "Ország",
  city: "Város",
  organization: "Szervezet",
  activity: "Tevékenység",
  program: "Program"
};

let registry = {countries:[]};
let searchIndex = {items:[]};
let globalEvents = {events:[]};
let activeSuggestions = [];
let activeIndex = -1;
let organizationLimit = 24;

const $ = (s) => document.querySelector(s);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, m => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[m]));
const normalize = (v) => String(v ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLocaleLowerCase("hu").trim();

function countryLabel(c){
  const n = c.name || {};
  return n.hu || n.en || String(c.iso2 || "").toUpperCase();
}

function isReady(c){
  return READY.has(c.researchStatus || "");
}

function typeLabel(item){
  if(item.type === "country" && item.ready === false) return "Ország · kutatás alatt";
  if(item.subtype === "education") return "Oktatás";
  return TYPE_LABELS[item.type] || "Találat";
}

function renderSuggestions(){
  const root = $("#globalSearchSuggestions");
  const input = $("#globalSearch");
  if(!root || !input) return;
  const q = normalize(input.value);
  activeIndex = -1;

  if(!q){
    activeSuggestions = [];
    root.hidden = true;
    root.innerHTML = "";
    input.setAttribute("aria-expanded","false");
    return;
  }

  const tokens = q.split(/\s+/).filter(Boolean);
  const score = (item) => {
    const label = normalize(item.label);
    const search = item.search || "";
    let s = 0;
    if(label === q) s += 100;
    if(label.startsWith(q)) s += 60;
    if(label.includes(q)) s += 30;
    if(tokens.every(t => search.includes(t))) s += 20;
    if(item.type === "country") s += 6;
    if(item.type === "organization") s += 4;
    if(item.type === "program") s += 5;
    return s;
  };

  activeSuggestions = (searchIndex.items || [])
    .map(item => ({item, score: score(item)}))
    .filter(x => x.score > 0)
    .sort((a,b) => b.score - a.score || String(a.item.label).localeCompare(String(b.item.label),"hu"))
    .slice(0,12)
    .map(x => x.item);

  if(!activeSuggestions.length){
    root.innerHTML = '<div class="global-search-empty">Nincs elérhető találat a már elkészült országok ellenőrzött adatai között.</div>';
    root.hidden = false;
    input.setAttribute("aria-expanded","true");
    return;
  }

  root.innerHTML = activeSuggestions.map((item,i) => {
    const meta = [typeLabel(item), item.countryLabel, item.city].filter(Boolean).join(" · ");
    return '<button type="button" role="option" aria-selected="false" data-index="'+i+'"><span><strong>'+esc(item.label)+'</strong><small>'+esc(meta)+'</small></span><b>→</b></button>';
  }).join("");
  root.hidden = false;
  input.setAttribute("aria-expanded","true");

  root.querySelectorAll("button").forEach(btn => {
    btn.addEventListener("mousedown", e => e.preventDefault());
    btn.addEventListener("click", () => chooseSuggestion(Number(btn.dataset.index)));
  });
}

function updateActive(){
  const buttons = [...document.querySelectorAll("#globalSearchSuggestions button")];
  buttons.forEach((b,i) => {
    const on = i === activeIndex;
    b.classList.toggle("active",on);
    b.setAttribute("aria-selected",on ? "true":"false");
    if(on) b.scrollIntoView({block:"nearest"});
  });
}

function chooseSuggestion(index){
  const item = activeSuggestions[index];
  if(!item) return;
  location.href = item.href;
}

function bindSearch(){
  const input = $("#globalSearch");
  if(!input) return;
  input.addEventListener("input", renderSuggestions);
  input.addEventListener("keydown", e => {
    if(!activeSuggestions.length) return;
    if(e.key === "ArrowDown"){
      e.preventDefault();
      activeIndex = (activeIndex + 1) % activeSuggestions.length;
      updateActive();
    }else if(e.key === "ArrowUp"){
      e.preventDefault();
      activeIndex = (activeIndex - 1 + activeSuggestions.length) % activeSuggestions.length;
      updateActive();
    }else if(e.key === "Enter" && activeIndex >= 0){
      e.preventDefault();
      chooseSuggestion(activeIndex);
    }else if(e.key === "Escape"){
      $("#globalSearchSuggestions").hidden = true;
      input.setAttribute("aria-expanded","false");
    }
  });
  input.addEventListener("blur", () => {
    setTimeout(() => {
      const root = $("#globalSearchSuggestions");
      if(root) root.hidden = true;
      input.setAttribute("aria-expanded","false");
    },120);
  });
  input.addEventListener("focus", () => {
    if(input.value.trim()) renderSuggestions();
  });
}

function renderCountryList(){
  const root = $("#worldCountryList");
  if(!root) return;
  const rows = [...(registry.countries || [])].sort((a,b) => countryLabel(a).localeCompare(countryLabel(b),"hu"));
  root.innerHTML = rows.map(c => {
    const ready = isReady(c);
    const count = c.counts?.organizations || 0;
    const status = c.researchStatus === "verified-zero" ? "Lezárt kutatás · nincs igazolt szervezet" : (ready ? count+" ellenőrzött szervezet" : count+" ellenőrzött · kutatás alatt");
    return '<a href="'+esc(c.route)+'" class="'+(ready?'country-ready':'country-building')+'"><strong>'+esc(countryLabel(c))+'</strong><span>'+esc(status)+'</span></a>';
  }).join("");
}

function addMapCountLabel(doc, el, country, ready){
  let box;
  try{ box = el.getBBox(); }catch(_){ return; }
  if(!box || !Number.isFinite(box.x) || !Number.isFinite(box.y)) return;
  const count = Number(country.counts?.organizations || 0);
  if(count <= 0) return;
  const ns = "http://www.w3.org/2000/svg";
  const text = doc.createElementNS(ns,"text");
  text.setAttribute("x", String(box.x + box.width/2));
  text.setAttribute("y", String(box.y + box.height/2));
  text.setAttribute("text-anchor","middle");
  text.setAttribute("dominant-baseline","central");
  text.setAttribute("font-family","Arial, sans-serif");
  text.setAttribute("font-weight","800");
  text.setAttribute("font-size", box.width < 8 || box.height < 8 ? "4.2" : "6.2");
  text.setAttribute("fill", ready ? "#24475d" : "#5f6166");
  text.setAttribute("stroke","#ffffff");
  text.setAttribute("stroke-width","2");
  text.setAttribute("paint-order","stroke");
  text.setAttribute("pointer-events","none");
  text.setAttribute("aria-hidden","true");
  text.textContent = String(count);
  (el.parentNode || doc.documentElement).appendChild(text);
}

function bindWorldMap(){
  const obj = $("#worldMap");
  const viewport = $("#worldMapViewport");
  if(!obj || !viewport) return;

  let scale = 1;
  let x = 0;
  let y = 0;
  let dragging = false;
  let pointerX = 0;
  let pointerY = 0;
  let startX = 0;
  let startY = 0;
  const minScale = 1;
  const maxScale = 6;

  const shell = obj.closest(".world-map-shell");
  const toolbar = shell?.querySelector(".world-map-toolbar");
  if(shell && toolbar && !toolbar.querySelector("[data-map-fullscreen]")){
    const fullscreen=document.createElement("button");
    fullscreen.type="button";
    fullscreen.dataset.mapFullscreen="";
    fullscreen.textContent="⛶";
    fullscreen.title="Térkép teljes képernyőn";
    fullscreen.setAttribute("aria-label","Térkép teljes képernyőn");
    const syncFullscreen=()=>{
      const active=document.fullscreenElement===shell||shell.classList.contains("map-fullscreen-fallback");
      fullscreen.textContent=active?"×":"⛶";
      fullscreen.title=active?"Teljes képernyő bezárása":"Térkép teljes képernyőn";
      fullscreen.setAttribute("aria-label",fullscreen.title);
      document.body.classList.toggle("map-fullscreen-open",active);
    };
    fullscreen.addEventListener("click",async()=>{
      const active=document.fullscreenElement===shell||shell.classList.contains("map-fullscreen-fallback");
      if(active){
        if(document.fullscreenElement) await document.exitFullscreen?.();
        shell.classList.remove("map-fullscreen-fallback");
      }else if(shell.requestFullscreen){
        try{await shell.requestFullscreen();}catch(_){shell.classList.add("map-fullscreen-fallback");}
      }else shell.classList.add("map-fullscreen-fallback");
      syncFullscreen();
      applyTransform();
    });
    document.addEventListener("fullscreenchange",()=>{syncFullscreen();applyTransform();});
    toolbar.appendChild(fullscreen);
  }

  const clampPan = () => {
    if(scale <= 1){ x = 0; y = 0; return; }
    const rect = viewport.getBoundingClientRect();
    const maxX = rect.width * (scale - 1) / 2;
    const maxY = rect.height * (scale - 1) / 2;
    x = Math.max(-maxX, Math.min(maxX, x));
    y = Math.max(-maxY, Math.min(maxY, y));
  };
  const applyTransform = () => {
    clampPan();
    obj.style.transform = `translate3d(${x}px,${y}px,0) scale(${scale})`;
    const surface=obj.contentDocument?.documentElement;
    if(surface) surface.style.touchAction=scale>1?"none":"pan-y";
    viewport.classList.toggle("is-zoomed", scale > 1);
    const z = $("#worldMapZoomValue");
    if(z) z.textContent = Math.round(scale*100)+"%";
  };
  const setScale = (next) => {
    scale = Math.max(minScale,Math.min(maxScale,next));
    applyTransform();
  };
  $("#worldMapZoomIn")?.addEventListener("click",()=>setScale(scale*1.45));
  $("#worldMapZoomOut")?.addEventListener("click",()=>setScale(scale/1.45));
  $("#worldMapZoomReset")?.addEventListener("click",()=>{scale=1;x=0;y=0;applyTransform();});
  viewport.addEventListener("wheel",e=>{
    e.preventDefault();
    setScale(scale*(e.deltaY<0?1.18:1/1.18));
  },{passive:false});
  viewport.addEventListener("pointerdown",e=>{
    if(scale<=1) return;
    dragging=true;pointerX=e.clientX;pointerY=e.clientY;startX=x;startY=y;
    viewport.setPointerCapture?.(e.pointerId);
    viewport.classList.add("is-dragging");
  });
  viewport.addEventListener("pointermove",e=>{
    if(!dragging) return;
    x=startX+(e.clientX-pointerX);y=startY+(e.clientY-pointerY);applyTransform();
  });
  const endDrag=e=>{
    dragging=false;viewport.classList.remove("is-dragging");
    try{viewport.releasePointerCapture?.(e.pointerId)}catch(_){}
  };
  viewport.addEventListener("pointerup",endDrag);
  viewport.addEventListener("pointercancel",endDrag);

  let pinchDistance = 0;
  viewport.addEventListener("touchstart",e=>{
    if(e.touches.length===2){
      pinchDistance=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY);
    }
  },{passive:true});
  viewport.addEventListener("touchmove",e=>{
    if(e.touches.length!==2 || !pinchDistance) return;
    const d=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY);
    setScale(scale*(d/pinchDistance));pinchDistance=d;
  },{passive:true});
  viewport.addEventListener("touchend",()=>{pinchDistance=0},{passive:true});

  const bindEmbeddedPan = surface => {
    if(!surface || surface.dataset.dorappPanBound) return;
    surface.dataset.dorappPanBound="true";
    surface.style.touchAction=scale>1?"none":"pan-y";
    surface.style.userSelect="none";
    const pointers=new Map();
    let dragStart=null;
    let pinchStart=null;
    let moved=false;
    const point=e=>({x:e.clientX,y:e.clientY});
    surface.addEventListener("pointerdown",e=>{
      pointers.set(e.pointerId,point(e));
      moved=false;
      try{surface.setPointerCapture(e.pointerId);}catch(_){}
      if(pointers.size===1 && scale>1){
        dragStart={px:e.clientX,py:e.clientY,x,y};
        viewport.classList.add("is-dragging");
      }else if(pointers.size===2){
        const p=[...pointers.values()];
        pinchStart={distance:Math.hypot(p[1].x-p[0].x,p[1].y-p[0].y),scale};
        dragStart=null;
        viewport.classList.add("is-dragging");
      }
    });
    surface.addEventListener("pointermove",e=>{
      if(!pointers.has(e.pointerId)) return;
      pointers.set(e.pointerId,point(e));
      if(pointers.size===2 && pinchStart?.distance){
        const p=[...pointers.values()];
        const distance=Math.hypot(p[1].x-p[0].x,p[1].y-p[0].y);
        setScale(pinchStart.scale*distance/pinchStart.distance);
        moved=true;
        e.preventDefault();
      }else if(dragStart && scale>1){
        const dx=e.clientX-dragStart.px;
        const dy=e.clientY-dragStart.py;
        if(Math.abs(dx)+Math.abs(dy)>4) moved=true;
        x=dragStart.x+dx;
        y=dragStart.y+dy;
        applyTransform();
        e.preventDefault();
      }
    },{passive:false});
    const end=e=>{
      pointers.delete(e.pointerId);
      try{surface.releasePointerCapture(e.pointerId);}catch(_){}
      if(pointers.size<2) pinchStart=null;
      if(!pointers.size){dragStart=null;viewport.classList.remove("is-dragging");}
    };
    surface.addEventListener("pointerup",end);
    surface.addEventListener("pointercancel",end);
    surface.addEventListener("click",e=>{if(moved){e.preventDefault();e.stopPropagation();moved=false;}},true);
    surface.addEventListener("wheel",e=>{e.preventDefault();setScale(scale*(e.deltaY<0?1.18:1/1.18));},{passive:false});
  };

  const decorateMap = () => {
    const doc = obj.contentDocument;
    if(!doc) return;
    bindEmbeddedPan(doc.documentElement);
    const byIso = Object.fromEntries((registry.countries || []).map(c => [String(c.iso2||"").toLowerCase(),c]));
    const paint = (el,fill) => {
      if(el.matches?.("path,polygon,rect,circle,ellipse")) el.style.fill = fill;
      el.querySelectorAll?.("path,polygon,rect,circle,ellipse").forEach(n => n.style.fill = fill);
    };
    const base = "#d9dde1";
    const readyColor = "#91cbaa";
    const readyHover = "#62ad87";
    const researchingColor = "#e6bb74";
    const researchingHover = "#d7a34d";
    const zeroColor = "#d96b67";
    const zeroHover = "#c84f4b";
    const buildingHover = "#c4cbd1";

    doc.documentElement.style.background = "#fff";
    doc.querySelectorAll("path,polygon,rect,circle,ellipse").forEach(el => {
      el.style.fill = base;
      el.style.stroke = "#ffffff";
      el.style.strokeWidth = ".65";
      el.style.transition = "fill .14s ease";
    });

    const processed = new Set();
    doc.querySelectorAll("[id]").forEach(el => {
      const iso = String(el.id||"").toLowerCase();
      const country = byIso[iso];
      if(!country || processed.has(iso)) return;
      processed.add(iso);
      const ready = isReady(country);
      const count = Number(country.counts?.organizations || 0);
      const verifiedZero = country.researchStatus === "verified-zero";
      const researching = ["researching", "partial"].includes(country.researchStatus);
      const baseFill = verifiedZero ? zeroColor : (ready ? readyColor : (researching ? researchingColor : base));
      paint(el,baseFill);
      const label = countryLabel(country);
      const status = verifiedZero ? "lezárt kutatás · jelenleg nincs igazolt magyar vonatkozás" : (ready ? count+" ellenőrzött szervezet · áttekintett ország" : (researching ? count+" ellenőrzött szervezet · kutatás alatt" : "még nem kutatott ország"));
      el.setAttribute("aria-label",label+" · "+status);

      const statusEl = $("#worldMapStatus");
      const over = () => {
        paint(el,verifiedZero ? zeroHover : (ready ? readyHover : (researching ? researchingHover : buildingHover)));
        if(statusEl) statusEl.textContent = label+" · "+status;
      };
      const out = () => paint(el,baseFill);
      el.addEventListener("mouseenter",over);
      el.addEventListener("mouseleave",out);
      el.style.cursor = "pointer";
      el.setAttribute("tabindex","0");
      el.setAttribute("role","link");
      const go = () => location.href = country.route;
      el.addEventListener("click",go);
      el.addEventListener("keydown",e => {
        if(e.key === "Enter" || e.key === " "){e.preventDefault();go();}
      });
      el.addEventListener("focus",over);
      el.addEventListener("blur",out);
      addMapCountLabel(doc,el,country,ready);
    });
  };
  obj.addEventListener("load", decorateMap);
  if(obj.contentDocument?.readyState === "complete"){
    decorateMap();
  }
  applyTransform();
}

function formatDate(value){
  if(!value) return "";
  const d = new Date(value);
  if(Number.isNaN(d.getTime())) return String(value);
  return new Intl.DateTimeFormat("hu-HU",{year:"numeric",month:"long",day:"numeric",hour:"2-digit",minute:"2-digit"}).format(d);
}

function populateCalendarCountries(){
  const select = $("#globalCalendarCountry");
  if(!select) return;
  const countries = [...new Map((globalEvents.events||[]).map(e => [e.country,e.countryLabel])).entries()]
    .sort((a,b) => String(a[1]).localeCompare(String(b[1]),"hu"));
  select.innerHTML = '<option value="">Minden ország</option>' + countries.map(([iso,label]) => '<option value="'+esc(iso)+'">'+esc(label)+'</option>').join("");
}

function renderGlobalCalendar(){
  const root = $("#globalCalendarGrid");
  const countEl = $("#globalCalendarCount");
  const empty = $("#globalCalendarEmpty");
  if(!root) return;
  const country = $("#globalCalendarCountry")?.value || "";
  const q = normalize($("#globalCalendarSearch")?.value || "");
  const rows = (globalEvents.events || []).filter(e => {
    if(country && e.country !== country) return false;
    if(!q) return true;
    return normalize([e.name,e.countryLabel,e.city,e.region,e.venue,e.organizer,(e.categories||[]).join(" ")].filter(Boolean).join(" ")).includes(q);
  });
  if(countEl) countEl.textContent = rows.length+" közelgő program";
  if(empty) empty.hidden = !!rows.length;
  root.innerHTML = rows.map(e => '<article class="global-event-card"><div class="global-event-meta">'+esc(e.countryLabel)+' · '+esc(formatDate(e.startDate))+'</div><h3>'+esc(e.name)+'</h3><p>'+esc([e.city,e.venue,e.organizer].filter(Boolean).join(" · "))+'</p><a href="'+esc(e.href)+'">Program részletei →</a></article>').join("");
}

function bindCalendar(){
  $("#globalCalendarCountry")?.addEventListener("change",()=>{void ensureCalendar().then(()=>{if(calendarPromise)renderGlobalCalendar();});});
  $("#globalCalendarSearch")?.addEventListener("input",()=>{void ensureCalendar().then(()=>{if(calendarPromise)renderGlobalCalendar();});});
}

function organizationItems(){
  return (searchIndex.items || []).filter(item => item.type === "organization");
}

function organizationType(item){
  return item.category || item.entityType || (item.subtype === "education" ? "Oktatás" : "Szervezet");
}

function shortCountryLabel(item){
  return item.country === "us" ? "USA" : item.countryLabel;
}

function populateOrganizationFilters(){
  const rows = organizationItems();
  const countrySelect = $("#organizationCountry");
  const typeSelect = $("#organizationType");
  if(countrySelect){
    const countries = [...new Map(rows.map(item => [item.country,item.countryLabel])).entries()]
      .sort((a,b) => String(a[1]).localeCompare(String(b[1]),"hu"));
    countrySelect.innerHTML = '<option value="">Minden ország</option>' + countries.map(([iso,label]) => '<option value="'+esc(iso)+'">'+esc(label)+'</option>').join("");
  }
  if(typeSelect){
    const types = [...new Set(rows.map(organizationType).filter(Boolean))].sort((a,b) => a.localeCompare(b,"hu"));
    typeSelect.innerHTML = '<option value="">Minden típus</option>' + types.map(type => '<option value="'+esc(type)+'">'+esc(type)+'</option>').join("");
  }
}

function renderOrganizations(resetLimit = false){
  const root = $("#organizationDirectory");
  if(!root) return;
  if(resetLimit) organizationLimit = 24;
  const country = $("#organizationCountry")?.value || "";
  const type = $("#organizationType")?.value || "";
  const q = normalize($("#organizationSearch")?.value || "");
  const rows = organizationItems().filter(item => {
    if(country && item.country !== country) return false;
    if(type && organizationType(item) !== type) return false;
    return !q || String(item.search || "").includes(q);
  }).sort((a,b) => String(a.label).localeCompare(String(b.label),"hu"));
  const visible = rows.slice(0,organizationLimit);
  const count = $("#organizationCount");
  const empty = $("#organizationEmpty");
  const more = $("#organizationMore");
  if(count) count.textContent = rows.length+" ellenőrzött találat";
  if(empty) empty.hidden = !!rows.length;
  if(more){
    more.hidden = visible.length >= rows.length;
    more.textContent = "További szervezetek ("+(rows.length-visible.length)+")";
  }
  root.innerHTML = visible.map(item => {
    const meta = [shortCountryLabel(item),item.city,organizationType(item)].filter(Boolean).join(" · ");
    return '<article class="global-organization-row"><div class="global-organization-copy"><div class="global-organization-meta">'+esc(meta)+'</div><h3><a href="'+esc(item.href)+'">'+esc(item.label)+'</a></h3>'+(item.summary?'<p>'+esc(item.summary)+'</p>':'')+'</div><a class="global-organization-link" href="'+esc(item.href)+'" aria-label="Adatlap – '+esc(item.label)+'">Adatlap <span aria-hidden="true">→</span></a></article>';
  }).join("");
}

function bindOrganizationDirectory(){
  $("#organizationCountry")?.addEventListener("change",()=>renderOrganizations(true));
  $("#organizationType")?.addEventListener("change",()=>renderOrganizations(true));
  $("#organizationSearch")?.addEventListener("input",()=>renderOrganizations(true));
  $("#organizationMore")?.addEventListener("click",()=>{organizationLimit += 24;renderOrganizations();});
  $("#organizationReset")?.addEventListener("click",()=>{
    if($("#organizationCountry")) $("#organizationCountry").value = "";
    if($("#organizationType")) $("#organizationType").value = "";
    if($("#organizationSearch")) $("#organizationSearch").value = "";
    renderOrganizations(true);
  });
}

let searchIndexPromise = null;
let calendarPromise = null;
let searchIndexLoaded = false;

function ensureSearchIndex(){
  if(!searchIndexPromise){
    searchIndexPromise = fetch("data/global-search-index.json",{cache:"no-store"})
      .then(r=>{if(!r.ok)throw new Error("search-index-unavailable");return r.json();})
      .then(data=>{
        searchIndex = data;
        searchIndexLoaded = true;
        $("#organizationCount")?.removeAttribute("role");
        populateOrganizationFilters();
        renderOrganizations();
        if($("#globalSearch")?.value.trim()) renderSuggestions();
        return data;
      })
      .catch(()=>{
        searchIndexPromise = null; // Permit a subsequent focus/input to retry.
        searchIndexLoaded = false;
        searchIndex = {items:[]};
        populateOrganizationFilters();
        renderOrganizations();
        const count = $("#organizationCount");
        if(count){
          count.textContent = "A szervezetadatok nem tölthetők be. Próbáld újra a keresőmezőre kattintva.";
          count.setAttribute("role","alert");
        }
        const empty = $("#organizationEmpty");
        if(empty) empty.hidden = true;
        const suggestions = $("#globalSearchSuggestions");
        if(suggestions && $("#globalSearch")?.value.trim()){
          suggestions.innerHTML = '<div class="global-search-empty" role="status">A kereső átmenetileg nem érhető el. Próbáld újra.</div>';
          suggestions.hidden = false;
        }
        return searchIndex;
      });
  }
  return searchIndexPromise;
}

function ensureCalendar(){
  if(!calendarPromise){
    calendarPromise = fetch("data/global-events.json",{cache:"no-store"})
      .then(r=>{if(!r.ok)throw new Error("calendar-unavailable");return r.json();})
      .then(data=>{
        globalEvents = data;
        $("#globalCalendarCount")?.removeAttribute("role");
        populateCalendarCountries();
        renderGlobalCalendar();
        return data;
      })
      .catch(()=>{
        calendarPromise = null; // Retry on next calendar interaction.
        globalEvents={events:[]};
        populateCalendarCountries();
        renderGlobalCalendar();
        const count = $("#globalCalendarCount");
        if(count){
          count.textContent = "A programnaptár nem tölthető be. Próbáld újra a szűrő használatával.";
          count.setAttribute("role","alert");
        }
        const empty = $("#globalCalendarEmpty");
        if(empty) empty.hidden = true;
        return globalEvents;
      });
  }
  return calendarPromise;
}

function loadWhenNear(selector,load){
  const target=$(selector);
  if(!target)return;
  if(!("IntersectionObserver" in window)){
    load();
    return;
  }
  const observer=new IntersectionObserver(entries=>{
    if(entries.some(entry=>entry.isIntersecting)){
      observer.disconnect();
      load();
    }
  },{rootMargin:"320px 0px"});
  observer.observe(target);
}

async function init(){
  const legacyHashRoutes = {
    "#naptar":"countries/at/#programok",
    "#oktatas":"countries/at/#oktatas",
    "#terkep":"countries/at/#terkep"
  };
  if(legacyHashRoutes[location.hash]){
    location.replace(legacyHashRoutes[location.hash]);
    return;
  }

  bindSearch();
  bindOrganizationDirectory();
  bindCalendar();

  $("#globalSearch")?.addEventListener("focus",()=>{void ensureSearchIndex();});
  $("#globalSearch")?.addEventListener("input",()=>{void ensureSearchIndex();});
  for(const id of ["#organizationCountry","#organizationType","#organizationSearch"]){
    $(id)?.addEventListener("focus",()=>{void ensureSearchIndex();});
    $(id)?.addEventListener("input",()=>{void ensureSearchIndex();});
    $(id)?.addEventListener("change",()=>{void ensureSearchIndex();});
  }
  $("#globalCalendarSearch")?.addEventListener("focus",()=>{void ensureCalendar();});
  $("#globalCalendarCountry")?.addEventListener("focus",()=>{void ensureCalendar();});

  let g;
  try {
    g=await fetch("data/global.json",{cache:"no-store"}).then(r=>{
      if(!r.ok)throw new Error("global-registry-unavailable");
      return r.json();
    });
  } catch (_) {
    const status=$("#worldMapStatus");
    if(status){
      status.textContent="Az országadatok átmenetileg nem érhetők el. Frissítsd az oldalt a próbálkozáshoz.";
      status.setAttribute("role","alert");
    }
    return;
  }
  registry=g;
  renderCountryList();
  bindWorldMap();

  const initialQuery = new URLSearchParams(location.search).get("q");
  if(initialQuery && $("#globalSearch")){
    $("#globalSearch").value=initialQuery;
    void ensureSearchIndex();
  }
  loadWhenNear("#szervezetek",()=>{void ensureSearchIndex();});
  loadWhenNear("#programnaptar",()=>{void ensureCalendar();});
}

requestAnimationFrame(()=>requestAnimationFrame(init));
