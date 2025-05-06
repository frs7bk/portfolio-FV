/**
 * Instagram Reel-style Carousel with Swiper.js
 * 
 * Features:
 * - Auto-sliding between images every 4 seconds
 * - Pause on hover
 * - Smooth transitions with fade effect
 * - Interactive navigation (arrows and pagination)
 * - Mobile-responsive design
 * - Vertical (9:16) aspect ratio for Instagram Reel style
 */

document.addEventListener('DOMContentLoaded', function() {
  console.log('بدء تهيئة كاروسيل انستجرام المحسّن');
  
  // التأكد من تحميل مكتبة Swiper
  if (typeof Swiper === 'undefined') {
    console.error('⚠️ مكتبة Swiper غير موجودة');
    // إضافة مكتبة Swiper ديناميكياً إذا لم تكن موجودة
    const swiperScript = document.createElement('script');
    swiperScript.src = 'https://cdn.jsdelivr.net/npm/swiper@8/swiper-bundle.min.js';
    swiperScript.onload = () => {
      console.log('✅ تم تحميل مكتبة Swiper بنجاح');
      startCarouselProcess();
    };
    document.head.appendChild(swiperScript);
    
    // إضافة ملف CSS الخاص بالمكتبة
    const swiperCSS = document.createElement('link');
    swiperCSS.rel = 'stylesheet';
    swiperCSS.href = 'https://cdn.jsdelivr.net/npm/swiper@8/swiper-bundle.min.css';
    document.head.appendChild(swiperCSS);
  } else {
    console.log('✅ مكتبة Swiper موجودة بالفعل');
    startCarouselProcess();
  }
  
  function startCarouselProcess() {
    console.log('⏱️ بدء تهيئة الكاروسيل...');
    
    // إضافة مستمع أحداث للتأكد من تحميل كل الصور
    window.addEventListener('load', function() {
      console.log('✅ تم تحميل الصفحة بالكامل');
      
      // تأكد من وجود حاوية الكاروسيل
      const carouselContainer = document.querySelector('.instagram-carousel-container');
      if (carouselContainer) {
        console.log('✅ العثور على حاوية الكاروسيل');
      } else {
        console.warn('⚠️ لم يتم العثور على حاوية الكاروسيل');
      }
    });
    
    // إنشاء الكاروسيل بعد تأخير أطول للتأكد من تحميل الصور
    setTimeout(() => {
      // تهيئة الكاروسيل مباشرة
      initInstagramCarousel();
      console.log('🚀 تم تهيئة كاروسيل انستجرام المحسّن');
      
      // تفعيل تأثيرات إضافية
      enhanceCarouselEffects();
      
      // طباعة معلومات إضافية عن الصور للمساعدة في تشخيص المشكلات
      logCarouselImagesInfo();
    }, 1000); // زيادة المدة لضمان تحميل الصور
  }
  
  // دالة جديدة لطباعة معلومات عن صور الكاروسيل
  function logCarouselImagesInfo() {
    const allCarouselImages = document.querySelectorAll('.instagram-reel-slide img');
    console.log(`📊 إجمالي صور الكاروسيل: ${allCarouselImages.length}`);
    
    allCarouselImages.forEach((img, index) => {
      console.log(`صورة #${index + 1}:`, {
        src: img.src,
        width: img.width,
        height: img.height,
        complete: img.complete,
        naturalWidth: img.naturalWidth,
        naturalHeight: img.naturalHeight
      });
    });
  }
  
  // إضافة تأثيرات إضافية للكاروسيل
  function enhanceCarouselEffects() {
    // تأثير للصور الحالية للكاروسيل
    const slides = document.querySelectorAll('.instagram-reel-slide');
    slides.forEach((slide, index) => {
      slide.style.opacity = '0';
      setTimeout(() => {
        slide.style.opacity = '1';
        slide.style.transition = 'opacity 0.5s ease-in-out';
      }, 100 * index);
    });
    
    // تحسين تجربة التنقل بالأزرار
    const navButtons = document.querySelectorAll('.swiper-button-next, .swiper-button-prev');
    navButtons.forEach(button => {
      button.addEventListener('mouseover', () => {
        button.style.transform = 'scale(1.15)';
      });
      button.addEventListener('mouseout', () => {
        button.style.transform = 'scale(1)';
      });
    });
  }
});

