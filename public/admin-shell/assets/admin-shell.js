const sections={
 dashboard:{title:"Dashboard",description:"مركز موحد لمتابعة أقسام AIO_TV.",icon:"⌂"},
 tv:{title:"TV",description:"إدارة القنوات والدول والتصنيفات وفحص البث.",icon:"▣",legacy:true},
 cameras:{title:"Cameras",description:"إدارة الكاميرات والمصادر وحالة التشغيل.",icon:"◉"},
 vod:{title:"VOD",description:"إدارة الأفلام والمسلسلات والمواسم والحلقات.",icon:"▷"},
 radios:{title:"Radios",description:"إدارة الإذاعات العربية والعالمية بصورة مستقلة.",icon:"♫"},
 users:{title:"المستخدمون والتسجيل",description:"الحسابات والتسجيل والأدوار والصلاحيات.",icon:"♙"},
 stores:{title:"المتاجر والتقييمات",description:"متابعة المتاجر والتقييمات ومراجعات المستخدمين.",icon:"▤"},
 subscriptions:{title:"الاشتراكات وإزالة الإعلانات",description:"إدارة الباقات والاشتراكات وخيارات إزالة الإعلانات.",icon:"◇"},
 ads:{title:"الإعلانات والإيرادات",description:"إدارة مواضع الإعلانات والوحدات ومؤشرات الإيرادات.",icon:"▧"},
 campaigns:{title:"المعلنون والحملات",description:"إدارة المعلنين والحملات الإعلانية وجدولتها.",icon:"◈"},
 billing:{title:"الفواتير والمدفوعات",description:"متابعة الفواتير والتحصيل وحالات الدفع.",icon:"▣"},
 reports:{title:"التقارير",description:"تقارير الأقسام والتصدير والمقارنات.",icon:"▥"},
 settings:{title:"الإعدادات",description:"إعدادات التطبيق واللوحة والخدمات.",icon:"⚙"},
 audit:{title:"سجل العمليات",description:"سجل مركزي للتغييرات والإجراءات الإدارية.",icon:"☷"},
 monitoring:{title:"مراقبة النظام",description:"متابعة الخدمات والبناء والنشر والأخطاء.",icon:"⌁"}
};
const app=document.getElementById("app"),pageTitle=document.getElementById("pageTitle"),pageDescription=document.getElementById("pageDescription"),pageBody=document.getElementById("pageBody"),currentSection=document.getElementById("currentSection");
function dashboardMarkup(){return `
  <div class="section-grid">
    <article class="overview-card overview-card-link" data-open-section="tv" role="button" tabindex="0" aria-label="فتح قسم البث التلفزيوني TV"><div class="card-icon">▣</div><strong>البث التلفزيوني TV</strong><small>القنوات والدول والتصنيفات وفحص البث.</small><div class="tv-summary" id="tvDashboardSummary">افتح قسم TV لتحميل بياناته الفعلية.</div></article>
    <article class="overview-card overview-card-link" data-open-section="cameras" role="button" tabindex="0" aria-label="فتح قسم الكاميرات Cameras"><div class="card-icon">◉</div><strong>الكاميرات Cameras</strong><small>الفيديو المباشر والصور الثابتة ومصادر API.</small><div class="camera-summary" id="cameraDashboardSummary">جارٍ تحميل بيانات الكاميرات...</div></article>
    <article class="overview-card"><div class="card-icon">▷</div><strong>مكتبة VOD</strong><small>الأفلام والمسلسلات والمواسم والحلقات.</small></article>
    <article class="overview-card overview-card-link" data-open-section="radios" role="button" tabindex="0" aria-label="فتح قسم الإذاعات Radios"><div class="card-icon">♫</div><strong>الإذاعات Radios</strong><small>الإذاعات العربية والعالمية وإدارتها.</small><div class="radio-summary" id="radioDashboardSummary">افتح قسم الإذاعات لتحميل الكتالوجين.</div></article>
    <article class="overview-card"><div class="card-icon">♙</div><strong>المستخدمون</strong><small>الحسابات والتسجيل والصلاحيات.</small></article>
    <article class="overview-card"><div class="card-icon">▥</div><strong>التقارير ومراقبة النظام</strong><small>مؤشرات الأداء وسجل العمليات وصحة الخدمات.</small></article>
  </div>
  <section class="panel"><h2>حالة تجهيز اللوحة</h2><p>يتم ربط الأقسام تدريجيًا. لا تُعرض إحصائيات إلا بعد تحميل بيانات القسم الفعلية والتحقق منها.</p></section>`;}
