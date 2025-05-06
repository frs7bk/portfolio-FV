/**
 * سكريبت عام يعمل على تحميل سكريبت إصلاح النوافذ المنبثقة في معرض الأعمال
 * هذا السكريبت سيتم تحميله في جميع الصفحات عبر وسم سكريبت مباشر في الصفحة
 */

// تحميل سكريبت إصلاح النوافذ المنبثقة
(function() {
    // التحقق مما إذا كنا في صفحة المعرض أولا
    if (window.location.pathname.includes('/instagram') || 
        window.location.pathname.includes('/portfolio')) {
        
        console.log("تحميل إصلاح النوافذ المنبثقة في معرض الأعمال");
        
        // إنشاء وسم سكريبت جديد
        const script = document.createElement('script');
        script.src = '/static/js/portfolio-modal-fix.js';
        script.defer = true;
        
        // إضافة السكريبت إلى الصفحة
        document.head.appendChild(script);
    }
})();