/**
 * Initialize Instagram-style carousels using Swiper
 */
function initInstagramCarousel() {
  // التحقق من وجود الكاروسيل في الصفحة العربية
  const arabicContainer = document.querySelector('.instagram-swiper');
  // التحقق من وجود الكاروسيل في الصفحة الإنجليزية
  const englishContainer = document.querySelector('.instagram-swiper-en');
  
  // تحديد اللغة الحالية للصفحة
  let isEnglishPage = window.location.pathname.includes('/en/');
  console.log(`الصفحة الحالية: ${isEnglishPage ? 'إنجليزي' : 'عربي'}`);
  
  let arabicSwiper = null;
  let englishSwiper = null;
  
  // تهيئة الكاروسيل العربي
  if (arabicContainer) {
    console.log('تهيئة الكاروسيل العربي');
    arabicSwiper = initSwiperCarousel('.instagram-swiper', {
      direction: 'horizontal',
      rtl: true, // Right-to-left for Arabic
      slidesPerView: 1,
      spaceBetween: 20,
      centeredSlides: true,
      loop: true,
      effect: 'fade',
      fadeEffect: {
        crossFade: true
      },
      autoplay: {
        delay: 3500,
        disableOnInteraction: false,
        pauseOnMouseEnter: true
      }
    });
  }
  
  // تهيئة الكاروسيل الإنجليزي أو محاولة استخدام نفس الكاروسيل للنسختين
  if (englishContainer) {
    console.log('تهيئة الكاروسيل الإنجليزي');
    englishSwiper = initSwiperCarousel('.instagram-swiper-en', {
      direction: 'horizontal',
      rtl: false, // Left-to-right for English
      slidesPerView: 1,
      spaceBetween: 20,
      centeredSlides: true,
      loop: true,
      effect: 'fade',
      fadeEffect: {
        crossFade: true
      },
      autoplay: {
        delay: 3500,
        disableOnInteraction: false,
        pauseOnMouseEnter: true
      }
    });
  } else if (isEnglishPage && arabicContainer) {
    // للصفحة الإنجليزية، إذا لم يتم العثور على حاوية الكاروسيل الإنجليزي
    // نحاول استخدام الكاروسيل العربي بإعدادات اللغة الإنجليزية
    console.log('استخدام الكاروسيل العربي للصفحة الإنجليزية');
    englishSwiper = initSwiperCarousel('.instagram-swiper', {
      direction: 'horizontal',
      rtl: false, // Left-to-right for English
      slidesPerView: 1,
      autoplay: {
        delay: 3500
      }
    });
  }
  
  // تسجيل حالة التهيئة
  console.log('تم تهيئة كاروسيل انستجرام:', {
    عربي: !!arabicSwiper,
    إنجليزي: !!englishSwiper
  });
  
  // معالجة الأخطاء بعد التهيئة وتحديث الكاروسيل عند تغيير حجم الشاشة
  window.addEventListener('resize', function() {
    if (arabicSwiper) arabicSwiper.update();
    if (englishSwiper) englishSwiper.update();
  });
  
  // إضافة تأثيرات متقدمة للكاروسيل (مثل تعتيم الشرائح غير النشطة)
  if (arabicSwiper) {
    arabicSwiper.on('slideChange', function() {
      highlightActiveSlide(arabicSwiper);
    });
    // تطبيق التأثير عند التهيئة
    highlightActiveSlide(arabicSwiper);
  }
  
  if (englishSwiper) {
    englishSwiper.on('slideChange', function() {
      highlightActiveSlide(englishSwiper);
    });
    // تطبيق التأثير عند التهيئة
    highlightActiveSlide(englishSwiper);
  }
}