function sectionMarkup(key){const section=sections[key];if(key==="dashboard")return dashboardMarkup();if(key==="radios")return radioMarkup();if(key==="cameras")return `<section class="panel camera-panel"><h2>ملخص الكاميرات ومصادر البيانات</h2><p id="cameraSectionSummary">جارٍ تحميل بيانات الكاميرات...</p><div class="camera-stats"><div><strong id="cameraVideoCount">—</strong><span>فيديو مباشر HLS / MJPEG / MP4</span></div><div><strong id="cameraSnapshotCount">—</strong><span>صور ثابتة JPEG / PNG</span></div><div><strong id="cameraCountryCount">—</strong><span>الدول</span></div><div><strong id="cameraActiveSources">—</strong><span>مصادر API نشطة</span></div><div><strong id="cameraPendingSources">—</strong><span>مصادر API معلّقة</span></div></div><div class="camera-health" id="cameraHealthSummary">تقرير فحص الكاميرات غير متاح حاليًا.</div><p class="camera-note">الأعداد أعلاه من كتالوج الكاميرات. الصور الثابتة ليست بث فيديو، والمصادر المعلّقة لا تُعد مصادر نشطة. هذا القسم للعرض فقط ولا يغيّر الكتالوج أو روابط الكاميرات أو آلية الفحص.</p></section>`;return `<div class="placeholder"><div class="placeholder-icon">${section.icon}</div><h2>${section.title}</h2><p>${section.description}</p><span class="note">هذا القسم ضمن خطة التنفيذ — لم يتم ربط وظائفه أو بياناته بعد.</span></div>`;}

