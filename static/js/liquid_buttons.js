/**
 * مؤثرات الأزرار السائلة والتحول
 */

document.addEventListener('DOMContentLoaded', function() {
  // تحسين أزرار النيون
  setupNeonButtons();
  
  // تفعيل القائمة المتحركة على الجوال
  setupMobileMenu();
  
  // إضافة تأثير التمرير على شريط التنقل
  handleScrollEffects();
  
  // تحريك الفقاعات في الخلفية
  animateBlobs();
});

/**
 * تهيئة أزرار النيون بتأثيرات التوهج
 */
function setupNeonButtons() {
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
 * تفعيل قائمة الجوال
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
 * تغيير نمط شريط التنقل عند التمرير
 */
function handleScrollEffects() {
  const navbar = document.querySelector('.eki-navbar');
  if (!navbar) return;
  
  window.addEventListener('scroll', () => {
    // تحديث حالة شريط التنقل
    if (window.scrollY > 50) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  });
}

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