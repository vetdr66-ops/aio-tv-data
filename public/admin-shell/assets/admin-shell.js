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
    <article class="overview-card"><div class="card-icon">▣</div><strong>البث التلفزيوني TV</strong><small>القنوات والدول والتصنيفات وفحص البث.</small></article>
    <article class="overview-card"><div class="card-icon">◉</div><strong>الكاميرات Cameras</strong><small>مصادر الكاميرات ومتابعة حالة التشغيل.</small></article>
    <article class="overview-card"><div class="card-icon">▷</div><strong>مكتبة VOD</strong><small>الأفلام والمسلسلات والمواسم والحلقات.</small></article>
    <article class="overview-card"><div class="card-icon">♫</div><strong>الإذاعات Radios</strong><small>الإذاعات العربية والعالمية وإدارتها.</small></article>
    <article class="overview-card"><div class="card-icon">♙</div><strong>المستخدمون</strong><small>الحسابات والتسجيل والصلاحيات.</small></article>
    <article class="overview-card"><div class="card-icon">▥</div><strong>التقارير ومراقبة النظام</strong><small>مؤشرات الأداء وسجل العمليات وصحة الخدمات.</small></article>
  </div>
  <section class="panel"><h2>حالة تجهيز اللوحة</h2><p>هذه مرحلة بناء الهيكل والتنقل فقط. لم يتم توصيل بيانات الأقسام أو إنشاء إحصائيات وهمية. سيظهر المحتوى الفعلي بعد تنفيذ وربط كل قسم واختباره.</p></section>`;}
function sectionMarkup(key){const section=sections[key];if(key==="dashboard")return dashboardMarkup();if(section.legacy)return '<div class="tv-frame-wrap"><iframe class="tv-frame" title="لوحة إدارة TV الحالية" src="../admin/" loading="eager"></iframe></div>';return `<div class="placeholder"><div class="placeholder-icon">${section.icon}</div><h2>${section.title}</h2><p>${section.description}</p><span class="note">هذا القسم ضمن خطة التنفيذ — لم يتم ربط وظائفه أو بياناته بعد.</span></div>`;}
function navigate(key){if(!sections[key])return;const section=sections[key];pageTitle.textContent=section.title;pageDescription.textContent=section.description;currentSection.textContent=section.title;pageBody.innerHTML=sectionMarkup(key);document.querySelectorAll(".nav-item").forEach(button=>button.classList.toggle("active",button.dataset.section===key));document.title="AIO_TV | "+section.title;app.classList.remove("mobile-nav-open");}
document.getElementById("mainNav").addEventListener("click",event=>{const button=event.target.closest("[data-section]");if(button)navigate(button.dataset.section);});
document.getElementById("sidebarToggle").addEventListener("click",()=>{if(window.matchMedia("(max-width: 720px)").matches)app.classList.toggle("mobile-nav-open");else app.classList.toggle("sidebar-collapsed");});
document.getElementById("sectionSearch").addEventListener("input",event=>{const query=event.target.value.trim().toLocaleLowerCase();if(!query)return;const match=Object.entries(sections).find(([key,value])=>(value.title+" "+key).toLocaleLowerCase().includes(query));if(match)navigate(match[0]);});
navigate("dashboard");
