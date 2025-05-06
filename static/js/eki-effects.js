/**
 * EKI Effects - JavaScript لتأثيرات موقع EKI Portfolio
 */

document.addEventListener('DOMContentLoaded', function() {
  // تحريك الفقاعات المتدرجة ببطء
  animateBlobs();
  
  // التحقق من وضع التمرير لتحديث شريط التنقل
  handleScrollEffects();
  
  // تفعيل أزرار النيون
  activateNeonButtons();
  
  // تفعيل قائمة الجوال
  setupMobileMenu();
  
  // زر العودة للأعلى
  setupBackToTop();
});

/**
 * تحريك الفقاعات المتدرجة ببطء
 */
function animateBlobs() {
  // التحقق من وجود الفقاعات في الصفحة
  const blobs = document.querySelectorAll('.blob');
  if (blobs.length === 0) return;
  
  // تحريك الفقاعات ببطء في اتجاهات عشوائية
  blobs.forEach(blob => {
    // تحديد موقع بداية عشوائي ضمن حدود معينة
    const startX = Math.random() * 10 - 5; // -5 to 5
    const startY = Math.random() * 10 - 5; // -5 to 5
    
    // تحريك الفقاعة ببطء
    setInterval(() => {
      const x = startX + Math.random() * 40 - 20; // -20 to 20
      const y = startY + Math.random() * 40 - 20; // -20 to 20
      blob.style.transform = `translate(${x}px, ${y}px)`;
    }, 10000); // كل 10 ثوانٍ
  });
}

/**
 * تغيير نمط شريط التنقل عند التمرير
 */
function handleScrollEffects() {
  const navbar = document.querySelector('.eki-navbar');
  if (!navbar) return;
  
  const backToTop = document.getElementById('backToTop');
  
  window.addEventListener('scroll', () => {
    // تحديث حالة شريط التنقل
    if (window.scrollY > 50) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
    
    // إظهار زر العودة للأعلى عند التمرير لأسفل
    if (backToTop) {
      if (window.scrollY > 300) {
        backToTop.classList.remove('opacity-0', 'invisible');
        backToTop.classList.add('opacity-100', 'visible');
      } else {
        backToTop.classList.add('opacity-0', 'invisible');
        backToTop.classList.remove('opacity-100', 'visible');
      }
    }
  });
}

/**
 * تفعيل وتهيئة أزرار النيون
 */
function activateNeonButtons() {
  const neonButtons = document.querySelectorAll('.btn-neon');
  
  neonButtons.forEach(button => {
    // إضافة تأثير التوهج عند تحريك المؤشر
    button.addEventListener('mousemove', e => {
      const rect = button.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      button.style.setProperty('--x', `${x}px`);
      button.style.setProperty('--y', `${y}px`);
    });
    
    // إزالة التأثير عند خروج المؤشر
    button.addEventListener('mouseleave', () => {
      button.style.setProperty('--x', '0px');
      button.style.setProperty('--y', '0px');
    });
  });
}

/**
 * تهيئة وتفعيل قائمة الجوال
 */
function setupMobileMenu() {
  const menuToggle = document.querySelector('.menu-toggle');
  const menuClose = document.querySelector('.menu-close');
  const mobileMenu = document.querySelector('.mobile-menu');
  
  if (!menuToggle || !menuClose || !mobileMenu) return;
  
  // فتح القائمة
  menuToggle.addEventListener('click', () => {
    mobileMenu.classList.remove('hidden');
    document.body.style.overflow = 'hidden'; // منع التمرير عند فتح القائمة
    
    // تأثير ظهور متدرج
    setTimeout(() => {
      mobileMenu.style.opacity = '1';
    }, 10);
  });
  
  // إغلاق القائمة
  menuClose.addEventListener('click', () => {
    mobileMenu.style.opacity = '0';
    
    setTimeout(() => {
      mobileMenu.classList.add('hidden');
      document.body.style.overflow = ''; // إعادة تفعيل التمرير
    }, 300);
  });
  
  // إغلاق القائمة عند النقر على أي رابط داخلها
  const mobileLinks = mobileMenu.querySelectorAll('a');
  mobileLinks.forEach(link => {
    link.addEventListener('click', () => {
      menuClose.click();
    });
  });
}

/**
 * تهيئة زر العودة للأعلى
 */
function setupBackToTop() {
  const backToTop = document.getElementById('backToTop');
  if (!backToTop) return;
  
  // تمرير للأعلى بسلاسة عند النقر على الزر
  backToTop.addEventListener('click', () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  });
}

/**
 * تغيير اللغة (إذا كان مطلوبًا)
 */
function toggleLanguage() {
  // يمكن تنفيذ التبديل بين اللغات هنا إذا كان مطلوبًا
  const currentPath = window.location.pathname;
  
  if (currentPath.startsWith('/en')) {
    // الانتقال للنسخة العربية
    window.location.href = currentPath.replace('/en', '');
  } else {
    // الانتقال للنسخة الإنجليزية
    window.location.href = '/en' + currentPath;
  }
}