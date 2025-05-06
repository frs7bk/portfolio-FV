/**
 * إضافة البرمجيات النصية ديناميكياً
 */
document.addEventListener('DOMContentLoaded', function() {
  // التحقق من عدم وجود البرمجية النصية مسبقاً
  if (!document.querySelector('script[src*="portfolio-modal-direct-fix.js"]')) {
    // إنشاء عنصر البرمجية النصية
    var script = document.createElement('script');
    script.src = '/static/js/portfolio-modal-direct-fix.js?v=' + Math.floor(Math.random() * 9000 + 1000);
    
    // إضافة البرمجية النصية إلى الصفحة
    document.body.appendChild(script);
    console.log('تم إضافة البرمجية النصية لإصلاح النوافذ المنبثقة');
  }
});