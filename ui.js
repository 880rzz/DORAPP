(()=> {
  const GA_ID="G-1FC22JEX2F";
  const CONSENT_KEY="dorapp_analytics_consent";

  function loadAnalytics(){
    if(window.__dorappGaLoaded) return;
    window.__dorappGaLoaded=true;
    window.dataLayer=window.dataLayer||[];
    window.gtag=function(){window.dataLayer.push(arguments)};
    gtag("js",new Date());
    gtag("config",GA_ID,{anonymize_ip:true});
    const s=document.createElement("script");
    s.async=true;
    s.src="https://www.googletagmanager.com/gtag/js?id="+encodeURIComponent(GA_ID);
    document.head.appendChild(s);
  }

  function setConsent(value){
    localStorage.setItem(CONSENT_KEY,value);
    if(value==="granted") loadAnalytics();
    const banner=document.querySelector(".consent-banner");
    if(banner) banner.remove();
  }

  function showConsent(){
    if(document.querySelector(".consent-banner")) return;
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
    if(saved==="granted") loadAnalytics();
    else if(saved!=="denied") showConsent();

    const footer=document.querySelector("footer .footer-grid");
    if(footer && !document.querySelector(".consent-settings")){
      const b=document.createElement("button");
      b.type="button";
      b.className="consent-settings";
      b.textContent="Adatvédelmi beállítások";
      b.addEventListener("click",()=>{
        localStorage.removeItem(CONSENT_KEY);
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

  document.addEventListener("DOMContentLoaded",()=>{
    initMobileNav();
    initConsent();
  });
})();