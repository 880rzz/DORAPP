(()=> {
  const GA_ID="G-1FC22JEX2F";
  const CONSENT_KEY="dorapp_analytics_consent";

  window.dataLayer=window.dataLayer||[];
  window.gtag=window.gtag||function(){window.dataLayer.push(arguments)};
  gtag("consent","default",{
    analytics_storage:"denied",
    ad_storage:"denied",
    ad_user_data:"denied",
    ad_personalization:"denied",
    wait_for_update:500
  });

  function analyticsConsent(value){
    gtag("consent","update",{
      analytics_storage:value,
      ad_storage:"denied",
      ad_user_data:"denied",
      ad_personalization:"denied"
    });
  }

  function clearAnalyticsCookies(){
    const host=location.hostname;
    const domains=[host,"."+host];
    const parts=host.split(".");
    if(parts.length>2) domains.push("."+parts.slice(-2).join("."));
    document.cookie.split(";").map(v=>v.split("=")[0].trim()).filter(name=>name==="_ga"||name.startsWith("_ga_")).forEach(name=>{
      document.cookie=`${name}=; Max-Age=0; path=/; SameSite=Lax`;
      domains.forEach(domain=>{document.cookie=`${name}=; Max-Age=0; path=/; domain=${domain}; SameSite=Lax`;});
    });
  }

  function loadAnalytics(){
    if(window.__dorappGaLoaded) return;
    window.__dorappGaLoaded=true;
    gtag("js",new Date());
    gtag("config",GA_ID,{anonymize_ip:true,allow_google_signals:false,allow_ad_personalization_signals:false});
    const s=document.createElement("script");
    s.async=true;
    s.src="https://www.googletagmanager.com/gtag/js?id="+encodeURIComponent(GA_ID);
    document.head.appendChild(s);
  }

  function setConsent(value){
    localStorage.setItem(CONSENT_KEY,value);
    analyticsConsent(value);
    if(value==="granted") loadAnalytics();
    else clearAnalyticsCookies();
    const banner=document.querySelector(".consent-banner");
    if(banner) banner.remove();
    document.body.classList.remove("consent-open");
  }

  function showConsent(){
    if(document.querySelector(".consent-banner")) return;
    document.body.classList.add("consent-open");
    const wrap=document.createElement("div");
    wrap.className="consent-banner";
    wrap.setAttribute("role","dialog");
    wrap.setAttribute("aria-label","Analitikai sütik beállítása");
    wrap.innerHTML='<div class="consent-copy"><strong>Adatvédelmi beállítások</strong><p>Az oldal alapfunkciói követés nélkül működnek. A Google Analytics csak az Ön hozzájárulása után töltődik be.</p></div><div class="consent-actions"><button type="button" class="consent-reject">Csak szükséges</button><button type="button" class="consent-accept">Analitika engedélyezése</button></div>';
    document.body.appendChild(wrap);
    wrap.querySelector(".consent-reject").addEventListener("click",()=>setConsent("denied"));
    wrap.querySelector(".consent-accept").addEventListener("click",()=>setConsent("granted"));
  }

  function initConsent(){
    const saved=localStorage.getItem(CONSENT_KEY);
    if(saved==="granted"){
      analyticsConsent("granted");
      loadAnalytics();
    }else if(saved!=="denied") showConsent();

    const footer=document.querySelector("footer .footer-grid");
    if(footer && !document.querySelector(".consent-settings")){
      const b=document.createElement("button");
      b.type="button";
      b.className="consent-settings";
      b.textContent="Adatvédelmi beállítások";
      b.addEventListener("click",()=>{
        setConsent("denied");
        showConsent();
      });
      footer.appendChild(b);
    }
  }

  function initMobileNav(){
    const row=document.querySelector(".navrow");
    const nav=row?.querySelector("nav");
    if(!row||!nav||row.querySelector(".menu-toggle")) return;
    if(!nav.id) nav.id="site-nav";
    const btn=document.createElement("button");
    btn.type="button";
    btn.className="menu-toggle";
    btn.setAttribute("aria-expanded","false");
    btn.setAttribute("aria-controls",nav.id);
    btn.setAttribute("aria-label","Menü megnyitása");
    btn.innerHTML='<span></span><span></span><span></span>';
    row.insertBefore(btn,nav);

    const close=()=>{
      btn.setAttribute("aria-expanded","false");
      btn.setAttribute("aria-label","Menü megnyitása");
      document.body.classList.remove("menu-open");
    };
    btn.addEventListener("click",()=>{
      const open=btn.getAttribute("aria-expanded")==="true";
      if(open) close();
      else {
        btn.setAttribute("aria-expanded","true");
        btn.setAttribute("aria-label","Menü bezárása");
        document.body.classList.add("menu-open");
      }
    });
    nav.addEventListener("click",e=>{if(e.target.closest("a")) close()});
    document.addEventListener("keydown",e=>{if(e.key==="Escape") close()});
    window.addEventListener("resize",()=>{if(window.innerWidth>760) close()},{passive:true});
  }


  function ensureFooterCredit(){
    let footer=document.querySelector("footer");
    if(!footer){
      footer=document.createElement("footer");
      footer.innerHTML='<div class="wrap footer-grid"></div>';
      document.body.appendChild(footer);
    }
    let grid=footer.querySelector(".footer-grid");
    if(!grid){
      grid=document.createElement("div");
      grid.className="wrap footer-grid";
      footer.appendChild(grid);
    }
    let credit=[...grid.children].find(node=>/Be Smart Kids Club csapata|Bécsi Magyar Iskola.*Be Smart Kids Club/.test(node.textContent||""));
    if(!credit){
      credit=document.createElement("div");
      grid.appendChild(credit);
    }
    credit.className="site-credit";
    credit.innerHTML='A <a href="https://www.magyariskola.at/" target="_blank" rel="noopener external">Bécsi Magyar Iskola</a> – <a href="https://rolunk.at/aktualis/a-fiataloknak-ma-mar-bizonyitek-kell-egy-becsi-kreativ-kozosseg-uj-generaciot-epit/" target="_blank" rel="noopener external">Be Smart Kids Club</a> csapata hozta létre.<br><a href="mailto:marketing@kozpontiszovetseg.at">marketing@kozpontiszovetseg.at</a>';
  }

  function initWhatsApp(){
    if(document.querySelector(".whatsapp-fab")) return;
    const link=document.createElement("a");
    const message="Üdvözlöm! A DORAPP-pal kapcsolatban szeretnék kérdezni.";
    link.className="whatsapp-fab";
    link.href="https://wa.me/4367761655592?text="+encodeURIComponent(message);
    link.target="_blank";
    link.rel="noopener external";
    link.setAttribute("aria-label","Írj nekünk WhatsAppon");
    link.title="Írj nekünk WhatsAppon";
    link.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M20.5 3.5A11.8 11.8 0 0 0 12.1 0C5.6 0 .3 5.3.3 11.8c0 2.1.5 4.1 1.6 5.9L.2 24l6.5-1.7a11.8 11.8 0 0 0 5.6 1.4h.1c6.5 0 11.8-5.3 11.8-11.8 0-3.2-1.3-6.1-3.7-8.4Zm-8.1 18.2h-.1c-1.8 0-3.5-.5-5-1.4l-.4-.2-3.9 1 1-3.8-.2-.4a9.8 9.8 0 1 1 8.6 4.8Zm5.4-7.3c-.3-.1-1.7-.8-2-.9-.3-.1-.5-.1-.7.2-.2.3-.8.9-.9 1.1-.2.2-.3.2-.6.1-1.7-.9-2.8-1.5-3.9-3.4-.3-.5.3-.5.9-1.6.1-.2 0-.4 0-.6l-.9-2.2c-.2-.5-.5-.5-.7-.5h-.6c-.2 0-.6.1-.9.4-.3.3-1.2 1.2-1.2 2.9s1.2 3.3 1.4 3.5c.2.2 2.4 3.7 5.9 5.2.8.4 1.5.6 2 .7.8.3 1.6.2 2.2.1.7-.1 1.7-.7 1.9-1.3.2-.6.2-1.2.2-1.3-.1-.2-.3-.3-.6-.4Z"/></svg>';
    document.body.appendChild(link);
  }

  document.addEventListener("DOMContentLoaded",()=>{
    ensureFooterCredit();
    initMobileNav();
    initConsent();
    initWhatsApp();
  });
})();
