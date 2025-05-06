/**
 * ملف جافاسكريبت للنافذة المنبثقة بنمط إنستغرام
 * توفر واجهة مشابهة لإنستغرام لعرض تفاصيل المشروع بما في ذلك الصور والتعليقات والإعجابات
 */

// متغير لتخزين معرف المشروع الحالي
let currentPortfolioId = null;

// إعداد النافذة المنبثقة بعد تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
  console.log('تهيئة النافذة المنبثقة بنمط إنستغرام...');
  
  // إنشاء عناصر النافذة المنبثقة إذا لم تكن موجودة
  createInstagramModal();
  
  // إضافة مستمعات الأحداث
  setupModalEvents();
  
  // إضافة مستمع الحدث لعناصر المعرض
  setupPortfolioItemEvents();
});

/**
 * إنشاء هيكل النافذة المنبثقة إذا لم يكن موجوداً
 */
function createInstagramModal() {
  // التحقق من وجود النافذة المنبثقة
  if (document.getElementById('instagram-modal')) {
    console.log('النافذة المنبثقة موجودة بالفعل');
    return;
  }

  console.log('إنشاء هيكل النافذة المنبثقة بنمط إنستغرام');
  
  // إنشاء النافذة المنبثقة
  const modal = document.createElement('div');
  modal.id = 'instagram-modal';
  modal.className = 'instagram-modal';
  
  // إنشاء محتوى النافذة المنبثقة
  modal.innerHTML = `
    <div class="instagram-modal-container">
      <button id="instagram-modal-close">×</button>
      
      <!-- قسم الصورة -->
      <div class="instagram-modal-image-container">
        <img id="modal-image" src="" alt="صورة المشروع">
      </div>
      
      <!-- قسم التفاصيل -->
      <div class="instagram-modal-details">
        <!-- رأس التفاصيل -->
        <div class="instagram-modal-header">
          <div>
            <div id="modal-project-title" class="modal-project-title"></div>
            <div id="modal-project-subtitle" class="modal-project-subtitle"></div>
          </div>
        </div>
        
        <!-- أزرار التفاعل -->
        <div class="instagram-modal-actions">
          <button id="like-button" class="modal-action-button">
            <i class="far fa-heart"></i> إعجاب
          </button>
          <button id="comment-button" class="modal-action-button">
            <i class="far fa-comment"></i> تعليق
          </button>
          <button id="share-button" class="modal-action-button">
            <i class="far fa-share-square"></i> مشاركة
          </button>
        </div>
        
        <!-- الإحصائيات -->
        <div class="instagram-modal-stats">
          <div id="modal-views" class="modal-stat-item">مشاهدة 0</div>
          <div id="modal-likes" class="modal-stat-item">إعجاب 0</div>
        </div>
        
        <!-- قسم التعليقات -->
        <div class="instagram-modal-comments">
          <div class="modal-comments-title">التعليقات</div>
          <div id="modal-comments-container">
            <div class="modal-comments-empty">فشل في تحصيل التعليقات</div>
          </div>
        </div>
        
        <!-- إضافة تعليق جديد -->
        <div class="instagram-modal-add-comment">
          <textarea id="modal-comment-input" class="modal-comment-input" placeholder="أضف تعليقاً..."></textarea>
          <button id="modal-comment-submit" class="modal-comment-submit">نشر</button>
        </div>
      </div>
    </div>
  `;
  
  // إضافة النافذة المنبثقة إلى المستند
  document.body.appendChild(modal);
  console.log('تم إنشاء النافذة المنبثقة بنجاح');
}

/**
 * إعداد مستمعات الأحداث للنافذة المنبثقة
 */
