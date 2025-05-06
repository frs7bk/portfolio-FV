/**
 * نظام كاروسيل لا نهائي مع تأثيرات انتقالية متقدمة - نسخة محسّنة ومصححة
 * Infinite Auto-Scrolling Carousel System - Enhanced & Fixed Version
 */

document.addEventListener('DOMContentLoaded', function() {
    // تأخير التنفيذ للتأكد من تحميل الصفحة بالكامل (تقليل وقت التأخير)
    setTimeout(initInfiniteCarousel, 300);
});

/**
 * تهيئة نظام الكاروسيل اللانهائي
 */
function initInfiniteCarousel() {
    const marqueeWrapper = document.getElementById('marqueeWrapper');
    if (!marqueeWrapper) return;
    
    // تعديل دور ووضع الحاوية
    marqueeWrapper.style.position = 'relative';
    marqueeWrapper.style.left = '0';
    
    // الحصول على جميع عناصر المشاريع الأصلية
    const originalItems = Array.from(marqueeWrapper.querySelectorAll('.marquee-item'));
    if (originalItems.length === 0) return;
    
    // متغيرات التحكم في سلوك الكاروسيل
    let autoScrollEnabled = true;     // تمكين التمرير التلقائي
    let isScrollPaused = false;       // هل التمرير متوقف مؤقتًا؟
    let isInteracting = false;        // هل المستخدم يتفاعل مع الكاروسيل؟
    let scrollSpeed = 1.2;            // سرعة التمرير الأساسية (زيادة من 0.8 إلى 1.2)
    let scrollPosition = 0;           // موقع التمرير الحالي
    let scrollAnimation = null;       // متغير تحكم في الحركة
    let totalWidth = 0;               // العرض الكلي لعناصر الكاروسيل الأصلية
    
    // حساب العرض الكلي للعناصر الأصلية
    function calculateTotalWidth() {
        totalWidth = 0;
        const uniqueItems = Array.from(marqueeWrapper.querySelectorAll('.marquee-item:not(.clone)'));
        uniqueItems.forEach(item => {
            totalWidth += item.offsetWidth;
        });
        return totalWidth;
    }
    
    // تشغيل تمرير الكاروسيل التلقائي
    function startAutoScroll() {
        if (!autoScrollEnabled) return;
        
        cancelAnimationFrame(scrollAnimation); // إلغاء أي حركة سابقة
        calculateTotalWidth(); // حساب العرض الكلي مرة واحدة
        
        function scroll() {
            if (isScrollPaused || isInteracting) {
                scrollAnimation = requestAnimationFrame(scroll);
                return;
            }
            
            scrollPosition -= scrollSpeed;
            marqueeWrapper.style.transform = `translateX(${scrollPosition}px)`;
            
            // إعادة ضبط الموقع عند وصول نهاية المعرض - هذا يجعل الكاروسيل لا نهائي بطريقة أفضل
            if (Math.abs(scrollPosition) >= totalWidth) {
                // بدلاً من نقل العناصر، نعيد موقع التمرير إلى البداية
                scrollPosition = 0;
                marqueeWrapper.style.transform = `translateX(${scrollPosition}px)`;
            }
            
            scrollAnimation = requestAnimationFrame(scroll);
        }
        
        scrollAnimation = requestAnimationFrame(scroll);
    }
    
    // إضافة مستمعات الأحداث للعنصر
    function addEventListenersToItem(item) {
        // تمرير المؤشر فوق العنصر
        item.addEventListener('mouseenter', function() {
            isInteracting = true; // تعيين حالة التفاعل
            
            this.style.transform = 'scale(1.05)';
            this.style.zIndex = '10';
            
            // إظهار معلومات المشروع
            const overlay = this.querySelector('.marquee-overlay');
            if (overlay) {
                overlay.style.opacity = '1';
            }
        });
        
        // مغادرة المؤشر للعنصر
        item.addEventListener('mouseleave', function() {
            // تأخير إعادة تعيين حالة التفاعل لمنع الحركة السريعة
            setTimeout(() => {
                isInteracting = false;
            }, 600); // تقليل وقت التأخير من 1000 إلى 600 مللي ثانية
            
            this.style.transform = 'scale(1)';
            this.style.zIndex = '1';
            
            // إخفاء معلومات المشروع
            const overlay = this.querySelector('.marquee-overlay');
            if (overlay) {
                overlay.style.opacity = '0';
            }
        });
        
        // النقر على العنصر
        item.addEventListener('click', function() {
            const portfolioId = this.getAttribute('data-id');
            if (portfolioId) {
                try {
                    // التحقق إذا كانت دالة viewPortfolio موجودة قبل الاستدعاء
                    if (typeof viewPortfolio === 'function') {
                        viewPortfolio(portfolioId);
                    } else {
                        console.log('Function viewPortfolio is not defined, continuing to navigate directly');
                    }
                } catch (e) {
                    console.log('Error viewing portfolio:', e);
                }
                window.location.href = `/portfolio/${portfolioId}`;
            }
        });
    }
    
    // إعادة ضبط وتحديث عناصر الكاروسيل
    function resetCarousel() {
        // إلغاء أي حركة حالية
        cancelAnimationFrame(scrollAnimation);
        
        // إعادة ضبط الموقع وأنماط الحاوية
        scrollPosition = 0;
        marqueeWrapper.style.transform = 'translateX(0)';
        
        // إضافة مستمعات الأحداث لجميع العناصر
        const allItems = marqueeWrapper.querySelectorAll('.marquee-item');
        allItems.forEach(item => {
            addEventListenersToItem(item);
        });
        
        // تطبيق مستمعات الأحداث الجديدة للإيقاف المؤقت فقط عند تمرير المؤشر على العناصر
        updateItemListeners();
        
        // حساب العرض الكلي للكاروسيل
        calculateTotalWidth();
        
        // بدء التمرير التلقائي من جديد
        startAutoScroll();
    }
    
    // إزالة تأثير تمرير المؤشر فوق الكاروسيل بأكمله
    // الآن سيتوقف الكاروسيل فقط عند تمرير المؤشر على أحد العناصر
    
    // تعديل مستمعات الأحداث للعناصر لإيقاف التمرير بشكل فردي
    function updateItemListeners() {
        const allItems = marqueeWrapper.querySelectorAll('.marquee-item');
        allItems.forEach(item => {
            // إيقاف التمرير عند تمرير المؤشر فوق العنصر
            item.addEventListener('mouseenter', function() {
                isScrollPaused = true;
            });
            
            // استئناف التمرير عند مغادرة المؤشر للعنصر
            item.addEventListener('mouseleave', function() {
                isScrollPaused = false;
            });
        });
    }
    
    // تطبيق مستمعات الأحداث الجديدة
    updateItemListeners();
    
    // إضافة class للتمييز بين العناصر الأصلية والمستنسخة
    originalItems.forEach(item => {
        item.classList.add('original');
    });
    
    // تهيئة الكاروسيل وبدء التمرير التلقائي
    resetCarousel();
    
    // تشغيل تصفية العناصر (إذا كانت موجودة)
    const filterButtons = document.querySelectorAll('.filter-btn');
    if (filterButtons.length > 0) {
        filterButtons.forEach(button => {
            button.addEventListener('click', function() {
                const filter = this.getAttribute('data-filter');
                
                // تحديث الفلاتر النشطة
                filterButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
                
                // إيقاف التمرير التلقائي مؤقتًا
                isScrollPaused = true;
                setTimeout(() => { isScrollPaused = false; }, 600); // تقليل وقت التأخير من 1000 إلى 600 مللي ثانية
                
                // تصفية العناصر
                const allItems = marqueeWrapper.querySelectorAll('.marquee-item');
                allItems.forEach(item => {
                    if (filter === 'all' || item.getAttribute('data-category') === filter) {
                        item.style.display = 'block';
                    } else {
                        item.style.display = 'none';
                    }
                });
            });
        });
    }
    
    // إعادة تهيئة الكاروسيل عند تغيير حجم النافذة
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(resetCarousel, 300);
    });
}

// تعريف WebKitCSSMatrix لمتصفحات قديمة
if (typeof WebKitCSSMatrix === 'undefined') {
    class WebKitCSSMatrix {
        constructor(transformString) {
            this.m41 = 0;
            if (transformString && transformString !== 'none') {
                const matrixMatch = transformString.match(/matrix.*\((.+)\)/);
                if (matrixMatch && matrixMatch[1]) {
                    const values = matrixMatch[1].split(',');
                    if (values.length >= 6) {
                        this.m41 = parseFloat(values[4]);
                    }
                }
            }
        }
    }
    window.WebKitCSSMatrix = WebKitCSSMatrix;
}