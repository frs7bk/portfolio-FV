/**
 * تم تعطيل أنيميشن التحميل بناءً على طلب المستخدم
 * الآن لا يوجد شاشة تحميل بين الصفحات كما في الصفحة الرئيسية
 */

// استبدال جميع شاشات التحميل بوظائف فارغة
document.addEventListener('DOMContentLoaded', function() {
  console.log("تم تعطيل جميع أنيميشنات التحميل");
  
  // إزالة السمات من النماذج
  document.querySelectorAll('form[data-loading-animation="true"]').forEach(form => {
    form.removeAttribute('data-loading-animation');
    form.removeAttribute('data-important-form');
  });
});

// إتاحة كائن فارغ ليتوافق مع الكود الموجود مسبقًا ولكن بدون أي وظائف تحميل
window.loadingAnimation = {
  show: function() {
    // لا شيء - تم تعطيل التحميل
    return;
  },
  hide: function() {
    // لا شيء - تم تعطيل التحميل
    return;
  }
};