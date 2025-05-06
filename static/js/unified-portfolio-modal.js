/**
 * ملف موحد للنوافذ المنبثقة لمعرض الأعمال
 * يجمع بين وظائف كافة ملفات جافاسكريبت المتعلقة بالنوافذ المنبثقة
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('تهيئة نظام النوافذ المنبثقة الموحد');
    
    // 1. إنشاء النافذة المنبثقة وإضافتها للصفحة إذا لم تكن موجودة
    createModalIfNotExists();
    
    // 2. إضافة أحداث للنقر على عناصر المعرض
    setupPortfolioItemEvents();
    
    // 3. إضافة أحداث للنافذة المنبثقة
    setupModalEvents();
});

/**
 * إنشاء هيكل النافذة المنبثقة وإضافتها للصفحة إذا لم تكن موجودة
 */
function createModalIfNotExists() {
    // التحقق مما إذا كانت النافذة المنبثقة موجودة بالفعل
    if (document.getElementById('instagram-modal')) {
        console.log('النافذة المنبثقة موجودة بالفعل');
        return;
    }
    
    console.log('إنشاء النافذة المنبثقة وإضافتها للصفحة');
    
    // إنشاء هيكل النافذة المنبثقة
    const modalHTML = `
    <div id="instagram-modal" class="instagram-modal">
        <button id="instagram-modal-close" class="instagram-modal-close">
            <i class="fas fa-times"></i>
        </button>
        
        <div class="instagram-modal-container">
            <!-- قسم الصورة (اليمين) -->
            <div class="instagram-modal-image">
                <img id="modal-image" src="" alt="صورة المشروع">
            </div>
            
            <!-- قسم المعلومات (اليسار) -->
            <div class="instagram-modal-info">
                <!-- ترويسة الملف الشخصي -->
                <div class="instagram-modal-header">
                    <div class="modal-profile">
                        <img src="/static/uploads/profile/profile.jpg" alt="الملف الشخصي" class="modal-profile-image">
                        <div class="modal-profile-name">
                            <h4>فيراس ديزاين</h4>
                            <p id="modal-category">فئة المشروع</p>
                        </div>
                    </div>
                    <div class="modal-actions">
                        <button id="fullscreen-btn" class="modal-action-btn">
                            <i class="fas fa-expand"></i>
                        </button>
                    </div>
                </div>
                
                <!-- محتوى المعلومات -->
                <div class="instagram-modal-content">
                    <!-- عنوان المشروع -->
                    <h3 id="modal-title" class="modal-title">عنوان المشروع</h3>
                    
                    <!-- وصف المشروع -->
                    <div id="modal-description" class="modal-description">وصف المشروع</div>
                    
                    <!-- رابط المشروع -->
                    <div id="modal-link-container" class="modal-link-container">
                        <a id="modal-link" href="#" target="_blank" class="modal-link">
                            <i class="fas fa-external-link-alt mr-2"></i>زيارة المشروع
                        </a>
                    </div>
                    
                    <!-- معلومات التاريخ -->
                    <div class="modal-date-container">
                        <p><i class="far fa-calendar-alt"></i> <span id="modal-date">التاريخ</span></p>
                    </div>
                </div>
                
                <!-- إحصائيات المشروع -->
                <div class="instagram-modal-footer">
                    <div class="modal-stats">
                        <div class="modal-stat">
                            <button id="like-button" class="like-button">
                                <i class="far fa-heart"></i>
                            </button>
                            <span id="modal-likes">0 إعجاب</span>
                        </div>
                        <div class="modal-stat">
                            <i class="far fa-eye"></i>
                            <span id="modal-views">0 مشاهدة</span>
                        </div>
                        <div class="modal-stat">
                            <i class="far fa-comment"></i>
                            <span id="modal-comments">0 تعليق</span>
                        </div>
                    </div>
                    <input type="hidden" id="modal-item-id" value="">
                    <input type="hidden" id="comment-portfolio-id" value="">
                </div>
                
                <!-- نموذج التعليقات -->
                <div id="comments-section" class="comments-section">
                    <h4 class="comments-title">التعليقات</h4>
                    <div id="comments-list" class="comments-list">
                        <!-- سيتم إضافة التعليقات هنا ديناميكيًا -->
                    </div>
                    
                    <div id="comment-form-container" class="comment-form-container">
                        <button id="add-comment-btn" class="add-comment-btn">
                            <i class="fas fa-plus-circle"></i> إضافة تعليق
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- نموذج إضافة تعليق -->
    <div id="comment-modal" class="comment-modal">
        <div class="comment-modal-content">
            <span class="close-comment-modal">&times;</span>
            <h3>إضافة تعليق</h3>
            
            <form id="comment-form" class="comment-form">
                <div class="form-group">
                    <label for="name">الاسم</label>
                    <input type="text" id="name" name="name" required>
                </div>
                
                <div class="form-group">
                    <label for="email">البريد الإلكتروني</label>
                    <input type="email" id="email" name="email" required>
                </div>
                
                <div class="form-group">
                    <label for="content">التعليق</label>
                    <textarea id="content" name="content" rows="4" required></textarea>
                </div>
                
                <input type="hidden" id="comment-portfolio-id" name="portfolio_id" value="">
                
                <div class="form-actions">
                    <button type="submit" class="submit-comment">إرسال التعليق</button>
                </div>
                
                <div class="form-message hidden"></div>
            </form>
        </div>
    </div>
    
    <!-- معرض الصور بالحجم الكامل -->
    <div id="fullscreen-gallery" class="fullscreen-gallery">
        <button id="close-gallery" class="close-gallery">
            <i class="fas fa-times"></i>
        </button>
        
        <div class="gallery-container">
            <img id="fullscreen-image" src="" alt="صورة المشروع بالحجم الكامل">
            
            <div class="gallery-controls">
                <button id="prev-image" class="gallery-nav">
                    <i class="fas fa-chevron-left"></i>
                </button>
                <div class="gallery-counter">
                    <span id="current-image">1</span>/<span id="total-images">1</span>
                </div>
                <button id="next-image" class="gallery-nav">
                    <i class="fas fa-chevron-right"></i>
                </button>
            </div>
            
            <div id="gallery-thumbnails" class="gallery-thumbnails">
                <!-- سيتم إضافة المصغرات هنا ديناميكيًا -->
            </div>
        </div>
    </div>
    `;
    
    // إضافة النافذة المنبثقة إلى نهاية الصفحة
    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

/**
 * إضافة أحداث النقر لعناصر المعرض
 */
function setupPortfolioItemEvents() {
    // إضافة حدث النقر لكل عنصر معرض
    const portfolioItems = document.querySelectorAll('.portfolio-item');
    portfolioItems.forEach(item => {
        item.addEventListener('click', function() {
            const portfolioId = this.getAttribute('data-id');
            if (portfolioId) {
                console.log(`النقر على المشروع رقم ${portfolioId}`);
                openPortfolioModal(portfolioId);
            }
        });
    });
}

/**
 * إضافة أحداث للنافذة المنبثقة
 */
function setupModalEvents() {
    // زر إغلاق النافذة المنبثقة
    const closeButton = document.getElementById('instagram-modal-close');
    if (closeButton) {
        closeButton.addEventListener('click', function() {
            closeInstagramModal();
        });
    }
    
    // زر الإعجاب
    const likeButton = document.getElementById('like-button');
    if (likeButton) {
        likeButton.addEventListener('click', function() {
            const portfolioId = document.getElementById('modal-item-id').value;
            likePortfolioItem(portfolioId);
        });
    }
    
    // زر العرض بالحجم الكامل
    const fullscreenBtn = document.getElementById('fullscreen-btn');
    if (fullscreenBtn) {
        fullscreenBtn.addEventListener('click', function() {
            openFullscreenGallery();
        });
    }
    
    // إغلاق المعرض بالحجم الكامل
    const closeGalleryBtn = document.getElementById('close-gallery');
    if (closeGalleryBtn) {
        closeGalleryBtn.addEventListener('click', function() {
            closeFullscreenGallery();
        });
    }
    
    // أزرار التنقل بين الصور
    const prevButton = document.getElementById('prev-image');
    const nextButton = document.getElementById('next-image');
    
    if (prevButton) {
        prevButton.addEventListener('click', function() {
            navigateGallery('prev');
        });
    }
    
    if (nextButton) {
        nextButton.addEventListener('click', function() {
            navigateGallery('next');
        });
    }
    
    // زر إضافة تعليق
    const addCommentBtn = document.getElementById('add-comment-btn');
    if (addCommentBtn) {
        addCommentBtn.addEventListener('click', function() {
            openCommentModal();
        });
    }
    
    // إغلاق نافذة التعليق
    const closeCommentModalBtn = document.querySelector('.close-comment-modal');
    if (closeCommentModalBtn) {
        closeCommentModalBtn.addEventListener('click', function() {
            closeCommentModal();
        });
    }
    
    // نموذج إضافة تعليق
    const commentForm = document.getElementById('comment-form');
    if (commentForm) {
        commentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitComment();
        });
    }
}

