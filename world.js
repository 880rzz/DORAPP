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
    const status = ready ? (c.researchStatus === "verified-zero" ? count+" ellenőrzött szervezet" : count+" szervezet") : count+" ellenőrzött · készül";
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
  let dragDistance = 0;
  let suppressCountryClickUntil = 0;
  const minScale = 1;
  const maxScale = 6;

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
    const zoomed = scale > 1;
    viewport.classList.toggle("is-zoomed", zoomed);
    obj.style.pointerEvents = zoomed ? "none" : "auto";
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
    dragging=true;pointerX=e.clientX;pointerY=e.clientY;startX=x;startY=y;dragDistance=0;
    e.preventDefault();
    viewport.setPointerCapture?.(e.pointerId);
    viewport.classList.add("is-dragging");
  });
  viewport.addEventListener("pointermove",e=>{
    if(!dragging) return;
    const dx=e.clientX-pointerX,dy=e.clientY-pointerY;
    dragDistance=Math.max(dragDistance,Math.hypot(dx,dy));
    x=startX+dx;y=startY+dy;applyTransform();
  });
  const endDrag=e=>{
    if(!dragging) return;
    if(dragDistance>5) suppressCountryClickUntil=performance.now()+250;
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

  obj.addEventListener("load", () => {
    const doc = obj.contentDocument;
    if(!doc) return;
    const byIso = Object.fromEntries((registry.countries || []).map(c => [String(c.iso2||"").toLowerCase(),c]));
    const paint = (el,fill) => {
      if(el.matches?.("path,polygon,rect,circle,ellipse")) el.style.fill = fill;
      el.querySelectorAll?.("path,polygon,rect,circle,ellipse").forEach(n => n.style.fill = fill);
    };
    const base = "#d9dde1";
    const readyColor = "#a9c9dc";
    const readyHover = "#82aec8";
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
      const baseFill = ready ? readyColor : base;
      paint(el,baseFill);
      const label = countryLabel(country);
      const status = ready ? count+" szervezet · kész ország" : count+" ellenőrzött szervezet · kutatás alatt";
      el.setAttribute("aria-label",label+" · "+status);

      const statusEl = $("#worldMapStatus");
      const over = () => {
        paint(el,ready ? readyHover : buildingHover);
        if(statusEl) statusEl.textContent = label+" · "+status;
      };
      const out = () => paint(el,baseFill);
      el.addEventListener("mouseenter",over);
      el.addEventListener("mouseleave",out);
      el.style.cursor = "pointer";
      el.setAttribute("tabindex","0");
      el.setAttribute("role","link");
      const go = () => location.href = country.route;
      el.addEventListener("click",e => {
        if(performance.now()<suppressCountryClickUntil){e.preventDefault();return;}
        go();
      });
      el.addEventListener("keydown",e => {
        if(e.key === "Enter" || e.key === " "){e.preventDefault();go();}
      });
      el.addEventListener("focus",over);
      el.addEventListener("blur",out);
      addMapCountLabel(doc,el,country,ready);
    });
  });
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
  $("#globalCalendarCountry")?.addEventListener("change",renderGlobalCalendar);
  $("#globalCalendarSearch")?.addEventListener("input",renderGlobalCalendar);
}

async function init(){
  const legacyHashRoutes = {
    "#naptar":"countries/at/#programok",
    "#oktatas":"countries/at/#oktatas",
    "#szervezetek":"countries/at/#kozossegek",
    "#terkep":"countries/at/#terkep"
  };
  if(legacyHashRoutes[location.hash]){
    location.replace(legacyHashRoutes[location.hash]);
    return;
  }
  const [g,s,e] = await Promise.all([
    fetch("data/global.json",{cache:"no-store"}).then(r => r.json()),
    fetch("data/global-search-index.json",{cache:"no-store"}).then(r => r.json()).catch(() => ({items:[]})),
    fetch("data/global-events.json",{cache:"no-store"}).then(r => r.json()).catch(() => ({events:[]}))
  ]);
  registry = g;
  searchIndex = s;
  globalEvents = e;
  bindSearch();
  renderCountryList();
  bindWorldMap();
  populateCalendarCountries();
  bindCalendar();
  renderGlobalCalendar();
}

init();
