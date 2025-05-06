/**
 * مدير النوافذ المنبثقة لمعرض الأعمال
 * ملف جديد يجمع كل الوظائف المتعلقة بالنوافذ المنبثقة في مكان واحد
 */

// التأكد من عدم تحميل الملف مرتين
if (typeof window.portfolioModalManagerLoaded === 'undefined') {
  window.portfolioModalManagerLoaded = true;
  
  // تنفيذ الكود عند اكتمال تحميل الصفحة
  document.addEventListener('DOMContentLoaded', function() {
    console.log('تهيئة مدير النوافذ المنبثقة لمعرض الأعمال');
    
    // التحقق من وجود النافذة المنبثقة وإضافتها إذا لم تكن موجودة
    if (!document.getElementById('portfolio-modal')) {
      console.log('إنشاء النافذة المنبثقة للمشاريع');
      
      // إنشاء النافذة المنبثقة
      const modalHTML = `
        <div id="portfolio-modal" class="portfolio-modal">
          <button id="close-modal" class="close-modal">&times;</button>
          
          <div class="modal-container">
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
                <div class="modal-meta">
                  <span id="modal-date"></span>
                </div>
              </div>
              
              <div class="modal-actions">
                <button id="like-button" type="button"><i class="far fa-heart"></i></button>
                <button type="button"><i class="far fa-share-square"></i></button>
              </div>
              
              <div class="modal-stats">
                <p id="modal-likes">0 إعجاب</p>
                <p id="modal-views">0 مشاهدة</p>
              </div>
              
              <input type="hidden" id="modal-item-id" value="">
            </div>
          </div>
        </div>
      `;
      
      // إضافة النافذة المنبثقة إلى نهاية الصفحة
      document.body.insertAdjacentHTML('beforeend', modalHTML);
      console.log('تم إضافة النافذة المنبثقة بنجاح');
    }
    
    // فتح النافذة المنبثقة
    window.openPortfolioModal = function(itemId) {
      console.log('فتح النافذة المنبثقة للمشروع رقم:', itemId);
      
      // تعيين معرف المشروع
      document.getElementById('modal-item-id').value = itemId;
      
      // الحصول على تفاصيل المشروع
      fetch(`/portfolio/${itemId}/detail`)
        .then(response => {
          if (!response.ok && response.status === 404) {
            // إذا لم يتم العثور على المسار القديم، جرب المسار الجديد
            return fetch(`/instagram/api/portfolio/${itemId}/details`);
          }
          return response;
        })
        .then(response => response.json())
        .then(data => {
          console.log('تم الحصول على تفاصيل المشروع:', data);
          
          // التعامل مع الاستجابة حسب التنسيق
          const item = data.item || data;
          
          // تعيين البيانات
          document.getElementById('modal-image').src = item.image_url;
          document.getElementById('modal-title').textContent = item.title;
          document.getElementById('modal-category').textContent = item.category;
          document.getElementById('modal-description').innerHTML = item.description;
          
          // رابط المشروع
          const linkContainer = document.getElementById('modal-link-container');
          if (item.link) {
            linkContainer.style.display = 'block';
            document.getElementById('modal-link').href = item.link;
          } else {
            linkContainer.style.display = 'none';
          }
          
          // زر الإعجاب
          const likeButton = document.getElementById('like-button');
          if (item.user_liked) {
            likeButton.classList.add('active');
            likeButton.querySelector('i').classList.remove('far');
            likeButton.querySelector('i').classList.add('fas');
            likeButton.querySelector('i').style.color = '#ef4444';
          } else {
            likeButton.classList.remove('active');
            likeButton.querySelector('i').classList.remove('fas');
            likeButton.querySelector('i').classList.add('far');
            likeButton.querySelector('i').style.color = '';
          }
          
          // الإحصائيات
          document.getElementById('modal-likes').textContent = `${item.likes_count || 0} إعجاب`;
          document.getElementById('modal-views').textContent = `${item.views_count || 0} مشاهدة`;
          
          // فتح النافذة المنبثقة
          const modal = document.getElementById('portfolio-modal');
          modal.style.display = 'block';
          document.body.style.overflow = 'hidden';
          
          // تسجيل المشاهدة
          recordView(itemId);
        })
        .catch(error => {
          console.error('خطأ في تحميل تفاصيل المشروع:', error);
        });
    };
    
    // تسجيل مشاهدة المشروع
    function recordView(itemId) {
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
        
        // تحديث عداد المشاهدات في الصفحة إذا كان موجوداً
        const viewsCounter = document.querySelector(`[data-views-id="${itemId}"]`);
        if (viewsCounter && data.views_count) {
          viewsCounter.textContent = data.views_count;
        }
      })
      .catch(error => {
        console.error('خطأ في تسجيل المشاهدة:', error);
      });
    }
    
    // تبديل حالة الإعجاب
    window.toggleLike = function(itemId) {
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
        if (data.liked) {
          likeButton.classList.add('active');
          likeButton.querySelector('i').classList.remove('far');
          likeButton.querySelector('i').classList.add('fas');
          likeButton.querySelector('i').style.color = '#ef4444';
        } else {
          likeButton.classList.remove('active');
          likeButton.querySelector('i').classList.remove('fas');
          likeButton.querySelector('i').classList.add('far');
          likeButton.querySelector('i').style.color = '';
        }
        
        // تحديث عداد الإعجابات في الصفحة
        document.getElementById('modal-likes').textContent = `${data.likes_count || 0} إعجاب`;
        
        // تحديث عداد الإعجابات في بطاقة المشروع إذا كانت موجودة
        const likesCounter = document.querySelector(`[data-likes-id="${itemId}"]`);
        if (likesCounter && data.likes_count !== undefined) {
          likesCounter.textContent = data.likes_count;
        }
      })
      .catch(error => {
        console.error('خطأ في تبديل حالة الإعجاب:', error);
      });
    };
    
    // إغلاق النافذة المنبثقة
    window.closePortfolioModal = function() {
      const modal = document.getElementById('portfolio-modal');
      if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
      }
    };
    
    // إضافة مستمعات الأحداث
    
    // مستمع لإغلاق النافذة المنبثقة
    document.getElementById('close-modal').addEventListener('click', closePortfolioModal);
    
    // مستمع للنقر خارج النافذة المنبثقة
    window.addEventListener('click', function(event) {
      const modal = document.getElementById('portfolio-modal');
      if (modal && event.target === modal) {
        closePortfolioModal();
      }
    });
    
    // مستمع لزر الإعجاب
    document.getElementById('like-button').addEventListener('click', function() {
      const itemId = document.getElementById('modal-item-id').value;
      if (itemId) {
        toggleLike(itemId);
      }
    });
    
    // إضافة مستمعات الأحداث لعناصر المشاريع
    document.querySelectorAll('.portfolio-item').forEach(item => {
      // الحصول على معرف المشروع
      const itemId = item.getAttribute('data-id');
      if (!itemId) return;
      
      // إضافة خاصية data-portfolio-id لتسهيل الوصول
      item.setAttribute('data-portfolio-id', itemId);
      
      // إضافة مستمع للنقر
      item.addEventListener('click', function(event) {
        event.preventDefault();
        openPortfolioModal(itemId);
      });
    });
    
    console.log('تم تهيئة مدير النوافذ المنبثقة بنجاح');
  });
}