/**
 * فتح النافذة المنبثقة مع بيانات المشروع
 * @param {string} portfolioId معرف المشروع
 */
function openPortfolioModal(portfolioId) {
    if (!portfolioId) {
        console.error('معرف المشروع غير محدد');
        return;
    }
    
    console.log(`فتح النافذة المنبثقة للمشروع رقم ${portfolioId}`);
    
    // طلب بيانات المشروع من الخادم
    fetch(`/portfolio/${portfolioId}/detail`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`فشل في جلب البيانات: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // عرض بيانات المشروع في النافذة المنبثقة
            displayPortfolioData(data);
            
            // فتح النافذة المنبثقة
            const modal = document.getElementById('instagram-modal');
            if (modal) {
                modal.style.display = 'flex';
                document.body.style.overflow = 'hidden';
            }
            
            // تحميل التعليقات
            loadComments(portfolioId);
            
            // تسجيل المشاهدة
            recordView(portfolioId);
        })
        .catch(error => {
            console.error('خطأ في جلب بيانات المشروع:', error);
            alert('عذرًا، حدث خطأ أثناء جلب بيانات المشروع');
        });
}

/**
 * إغلاق النافذة المنبثقة
 */
function closeInstagramModal() {
    const modal = document.getElementById('instagram-modal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

/**
 * عرض بيانات المشروع في النافذة المنبثقة
 * @param {Object} data بيانات المشروع
 */
function displayPortfolioData(data) {
    console.log('عرض بيانات المشروع:', data);
    
    // تعيين بيانات المشروع في النافذة المنبثقة
    document.getElementById('modal-title').textContent = data.title;
    document.getElementById('modal-image').src = data.image_url;
    document.getElementById('modal-category').textContent = data.category;
    document.getElementById('modal-description').innerHTML = data.description;
    document.getElementById('modal-date').textContent = formatDate(data.created_at);
    document.getElementById('modal-likes').textContent = `${data.likes_count} إعجاب`;
    document.getElementById('modal-views').textContent = `${data.views_count} مشاهدة`;
    document.getElementById('modal-comments').textContent = `${data.comments_count || 0} تعليق`;
    document.getElementById('modal-item-id').value = data.id;
    document.getElementById('comment-portfolio-id').value = data.id;
    
    // إضافة رابط المشروع إذا كان متوفرًا
    const linkContainer = document.getElementById('modal-link-container');
    const modalLink = document.getElementById('modal-link');
    
    if (data.link && data.link.trim() !== '') {
        modalLink.href = data.link;
        linkContainer.style.display = 'block';
    } else {
        linkContainer.style.display = 'none';
    }
    
    // تحديث زر الإعجاب
    const likeButton = document.getElementById('like-button');
    const likeIcon = likeButton.querySelector('i');
    
    if (data.user_liked) {
        likeButton.classList.add('active');
        likeIcon.classList.remove('far');
        likeIcon.classList.add('fas');
        likeIcon.style.color = '#ef4444';
    } else {
        likeButton.classList.remove('active');
        likeIcon.classList.remove('fas');
        likeIcon.classList.add('far');
        likeIcon.style.color = '';
    }
}

/**
 * تسجيل مشاهدة للمشروع
 * @param {string} portfolioId معرف المشروع
 */
function recordView(portfolioId) {
    fetch(`/portfolio/${portfolioId}/view`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // تحديث عداد المشاهدات في النافذة المنبثقة
            document.getElementById('modal-views').textContent = `${data.views_count} مشاهدة`;
            
            // تحديث عداد المشاهدات في شبكة المشاريع إذا كان موجودًا
            const portfolioItem = document.querySelector(`.portfolio-item[data-id="${portfolioId}"]`);
            if (portfolioItem) {
                const viewsElement = portfolioItem.querySelector('.item-stat:last-child span');
                if (viewsElement) {
                    viewsElement.textContent = data.views_count;
                }
            }
        }
    })
    .catch(error => {
        console.error('خطأ في تسجيل المشاهدة:', error);
    });
}

/**
 * تحميل التعليقات للمشروع
 * @param {string} portfolioId معرف المشروع
 */
function loadComments(portfolioId) {
    const commentsList = document.getElementById('comments-list');
    
    if (!commentsList) return;
    
    commentsList.innerHTML = `
    <div class="comments-loading">
        <i class="fas fa-spinner fa-spin"></i> جاري تحميل التعليقات...
    </div>
    `;
    
    fetch(`/api/portfolio/${portfolioId}/comments`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.comments) {
                if (data.comments.length === 0) {
                    commentsList.innerHTML = `
                    <div class="no-comments">
                        <p>لا توجد تعليقات حتى الآن. كن أول من يعلق!</p>
                    </div>
                    `;
                    return;
                }
                
                commentsList.innerHTML = '';
                
                data.comments.forEach(comment => {
                    const commentElement = document.createElement('div');
                    commentElement.className = 'comment-item';
                    commentElement.innerHTML = `
                    <div class="comment-header">
                        <div class="comment-author">
                            <i class="fas fa-user-circle"></i>
                            <span>${comment.name}</span>
                        </div>
                        <div class="comment-date">
                            <i class="far fa-clock"></i>
                            <span>${formatDate(comment.created_at)}</span>
                        </div>
                    </div>
                    <div class="comment-content">
                        <p>${comment.content}</p>
                    </div>
                    `;
                    
                    commentsList.appendChild(commentElement);
                });
                
                // تحديث عداد التعليقات
                document.getElementById('modal-comments').textContent = `${data.comments.length} تعليق`;
            } else {
                commentsList.innerHTML = `
                <div class="comments-error">
                    <p>حدث خطأ أثناء تحميل التعليقات. حاول مرة أخرى لاحقًا.</p>
                </div>
                `;
            }
        })
        .catch(error => {
            console.error('خطأ في تحميل التعليقات:', error);
            commentsList.innerHTML = `
            <div class="comments-error">
                <p>حدث خطأ أثناء تحميل التعليقات. حاول مرة أخرى لاحقًا.</p>
            </div>
            `;
        });
}

/**
 * فتح نافذة إضافة تعليق
 */
function openCommentModal() {
    const commentModal = document.getElementById('comment-modal');
    if (commentModal) {
        commentModal.style.display = 'block';
    }
}

/**
 * إغلاق نافذة إضافة تعليق
 */
function closeCommentModal() {
    const commentModal = document.getElementById('comment-modal');
    if (commentModal) {
        commentModal.style.display = 'none';
    }
}

/**
 * إرسال تعليق جديد
 */
function submitComment() {
    const portfolioId = document.getElementById('comment-portfolio-id').value;
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const content = document.getElementById('content').value.trim();
    const formMessage = document.querySelector('.form-message');
    
    // التحقق من وجود جميع الحقول
    if (!name || !email || !content) {
        formMessage.textContent = 'يرجى تعبئة جميع الحقول المطلوبة';
        formMessage.className = 'form-message error';
        formMessage.classList.remove('hidden');
        return;
    }
    
    // التحقق من صحة البريد الإلكتروني
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        formMessage.textContent = 'يرجى إدخال بريد إلكتروني صحيح';
        formMessage.className = 'form-message error';
        formMessage.classList.remove('hidden');
        return;
    }
    
    // إرسال التعليق للخادم
    fetch(`/api/portfolio/${portfolioId}/comments`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': getCSRFToken()
        },
        body: JSON.stringify({
            name,
            email,
            content
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // مسح النموذج
            document.getElementById('name').value = '';
            document.getElementById('email').value = '';
            document.getElementById('content').value = '';
            
            // عرض رسالة نجاح
            formMessage.textContent = 'تم إرسال تعليقك بنجاح وهو قيد المراجعة من الإدارة. شكراً لك!';
            formMessage.className = 'form-message success';
            formMessage.classList.remove('hidden');
            
            // إغلاق النافذة بعد فترة قصيرة
            setTimeout(() => {
                closeCommentModal();
            }, 3000);
        } else {
            formMessage.textContent = data.message || 'حدث خطأ أثناء إرسال التعليق. الرجاء المحاولة مرة أخرى.';
            formMessage.className = 'form-message error';
            formMessage.classList.remove('hidden');
        }
    })
    .catch(error => {
        console.error('خطأ في إرسال التعليق:', error);
        formMessage.textContent = 'حدث خطأ في النظام. الرجاء المحاولة مرة أخرى.';
        formMessage.className = 'form-message error';
        formMessage.classList.remove('hidden');
    });
}

/**
 * تبديل حالة الإعجاب بمشروع
 * @param {string} portfolioId معرف المشروع
 */
function likePortfolioItem(portfolioId) {
    fetch(`/portfolio/${portfolioId}/like`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // تحديث زر الإعجاب
            const likeButton = document.getElementById('like-button');
            const likeIcon = likeButton.querySelector('i');
            
            // تحديث عداد الإعجابات
            document.getElementById('modal-likes').textContent = `${data.likes_count} إعجاب`;
            
            // تغيير شكل الزر بناءً على حالة الإعجاب
            if (data.liked) {
                likeButton.classList.add('active');
                likeIcon.classList.remove('far');
                likeIcon.classList.add('fas');
                likeIcon.style.color = '#ef4444';
            } else {
                likeButton.classList.remove('active');
                likeIcon.classList.remove('fas');
                likeIcon.classList.add('far');
                likeIcon.style.color = '';
            }
            
            // تحديث عداد الإعجابات في شبكة المشاريع إذا كان موجودًا
            const portfolioItem = document.querySelector(`.portfolio-item[data-id="${portfolioId}"]`);
            if (portfolioItem) {
                const likesElement = portfolioItem.querySelector('.item-stat:first-child span');
                if (likesElement) {
                    likesElement.textContent = data.likes_count;
                }
            }
        }
    })
    .catch(error => {
        console.error('خطأ في تبديل حالة الإعجاب:', error);
    });
}

/**
 * فتح معرض الصور بالحجم الكامل
 */
function openFullscreenGallery() {
    // الحصول على مكونات المعرض
    const fullscreenGallery = document.getElementById('fullscreen-gallery');
    const fullscreenImage = document.getElementById('fullscreen-image');
    const galleryThumbnails = document.getElementById('gallery-thumbnails');
    
    // تجهيز الصور المتاحة للمعرض
    currentGalleryImages = [];
    
    // إضافة الصورة الرئيسية
    const mainImage = document.getElementById('modal-image').src;
    currentGalleryImages.push(mainImage);
    
    // تعيين الصورة الحالية
    fullscreenImage.src = mainImage;
    currentImageIndex = 0;
    
    // تحديث عداد الصور
    document.getElementById('current-image').textContent = '1';
    document.getElementById('total-images').textContent = currentGalleryImages.length;
    
    // إضافة المصغرات
    galleryThumbnails.innerHTML = '';
    currentGalleryImages.forEach((src, index) => {
        const thumbnail = document.createElement('div');
        thumbnail.className = `thumbnail ${index === 0 ? 'active' : ''}`;
        thumbnail.innerHTML = `<img src="${src}" alt="صورة مصغرة ${index + 1}">`;
        
        // إضافة حدث النقر
        thumbnail.addEventListener('click', function() {
            currentImageIndex = index;
            updateFullscreenGallery();
        });
        
        galleryThumbnails.appendChild(thumbnail);
    });
    
    // إظهار المعرض
    fullscreenGallery.style.display = 'flex';
    
    // منع التمرير في الصفحة الخلفية
    document.body.style.overflow = 'hidden';
}

/**
 * إغلاق معرض الصور بالحجم الكامل
 */
function closeFullscreenGallery() {
    const fullscreenGallery = document.getElementById('fullscreen-gallery');
    if (fullscreenGallery) {
        fullscreenGallery.style.display = 'none';
        document.body.style.overflow = '';
    }
}

/**
 * التنقل بين الصور في المعرض
 * @param {string} direction اتجاه التنقل (prev أو next)
 */
function navigateGallery(direction) {
    if (!currentGalleryImages || currentGalleryImages.length <= 1) return;
    
    if (direction === 'next') {
        currentImageIndex = (currentImageIndex + 1) % currentGalleryImages.length;
    } else {
        currentImageIndex = (currentImageIndex - 1 + currentGalleryImages.length) % currentGalleryImages.length;
    }
    
    updateFullscreenGallery();
}

/**
 * تحديث عرض معرض الصور بالحجم الكامل
 */
function updateFullscreenGallery() {
    const fullscreenImage = document.getElementById('fullscreen-image');
    fullscreenImage.src = currentGalleryImages[currentImageIndex];
    
    // تحديث المصغرات النشطة
    document.querySelectorAll('.thumbnail').forEach((thumb, index) => {
        if (index === currentImageIndex) {
            thumb.classList.add('active');
        } else {
            thumb.classList.remove('active');
        }
    });
    
    // تحديث عداد الصور
    document.getElementById('current-image').textContent = currentImageIndex + 1;
}

/**
 * تنسيق التاريخ بتنسيق عربي
 * @param {string} dateString سلسلة التاريخ
 * @return {string} التاريخ المنسق
 */
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('ar-SA', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

/**
 * الحصول على رمز CSRF
 * @return {string} رمز CSRF
 */
function getCSRFToken() {
    // محاولة الحصول على الرمز من عنصر meta
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    if (metaToken) {
        return metaToken.getAttribute('content');
    }
    
    // محاولة الحصول على الرمز من الكوكيز
    const csrfCookie = document.cookie.split('; ').find(row => row.startsWith('csrf_token='));
    if (csrfCookie) {
        return csrfCookie.split('=')[1];
    }
    
    // إذا لم نجد الرمز
    console.warn('لم يتم العثور على رمز CSRF. قد لا تعمل النماذج بشكل صحيح.');
    return '';
}

// متغيرات عامة للمعرض
let currentGalleryImages = [];
let currentImageIndex = 0;

// إغلاق الأقواس المتبقية (إصلاح الخطأ النحوي)
}); // إغلاق event listener
