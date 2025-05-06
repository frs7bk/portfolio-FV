/**
 * سكريبت لإزالة أي شاشات تحميل متبقية
 * تم إنشاؤه بناءً على طلب المستخدم
 */

document.addEventListener('DOMContentLoaded', function() {
  // إزالة أي عناصر تحميل متبقية
  const removeLoaders = () => {
    // شاشة التحميل الرئيسية
    const pageLoader = document.getElementById('pageLoader');
    if (pageLoader) {
      pageLoader.remove();
    }
    
    // أي عناصر أخرى بفئة loading
    document.querySelectorAll('.loading, .loading-overlay, .loader').forEach(loader => {
      loader.remove();
    });
    
    // إزالة أي عناصر غير مرئية بفئة تحتوي على loading
    document.querySelectorAll('[class*="loading"]').forEach(element => {
      if (element.style.display === 'none' || 
          element.classList.contains('hidden') || 
          element.style.visibility === 'hidden' ||
          element.style.opacity === '0') {
        element.remove();
      }
    });
    
    // إخفاء أي عناصر قد تظهر لاحقاً
    const hideLoaders = `
      .loading-overlay, .loading, .loader, [class*="loading"] {
        display: none !important;
        opacity: 0 !important;
        visibility: hidden !important;
      }
    `;
    
    // إضافة أنماط CSS لتعطيل أي تحميل في المستقبل
    const style = document.createElement('style');
    style.textContent = hideLoaders;
    document.head.appendChild(style);
    
    console.log('تم إزالة جميع عناصر التحميل بنجاح');
  };
  
  // تنفيذ الإزالة مرتين مع فاصل زمني
  removeLoaders();
  setTimeout(removeLoaders, 500);
});