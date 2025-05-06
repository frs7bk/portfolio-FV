/**
 * smooth-effects.js - تأثيرات حركية سلسة لتحسين تجربة المستخدم
 * 
 * تم إنشاؤه لموقع فراس للتصميم لإضافة تأثيرات حركية متقدمة لعناصر معرض الأعمال والخدمات
 */

document.addEventListener('DOMContentLoaded', function() {
  // تهيئة التأثيرات الحركية
  initSmoothEffects();
  
  // تهيئة تأثير التمرير السلس للروابط
  initSmoothScroll();
  
  // تهيئة تأثيرات الظهور عند التمرير
  initScrollReveal();
  
  // تهيئة تأثير hover للعناصر
  initHoverEffects();
});

/**
 * تهيئة التأثيرات الحركية العامة
 */
function initSmoothEffects() {
  console.log('تهيئة التأثيرات الحركية السلسة...');
  
  // إضافة فئة التحميل المكتمل لعنصر body
  setTimeout(() => {
    document.body.classList.add('loaded');
  }, 300);
  
  // تفعيل تأثيرات مكتبة AOS إذا كانت موجودة
  if (typeof AOS !== 'undefined') {
    AOS.init({
      duration: 1200, // زيادة المدة لتأثير أبطأ وأكثر جمالًا
      easing: 'ease-out',
      once: false,
      mirror: true,
      delay: 200, // إضافة تأخير بين التأثيرات
      anchorPlacement: 'top-bottom',
      disable: 'mobile'
    });
    
    console.log('تم تهيئة مكتبة AOS للتأثيرات');
  }
  
  // إضافة تأثير ظهور متدرج للعناصر مع تأخير أطول بين العناصر
  const staggeredElements = document.querySelectorAll('.staggered-item');
  staggeredElements.forEach((el, index) => {
    el.style.transitionDelay = `${index * 0.15}s`; // زيادة التأخير بين العناصر
    // إضافة تأخير مبدأي قبل بدء التأثيرات
    setTimeout(() => {
      el.classList.add('fade-in');
    }, 100);
  });
}

/**
 * تهيئة تأثير التمرير السلس للروابط الداخلية
 */
function initSmoothScroll() {
  // اختيار جميع الروابط الداخلية التي تبدأ بـ #
  const internalLinks = document.querySelectorAll('a[href^="#"]:not([href="#"])');
  
  internalLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      
      const targetId = this.getAttribute('href');
      const targetElement = document.querySelector(targetId);
      
      if (targetElement) {
        // استخدام scrollIntoView مع سلوك سلس
        targetElement.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
        
        // إضافة تأثير وميض للعنصر المستهدف
        setTimeout(() => {
          targetElement.classList.add('highlight-target');
          setTimeout(() => {
            targetElement.classList.remove('highlight-target');
          }, 1500);
        }, 500);
      }
    });
  });
}

/**
 * تهيئة تأثيرات الظهور عند التمرير
 */
function initScrollReveal() {
  const observerOptions = {
    root: null, // استخدام viewport كعنصر المراقب
    rootMargin: '0px',
    threshold: 0.1 // النسبة المئوية للعنصر التي يجب أن تكون مرئية
  };
  
  // إنشاء كائن IntersectionObserver للمراقبة
  const elementObserver = new IntersectionObserver((entries, elementObserver) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        // إضافة فئة animated للعنصر عندما يصبح مرئيًا
        entry.target.classList.add('animated');
        
        // إيقاف مراقبة العنصر بعد تفعيل التأثير (اختياري)
        if (entry.target.hasAttribute('data-animate-once')) {
          elementObserver.unobserve(entry.target);
        }
      } else if (!entry.target.hasAttribute('data-animate-once')) {
        // إزالة فئة animated عند الخروج من مجال الرؤية (إذا كان مطلوبًا)
        entry.target.classList.remove('animated');
      }
    });
  }, observerOptions);
  
  // العناصر التي نرغب في مراقبتها
  const elements = document.querySelectorAll('.scroll-reveal');
  elements.forEach(el => {
    elementObserver.observe(el);
  });
}

/**
 * تهيئة تأثيرات الحركة عند مرور المؤشر فوق العناصر
 */
function initHoverEffects() {
  // تأثير الإضاءة 3D للبطاقات
  const cards = document.querySelectorAll('.hover-3d');
  
  cards.forEach(card => {
    card.addEventListener('mousemove', e => {
      // الحصول على موقع المؤشر بالنسبة للبطاقة
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left; // المسافة من اليسار
      const y = e.clientY - rect.top; // المسافة من الأعلى
      
      // حساب موقع المؤشر كنسبة مئوية
      const xPercent = x / rect.width;
      const yPercent = y / rect.height;
      
      // حساب الميل استنادًا إلى موقع المؤشر
      const rotateX = (0.5 - yPercent) * 10; // ميل أفقي (حول المحور X)
      const rotateY = (xPercent - 0.5) * 10; // ميل عمودي (حول المحور Y)
      
      // تطبيق التحويل
      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
      
      // تعديل موقع الإضاءة
      const glow = card.querySelector('.hover-glow');
      if (glow) {
        glow.style.background = `radial-gradient(circle at ${xPercent * 100}% ${yPercent * 100}%, rgba(255,255,255,0.2), transparent)`;
      }
    });
    
    // إعادة تعيين التحويل عند مغادرة المؤشر
    card.addEventListener('mouseleave', () => {
      card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0)';
      
      const glow = card.querySelector('.hover-glow');
      if (glow) {
        glow.style.background = 'transparent';
      }
    });
  });
  
  // تأثير التكبير السلس لعناصر المشاريع
  const portfolioItems = document.querySelectorAll('.portfolio-item');
  portfolioItems.forEach(item => {
    item.addEventListener('mouseenter', function() {
      this.classList.add('hover-zoom');
    });
    
    item.addEventListener('mouseleave', function() {
      this.classList.remove('hover-zoom');
    });
  });
}

/**
 * تحديث تأثيرات الظهور عند التمرير بعد تحميل محتوى جديد
 */
function refreshScrollEffects() {
  // تحديث تأثيرات AOS
  if (typeof AOS !== 'undefined') {
    AOS.refresh();
  }
  
  // إعادة تهيئة تأثير hover
  initHoverEffects();
  
  // إعادة تعيين العناصر المتدرجة مع تأخير أطول للعناصر الجديدة
  const newStaggeredElements = document.querySelectorAll('.staggered-item:not(.fade-in)');
  newStaggeredElements.forEach((el, index) => {
    el.style.transitionDelay = `${index * 0.2}s`; // زيادة التأخير بشكل أكبر للعناصر الجديدة
    setTimeout(() => {
      el.classList.add('fade-in');
    }, 200); // تأخير أكبر للعناصر المضافة حديثاً
  });
  
  console.log('تم تحديث تأثيرات الظهور');
}

// تصدير الدوال للاستخدام الخارجي
window.SmoothEffects = {
  refresh: refreshScrollEffects,
  initHoverEffects: initHoverEffects,
  initScrollReveal: initScrollReveal
};