// دالة مساعدة لإبراز الشريحة النشطة وتعتيم الشرائح الأخرى
function highlightActiveSlide(swiper) {
  if (!swiper) return;
  
  const slides = swiper.slides;
  for (let i = 0; i < slides.length; i++) {
    const slide = slides[i];
    if (slide.classList.contains('swiper-slide-active')) {
      slide.style.opacity = '1';
      slide.style.transform = 'scale(1)';
    } else {
      slide.style.opacity = '0.6';
      slide.style.transform = 'scale(0.85)';
    }
  }
}

/**
 * تقوم هذه الدالة بمعالجة وإصلاح مسارات الصور للكاروسيل
 * يتم التأكد من أن جميع الصور موجودة وتعمل، مع محاولة إصلاح أي مسارات غير صحيحة
 */
function fixCarouselImagePaths() {
  // العثور على جميع صور الكاروسيل في الصفحة
  const allCarouselImages = document.querySelectorAll('.instagram-reel-slide img');
  console.log(`🔍 وجدت ${allCarouselImages.length} صورة في الكاروسيل`);
  
  // إذا لم تكن هناك صور، لا حاجة للاستمرار
  if (allCarouselImages.length === 0) {
    console.log('⚠️ لم يتم العثور على صور في الكاروسيل');
    return;
  }
  
  // معالجة كل صورة للتأكد من صحة مسارها
  allCarouselImages.forEach((img, index) => {
    // التحقق إذا كان المسار يحتوي على "/uploads/carousel/"
    if (!img.src.includes('/uploads/carousel/')) {
      console.log(`⚠️ مسار الصورة ${index + 1} ليس صحيحاً: ${img.src}`);
      
      // استخراج اسم الملف من المسار (آخر جزء بعد "/")
      const filename = img.src.split('/').pop();
      if (filename) {
        // بناء المسار الصحيح
        const correctPath = `/static/uploads/carousel/${filename}`;
        console.log(`🔧 تصحيح المسار إلى: ${correctPath}`);
        img.src = correctPath;
      }
    }
    
    // إضافة معالج أحداث لرصد حالة تحميل الصورة
    img.addEventListener('load', () => {
      console.log(`✅ تم تحميل الصورة ${index + 1} بنجاح: ${img.src}`);
      // إضافة تأثير ظهور الصورة بشكل تدريجي
      img.style.opacity = '0';
      setTimeout(() => {
        img.style.opacity = '1';
        img.style.transition = 'opacity 0.5s ease-in-out';
      }, 50 * index);
    });
    
    img.addEventListener('error', () => {
      console.error(`❌ فشل تحميل الصورة ${index + 1}: ${img.src}`);
      // محاولة أخرى لتحميل الصورة مع صيغة مختلفة
      const filename = img.src.split('/').pop();
      if (filename) {
        const extension = filename.split('.').pop().toLowerCase();
        let newFilename = filename;
        
        // محاولة تغيير صيغة الصورة إذا كانت غير معيارية
        if (!['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(extension)) {
          newFilename = filename.replace(/\.[^/.]+$/, "") + '.jpg';
          console.log(`🔄 محاولة تحميل الصورة بصيغة jpg: ${newFilename}`);
        }
        
        // استخدام المسار المطلق للصورة
        img.src = `/static/uploads/carousel/${newFilename}`;
      }
    });
  });
}

/**
 * Initialize a Swiper carousel with customized settings
 * 
 * @param {string} selector - CSS selector for the Swiper container
 * @param {Object} options - Additional Swiper options
 * @returns {Swiper|null} - Swiper instance or null if initialization failed
 */
function initSwiperCarousel(selector, options = {}) {
  const container = document.querySelector(selector);
  if (!container) {
    console.log(`Carousel container '${selector}' not found`);
    return null;
  }
  
  try {
    // Default settings for Instagram-style carousels
    const defaultSettings = {
      slidesPerView: 1,
      spaceBetween: 20,
      centeredSlides: true,
      loop: true,
      loopAdditionalSlides: 2,
      grabCursor: true,
      autoplay: {
        delay: 3500, // Auto-slide every 3.5 seconds
        disableOnInteraction: false, // Continue autoplay after user interaction
        pauseOnMouseEnter: true // Pause on hover
      },
      effect: 'fade', // Smooth fade transition between slides
      fadeEffect: {
        crossFade: true // Enable cross-fade effect
      },
      speed: 800, // Transition speed in milliseconds
      navigation: {
        nextEl: '.swiper-button-next',
        prevEl: '.swiper-button-prev'
      },
      pagination: {
        el: '.swiper-pagination',
        clickable: true,
        dynamicBullets: true
      },
      // Responsive breakpoints
      breakpoints: {
        // Mobile devices
        320: {
          slidesPerView: 1,
          spaceBetween: 10
        },
        // Tablets
        768: {
          slidesPerView: 1,
          spaceBetween: 15
        },
        // Desktop
        1024: {
          slidesPerView: 1,
          spaceBetween: 20
        }
      }
    };
    
    // Merge default settings with custom options
    const swiperSettings = { ...defaultSettings, ...options };
    
    // Initialize Swiper with merged settings
    const swiper = new Swiper(container, swiperSettings);
    
    // Add hover event listeners to pause/resume autoplay
    const swiperElement = container.closest('.instagram-carousel-container');
    if (swiperElement) {
      swiperElement.addEventListener('mouseenter', () => {
        swiper.autoplay.stop();
        // Add subtle indication that autoplay is paused
        swiperElement.style.boxShadow = '0 0 0 2px rgba(251, 191, 36, 0.5)';
      });
      
      swiperElement.addEventListener('mouseleave', () => {
        swiper.autoplay.start();
        // Remove pause indication
        swiperElement.style.boxShadow = '';
      });
    }
    
    // Return the Swiper instance
    return swiper;
  } catch (error) {
    console.error(`Error initializing Swiper carousel for '${selector}':`, error);
    return null;
  }
}

// إضافة أنماط للتحسين من تجربة المستخدم
(function() {
  // تحسين من تنسيق الصفحة - نتأكد من عدم وجود styleElement سابق
  const existingStyle = document.getElementById('instagram-carousel-styles');
  if (existingStyle) {
    existingStyle.remove();
  }
  
  const styleElement = document.createElement('style');
  styleElement.id = 'instagram-carousel-styles';
  styleElement.textContent = `
    /* Add transition to carousel container on hover */
    .instagram-carousel-container {
      transition: box-shadow 0.3s ease;
      overflow: visible;
      z-index: 1;
      margin: 2rem auto;
    }
    
    /* Custom animation for slide transition */
    .swiper-slide-active .instagram-reel-slide {
      animation: slideActiveAnim 0.5s ease-out;
    }
    
    /* تأثيرات احترافية للكاروسيل */
    .instagram-reel-slide {
      transition: all 0.4s cubic-bezier(0.25, 0.1, 0.25, 1);
      position: relative;
      overflow: hidden;
      max-width: 340px;
      margin: 0 auto;
      border-radius: 12px;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
      transform: translateZ(0); /* Force hardware acceleration */
    }
    
    .instagram-reel-slide::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: linear-gradient(to bottom, rgba(0,0,0,0) 70%, rgba(0,0,0,0.7) 100%);
      opacity: 0.7;
      z-index: 1;
      transition: opacity 0.4s ease;
    }
    
    .instagram-reel-slide:hover {
      transform: scale(1.03) translateY(-5px);
      box-shadow: 0 15px 30px rgba(0, 0, 0, 0.4);
    }
    
    .instagram-reel-slide:hover::before {
      opacity: 0.5;
    }
    
    .instagram-reel-slide img {
      transition: transform 0.8s ease;
    }
    
    .instagram-reel-slide:hover img {
      transform: scale(1.05);
    }
    
    /* تحريك الشرائح بتأثير جميل */
    @keyframes slideActiveAnim {
      0% { transform: scale(0.92); opacity: 0.6; filter: blur(3px); }
      30% { filter: blur(0); }
      100% { transform: scale(1); opacity: 1; }
    }
    
    /* Improve accessibility with focus styles */
    .swiper-button-next:focus,
    .swiper-button-prev:focus,
    .swiper-pagination-bullet:focus {
      outline: 2px solid rgba(251, 191, 36, 0.5);
    }
  `;
  document.head.appendChild(styleElement);
});