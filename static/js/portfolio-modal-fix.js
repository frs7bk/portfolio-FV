/**
 * إصلاح النوافذ المنبثقة لمعرض الأعمال
 * هذا الملف يعيد تعريف وظائف التفاعل مع النوافذ المنبثقة بحيث تتوافق مع المسارات الحالية
 */

// إعلان عالمي للمسارات المتاحة
const API_PATHS = {
    DETAILS: ['/portfolio/:id/detail', '/instagram/api/portfolio/:id/details'],
    VIEW: ['/portfolio/:id/view', '/instagram/api/portfolio/:id/view'],
    LIKE: ['/portfolio/:id/like', '/instagram/api/portfolio/:id/like']
};

// تسجيل بداية تحميل الملف
console.log("جاري تهيئة إصلاح النوافذ المنبثقة للمشاريع...");

// الوظيفة الرئيسية لفتح النافذة المنبثقة
function openPortfolioModal(itemId) {
    console.log("فتح النافذة المنبثقة للمشروع رقم:", itemId);
    
    // استخدام المسار الرئيسي أولاً (المسار القديم)
    let apiUrl = `/portfolio/${itemId}/detail`;
    
    // محاولة فتح التفاصيل
    fetch(apiUrl)
        .then(response => {
            if (!response.ok && response.status === 404) {
                // إذا لم يتم العثور على المسار القديم، جرب المسار الجديد
                return fetch(`/instagram/api/portfolio/${itemId}/details`);
            }
            return response;
        })
        .then(response => response.json())
        .then(data => {
            // فتح النافذة المنبثقة وتعبئة البيانات
            updateModalContent(data);
            recordView(itemId);
        })
        .catch(error => {
            console.error('خطأ في تحميل تفاصيل المشروع:', error);
        });
}

// تحديث محتوى النافذة المنبثقة
function updateModalContent(data) {
    // التعامل مع الاستجابة حسب التنسيق
    let item = data.item || data;
    
    // فتح النافذة المنبثقة
    let modal = document.getElementById('portfolio-modal');
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        
        // تعيين البيانات
        let modalImage = document.getElementById('modal-image');
        if (modalImage) modalImage.src = item.image_url;
        
        let modalTitle = document.getElementById('modal-title');
        if (modalTitle) modalTitle.textContent = item.title;
        
        let modalCategory = document.getElementById('modal-category');
        if (modalCategory) modalCategory.textContent = item.category;
        
        let modalDescription = document.getElementById('modal-description');
        if (modalDescription) modalDescription.innerHTML = item.description;
        
        // تعيين أزرار التفاعل
        let likeButton = document.getElementById('like-button');
        if (likeButton) {
            likeButton.dataset.id = item.id;
            likeButton.classList.toggle('liked', item.user_liked);
        }
    }
}

// تسجيل مشاهدة المشروع
function recordView(itemId) {
    // إعادة توجيه مسار API لتوافق إما المسار الجديد أو القديم
    let apiUrl = `/instagram/api/portfolio/${itemId}/view`;
    
    // محاولة تسجيل المشاهدة باستخدام المسار الجديد
    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok && response.status === 404) {
            // إذا لم يتم العثور على المسار الجديد، جرب المسار القديم
            return fetch(`/portfolio/${itemId}/view`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
        }
        return response;
    })
    .then(response => response.json())
    .then(data => {
        console.log('تم تسجيل المشاهدة بنجاح');
        
        // تحديث عداد المشاهدات في الصفحة إذا كان موجودًا
        let viewsCounter = document.querySelector(`[data-views-id="${itemId}"]`);
        if (viewsCounter && data.views_count) {
            viewsCounter.textContent = data.views_count;
        }
    })
    .catch(error => {
        console.error('خطأ في تسجيل المشاهدة:', error);
    });
}

// تبديل حالة الإعجاب
function toggleLike(itemId) {
    // إعادة توجيه مسار API لتوافق إما المسار الجديد أو القديم
    let apiUrl = `/instagram/api/portfolio/${itemId}/like`;
    
    // محاولة تبديل الإعجاب باستخدام المسار الجديد
    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok && response.status === 404) {
            // إذا لم يتم العثور على المسار الجديد، جرب المسار القديم
            return fetch(`/portfolio/${itemId}/like`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
        }
        return response;
    })
    .then(response => response.json())
    .then(data => {
        console.log('تم تبديل حالة الإعجاب بنجاح');
        
        // تحديث زر الإعجاب
        let likeButton = document.querySelector(`[data-like-id="${itemId}"]`);
        if (likeButton) {
            likeButton.classList.toggle('liked', data.liked);
        }
        
        // تحديث عداد الإعجابات في الصفحة
        let likesCounter = document.querySelector(`[data-likes-id="${itemId}"]`);
        if (likesCounter && data.likes_count !== undefined) {
            likesCounter.textContent = data.likes_count;
        }
    })
    .catch(error => {
        console.error('خطأ في تبديل حالة الإعجاب:', error);
    });
}

// إغلاق النافذة المنبثقة
function closeModal() {
    let modal = document.getElementById('portfolio-modal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// إضافة مستمعي الأحداث عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    // مستمع لإغلاق النافذة المنبثقة
    let closeButton = document.getElementById('close-modal');
    if (closeButton) {
        closeButton.addEventListener('click', closeModal);
    }
    
    // مستمع للنقر خارج النافذة المنبثقة
    window.addEventListener('click', function(event) {
        let modal = document.getElementById('portfolio-modal');
        if (modal && event.target === modal) {
            closeModal();
        }
    });
    
    // مستمع لأزرار الإعجاب
    document.querySelectorAll('[data-like-id]').forEach(button => {
        button.addEventListener('click', function() {
            toggleLike(this.dataset.likeId);
        });
    });
    
    // إعادة تعريف وظيفة فتح النافذة المنبثقة للصفحة بأكملها
    window.openPortfolioModal = openPortfolioModal;
    
    console.log('تم تهيئة إصلاح النوافذ المنبثقة لمعرض الأعمال');
});

// إصلاح الروابط الحالية في الصفحة
document.addEventListener('DOMContentLoaded', function() {
    // إصلاح روابط المشاريع
    document.querySelectorAll('[data-portfolio-id]').forEach(element => {
        element.addEventListener('click', function(event) {
            event.preventDefault();
            openPortfolioModal(this.dataset.portfolioId);
        });
    });
});
