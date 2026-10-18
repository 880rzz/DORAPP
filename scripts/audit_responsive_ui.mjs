import { chromium } from "playwright";
import fs from "node:fs/promises";

const base=process.env.DORAPP_TEST_BASE||"http://127.0.0.1:4173";
const widths=[320,375,390,621,768,1024,1180,1280,1440,1600,1920,2560,3840];
// Event pages are regenerated from the active feed; never pin the UI audit to an expired event.
const eventPages=(await fs.readdir("esemenyek")).filter(name=>name.endsWith(".html")).sort();
const eventRoute=eventPages.length ? "/esemenyek/"+encodeURIComponent(eventPages[0]) : null;
const routes=[
  "/index.html",
  "/countries/at/",
  "/szervezetek/becsi-magyar-iskola.html",
  "/oktatas/abis-linz-hungarian.html",
  ...(eventRoute ? [eventRoute] : []),
  "/kategoriak/csalad.html",
  "/tartomanyok/wien.html",
  "/forrasok.html",
  "/adatminoseg.html",
  "/countries/at/organizations/becsi-magyar-iskola.html",
  "/countries/at/education/abis-linz-hungarian.html"
];
const screenshotWidths=new Set([320,390,768,1440,2560,3840]);
const screenshotRoutes=new Set(["/index.html","/countries/at/","/szervezetek/becsi-magyar-iskola.html","/forrasok.html","/adatminoseg.html"]);
const report={generatedAt:new Date().toISOString(),widths,routes,pages:[],interactions:{},failures:[]};
await fs.mkdir("artifacts/ui-screenshots",{recursive:true});

const browser=await chromium.launch({headless:true});
const context=await browser.newContext();
await context.addInitScript(()=>localStorage.setItem("dorapp_analytics_consent","denied"));

for(const width of widths){
  for(const route of routes){
    const page=await context.newPage();
    await page.setViewportSize({width,height:width<=621?844:1000});
    const response=await page.goto(base+route,{waitUntil:"networkidle",timeout:45000});
    await page.waitForTimeout(120);
    const audit=await page.evaluate(()=>{
      const root=document.documentElement;
      const visible=el=>{
        const style=getComputedStyle(el);
        const rect=el.getBoundingClientRect();
        return style.display!=="none"&&style.visibility!=="hidden"&&rect.width>0&&rect.height>0;
      };
      const clipped=[...document.querySelectorAll("button,summary,input,select,h1,h2,h3")]
        .filter(visible)
        .filter(el=>el.scrollWidth>el.clientWidth+2&&!["auto","scroll"].includes(getComputedStyle(el).overflowX))
        .slice(0,12)
        .map(el=>({tag:el.tagName,text:(el.textContent||el.getAttribute("aria-label")||"").trim().slice(0,80)}));
      return {
        title:document.title,
        designLoaded:[...document.styleSheets].some(sheet=>(sheet.href||"").includes("design-editorial.css")),
        horizontalOverflow:root.scrollWidth>innerWidth+2,
        scrollWidth:root.scrollWidth,
        innerWidth,
        clipped,
        hasHeader:!!document.querySelector(".topbar"),
        hasFooter:!!document.querySelector("footer"),
        hasMain:!!document.querySelector("main")
      };
    });
    const row={width,route,status:response?.status()||0,...audit};
    report.pages.push(row);
    if(row.status>=400||!row.designLoaded||row.horizontalOverflow||row.clipped.length||!row.hasHeader||!row.hasFooter||!row.hasMain)report.failures.push(row);
    if(screenshotWidths.has(width)&&screenshotRoutes.has(route)){
      const slug=route.replace(/^\/+|\/+$/g,"").replace(/[^a-z0-9]+/gi,"-")||"home";
      await page.screenshot({path:`artifacts/ui-screenshots/${slug}-${width}.png`,fullPage:true});
    }
    await page.close();
  }
}

const page=await context.newPage();
await page.setViewportSize({width:390,height:844});
await page.goto(base+"/index.html",{waitUntil:"networkidle"});
await page.locator("#globalSearch").fill("Ausztria");
await page.waitForSelector("#globalSearchSuggestions button");
report.interactions.searchSuggestions=await page.locator("#globalSearchSuggestions button").count()>0;
await page.locator("#globalSearch").press("ArrowDown");
report.interactions.searchKeyboardActive=await page.locator("#globalSearchSuggestions button.active").count()===1;
await page.locator("#globalSearch").press("Escape");
report.interactions.searchEscape=await page.locator("#globalSearchSuggestions").getAttribute("hidden")!==null;
await page.locator("#organizationSearch").fill("___nincs_ilyen_szervezet___");
await page.waitForTimeout(150);
report.interactions.directoryEmpty=await page.locator("#organizationEmpty").isVisible();
await page.locator("#organizationReset").click();
report.interactions.directoryReset=(await page.locator("#organizationSearch").inputValue())==="";
const beforeZoom=await page.locator("#worldMapZoomValue").textContent();
await page.locator("#worldMapZoomIn").click();
report.interactions.worldMapZoom=beforeZoom!==await page.locator("#worldMapZoomValue").textContent();
const toggle=page.locator(".menu-toggle");
report.interactions.mobileMenuPresent=await toggle.count()===1;
if(await toggle.count()){
  await toggle.click();
  const opened=await toggle.getAttribute("aria-expanded")==="true";
  await page.keyboard.press("Escape");
  report.interactions.mobileMenu=opened&&await toggle.getAttribute("aria-expanded")==="false";
}
await page.close();