const tvFrameWrap=document.getElementById("tvFrameWrap");
let tvFrameSessionSent=false;
function ensureTvFrame(){
 let frame=tvFrameWrap.querySelector(".tv-frame");
 if(frame)return frame;
 frame=document.createElement("iframe");
 frame.className="tv-frame";
 frame.title="لوحة إدارة TV الحالية";
 frame.src="../admin/";
 frame.loading="eager";
 frame.addEventListener("load",()=>{
  if(sessionToken&&!tvFrameSessionSent){
   frame.contentWindow.postMessage({type:"AIO_TV_ADMIN_SESSION",accessToken:sessionToken},window.location.origin);
   tvFrameSessionSent=true;
  }
 });
 tvFrameWrap.appendChild(frame);
 return frame;
}
function navigate(key){
 if(!sections[key])return;
 const section=sections[key];
 pageTitle.textContent=section.title;
 pageDescription.textContent=section.description;
 currentSection.textContent=section.title;
 if(section.legacy){
  pageBody.hidden=true;
  tvFrameWrap.hidden=false;
  ensureTvFrame();
 }else{
  tvFrameWrap.hidden=true;
  pageBody.hidden=false;
  pageBody.innerHTML=sectionMarkup(key);
  if(key==="dashboard"){
   renderDashboardTvSummary();
   requestTvDashboardSummary();
  }
  if(key==="dashboard"||key==="cameras"){
   renderCameraSummary();
   loadCameraDashboardData();
  }
  if(key==="radios"){
   bindRadioControls();
   renderRadioDashboardSummary();
   loadRadioAdminData();
  }
 }
 document.querySelectorAll(".nav-item").forEach(button=>button.classList.toggle("active",button.dataset.section===key));
 document.title="AIO_TV | "+section.title;
 app.classList.remove("mobile-nav-open");
}
let tvDashboardSummary=null;
let cameraCatalogSummary=null,cameraHealthSummary=null,cameraLoadPromise=null,cameraLoadError="";
function cameraHealthText(){
 if(!cameraHealthSummary)return "تقرير فحص الكاميرات غير متاح حاليًا.";
 const s=cameraHealthSummary.summary||{};
 const date=cameraHealthSummary.generated_at?new Date(cameraHealthSummary.generated_at).toLocaleString("ar-EG"):"غير محدد";
 return "آخر فحص: "+date+" — تم فحص "+Number(cameraHealthSummary.checked_count||0)+" كاميرا فيديو: يعمل "+Number(s.working||0)+" — متوقف "+Number(s.down||0)+" — تعذر التحقق "+Number(s.unknown||0)+".";
}
function cameraCatalogText(){
 if(!cameraCatalogSummary)return cameraLoadError||"جارٍ تحميل بيانات الكاميرات...";
 const types=cameraCatalogSummary.camera_types||{},api=cameraCatalogSummary.api_source_catalog||{};
 return "فيديو مباشر: "+Number((types.video||{}).count||0)+" • صور ثابتة: "+Number((types.snapshots||{}).count||0)+" • الدول: "+Number(cameraCatalogSummary.country_count||0)+" • مصادر API نشطة: "+Number(api.active_source_count||0)+" • معلّقة: "+Number(api.pending_source_count||0);
}
function renderCameraSummary(){
 const dashboard=document.getElementById("cameraDashboardSummary");
 if(dashboard)dashboard.textContent=cameraCatalogText()+" • "+cameraHealthText();
 const section=document.getElementById("cameraSectionSummary");
 if(section)section.textContent=cameraCatalogText();
 const health=document.getElementById("cameraHealthSummary");
 if(health)health.textContent=cameraHealthText();
 if(cameraCatalogSummary){
  const types=cameraCatalogSummary.camera_types||{},api=cameraCatalogSummary.api_source_catalog||{};
  const values={cameraVideoCount:(types.video||{}).count,cameraSnapshotCount:(types.snapshots||{}).count,cameraCountryCount:cameraCatalogSummary.country_count,cameraActiveSources:api.active_source_count,cameraPendingSources:api.pending_source_count};
  Object.entries(values).forEach(([id,value])=>{const node=document.getElementById(id);if(node)node.textContent=Number(value||0).toLocaleString("en-US");});
 }
}
async function loadCameraDashboardData(){
 if(cameraLoadPromise)return cameraLoadPromise;
 cameraLoadPromise=(async()=>{
  try{
   const base=new URL("../cameras/",window.location.href);
   const catalogResponse=await fetch(new URL("catalog.json",base),{cache:"no-store"});
   if(!catalogResponse.ok)throw Error("تعذر تحميل كتالوج الكاميرات (HTTP "+catalogResponse.status+")");
   cameraCatalogSummary=await catalogResponse.json();
   cameraLoadError="";
   try{
    const healthResponse=await fetch(new URL("health-report.json",base),{cache:"no-store"});
    if(healthResponse.ok)cameraHealthSummary=await healthResponse.json();
    else cameraHealthSummary=null;
   }catch(_){cameraHealthSummary=null;}
  }catch(error){cameraLoadError="تعذر تحميل بيانات الكاميرات: "+(error.message||String(error));}
  renderCameraSummary();
 })();
 return cameraLoadPromise;
}