function setupModalEvents() {
  // زر الإغلاق
  const closeButton = document.getElementById('instagram-modal-close');
  if (closeButton) {
    closeButton.addEventListener('click', closeInstagramModal);
  }
  
  // النقر خارج المحتوى
  const modal = document.getElementById('instagram-modal');
  if (modal) {
    modal.addEventListener('click', function(e) {
      if (e.target === this) {
        closeInstagramModal();
      }
    });
  }
  
  // زر الإعجاب
  const likeButton = document.getElementById('like-button');
  if (likeButton) {
    likeButton.addEventListener('click', function() {
      if (currentPortfolioId) {
        toggleLike(currentPortfolioId);
      }
    });
  }
  
  // زر إضافة تعليق
  const commentSubmit = document.getElementById('modal-comment-submit');
  if (commentSubmit) {
    commentSubmit.addEventListener('click', function() {
      if (currentPortfolioId) {
        submitComment(currentPortfolioId);
      }
    });
  }
  
  // إضافة تعليق بالضغط على Enter
  const commentInput = document.getElementById('modal-comment-input');
  if (commentInput) {
    commentInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (currentPortfolioId) {
          submitComment(currentPortfolioId);
        }
      }
    });
  }
  
  console.log('تم إعداد أحداث النافذة المنبثقة');
}

/**
 * إعداد مستمعات أحداث عناصر المعرض
 */
function setupPortfolioItemEvents() {
  // الحصول على جميع عناصر المعرض
  const portfolioItems = document.querySelectorAll('.portfolio-item');
  
  console.log(`تم العثور على ${portfolioItems.length} عنصر معرض`);
  
  // إضافة مستمع الحدث لكل عنصر
  portfolioItems.forEach(function(item) {
    const itemId = item.getAttribute('data-id');
    if (itemId) {
      item.addEventListener('click', function(e) {
        // منع السلوك الافتراضي للروابط
        e.preventDefault();
        console.log(`تم النقر على عنصر المعرض بالمعرف ${itemId}`);
        openInstagramModal(itemId);
      });
    }
  });
}

/**
 * فتح النافذة المنبثقة وتحميل بيانات المشروع
 * @param {string} portfolioId - معرف المشروع
 */
function openInstagramModal(portfolioId) {
  console.log(`فتح النافذة المنبثقة للمشروع رقم ${portfolioId}`);
  
  // تخزين معرف المشروع الحالي
  currentPortfolioId = portfolioId;
  
  // عرض النافذة المنبثقة
  const modal = document.getElementById('instagram-modal');
  modal.style.display = 'flex';
  
  // منع التمرير في الصفحة الخلفية
  document.body.style.overflow = 'hidden';
  
  // تحميل بيانات المشروع
  fetch(`/portfolio/api/item/${portfolioId}`)
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // ملئ النافذة بالبيانات
        document.getElementById('modal-image').src = data.item.image_url;
        document.getElementById('modal-project-title').textContent = data.item.title;
        document.getElementById('modal-project-subtitle').textContent = data.item.id;
        document.getElementById('modal-views').textContent = `مشاهدة ${data.item.views || 0}`;
        document.getElementById('modal-likes').textContent = `إعجاب ${data.item.likes || 0}`;
        
        // تحديث زر الإعجاب
        updateLikeButton(data.item.user_liked || false);
        
        // تحميل التعليقات
        loadComments(portfolioId);
        
        // تسجيل المشاهدة
        recordView(portfolioId);
      } else {
        console.error('خطأ في تحميل بيانات المشروع:', data.message);
      }
    })
    .catch(error => {
      console.error('خطأ في طلب بيانات المشروع:', error);
    });
}

/**
 * إغلاق النافذة المنبثقة
 */
function closeInstagramModal() {
  console.log('إغلاق النافذة المنبثقة');
  
  // إخفاء النافذة المنبثقة
  const modal = document.getElementById('instagram-modal');
  modal.style.display = 'none';
  
  // إعادة تمكين التمرير
  document.body.style.overflow = '';
  
  // إعادة تعيين المشروع الحالي
  currentPortfolioId = null;
}

/**
 * تحميل التعليقات للمشروع
 * @param {string} portfolioId - معرف المشروع
 */
