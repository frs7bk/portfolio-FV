/**
 * نظام النافذة المنبثقة على طراز انستاغرام - نسخة مبسطة
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("تم تحميل ملف simple-instagram-modal.js");
    
    // 1. إنشاء عناصر النافذة المنبثقة
    createModal();
    
    // 2. إضافة معالجات الأحداث لعناصر المعرض
    setupGalleryItemEvents();
});

// إنشاء النافذة المنبثقة وإضافتها للصفحة
function createModal() {
    // التحقق من وجود النافذة المنبثقة
    if (document.getElementById('instagram-modal')) {
        return;
    }
    
    // إنشاء هيكل النافذة المنبثقة
    const modalHTML = `
    <div id="instagram-modal" class="instagram-modal">
        <button id="instagram-modal-close" class="instagram-modal-close">
            <i class="fas fa-times"></i>
        </button>
        
        <div class="instagram-modal-container">
            <!-- قسم الصورة (اليمين) -->
            <div class="instagram-modal-image">
                <img id="instagram-modal-main-image" src="" alt="صورة المشروع">
                
                <!-- أزرار التنقل بين الصور -->
                <button id="instagram-gallery-prev" class="instagram-gallery-nav instagram-gallery-prev">
                    <i class="fas fa-chevron-right"></i>
                </button>
                <button id="instagram-gallery-next" class="instagram-gallery-nav instagram-gallery-next">
                    <i class="fas fa-chevron-left"></i>
                </button>
            </div>
            
            <!-- قسم المحتوى (اليسار) -->
            <div class="instagram-modal-content">
                <!-- رأس النافذة -->
                <div class="instagram-modal-header">
                    <span id="instagram-modal-category" class="instagram-modal-category"></span>
                    <h3 id="instagram-modal-title"></h3>
                </div>
                
                <!-- تفاصيل المشروع -->
                <div class="instagram-modal-details">
                    <div id="instagram-modal-description"></div>
                    
                    <div id="instagram-modal-link-container" style="display: none;">
                        <a id="instagram-modal-link" href="#" target="_blank" class="btn-glow py-2 px-4 mt-3 inline-block rounded-lg">زيارة المشروع</a>
                    </div>
                    
                    <div class="instagram-modal-meta">
                        <span id="instagram-modal-date" class="instagram-modal-date"></span>
                    </div>
                </div>
                
                <!-- أزرار التفاعل -->
                <div class="instagram-modal-actions">
                    <button id="instagram-like-button" type="button">
                        <i class="far fa-heart"></i>
                    </button>
                    <button id="instagram-comment-button" type="button">
                        <i class="far fa-comment"></i>
                    </button>
                    <button id="instagram-share-button" type="button">
                        <i class="far fa-share-square"></i>
                    </button>
                </div>
                
                <!-- إحصائيات المشروع -->
                <div class="instagram-modal-stats">
                    <div id="instagram-modal-likes">0 إعجاب</div>
                    <div id="instagram-modal-views">0 مشاهدة</div>
                </div>
                
                <!-- قسم التعليقات -->
                <div class="instagram-modal-comments">
                    <div class="instagram-modal-comments-title">التعليقات</div>
                    <div id="instagram-comments-container">
                        <div class="no-comments-message">لا توجد تعليقات حتى الآن. كن أول من يعلق!</div>
                    </div>
                </div>
                
                <!-- حقل إضافة تعليق -->
                <div class="instagram-add-comment">
                    <input type="hidden" id="instagram-comment-project-id" value="">
                    <input type="text" id="instagram-comment-content" placeholder="أضف تعليقًا...">
                    <button id="instagram-comment-submit">نشر</button>
                </div>
            </div>
        </div>
    </div>
    `;
    
    // إضافة النافذة المنبثقة للصفحة
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // إضافة معالجات الأحداث للنافذة المنبثقة
    const modal = document.getElementById('instagram-modal');
    const closeButton = document.getElementById('instagram-modal-close');
    
    // إغلاق النافذة عند النقر على زر الإغلاق
    closeButton.addEventListener('click', function() {
        closeModal();
    });
    
    // إغلاق النافذة عند النقر خارج المحتوى
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });
    
    // الإعجاب بالمشروع
    document.getElementById('instagram-like-button').addEventListener('click', function() {
        const projectId = this.getAttribute('data-id');
        if (projectId) {
            likeProject(projectId);
        }
    });
    
    // معالج حدث إرسال التعليق
    document.getElementById('instagram-comment-submit').addEventListener('click', function() {
        submitComment();
    });
    
    // معالج حدث الضغط على Enter في حقل التعليق
    document.getElementById('instagram-comment-content').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            submitComment();
        }
    });
    
    // أزرار التنقل بين صور المعرض
    document.getElementById('instagram-gallery-prev').addEventListener('click', function() {
        navigateGallery('prev');
    });
    
    document.getElementById('instagram-gallery-next').addEventListener('click', function() {
        navigateGallery('next');
    });
    
    // التركيز على حقل التعليق عند النقر على زر التعليق
    document.getElementById('instagram-comment-button').addEventListener('click', function() {
        document.getElementById('instagram-comment-content').focus();
    });
    
    // إضافة استجابة للضغط على ESC لإغلاق النافذة
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
    
    // CSS styles التأكد من تحميل الـ
    if (!document.getElementById('instagram-modal-styles')) {
        const styleLink = document.createElement('link');
        styleLink.id = 'instagram-modal-styles';
        styleLink.rel = 'stylesheet';
        styleLink.href = `/static/css/instagram-modal.css?v=${Date.now()}`;
        document.head.appendChild(styleLink);
    }
}

// إضافة معالجات الأحداث لعناصر المعرض
function setupGalleryItemEvents() {
    console.log("إعداد معالجات أحداث عناصر المعرض");
    
    // البحث عن جميع عناصر المعرض وإضافة معالج الحدث لها
    const galleryItems = document.querySelectorAll('.portfolio-item');
    
    galleryItems.forEach(item => {
        console.log("تم العثور على عنصر معرض:", item.getAttribute('data-id'));
        
        // إضافة معالج النقر لفتح النافذة المنبثقة
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const projectId = this.getAttribute('data-id');
            console.log("تم النقر على عنصر المعرض:", projectId);
            openModal(projectId);
        });
    });
}

// المتغيرات العالمية
let currentProject = null; // المشروع الحالي
let galleryImages = []; // صور المعرض
let currentImageIndex = 0; // مؤشر الصورة الحالية

// فتح النافذة المنبثقة
function openModal(projectId) {
    console.log("فتح النافذة المنبثقة للمشروع:", projectId);
    
    currentProject = projectId;
    
    // عرض النافذة المنبثقة
    const modal = document.getElementById('instagram-modal');
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden'; // منع التمرير
    
    // تحميل بيانات المشروع
    loadProjectData(projectId);
}

// تحميل بيانات المشروع
function loadProjectData(projectId) {
    console.log("تحميل بيانات المشروع:", projectId);
    
    // عرض حالة التحميل
    document.getElementById('instagram-modal-title').textContent = 'جاري التحميل...';
    document.getElementById('instagram-modal-description').innerHTML = '';
    
    // الحصول على بيانات المشروع من الخادم
    fetch(`/portfolio/${projectId}/detail`)
        .then(response => {
            if (!response.ok) {
                throw new Error('فشل في تحميل بيانات المشروع');
            }
            return response.json();
        })
        .then(data => {
            console.log("تم استلام بيانات المشروع:", data);
            
            // عرض بيانات المشروع
            displayProjectData(data);
            
            // تسجيل المشاهدة
            recordView(projectId);
        })
        .catch(error => {
            console.error('خطأ في تحميل بيانات المشروع:', error);
            document.getElementById('instagram-modal-title').textContent = 'حدث خطأ';
            document.getElementById('instagram-modal-description').innerHTML = '<p>فشل في تحميل بيانات المشروع. يرجى المحاولة مرة أخرى.</p>';
        });
}

// عرض بيانات المشروع في النافذة المنبثقة
function displayProjectData(data) {
    console.log("عرض بيانات المشروع:", data);
    
    // تعيين بيانات المشروع الأساسية
    document.getElementById('instagram-modal-title').textContent = data.title;
    document.getElementById('instagram-modal-category').textContent = data.category;
    document.getElementById('instagram-modal-description').innerHTML = data.description;
    document.getElementById('instagram-modal-main-image').src = data.image_url;
    document.getElementById('instagram-modal-likes').textContent = `${data.likes_count} إعجاب`;
    document.getElementById('instagram-modal-views').textContent = `${data.views_count} مشاهدة`;
    
    // تعيين التاريخ بتنسيق مناسب
    const createdDate = new Date(data.created_at);
    const formattedDate = new Intl.DateTimeFormat('ar-SA', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    }).format(createdDate);
    document.getElementById('instagram-modal-date').textContent = formattedDate;
    
    // تعيين حالة الإعجاب
    const likeButton = document.getElementById('instagram-like-button');
    likeButton.setAttribute('data-id', data.id);
    
    if (data.user_liked) {
        likeButton.classList.add('active');
        likeButton.querySelector('i').classList.remove('far');
        likeButton.querySelector('i').classList.add('fas');
    } else {
        likeButton.classList.remove('active');
        likeButton.querySelector('i').classList.remove('fas');
        likeButton.querySelector('i').classList.add('far');
    }
    
    // تعيين رابط المشروع (إذا كان موجودًا)
    const linkContainer = document.getElementById('instagram-modal-link-container');
    if (data.link && data.link.trim() !== '') {
        linkContainer.style.display = 'block';
        document.getElementById('instagram-modal-link').href = data.link;
    } else {
        linkContainer.style.display = 'none';
    }
    
    // تعيين معرّف المشروع لحقل التعليق
    document.getElementById('instagram-comment-project-id').value = data.id;
    
    // عرض التعليقات
    displayComments(data.comments);
    
    // إعداد معرض الصور (إذا كان هناك صور إضافية)
    setupGallery(data);
}

// عرض التعليقات
function displayComments(comments) {
    console.log("عرض التعليقات:", comments);
    
    const commentsContainer = document.getElementById('instagram-comments-container');
    commentsContainer.innerHTML = '';
    
    if (!comments || comments.length === 0) {
        commentsContainer.innerHTML = '<div class="no-comments-message">لا توجد تعليقات حتى الآن. كن أول من يعلق!</div>';
        return;
    }
    
    // إنشاء عنصر HTML لكل تعليق
    comments.forEach(comment => {
        const commentEl = document.createElement('div');
        commentEl.className = 'instagram-comment';
        commentEl.dataset.id = comment.id;
        
        const date = new Date(comment.created_at);
        const formattedDate = new Intl.DateTimeFormat('ar-SA', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        }).format(date);
        
        commentEl.innerHTML = `
            <div class="instagram-comment-header">
                <div class="instagram-comment-user">${comment.user_name || 'زائر'}</div>
                <div class="instagram-comment-date">${formattedDate}</div>
            </div>
            <div class="instagram-comment-content">${comment.content}</div>
            <div class="instagram-comment-actions">
                <div class="instagram-comment-like" data-id="${comment.id}">
                    <span>${comment.likes_count || 0}</span>
                    <i class="${comment.user_liked ? 'fas' : 'far'} fa-heart"></i>
                </div>
            </div>
        `;
        
        // إضافة معالج الحدث للإعجاب بالتعليق
        const likeBtn = commentEl.querySelector('.instagram-comment-like');
        likeBtn.addEventListener('click', function() {
            likeComment(comment.id);
        });
        
        commentsContainer.appendChild(commentEl);
    });
}

// إعداد معرض الصور
function setupGallery(data) {
    console.log("إعداد معرض الصور");
    
    // إعادة تعيين مصفوفة الصور
    galleryImages = [];
    
    // إضافة الصورة الرئيسية أولًا
    galleryImages.push(data.image_url);
    
    // إضافة الصور الإضافية (إذا وجدت)
    if (data.carousel_images && data.carousel_images.length > 0) {
        galleryImages = galleryImages.concat(data.carousel_images);
    }
    
    // تعيين الصورة الحالية
    currentImageIndex = 0;
    
    // إظهار/إخفاء أزرار التنقل حسب عدد الصور
    const prevButton = document.getElementById('instagram-gallery-prev');
    const nextButton = document.getElementById('instagram-gallery-next');
    
    if (galleryImages.length <= 1) {
        prevButton.style.display = 'none';
        nextButton.style.display = 'none';
    } else {
        prevButton.style.display = 'flex';
        nextButton.style.display = 'flex';
    }
}

// التنقل بين صور المعرض
function navigateGallery(direction) {
    console.log("التنقل في المعرض:", direction);
    
    if (galleryImages.length <= 1) return;
    
    // تغيير مؤشر الصورة الحالية
    if (direction === 'prev') {
        currentImageIndex = (currentImageIndex - 1 + galleryImages.length) % galleryImages.length;
    } else {
        currentImageIndex = (currentImageIndex + 1) % galleryImages.length;
    }
    
    // تحديث الصورة
    const imageElement = document.getElementById('instagram-modal-main-image');
    imageElement.src = galleryImages[currentImageIndex];
}

// إغلاق النافذة المنبثقة
function closeModal() {
    console.log("إغلاق النافذة المنبثقة");
    
    const modal = document.getElementById('instagram-modal');
    modal.style.display = 'none';
    document.body.style.overflow = ''; // إعادة تمكين التمرير
}

// تسجيل مشاهدة للمشروع
function recordView(projectId) {
    console.log("تسجيل مشاهدة للمشروع:", projectId);
    
    fetch(`/portfolio/${projectId}/view`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // تحديث عدد المشاهدات في النافذة المنبثقة
            document.getElementById('instagram-modal-views').textContent = `${data.views_count} مشاهدة`;
        }
    })
    .catch(error => {
        console.error('خطأ في تسجيل المشاهدة:', error);
    });
}

// الإعجاب بمشروع
function likeProject(projectId) {
    console.log("الإعجاب بالمشروع:", projectId);
    
    fetch(`/portfolio/${projectId}/like`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // تحديث حالة الإعجاب
            const likeButton = document.getElementById('instagram-like-button');
            
            if (data.liked) {
                likeButton.classList.add('active');
                likeButton.querySelector('i').classList.remove('far');
                likeButton.querySelector('i').classList.add('fas');
            } else {
                likeButton.classList.remove('active');
                likeButton.querySelector('i').classList.remove('fas');
                likeButton.querySelector('i').classList.add('far');
            }
            
            // تحديث عدد الإعجابات
            document.getElementById('instagram-modal-likes').textContent = `${data.likes_count} إعجاب`;
        }
    })
    .catch(error => {
        console.error('خطأ في تبديل الإعجاب:', error);
    });
}

// الإعجاب بتعليق
function likeComment(commentId) {
    console.log("الإعجاب بالتعليق:", commentId);
    
    fetch(`/comment/${commentId}/like`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // تحديث حالة الإعجاب بالتعليق
            const commentEl = document.querySelector(`.instagram-comment[data-id="${commentId}"]`);
            if (commentEl) {
                const likeBtn = commentEl.querySelector('.instagram-comment-like');
                const countEl = likeBtn.querySelector('span');
                const iconEl = likeBtn.querySelector('i');
                
                // تحديث العدد
                countEl.textContent = data.likes_count;
                
                // تحديث الأيقونة
                if (data.liked) {
                    iconEl.classList.remove('far');
                    iconEl.classList.add('fas');
                } else {
                    iconEl.classList.remove('fas');
                    iconEl.classList.add('far');
                }
            }
        }
    })
    .catch(error => {
        console.error('خطأ في الإعجاب بالتعليق:', error);
    });
}

// إرسال تعليق جديد
function submitComment() {
    console.log("إرسال تعليق جديد");
    
    const projectId = document.getElementById('instagram-comment-project-id').value;
    const content = document.getElementById('instagram-comment-content').value.trim();
    
    if (!content) {
        alert('الرجاء كتابة تعليق قبل النشر');
        return;
    }
    
    const formData = new FormData();
    formData.append('content', content);
    
    fetch(`/portfolio/${projectId}/comment`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // مسح المحتوى
            document.getElementById('instagram-comment-content').value = '';
            
            // تحديث التعليقات
            displayComments(data.comments);
        } else {
            alert(data.message || 'حدث خطأ أثناء إرسال التعليق');
        }
    })
    .catch(error => {
        console.error('خطأ في إرسال التعليق:', error);
        alert('حدث خطأ أثناء إرسال التعليق. الرجاء المحاولة مرة أخرى.');
    });
}

// إضافة دعم لتحميل النافذة المنبثقة بعد إضافة عناصر جديدة للمعرض
function reinitializeGalleryItems() {
    console.log("إعادة تهيئة عناصر المعرض");
    setupGalleryItemEvents();
}

// دعم لمعالجات الأحداث العامة
window.instagramModal = {
    reinitializeGalleryItems: reinitializeGalleryItems
};