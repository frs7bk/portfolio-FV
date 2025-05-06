/**
 * ملف جافاسكريبت للنافذة المنبثقة بنمط إنستغرام
 */

// المتغيرات العامة
let currentPortfolioId = null;
let modalInitialized = false;

// تنفيذ بعد تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
  // إنشاء النافذة المنبثقة إذا لم تكن موجودة
  if (!document.getElementById('instagram-modal')) {
    initInstagramModal();
  }
  
  // إضافة مستمعات الأحداث لعناصر المعرض
  setupPortfolioItemEvents();
});

/**
 * إنشاء هيكل النافذة المنبثقة
 */
function initInstagramModal() {
  if (modalInitialized) return;
  
  // إنشاء عنصر النافذة المنبثقة
  const modal = document.createElement('div');
  modal.id = 'instagram-modal';
  
  // إضافة المحتوى الداخلي للنافذة
  modal.innerHTML = `
    <button id="instagram-modal-close">&times;</button>
    <div class="instagram-modal-container">
      <!-- صورة المشروع -->
      <div class="instagram-modal-image">
        <img id="modal-portfolio-image" src="" alt="صورة المشروع">
      </div>
      
      <!-- تفاصيل المشروع -->
      <div class="instagram-modal-details">
        <!-- رأس التفاصيل -->
        <div class="instagram-modal-header">
          <div class="modal-project-info">
            <div id="modal-project-title" class="modal-project-title"></div>
            <div id="modal-project-category" class="modal-project-category"></div>
          </div>
        </div>
        
        <!-- أزرار التفاعل -->
        <div class="instagram-modal-actions">
          <button id="modal-like-button" class="instagram-modal-action-button" title="أضف إعجاب">
            <i class="far fa-heart"></i> إعجاب
          </button>
          <button id="modal-share-button" class="instagram-modal-action-button" title="مشاركة الرابط">
            <i class="fas fa-share-alt"></i> مشاركة
          </button>
          <a id="modal-external-link" href="#" target="_blank" class="instagram-modal-action-button" title="فتح الرابط الخارجي">
            <i class="fas fa-external-link-alt"></i> عرض
          </a>
        </div>
        
        <!-- إحصائيات المشروع -->
        <div class="instagram-modal-stats">
          <div id="modal-views-count" class="instagram-modal-stat"><i class="fas fa-eye"></i> <span>0</span></div>
          <div id="modal-likes-count" class="instagram-modal-stat"><i class="fas fa-heart"></i> <span>0</span></div>
          <div id="modal-date" class="instagram-modal-stat"><i class="fas fa-calendar"></i> <span></span></div>
        </div>

        <!-- وصف المشروع -->
        <div class="instagram-modal-description">
          <h3>عن المشروع</h3>
          <div id="modal-project-description" class="modal-project-description"></div>
        </div>
      </div>
    </div>
  `;
  
  // إضافة النافذة للمستند
  document.body.appendChild(modal);
  
  // إضافة مستمعات الأحداث للنافذة
  setupModalEvents();
  
  modalInitialized = true;
}

/**
 * إضافة مستمعات الأحداث للنافذة المنبثقة
 */
function setupModalEvents() {
  // زر الإغلاق
  const closeButton = document.getElementById('instagram-modal-close');
  if (closeButton) {
    closeButton.addEventListener('click', closeModal);
  }
  
  // إغلاق النافذة عند النقر خارجها
  const modal = document.getElementById('instagram-modal');
  if (modal) {
    modal.addEventListener('click', function(e) {
      if (e.target === modal) {
        closeModal();
      }
    });
  }
  
  // زر الإعجاب
  const likeButton = document.getElementById('modal-like-button');
  if (likeButton) {
    likeButton.addEventListener('click', function() {
      toggleLike();
    });
  }
  
  // زر المشاركة
  const shareButton = document.getElementById('modal-share-button');
  if (shareButton) {
    shareButton.addEventListener('click', function(e) {
      e.preventDefault();
      // نسخ رابط المشروع إلى الحافظة
      const url = window.location.origin + '/portfolio/' + currentPortfolioId;
      navigator.clipboard.writeText(url).then(function() {
        // عرض رسالة نجاح النسخ
        showNotification('تم نسخ رابط المشروع بنجاح');
      }, function() {
        // في حالة حدوث خطأ
        showNotification('حدث خطأ أثناء نسخ الرابط', 'error');
      });
    });
  }
  
  // رابط فتح العرض الخارجي
  const externalLink = document.getElementById('modal-external-link');
  if (externalLink) {
    externalLink.addEventListener('click', function() {
      // الرابط معين في بيانات المشروع
      // يعمل النقر على فتح الرابط في نافذة جديدة
    });
  }
}

