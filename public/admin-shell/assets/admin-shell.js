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
    <article class="overview-card"><div class="card-icon">◉</div><strong>الكاميرات Cameras</strong><small>مصادر الكاميرات ومتابعة حالة التشغيل.</small></article>
    <article class="overview-card"><div class="card-icon">▷</div><strong>مكتبة VOD</strong><small>الأفلام والمسلسلات والمواسم والحلقات.</small></article>
    <article class="overview-card"><div class="card-icon">♫</div><strong>الإذاعات Radios</strong><small>الإذاعات العربية والعالمية وإدارتها.</small></article>
    <article class="overview-card"><div class="card-icon">♙</div><strong>المستخدمون</strong><small>الحسابات والتسجيل والصلاحيات.</small></article>
    <article class="overview-card"><div class="card-icon">▥</div><strong>التقارير ومراقبة النظام</strong><small>مؤشرات الأداء وسجل العمليات وصحة الخدمات.</small></article>
  </div>
  <section class="panel"><h2>حالة تجهيز اللوحة</h2><p>يتم ربط الأقسام تدريجيًا. لا تُعرض إحصائيات إلا بعد تحميل بيانات القسم الفعلية والتحقق منها.</p></section>`;}
function sectionMarkup(key){const section=sections[key];if(key==="dashboard")return dashboardMarkup();return `<div class="placeholder"><div class="placeholder-icon">${section.icon}</div><h2>${section.title}</h2><p>${section.description}</p><span class="note">هذا القسم ضمن خطة التنفيذ — لم يتم ربط وظائفه أو بياناته بعد.</span></div>`;}

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
 }
 document.querySelectorAll(".nav-item").forEach(button=>button.classList.toggle("active",button.dataset.section===key));
 document.title="AIO_TV | "+section.title;
 app.classList.remove("mobile-nav-open");
}
let tvDashboardSummary=null;
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