let radioCatalogs=null,radioLoadPromise=null,radioFileSha=null,radioOverrides=null;
let selectedRadioCatalog="radio_arabic_quran",selectedRadioId=null;
function radioMarkup(){
 return `
 <section class="panel radio-panel">
  <div class="radio-toolbar">
   <div><h2>كتالوج الإذاعات</h2><p>إدارة الإذاعات العربية والقرآن والعالمية. التعديلات تُحفظ في GitHub وتُنشر تلقائيًا.</p></div>
   <div class="radio-toolbar-actions">
    <select id="radioCatalogSelect" aria-label="نوع كتالوج الإذاعة"><option value="radio_arabic_quran">الإذاعات العربية والقرآن</option><option value="radio_world">الإذاعات العالمية والموجات القصيرة</option></select>
    <button class="radio-primary" id="radioAddButton" type="button">إضافة إذاعة</button>
   </div>
  </div>
  <div class="radio-stats">
   <div><strong id="radioTotalCount">—</strong><span>إجمالي الإذاعات</span></div><div><strong id="radioCountryCount">—</strong><span>الدول</span></div><div><strong id="radioStreamCount">—</strong><span>روابط بث مباشرة</span></div><div><strong id="radioNoStreamCount">—</strong><span>بدون رابط مباشر</span></div>
  </div>
  <div class="radio-list-tools"><input id="radioSearch" type="search" placeholder="ابحث بالاسم أو الدولة أو المعرّف..."><span id="radioListCount"></span></div>
  <div class="radio-table-wrap"><table class="radio-table"><thead><tr><th>اسم الإذاعة</th><th>الدولة</th><th>التصنيف</th><th>البث</th><th>الإجراءات</th></tr></thead><tbody id="radioRows"><tr><td colspan="5">جارٍ تحميل الكتالوج...</td></tr></tbody></table></div>
  <p class="radio-status" id="radioStatus" role="status">يتم تحميل بيانات الإذاعات...</p>
 </section>
 <section class="panel radio-editor" id="radioEditor" hidden>
  <div class="radio-toolbar"><h2 id="radioEditorTitle">إضافة إذاعة جديدة</h2><span class="radio-editor-note">الحقول الأساسية مطلوبة؛ رابط البث اختياري لخدمات الموجات القصيرة.</span></div>
  <div class="radio-form-grid">
   <label>المعرّف الفريد<input id="radioId" autocomplete="off" placeholder="EG_STATION_NAME"></label><label>اسم الإذاعة<input id="radioName" autocomplete="off"></label>
   <label>الدولة<input id="radioCountry" autocomplete="off" placeholder="Egypt"></label><label>رمز الدولة<input id="radioCountryCode" maxlength="2" autocomplete="off" placeholder="EG"></label>
   <label>المنطقة<input id="radioRegion" autocomplete="off" placeholder="Africa / Asia"></label><label>اللغات<input id="radioLanguages" autocomplete="off" placeholder="Arabic, English"></label>
   <label>التصنيفات<input id="radioCategories" autocomplete="off" placeholder="music, news, quran"></label><label>صيغة البث<input id="radioFormat" autocomplete="off" placeholder="MP3 / AAC / HLS"></label>
   <label class="radio-wide">رابط البث<input id="radioStreamUrl" type="url" autocomplete="off" placeholder="https://..."></label>
   <label>المصدر<input id="radioSource" autocomplete="off"></label><label>رابط المصدر<input id="radioSourceUrl" type="url" autocomplete="off" placeholder="https://..."></label>
   <label class="radio-wide">حالة التحقق<input id="radioStationStatus" autocomplete="off" placeholder="listed_not_independently_tested"></label>
  </div>
  <div class="radio-editor-actions"><button class="radio-primary" id="radioSaveButton" type="button">حفظ الإذاعة</button><button class="radio-secondary" id="radioCancelButton" type="button">إلغاء</button></div>
 </section>`;
}
function radioEscape(value){return String(value==null?"":value).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function radioCatalog(){return radioCatalogs&&radioCatalogs[selectedRadioCatalog]}
function renderRadioDashboardSummary(){
 const target=document.getElementById("radioDashboardSummary");if(!target)return;
 if(!radioCatalogs){target.textContent="افتح قسم الإذاعات لتحميل الكتالوجين.";return;}
 const all=Object.values(radioCatalogs).flatMap(c=>c.stations||[]);
 target.textContent="إذاعات: "+all.length+" • دول: "+new Set(all.map(s=>s.country_code).filter(Boolean)).size+" • روابط بث: "+all.filter(s=>s.stream_url).length;
}
function setRadioStatus(message){const node=document.getElementById("radioStatus");if(node)node.textContent=message}
async function loadRadioAdminData(){
 if(radioLoadPromise){try{await radioLoadPromise;}catch(_){}renderRadioDashboardSummary();renderRadioTable();return;}
 radioLoadPromise=(async()=>{
  try{
   const response=await fetch(WORKER+"/github/overrides",{headers:{Accept:"application/json",Authorization:"Bearer "+sessionToken},cache:"no-store"});
   const data=await response.json().catch(()=>({}));if(!response.ok)throw Error(data.message||data.error||("HTTP "+response.status));
   radioFileSha=data.sha;radioOverrides=JSON.parse(radioDecode64(data.content));radioCatalogs=radioOverrides.radio_catalogs;
   if(!radioCatalogs||!radioCatalogs.radio_arabic_quran||!radioCatalogs.radio_world)throw Error("كتالوجات الإذاعات غير مهيأة داخل بيانات الإدارة.");
   renderRadioDashboardSummary();renderRadioTable();
   setRadioStatus("تم تحميل "+radioCatalog().stations.length+" إذاعة من GitHub. يمكنك الإضافة والتعديل والحذف.");
  }catch(error){setRadioStatus("تعذر تحميل كتالوج الإذاعات: "+(error.message||String(error)));throw error;}
 })();
 try{await radioLoadPromise;}catch(_){}
}
function renderRadioTable(){
 const catalog=radioCatalog(),rows=document.getElementById("radioRows");if(!catalog||!rows)return;
 const query=(document.getElementById("radioSearch")?.value||"").trim().toLocaleLowerCase();
 const stations=(catalog.stations||[]).filter(s=>[s.id,s.name,s.country,s.country_code,...(s.categories||[]),...(s.languages||[])].join(" ").toLocaleLowerCase().includes(query));
 const countries=new Set((catalog.stations||[]).map(s=>s.country_code).filter(Boolean)),streams=(catalog.stations||[]).filter(s=>s.stream_url).length;
 const values={radioTotalCount:catalog.stations.length,radioCountryCount:countries.size,radioStreamCount:streams,radioNoStreamCount:catalog.stations.length-streams,radioListCount:"عرض "+stations.length+" من "+catalog.stations.length};
 Object.entries(values).forEach(([id,value])=>{const node=document.getElementById(id);if(node)node.textContent=typeof value==="number"?value.toLocaleString("en-US"):value;});
 rows.innerHTML=stations.map(s=>'<tr><td><strong>'+radioEscape(s.name)+'</strong><small>'+radioEscape(s.id)+'</small></td><td>'+radioEscape(s.country)+' ('+radioEscape(s.country_code)+')</td><td>'+radioEscape((s.categories||[]).join(", ")||"—")+'</td><td><span class="radio-stream-badge '+(s.stream_url?"has-stream":"no-stream")+'">'+(s.stream_url?"رابط متاح":"بدون رابط")+'</span></td><td><div class="radio-row-actions"><button type="button" data-radio-edit="'+radioEscape(s.id)+'">تعديل</button><button type="button" class="delete" data-radio-delete="'+radioEscape(s.id)+'">حذف</button></div></td></tr>').join("")||'<tr><td colspan="5">لا توجد إذاعات مطابقة.</td></tr>';
 rows.querySelectorAll("[data-radio-edit]").forEach(button=>button.addEventListener("click",()=>editRadio(button.dataset.radioEdit)));
 rows.querySelectorAll("[data-radio-delete]").forEach(button=>button.addEventListener("click",()=>deleteRadio(button.dataset.radioDelete)));
}
function resetRadioEditor(){selectedRadioId=null;const editor=document.getElementById("radioEditor");if(editor)editor.hidden=true;const id=document.getElementById("radioId");if(id)id.disabled=false}
function editRadio(id){
 const station=radioCatalog().stations.find(s=>s.id===id);if(!station)return;selectedRadioId=id;
 const fields={radioId:station.id,radioName:station.name,radioCountry:station.country,radioCountryCode:station.country_code,radioRegion:station.region||"",radioLanguages:(station.languages||[]).join(", "),radioCategories:(station.categories||[]).join(", "),radioStreamUrl:station.stream_url||"",radioFormat:station.format||"",radioSource:station.source||"",radioSourceUrl:station.source_url||"",radioStationStatus:station.status||""};
 Object.entries(fields).forEach(([key,value])=>{const node=document.getElementById(key);if(node)node.value=value});
 document.getElementById("radioId").disabled=true;document.getElementById("radioEditorTitle").textContent="تعديل بيانات الإذاعة";document.getElementById("radioEditor").hidden=false;document.getElementById("radioEditor").scrollIntoView({behavior:"smooth",block:"start"});
}
function addRadio(){
 selectedRadioId=null;["radioId","radioName","radioCountry","radioCountryCode","radioRegion","radioLanguages","radioCategories","radioStreamUrl","radioFormat","radioSource","radioSourceUrl","radioStationStatus"].forEach(id=>{const node=document.getElementById(id);if(node)node.value=""});
 document.getElementById("radioId").disabled=false;document.getElementById("radioStationStatus").value="listed_not_independently_tested";document.getElementById("radioEditorTitle").textContent="إضافة إذاعة جديدة";document.getElementById("radioEditor").hidden=false;document.getElementById("radioEditor").scrollIntoView({behavior:"smooth",block:"start"});
}
function radioList(value){return value.split(",").map(s=>s.trim()).filter(Boolean)}
async function saveRadio(){
 try{
  if(!radioCatalogs||!radioOverrides)throw Error("لم يتم تحميل كتالوج الإذاعات.");
  const value=id=>document.getElementById(id).value.trim(),id=value("radioId"),name=value("radioName"),country=value("radioCountry"),countryCode=value("radioCountryCode").toUpperCase(),streamUrl=value("radioStreamUrl"),sourceUrl=value("radioSourceUrl");
  if(!id||!name||!country||!countryCode)throw Error("أدخل المعرّف والاسم والدولة ورمز الدولة.");
  if(!/^[A-Za-z0-9_-]+$/.test(id))throw Error("المعرّف يقبل الحروف الإنجليزية والأرقام والشرطة فقط.");
  for(const url of [streamUrl,sourceUrl])if(url&&!/^https?:\/\//i.test(url))throw Error("تأكد من صحة روابط البث والمصدر.");
  const stations=radioCatalog().stations,existing=selectedRadioId?stations.find(s=>s.id===selectedRadioId):null;
  if(!existing&&stations.some(s=>s.id===id))throw Error("هذا المعرّف موجود بالفعل.");
  const station={id,name,country,country_code:countryCode,region:value("radioRegion"),languages:radioList(value("radioLanguages")),categories:radioList(value("radioCategories")),stream_url:streamUrl,format:value("radioFormat"),source:value("radioSource"),source_url:sourceUrl,status:value("radioStationStatus")||"listed_not_independently_tested"};
  if(existing)Object.assign(existing,station);else stations.push(station);
  await saveRadioCatalogs(existing?"edit":"add",id);resetRadioEditor();renderRadioTable();renderRadioDashboardSummary();setRadioStatus("تم حفظ الإذاعة في GitHub. يجري نشر الكتالوج المحدّث تلقائيًا.");
 }catch(error){setRadioStatus("تعذر حفظ الإذاعة: "+(error.message||String(error)));}
}
async function deleteRadio(id){
 const stations=radioCatalog().stations,index=stations.findIndex(s=>s.id===id);if(index<0)return;const station=stations[index];
 if(!confirm("حذف الإذاعة «"+station.name+"» نهائيًا من الكتالوج؟"))return;
 stations.splice(index,1);
 try{await saveRadioCatalogs("delete",id);resetRadioEditor();renderRadioTable();renderRadioDashboardSummary();setRadioStatus("تم حذف الإذاعة من GitHub ونشر التغيير تلقائيًا.");}
 catch(error){setRadioStatus("تعذر حذف الإذاعة: "+(error.message||String(error)));}
}
function radioDecode64(value){const binary=atob(String(value||"").replace(/\n/g,""));return new TextDecoder().decode(Uint8Array.from(binary,c=>c.charCodeAt(0)))}
function radioEncode64(value){const bytes=new TextEncoder().encode(value);let binary="";bytes.forEach(byte=>binary+=String.fromCharCode(byte));return btoa(binary)}
async function saveRadioCatalogs(action,id){
 radioOverrides.radio_catalogs=radioCatalogs;radioOverrides.radio_audit=radioOverrides.radio_audit||[];radioOverrides.radio_audit.push({catalog:selectedRadioCatalog,station_id:id,action,changed_at:new Date().toISOString()});
 const content=JSON.stringify(radioOverrides,null,2)+"\n";
 const response=await fetch(WORKER+"/github/overrides",{method:"PUT",headers:{Accept:"application/json","Content-Type":"application/json",Authorization:"Bearer "+sessionToken},body:JSON.stringify({message:action+" radio station "+id,content:radioEncode64(content),sha:radioFileSha})});
 const result=await response.json().catch(()=>({}));if(!response.ok)throw Error(result.message||result.error||("HTTP "+response.status));radioFileSha=result.sha;
}
function bindRadioControls(){
 const select=document.getElementById("radioCatalogSelect");
 if(select){select.value=selectedRadioCatalog;select.addEventListener("change",()=>{selectedRadioCatalog=select.value;resetRadioEditor();renderRadioTable()})}
 document.getElementById("radioSearch")?.addEventListener("input",renderRadioTable);
 document.getElementById("radioAddButton")?.addEventListener("click",addRadio);
 document.getElementById("radioSaveButton")?.addEventListener("click",saveRadio);
 document.getElementById("radioCancelButton")?.addEventListener("click",resetRadioEditor);
}

function requestTvDashboardSummary(){
 const frame=tvFrameWrap.querySelector(".tv-frame");
 if(frame)frame.contentWindow.postMessage({type:"AIO_TV_REQUEST_DASHBOARD_SUMMARY"},window.location.origin);
}
function renderDashboardTvSummary(){
 const target=document.getElementById("tvDashboardSummary");
 if(!target)return;
 if(!tvDashboardSummary){target.textContent="افتح قسم TV لتحميل بياناته الفعلية.";return;}
 const s=tvDashboardSummary;
 const parts=["قنوات لديها بث: "+s.channelsWithStreams,"بلا بث: "+s.channelsWithoutStreams,"الدول: "+s.countries,"التصنيفات: "+s.categories,"روابط البث: "+s.streamLinks,"المؤرشفة: "+s.archivedChannels];
 if(s.health){parts.push("آخر فحص"+(s.health.generatedAt?" ("+new Date(s.health.generatedAt).toLocaleString("ar-EG")+")":"")+": يعمل "+s.health.working+" — متوقف "+s.health.down+" — تعذر التحقق "+s.health.unknown);}
 else{parts.push("تقرير فحص البث غير متاح حاليًا.");}
 target.textContent=parts.join(" • ");
}
pageBody.addEventListener("click",event=>{
 const card=event.target.closest("[data-open-section]");
 if(card)navigate(card.dataset.openSection);
});
pageBody.addEventListener("keydown",event=>{
 const card=event.target.closest("[data-open-section]");
 if(card&&(event.key==="Enter"||event.key===" ")){event.preventDefault();navigate(card.dataset.openSection);}
});
window.addEventListener("message",event=>{
 const frame=tvFrameWrap.querySelector(".tv-frame");
 if(event.origin!==window.location.origin||!frame||event.source!==frame.contentWindow)return;
 const data=event.data||{};
 if(data.type!=="AIO_TV_DASHBOARD_SUMMARY"||!data.summary)return;
 tvDashboardSummary=data.summary;
 renderDashboardTvSummary();
});
document.getElementById("mainNav").addEventListener("click",event=>{const button=event.target.closest("[data-section]");if(button)navigate(button.dataset.section);});
document.getElementById("sidebarToggle").addEventListener("click",()=>{if(window.matchMedia("(max-width: 720px)").matches)app.classList.toggle("mobile-nav-open");else app.classList.toggle("sidebar-collapsed");});
document.getElementById("sectionSearch").addEventListener("input",event=>{const query=event.target.value.trim().toLocaleLowerCase();if(!query)return;const match=Object.entries(sections).find(([key,value])=>(value.title+" "+key).toLocaleLowerCase().includes(query));if(match)navigate(match[0]);});

const WORKER="https://aio-tv-admin-api.vetdr66-1fe.workers.dev";
const authGate=document.getElementById("authGate"),loginForm=document.getElementById("loginForm"),loginButton=document.getElementById("loginButton"),loginStatus=document.getElementById("loginStatus"),adminPassword=document.getElementById("adminPassword");
let sessionToken=null;
loginForm.addEventListener("submit",async event=>{
 event.preventDefault();
 const password=adminPassword.value;
 if(!password)return;
 loginButton.disabled=true;loginStatus.textContent="جارٍ التحقق من بيانات الدخول...";
 try{
  const response=await fetch(WORKER+"/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({password})});
  const result=await response.json().catch(()=>({}));
  if(!response.ok)throw Error(result.message||result.error||("HTTP "+response.status));
  if(!result.access_token)throw Error("لم يُرجع الخادم رمز جلسة صالحًا.");
  sessionToken=result.access_token;
  adminPassword.value="";
  authGate.hidden=true;
  app.hidden=false;
  loginStatus.textContent="";
  navigate("dashboard");
 }catch(error){
  sessionToken=null;
  loginStatus.textContent="تعذر تسجيل الدخول: "+(error.message||String(error));
 }finally{loginButton.disabled=false;}
});