/**
 * إضافة مستمعات الأحداث لعناصر المعرض
 */
function setupPortfolioItemEvents() {
  // الحصول على جميع عناصر المعرض
  const portfolioItems = document.querySelectorAll('.portfolio-item');
  
  // إضافة مستمع لكل عنصر
  portfolioItems.forEach(item => {
    item.addEventListener('click', function(e) {
      e.preventDefault();
      const portfolioId = this.getAttribute('data-id');
      if (portfolioId) {
        openModal(portfolioId);
      }
    });
  });
}

/**
 * فتح النافذة المنبثقة وتحميل بيانات المشروع
 */
function openModal(portfolioId) {
  currentPortfolioId = portfolioId;
  
  // إظهار النافذة
  const modal = document.getElementById('instagram-modal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden'; // منع التمرير في الخلفية
  }
  
  // تحميل بيانات المشروع
  fetch(`/portfolio/${portfolioId}/details`)
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // تحديث بيانات النافذة
        document.getElementById('modal-portfolio-image').src = data.item.image_url;
        document.getElementById('modal-project-title').textContent = data.item.title;
        document.getElementById('modal-project-category').textContent = data.item.category || '';
        
        // تحديث الإحصائيات
        const viewsElement = document.querySelector('#modal-views-count span');
        const likesElement = document.querySelector('#modal-likes-count span');
        const dateElement = document.querySelector('#modal-date span');
        
        if (viewsElement) viewsElement.textContent = data.item.views_count || 0;
        if (likesElement) likesElement.textContent = data.item.likes_count || 0;
        if (dateElement) dateElement.textContent = data.item.created_at || '';
        
        // إضافة الوصف
        const descElement = document.getElementById('modal-project-description');
        if (descElement) descElement.innerHTML = data.item.description || '';
        
        // تحديث الرابط الخارجي إذا كان موجود
        const externalLink = document.getElementById('modal-external-link');
        if (externalLink && data.item.external_url) {
          externalLink.href = data.item.external_url;
        } else if (externalLink) {
          externalLink.style.display = 'none';
        }

        // تحديث حالة زر الإعجاب
        updateLikeButton(data.item.user_liked || false);
        
        // تسجيل مشاهدة
        recordView();
      }
    })
    .catch(error => {
      console.error('حدث خطأ في تحميل بيانات المشروع:', error);
    });
}

/**
 * إغلاق النافذة المنبثقة
 */
function closeModal() {
  const modal = document.getElementById('instagram-modal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = ''; // إعادة تمكين التمرير
  }
  currentPortfolioId = null;
}

/**
 * تسجيل مشاهدة للمشروع
 */
function recordView() {
  if (!currentPortfolioId) return;
  
  fetch(`/portfolio/${currentPortfolioId}/view`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // تحديث عداد المشاهدات
        const viewsElement = document.querySelector('#modal-views-count span');
        if (viewsElement) viewsElement.textContent = data.views_count || 0;
      }
    })
    .catch(error => {
      console.error('حدث خطأ في تسجيل المشاهدة:', error);
    });
}

/**
 * تبديل حالة الإعجاب
 */