const country=await context.newPage();
await country.setViewportSize({width:390,height:844});
await country.goto(base+"/countries/at/",{waitUntil:"networkidle"});
await country.waitForFunction(()=>{
  const map=document.querySelector("#countrySubdivisionMap");
  return map?.contentDocument?.documentElement?.dataset?.dorappCountryMapBound==="true";
},{timeout:15000});
await country.locator("[data-country-map-zoom-in]").click();
await country.waitForFunction(()=>document.querySelector(".country-map-viewport")?.classList.contains("is-zoomed"));
report.interactions.countryMapZoom=await country.locator(".country-map-viewport").evaluate(element=>element.classList.contains("is-zoomed"));
await country.close();

// Verify that transient API failures are not represented as genuine empty results.
const failurePage=await context.newPage();
await failurePage.route("**/data/global-search-index.json",route=>route.abort());
await failurePage.goto(base+"/index.html",{waitUntil:"networkidle"});
await failurePage.locator("#organizationSearch").fill("próba");
await failurePage.waitForFunction(()=>document.querySelector("#organizationCount")?.textContent?.includes("nem tölthetők be"));
report.interactions.directoryFetchErrorVisible=await failurePage.locator("#organizationCount").textContent().then(x=>x.includes("Próbáld újra"));
await failurePage.unroute("**/data/global-search-index.json");
await failurePage.locator("#organizationSearch").fill("Ausztria");
await failurePage.waitForFunction(()=>!document.querySelector("#organizationCount")?.textContent?.includes("nem tölthetők be"));
report.interactions.directoryFetchRetry=!(await failurePage.locator("#organizationCount").textContent()).includes("nem tölthetők be");
await failurePage.route("**/data/global-events.json",route=>route.abort());
await failurePage.locator("#globalCalendarSearch").fill("próba");
await failurePage.waitForFunction(()=>document.querySelector("#globalCalendarCount")?.textContent?.includes("nem tölthető be"));
report.interactions.calendarFetchErrorVisible=(await failurePage.locator("#globalCalendarCount").textContent()).includes("Próbáld újra");
await failurePage.unroute("**/data/global-events.json");
await failurePage.locator("#globalCalendarSearch").fill("");
await failurePage.waitForFunction(()=>!document.querySelector("#globalCalendarCount")?.textContent?.includes("nem tölthető be"));
report.interactions.calendarFetchRetry=!(await failurePage.locator("#globalCalendarCount").textContent()).includes("nem tölthető be");
await failurePage.close();

// A registry outage must be communicated instead of leaving a silently blank map.
const registryFailure=await context.newPage();
await registryFailure.route("**/data/global.json",route=>route.abort());
await registryFailure.goto(base+"/index.html",{waitUntil:"networkidle"});
await registryFailure.waitForFunction(()=>document.querySelector("#worldMapStatus")?.textContent?.includes("átmenetileg nem érhetők el"));
report.interactions.registryFetchErrorVisible=(await registryFailure.locator("#worldMapStatus").textContent()).includes("Frissítsd az oldalt");
await registryFailure.close();

const consentContext=await browser.newContext();
const consentPage=await consentContext.newPage();
const analyticsRequests=[];
consentPage.on("request",request=>{if(request.url().includes("googletagmanager.com"))analyticsRequests.push(request.url())});
await consentPage.goto(base+"/index.html",{waitUntil:"networkidle"});
report.interactions.analyticsBeforeConsent=analyticsRequests.length;
await consentPage.locator(".consent-accept").click();
await consentPage.waitForTimeout(500);
report.interactions.analyticsAfterConsentRequest=analyticsRequests.length>0;
await consentContext.close();

for(const [key,value] of Object.entries(report.interactions)){
  if(key==="analyticsBeforeConsent"?value!==0:value!==true)report.failures.push({interaction:key,value});
}
await fs.writeFile("artifacts/responsive-ui-report.json",JSON.stringify(report,null,2));
await browser.close();
if(report.failures.length){
  console.error(JSON.stringify(report.failures.slice(0,30),null,2));
  process.exit(1);
}
console.log(`responsive_ui pages=${report.pages.length} screenshots=${screenshotWidths.size*screenshotRoutes.size} interactions=${Object.keys(report.interactions).length}`);
