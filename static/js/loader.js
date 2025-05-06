/**
 * EKI Loader - JavaScript لشاشة التحميل المبدئية
 */

document.addEventListener('DOMContentLoaded', function() {
  // التحقق من وجود شاشة التحميل
  const pageLoader = document.getElementById('pageLoader');
  if (!pageLoader) return;
  
  // إظهار شاشة التحميل مباشرة
  pageLoader.style.display = 'flex';
  
  // إخفاء شاشة التحميل بعد انتهاء تحميل الصفحة
  setTimeout(() => {
    pageLoader.classList.add('fade-out');
    
    // إزالة شاشة التحميل من الـ DOM بعد انتهاء التأثير
    setTimeout(() => {
      pageLoader.style.display = 'none';
      
      // إظهار العناصر بتأثير فيد إن تدريجي
      animatePageEntrance();
    }, 500);
  }, 1000); // عرض لوحة التحميل لمدة 1.5 ثانية
});

/**
 * تأثير ظهور عناصر الصفحة تدريجيًا
 */
function animatePageEntrance() {
  // العناصر التي ستظهر تدريجيًا
  const fadeElements = document.querySelectorAll('.fade-in-up, .fade-in');
  
  // تطبيق التأخير على كل عنصر
  fadeElements.forEach((element, index) => {
    // تحديد مقدار التأخير بناءً على موقع العنصر
    const delay = index * 0.1; // 100ms لكل عنصر
    element.style.animationDelay = `${delay}s`;
    
    // تفعيل العنصر
    element.style.animationPlayState = 'running';
  });
}

/**
 * تهيئة وتفعيل الرسوم المتحركة للشاشة الترحيبية
 */
document.addEventListener('DOMContentLoaded', function() {
  // التحقق من وجود الشاشة الترحيبية
  const introOverlay = document.getElementById('introOverlay');
  if (!introOverlay) return;
  
  // إظهار الشاشة الترحيبية إذا لم يتم عرضها من قبل
  const introShown = sessionStorage.getItem('introShown');
  
  if (!introShown) {
    introOverlay.classList.remove('hidden');
    
    // تحريك الفقاعات في الشاشة الترحيبية
    animateWelcomeBlobs();
    
    // إخفاء الشاشة الترحيبية بعد بضع ثوانٍ
    setTimeout(() => {
      // تأثير التلاشي
      introOverlay.style.opacity = '0';
      
      // إزالة الشاشة الترحيبية بعد انتهاء التأثير
      setTimeout(() => {
        introOverlay.classList.add('hidden');
      }, 1000);
      
      // تخزين معلومات أن الشاشة الترحيبية قد تم عرضها
      sessionStorage.setItem('introShown', 'true');
    }, 5000); // عرض الشاشة الترحيبية لمدة 5 ثوانٍ
  }
});

/**
 * تحريك فقاعات الشاشة الترحيبية
 */
function animateWelcomeBlobs() {
  // التحقق من وجود فقاعات في الشاشة الترحيبية
  const welcomeBlobs = document.querySelectorAll('.welcome-blob');
  if (welcomeBlobs.length === 0) return;
  
  // تحريك كل فقاعة بشكل عشوائي وبطيء
  welcomeBlobs.forEach(blob => {
    // حركة خفيفة لكل فقاعة
    setInterval(() => {
      const x = Math.random() * 10 - 5;
      const y = Math.random() * 10 - 5;
      const scale = 0.95 + Math.random() * 0.2;
      
      blob.style.transform = `translate(${x}px, ${y}px) scale(${scale})`;
    }, 3000);
  });
}