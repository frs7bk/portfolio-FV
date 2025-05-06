/**
 * إصلاح مباشر للنوافذ المنبثقة في معرض الأعمال
 * ملف بسيط يُضاف مباشرة إلى صفحة المعرض
 */

// التأكد من عدم تحميل الملف مرتين
if (typeof window.portfolioModalDirectFixLoaded === 'undefined') {
  window.portfolioModalDirectFixLoaded = true;
  
  console.log('تهيئة الإصلاح المباشر للنوافذ المنبثقة');
  
  // تنفيذ كود الإصلاح عند اكتمال تحميل الصفحة
  document.addEventListener('DOMContentLoaded', function() {
    // إضافة مستمعات الأحداث لعناصر المعرض
    fixPortfolioItemsClickEvent();
  });
  
  // إصلاح أحداث النقر على عناصر المعرض
  function fixPortfolioItemsClickEvent() {
    // الحصول على جميع عناصر المعرض
    const portfolioItems = document.querySelectorAll('.portfolio-item');
    console.log('عدد عناصر المعرض:', portfolioItems.length);
    
    // إضافة مستمع حدث النقر لكل عنصر
    portfolioItems.forEach(function(item) {
      // الحصول على معرف المشروع
      const itemId = item.getAttribute('data-id');
      if (!itemId) return;
      
      // استبدال العنصر لإزالة أي مستمعات أحداث موجودة
      const newItem = item.cloneNode(true);
      item.parentNode.replaceChild(newItem, item);
      
      // إضافة مستمع حدث النقر الجديد
      newItem.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('تم النقر على المشروع رقم:', itemId);
        
        // استدعاء وظيفة عرض النافذة المنبثقة
        fetch(`/portfolio/${itemId}/detail`)
          .then(response => response.json())
          .then(data => {
            // إنشاء النافذة المنبثقة إذا لم تكن موجودة
            ensureModalExists();
            
            // عرض البيانات
            showPortfolioModal(data);
            
            // تسجيل المشاهدة
            recordViewCount(itemId);
          })
          .catch(error => {
            console.error('خطأ في جلب بيانات المشروع:', error);
          });
      });
    });
    
    console.log('تم إصلاح أحداث النقر لعناصر المعرض');
  }
  
  // التأكد من وجود النافذة المنبثقة
  function ensureModalExists() {
    if (document.getElementById('portfolio-modal')) {
      return; // النافذة المنبثقة موجودة بالفعل
    }
    
    console.log('إنشاء النافذة المنبثقة');
    
    // إنشاء النافذة المنبثقة
    const modalHTML = `
      <div id="portfolio-modal" class="portfolio-modal">
        <button id="close-modal" class="close-modal">&times;</button>
        
        <div class="modal-container animate__animated animate__zoomIn animate__faster">
          <div class="modal-image">
            <img id="modal-image" src="" alt="صورة المشروع">
          </div>
          
          <div class="modal-content">
            <div class="modal-header">
              <img src="/static/uploads/profile.png" alt="صورة الملف الشخصي">
              <h4>فيراس ديزاين</h4>
            </div>
            
            <div class="modal-details">
              <h3 id="modal-title"></h3>
              <span id="modal-category" class="modal-category"></span>
              <div id="modal-description"></div>
              <div id="modal-link-container" style="display: none;">
                <a id="modal-link" href="#" target="_blank" class="btn btn-primary mt-2">زيارة المشروع</a>
              </div>
            </div>
            
            <div class="modal-actions">
              <button id="like-button" data-id="" type="button">
                <i class="far fa-heart"></i>
              </button>
            </div>
            
            <div class="modal-stats">
              <p id="modal-likes">0 إعجاب</p>
              <p id="modal-views">0 مشاهدة</p>
            </div>
          </div>
        </div>
      </div>
    `;
    
    // إضافة النافذة المنبثقة إلى نهاية الصفحة
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // إضافة مستمعات الأحداث للنافذة المنبثقة
    
    // إغلاق النافذة المنبثقة
    document.getElementById('close-modal').addEventListener('click', function() {
      document.getElementById('portfolio-modal').style.display = 'none';
      document.body.style.overflow = '';
    });
    
    // النقر خارج النافذة المنبثقة لإغلاقها
    document.getElementById('portfolio-modal').addEventListener('click', function(e) {
      if (e.target === this) {
        this.style.display = 'none';
        document.body.style.overflow = '';
      }
    });
    
    // تبديل حالة الإعجاب
    document.getElementById('like-button').addEventListener('click', function() {
      const itemId = this.getAttribute('data-id');
      if (!itemId) return;
      
      toggleLike(itemId);
    });
    
    console.log('تم إنشاء النافذة المنبثقة بنجاح');
  }
  
  // عرض النافذة المنبثقة مع البيانات
  function showPortfolioModal(data) {
    console.log('عرض بيانات المشروع في النافذة المنبثقة:', data);
    
    // تعيين البيانات
    document.getElementById('modal-image').src = data.image_url;
    document.getElementById('modal-title').textContent = data.title;
    document.getElementById('modal-category').textContent = data.category;
    document.getElementById('modal-description').innerHTML = data.description;
    
    // تعيين معرف المشروع لزر الإعجاب
    document.getElementById('like-button').setAttribute('data-id', data.id);
    
    // تعيين حالة الإعجاب
    const likeButton = document.getElementById('like-button');
    if (data.user_liked) {
      likeButton.querySelector('i').className = 'fas fa-heart';
      likeButton.querySelector('i').style.color = '#ef4444';
    } else {
      likeButton.querySelector('i').className = 'far fa-heart';
      likeButton.querySelector('i').style.color = '';
    }
    
    // تعيين عدد الإعجابات والمشاهدات
    document.getElementById('modal-likes').textContent = `${data.likes_count || 0} إعجاب`;
    document.getElementById('modal-views').textContent = `${data.views_count || 0} مشاهدة`;
    
    // تعيين رابط المشروع إذا كان موجودًا
    const linkContainer = document.getElementById('modal-link-container');
    if (data.link) {
      linkContainer.style.display = 'block';
      document.getElementById('modal-link').href = data.link;
    } else {
      linkContainer.style.display = 'none';
    }
    
    // عرض النافذة المنبثقة
    const modal = document.getElementById('portfolio-modal');
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    
    console.log('تم عرض النافذة المنبثقة بنجاح');
  }
  
  // تسجيل مشاهدة للمشروع
  function recordViewCount(itemId) {
    console.log('تسجيل مشاهدة للمشروع رقم:', itemId);
    
    fetch(`/portfolio/${itemId}/view`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    .then(response => response.json())
    .then(data => {
      console.log('تم تسجيل المشاهدة بنجاح:', data);
      
      // تحديث عداد المشاهدات في النافذة المنبثقة
      document.getElementById('modal-views').textContent = `${data.views_count || 0} مشاهدة`;
    })
    .catch(error => {
      console.error('خطأ في تسجيل المشاهدة:', error);
    });
  }
  
  // تبديل حالة الإعجاب بالمشروع
  function toggleLike(itemId) {
    console.log('تبديل حالة الإعجاب للمشروع رقم:', itemId);
    
    fetch(`/portfolio/${itemId}/like`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    .then(response => response.json())
    .then(data => {
      console.log('تم تبديل حالة الإعجاب بنجاح:', data);
      
      // تحديث زر الإعجاب
      const likeButton = document.getElementById('like-button');
      const icon = likeButton.querySelector('i');
      
      if (data.liked) {
        icon.className = 'fas fa-heart';
        icon.style.color = '#ef4444';
        icon.classList.add('heart-anim');
        setTimeout(() => icon.classList.remove('heart-anim'), 600);
      } else {
        icon.className = 'far fa-heart';
        icon.style.color = '';
      }
      
      // تحديث عداد الإعجابات في النافذة المنبثقة
      document.getElementById('modal-likes').textContent = `${data.likes_count || 0} إعجاب`;
      
      // تحديث عداد الإعجابات في الصفحة
      const portfolioItem = document.querySelector(`.portfolio-item[data-id="${itemId}"]`);
      if (portfolioItem) {
        const likesCounter = portfolioItem.querySelector('.fa-heart + span');
        if (likesCounter) {
          likesCounter.textContent = data.likes_count || 0;
        }
      }
    })
    .catch(error => {
      console.error('خطأ في تبديل حالة الإعجاب:', error);
    });
  }
}