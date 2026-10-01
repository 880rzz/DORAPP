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
    if(ready){
      return '<a href="'+esc(c.route)+'"><strong>'+esc(countryLabel(c))+'</strong><span>'+esc(status)+'</span></a>';
    }
    return '<div class="country-unavailable" aria-disabled="true"><strong>'+esc(countryLabel(c))+'</strong><span>'+esc(status)+'</span></div>';
  }).join("");
}

function addMapCountLabel(doc, el, country, ready){
  let box;
  try{ box = el.getBBox(); }catch(_){ return; }
  if(!box || !Number.isFinite(box.x) || !Number.isFinite(box.y)) return;
  const ns = "http://www.w3.org/2000/svg";
  const text = doc.createElementNS(ns,"text");
  text.setAttribute("x", String(box.x + box.width/2));
  text.setAttribute("y", String(box.y + box.height/2));
  text.setAttribute("text-anchor","middle");
  text.setAttribute("dominant-baseline","central");
  text.setAttribute("font-family","Arial, sans-serif");
  text.setAttribute("font-weight","700");
  text.setAttribute("font-size", box.width < 8 || box.height < 8 ? "3.5" : "5.5");
  text.setAttribute("fill", ready ? "#ffffff" : "#5f6166");
  text.setAttribute("stroke", ready ? "#7b1d24" : "#d7d8db");
  text.setAttribute("stroke-width","1.4");
  text.setAttribute("paint-order","stroke");
  text.setAttribute("pointer-events","none");
  text.setAttribute("aria-hidden","true");
  text.textContent = String(country.counts?.organizations ?? 0);
  (el.parentNode || doc.documentElement).appendChild(text);
}

function bindWorldMap(){
  const obj = $("#worldMap");
  if(!obj) return;
  obj.addEventListener("load", () => {
    const doc = obj.contentDocument;
    if(!doc) return;
    const byIso = Object.fromEntries((registry.countries || []).map(c => [String(c.iso2||"").toLowerCase(),c]));
    const paint = (el,fill) => {
      if(el.matches?.("path,polygon,rect,circle,ellipse")) el.style.fill = fill;
      el.querySelectorAll?.("path,polygon,rect,circle,ellipse").forEach(n => n.style.fill = fill);
    };
    const base = "#d7d8db";
    const readyColor = "#7b1d24";
    const hoverColor = "#551419";

    doc.documentElement.style.background = "#fff";
    doc.querySelectorAll("path,polygon,rect,circle,ellipse").forEach(el => {
      el.style.fill = base;
      el.style.stroke = "#fff";
      el.style.strokeWidth = ".65";
      el.style.transition = "fill .14s ease";
    });

    const processed = new Set();
    doc.querySelectorAll("[id]").forEach(el => {
      const iso = String(el.id||"").toLowerCase();
      const c = byIso[iso];
      if(!c || processed.has(iso)) return;
      processed.add(iso);
      const ready = isReady(c);
      paint(el, ready ? readyColor : base);
      const label = countryLabel(c);
      const count = c.counts?.organizations || 0;
      const status = ready ? count+" szervezet" : count+" ellenőrzött szervezet · még nincs kész";
      el.setAttribute("aria-label", label+" · "+status);

      const statusEl = $("#worldMapStatus");
      const over = () => {
        if(ready) paint(el,hoverColor);
        if(statusEl) statusEl.textContent = label+" · "+status;
      };
      const out = () => paint(el, ready ? readyColor : base);
      el.addEventListener("mouseenter",over);
      el.addEventListener("mouseleave",out);

      if(ready){
        el.style.cursor = "pointer";
        el.setAttribute("tabindex","0");
        el.setAttribute("role","link");
        const go = () => location.href = c.route;
        el.addEventListener("click",go);
        el.addEventListener("keydown",e => {
          if(e.key === "Enter" || e.key === " "){
            e.preventDefault();
            go();
          }
        });
        el.addEventListener("focus",over);
        el.addEventListener("blur",out);
      }else{
        el.style.cursor = "default";
        el.setAttribute("aria-disabled","true");
      }
      addMapCountLabel(doc,el,c,ready);
    });
  });
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
    "#terkep":"countries/at/#teruleti-attekintes"
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