function toggleLike() {
  if (!currentPortfolioId) return;
  
  // عرض مؤشر التحميل قبل إرسال الطلب
  const likeButton = document.getElementById('modal-like-button');
  if (likeButton) {
    const originalHTML = likeButton.innerHTML;
    likeButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    likeButton.disabled = true;
  }
  
  fetch(`/portfolio/${currentPortfolioId}/like`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // تحديث عدد الإعجابات
        const likesElement = document.querySelector('#modal-likes-count span');
        if (likesElement) likesElement.textContent = data.likes_count || 0;
        
        // تحديث حالة زر الإعجاب
        updateLikeButton(data.liked || false);
        
        // عرض رسالة إشعار للمستخدم
        if (data.liked) {
          // تم إضافة إعجاب وإرسال إشعار عبر تلغرام
          showNotification('تم إضافة إعجابك بنجاح ❤️ وتم إرسال إشعار');
        } else {
          showNotification('تم إزالة إعجابك');
        }
      } else {
        // في حالة الفشل
        showNotification('حدث خطأ أثناء تبديل حالة الإعجاب', 'error');
        // إعادة الزر لحالته الأصلية
        if (likeButton) {
          likeButton.disabled = false;
          updateLikeButton(false);
        }
      }
    })
    .catch(error => {
      console.error('حدث خطأ في تبديل حالة الإعجاب:', error);
      showNotification('حدث خطأ في الاتصال بالخادم', 'error');
      // إعادة الزر لحالته الأصلية
      if (likeButton) {
        likeButton.disabled = false;
        updateLikeButton(false);
      }
    });
}

/**
 * تحديث شكل زر الإعجاب
 */
function updateLikeButton(isLiked) {
  const likeButton = document.getElementById('modal-like-button');
  if (likeButton) {
    if (isLiked) {
      likeButton.innerHTML = '<i class="fas fa-heart" style="color: #e74c3c;"></i> إعجاب';
      likeButton.classList.add('liked');
    } else {
      likeButton.innerHTML = '<i class="far fa-heart"></i> إعجاب';
      likeButton.classList.remove('liked');
    }
  }
}

/**
 * عرض إشعار للمستخدم
 */
function showNotification(message, type = 'success') {
  // التحقق من وجود حاوية الإشعارات، وإنشاؤها إذا لم تكن موجودة
  let container = document.getElementById('notification-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'notification-container';
    container.style.position = 'fixed';
    container.style.top = '20px';
    container.style.right = '20px';
    container.style.zIndex = '10000';
    document.body.appendChild(container);
  }

  // إنشاء عنصر الإشعار
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.style.backgroundColor = type === 'success' ? 'rgba(79, 70, 229, 0.9)' : 'rgba(220, 38, 38, 0.9)';
  notification.style.color = 'white';
  notification.style.padding = '12px 20px';
  notification.style.borderRadius = '8px';
  notification.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
  notification.style.marginBottom = '10px';
  notification.style.minWidth = '250px';
  notification.style.backdropFilter = 'blur(8px)';
  notification.style.border = '1px solid ' + (type === 'success' ? 'rgba(99, 102, 241, 0.4)' : 'rgba(255, 99, 71, 0.4)');
  notification.style.transform = 'translateX(100%)';
  notification.style.opacity = '0';
  notification.style.transition = 'all 0.3s cubic-bezier(0.165, 0.84, 0.44, 1)';

  // إضافة الرمز والرسالة
  const icon = type === 'success' ? '<i class="fas fa-check-circle" style="margin-left: 10px;"></i>' : '<i class="fas fa-exclamation-circle" style="margin-left: 10px;"></i>';
  notification.innerHTML = `${icon} ${message}`;

  // إضافة الإشعار إلى الحاوية
  container.appendChild(notification);

  // ظهور الإشعار بتأثير حركي
  setTimeout(() => {
    notification.style.transform = 'translateX(0)';
    notification.style.opacity = '1';
  }, 50);

  // إخفاء الإشعار بعد فترة
  setTimeout(() => {
    notification.style.transform = 'translateX(100%)';
    notification.style.opacity = '0';
    
    // إزالة الإشعار من DOM بعد انتهاء التأثير
    setTimeout(() => {
      notification.remove();
    }, 300);
  }, 3000);
}