function loadComments(portfolioId) {
  console.log(`تحميل التعليقات للمشروع رقم ${portfolioId}`);
  
  const commentsContainer = document.getElementById('modal-comments-container');
  commentsContainer.innerHTML = '<div class="loading">\u062c\u0627\u0631\u064a \u062a\u062d\u0645\u064a\u0644 \u0627\u0644\u062a\u0639\u0644\u064a\u0642\u0627\u062a...</div>';
  
  fetch(`/comments/api/portfolio/${portfolioId}`)
    .then(response => response.json())
    .then(data => {
      if (data.success && data.comments) {
        if (data.comments.length > 0) {
          // بناء قائمة التعليقات
          let commentsHtml = '';
          data.comments.forEach(comment => {
            commentsHtml += `
              <div class="modal-comment">
                <strong>${comment.author || 'مستخدم'}</strong>: ${comment.content}
              </div>
            `;
          });
          commentsContainer.innerHTML = commentsHtml;
        } else {
          commentsContainer.innerHTML = '<div class="modal-comments-empty">\u0644\u0627 \u062a\u0648\u062c\u062f \u062a\u0639\u0644\u064a\u0642\u0627\u062a \u0628\u0639\u062f. \u0643\u0646 \u0623\u0648\u0644 \u0645\u0646 \u064a\u0639\u0644\u0642!</div>';
        }
      } else {
        commentsContainer.innerHTML = '<div class="modal-comments-empty">\u0641\u0634\u0644 \u0641\u064a \u062a\u062d\u0645\u064a\u0644 \u0627\u0644\u062a\u0639\u0644\u064a\u0642\u0627\u062a</div>';
      }
    })
    .catch(error => {
      console.error('خطأ في تحميل التعليقات:', error);
      commentsContainer.innerHTML = '<div class="modal-comments-empty">\u062d\u062f\u062b \u062e\u0637\u0623 \u0623\u062b\u0646\u0627\u0621 \u062a\u062d\u0645\u064a\u0644 \u0627\u0644\u062a\u0639\u0644\u064a\u0642\u0627\u062a</div>';
    });
}

/**
 * تسجيل مشاهدة للمشروع
 * @param {string} portfolioId - معرف المشروع
 */
function recordView(portfolioId) {
  console.log(`تسجيل مشاهدة للمشروع رقم ${portfolioId}`);
  
  fetch(`/portfolio/api/view/${portfolioId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest' // للتمييز بين الطلبات العادية والطلبات AJAX
    }
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // تحديث عداد المشاهدات
        document.getElementById('modal-views').textContent = `مشاهدة ${data.views || 0}`;
      }
    })
    .catch(error => {
      console.error('خطأ في تسجيل المشاهدة:', error);
    });
}

/**
 * تبديل حالة الإعجاب للمشروع
 * @param {string} portfolioId - معرف المشروع
 */
function toggleLike(portfolioId) {
  console.log(`تبديل حالة الإعجاب للمشروع رقم ${portfolioId}`);
  
  fetch(`/portfolio/api/like/${portfolioId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // تحديث عداد الإعجابات
        document.getElementById('modal-likes').textContent = `إعجاب ${data.likes || 0}`;
        
        // تحديث حالة زر الإعجاب
        updateLikeButton(data.user_liked || false);
      }
    })
    .catch(error => {
      console.error('خطأ في تبديل حالة الإعجاب:', error);
    });
}

/**
 * تحديث مظهر زر الإعجاب
 * @param {boolean} isLiked - هل أعجب المستخدم بالمشروع
 */
function updateLikeButton(isLiked) {
  const likeButton = document.getElementById('like-button');
  
  if (isLiked) {
    likeButton.innerHTML = '<i class="fas fa-heart" style="color: #e74c3c;"></i> إعجاب';
    likeButton.classList.add('liked');
  } else {
    likeButton.innerHTML = '<i class="far fa-heart"></i> إعجاب';
    likeButton.classList.remove('liked');
  }
}

/**
 * إرسال تعليق جديد
 * @param {string} portfolioId - معرف المشروع
 */
function submitComment(portfolioId) {
  const commentInput = document.getElementById('modal-comment-input');
  const commentText = commentInput.value.trim();
  
  if (!commentText) {
    return;
  }
  
  console.log(`إرسال تعليق جديد للمشروع ${portfolioId}: ${commentText}`);
  
  fetch(`/comments/api/add/${portfolioId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify({ content: commentText })
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // مسح حقل الإدخال
        commentInput.value = '';
        
        // إعادة تحميل التعليقات
        loadComments(portfolioId);
      } else {
        alert(رسالة خطأ: ${data.message || 'حدث خطأ أثناء إرسال التعليق'});
      }
    })
    .catch(error => {
      console.error('خطأ في إرسال التعليق:', error);
      alert('حدث خطأ أثناء إرسال التعليق. الرجاء المحاولة مرة أخرى لاحقاً.');
    });
}
