/**
 * حل موحد للتعامل مع أزرار الحذف والتعديل في لوحة الإدارة
 * هذا الملف يجمع كل الحلول لمشاكل الأزرار والنوافذ المنبثقة
 */

document.addEventListener('DOMContentLoaded', function() {
  console.log('تهيئة نظام إجراءات لوحة الإدارة الموحد...');
  
  // تهيئة أزرار الحذف المباشر
  initializeAllDeleteButtons();
  
  // إصلاح مشكلة النوافذ المنبثقة
  fixModalBackdropIssue();
  
  // تهيئة تحميل الأنيميشن
  setupLoadingAnimations();
  
  console.log('تم تهيئة نظام الإجراءات بنجاح');
});

/**
 * تهيئة كل أزرار الحذف
 */
function initializeAllDeleteButtons() {
  // قائمة الأزرار المستهدفة بحسب أنواعها
  const buttonSelectors = [
    '.delete-portfolio-item',
    '.delete-carousel-item',
    '.delete-service',
    '.delete-testimonial',
    '.delete-comment-item',
    '.delete-social-media',
    '.delete-message-item',
    '.delete-service-request',
    '[data-action="delete"]',
    '[data-delete-url]'
  ];
  
  // تجميع كل الأزرار
  const allButtons = document.querySelectorAll(buttonSelectors.join(', '));
  
  if (allButtons.length === 0) {
    return;
  }
  
  // إعادة تعريف كل الأزرار
  allButtons.forEach(button => {
    // إزالة أي معالجات أحداث سابقة
    const newButton = button.cloneNode(true);
    button.parentNode.replaceChild(newButton, button);
    
    // إضافة معالج أحداث جديد
    newButton.addEventListener('click', function(event) {
      event.preventDefault();
      
      // استخراج المعلومات من زر الحذف
      const itemId = this.getAttribute('data-id') || this.getAttribute('data-item-id');
      const itemTitle = this.getAttribute('data-title') || this.getAttribute('data-name') || 'هذا العنصر';
      const confirmMessage = this.getAttribute('data-confirm-message') || 
                              `هل أنت متأكد من أنك تريد حذف "${itemTitle}"؟\nهذا الإجراء لا يمكن التراجع عنه.`;
      
      // تحديد عنوان URL للحذف
      let deleteUrl = this.getAttribute('data-delete-url') || this.getAttribute('href');
      
      // بناء العنوان من النوع والمعرف إذا لم يكن محدداً مسبقاً
      if (!deleteUrl && itemId) {
        const type = this.getAttribute('data-type') || 
                     this.className.replace(/.*delete-([a-z-]+).*/, '$1').replace('-item', '');
        
        if (type) {
          // تحديد المسار المناسب بناءً على نوع الكائن
          if (type === 'messages') {
            deleteUrl = `/messaging/message/${itemId}/delete`;
          } else if (type === 'service-requests') {
            deleteUrl = `/messaging/request/${itemId}/delete`;
          } else if (type === 'comments') {
            deleteUrl = `/admin/comments/${itemId}/delete`;
          } else if (type === 'testimonials') {
            deleteUrl = `/admin/testimonials/${itemId}/delete`;
          } else if (type === 'carousel') {
            deleteUrl = `/admin/homepage-carousel/${itemId}/delete`;
          } else {
            // المسار الافتراضي
            deleteUrl = `/admin/${type}/${itemId}/delete`;
          }
        }
      }
      
      // التحقق من وجود العنوان
      if (!deleteUrl) {
        console.error('لم يتم العثور على عنوان URL للحذف:');
        console.error('- المعرف: ' + itemId);
        console.error('- العنوان: ' + itemTitle);
        console.error('- الفئة: ' + this.className);
        return;
      }
      
      // استخدام تأكيد المتصفح المدمج
      if (confirm(confirmMessage)) {
        // تحديد طريقة الإرسال
        const method = this.getAttribute('data-method') || 'POST';
        
        if (method.toUpperCase() === 'GET') {
          // الانتقال مباشرة للعنوان
          window.location.href = deleteUrl;
        } else {
          // إنشاء نموذج مؤقت للإرسال
          const form = document.createElement('form');
          form.method = method;
          form.action = deleteUrl;
          form.style.display = 'none';
          
          // إضافة رمز CSRF
          const csrfTokens = document.querySelectorAll('input[name="csrf_token"]');
          if (csrfTokens.length > 0) {
            const csrf = document.createElement('input');
            csrf.type = 'hidden';
            csrf.name = 'csrf_token';
            csrf.value = csrfTokens[0].value;
            form.appendChild(csrf);
          }
          
          // إضافة النموذج للصفحة وإرساله
          document.body.appendChild(form);
          
          // إظهار أنيميشن التحميل
          if (window.loadingAnimation) {
            window.loadingAnimation.show();
          }
          
          form.submit();
        }
      }
    });
  });
  
  console.log(`تمت تهيئة ${allButtons.length} زر حذف مباشر`);
}

/**
 * إصلاح مشكلة النوافذ المنبثقة
 */
function fixModalBackdropIssue() {
  // تعطيل النوافذ المنبثقة القديمة
  disableExistingModals();
  
  // إزالة الطبقات الشفافة المتبقية
  removeExistingBackdrops();
  
  // تجاوز وظائف Bootstrap modal
  overrideBootstrapModal();
}

/**
 * تعطيل النوافذ المنبثقة القديمة
 */
function disableExistingModals() {
  // إزالة جميع المودالات المفتوحة
  document.querySelectorAll('.modal.show').forEach(modal => {
    modal.style.display = 'none';
    modal.classList.remove('show');
  });
  
  // إزالة فئات إظهار المودال من الجسم
  document.body.classList.remove('modal-open');
}

/**
 * إزالة جميع الطبقات الشفافة المتبقية
 */
function removeExistingBackdrops() {
  document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
}

/**
 * تجاوز وظائف Bootstrap modal
 */
function overrideBootstrapModal() {
  if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
    // حفظ الدالة الأصلية
    const originalModalShow = bootstrap.Modal.prototype.show;
    
    // استبدال الدالة
    bootstrap.Modal.prototype.show = function() {
      // تنظيف أي بقايا من المودالات السابقة
      removeExistingBackdrops();
      
      // استدعاء الدالة الأصلية
      originalModalShow.apply(this, arguments);
      
      // رفع مستوى z-index للمودال الجديد
      const modalEl = this._element;
      if (modalEl) {
        modalEl.style.zIndex = '1050';
      }
    };
  }
}

/**
 * تهيئة أنيميشن التحميل
 */
function setupLoadingAnimations() {
  // تطبيق أنيميشن التحميل على النماذج
  document.querySelectorAll('form[data-loading-animation="true"]').forEach(form => {
    form.addEventListener('submit', function() {
      if (window.loadingAnimation) {
        window.loadingAnimation.show();
      }
    });
  });
  
  // تطبيق أنيميشن التحميل على الروابط
  document.querySelectorAll('a[data-loading-animation="true"]').forEach(link => {
    link.addEventListener('click', function(e) {
      // تجاهل الروابط التي تفتح في نافذة جديدة
      if (this.target === '_blank') return;
      
      if (window.loadingAnimation) {
        window.loadingAnimation.show();
      }
    });
  });
}