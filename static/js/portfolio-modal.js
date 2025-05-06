/**
 * وظائف النافذة المنبثقة لمعرض الأعمال
 */

document.addEventListener('DOMContentLoaded', function() {
    // إعداد النافذة المنبثقة
    setupPortfolioModal();
    
    // إضافة مستمعي الأحداث لعناصر معرض الأعمال
    const portfolioItems = document.querySelectorAll('.portfolio-item');
    portfolioItems.forEach(item => {
        item.addEventListener('click', function() {
            const portfolioId = this.getAttribute('data-id');
            openPortfolioModal(portfolioId);
        });
    });
});

/**
 * إعداد النافذة المنبثقة وإضافتها إلى صفحة DOM
 */
function setupPortfolioModal() {
    // إنشاء هيكل النافذة المنبثقة في حال عدم وجوده
    if (!document.querySelector('.portfolio-modal-overlay')) {
        const modalHTML = `
            <div class="portfolio-modal-overlay">
                <div class="portfolio-modal">
                    <button class="modal-close"><i class="fas fa-times"></i></button>
                    <div class="modal-image-container">
                        <!-- ستتم إضافة الصورة ديناميكيًا هنا -->
                    </div>
                    <div class="modal-content">
                        <!-- سيتم عرض المحتوى ديناميكيًا هنا -->
                    </div>
                </div>
            </div>
        `;
        
        // إضافة النافذة المنبثقة إلى نهاية body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // إضافة مستمع لزر الإغلاق
        const closeButton = document.querySelector('.modal-close');
        closeButton.addEventListener('click', closePortfolioModal);
        
        // إغلاق النافذة عند النقر خارجها
        const modalOverlay = document.querySelector('.portfolio-modal-overlay');
        modalOverlay.addEventListener('click', function(event) {
            if (event.target === modalOverlay) {
                closePortfolioModal();
            }
        });
        
        // إضافة مستمع لمفتاح ESC
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                closePortfolioModal();
            }
        });
    }
}

/**
 * فتح النافذة المنبثقة للمشروع
 * @param {number} portfolioId - معرف المشروع
 */
function openPortfolioModal(portfolioId) {
    // إظهار مؤشر التحميل في النافذة المنبثقة
    const modalOverlay = document.querySelector('.portfolio-modal-overlay');
    const modalImageContainer = document.querySelector('.modal-image-container');
    const modalContent = document.querySelector('.modal-content');
    const modal = document.querySelector('.portfolio-modal');
    
    // تحضير المحتوى للعرض بدون مؤشر تحميل
    modalImageContainer.innerHTML = '';
    modalContent.innerHTML = '';
    
    // إضافة الصفوف لتطبيق التأثيرات الحركية المتميزة
    modal.classList.add('fade-in');
    
    // إظهار النافذة المنبثقة بشكل مباشر
    modalOverlay.classList.add('active');
    document.body.style.overflow = 'hidden'; // منع التمرير في الصفحة الخلفية
    
    // الحصول على تفاصيل المشروع من الخادم
    fetch(`/portfolio/${portfolioId}/detail`)
        .then(response => {
            if (!response.ok) {
                throw new Error('حدث خطأ أثناء جلب بيانات المشروع');
            }
            return response.json();
        })
        .then(data => {
            // عرض البيانات في النافذة المنبثقة
            displayPortfolioModal(data);
            
            // تفعيل الإغلاق عن طريق ESC
            document.addEventListener('keydown', handleEscapeKey);
            
            // زيادة عدد المشاهدات
            incrementViewCount(portfolioId);
        })
        .catch(error => {
            console.error('خطأ:', error);
            modalContent.innerHTML = '<div class="error-message">عذراً، حدث خطأ أثناء جلب بيانات المشروع</div>';
        });
}

/**
 * زيادة عدد مشاهدات المشروع
 * @param {number} portfolioId - معرف المشروع
 */
function incrementViewCount(portfolioId) {
    fetch(`/portfolio/${portfolioId}/view`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // تحديث عداد المشاهدات في النافذة المنبثقة
            const viewsCountElement = document.querySelector('.modal-view-count');
            if (viewsCountElement) {
                viewsCountElement.textContent = data.views_count;
            }
        }
    })
    .catch(error => {
        console.error('خطأ أثناء تحديث عدد المشاهدات:', error);
    });
}

/**
 * عرض النافذة المنبثقة مع بيانات المشروع
 * @param {Object} data - بيانات المشروع
 */
function displayPortfolioModal(data) {
    const modalOverlay = document.querySelector('.portfolio-modal-overlay');
    const modalImageContainer = document.querySelector('.modal-image-container');
    const modalContent = document.querySelector('.modal-content');
    
    // تنظيف المحتوى الحالي
    modalImageContainer.innerHTML = '';
    modalContent.innerHTML = '';
    
    // إضافة الصورة (أو معرض الصور)
    if (data.carousel_images && data.carousel_images.length > 0) {
        // إنشاء معرض الصور إذا كان هناك أكثر من صورة
        const carouselHTML = createCarouselHTML(data.image_url, data.carousel_images);
        modalImageContainer.innerHTML = carouselHTML;
        
        // تفعيل وظائف معرض الصور
        setupCarousel();
    } else {
        // عرض صورة واحدة فقط
        modalImageContainer.innerHTML = `<img src="${data.image_url}" alt="${data.title}" class="modal-image">`;
    }
    
    // إضافة المحتوى
    const contentHTML = `
        <div class="modal-header">
            <h2 class="modal-title">${data.title}</h2>
            <div class="modal-category">${data.category}</div>
            <div class="modal-created-at">${formatDate(data.created_at)}</div>
        </div>
        <div class="modal-description">${data.description}</div>
        <div class="modal-stats">
            <div class="modal-stat">
                <i class="fas fa-eye"></i>
                <span class="modal-view-count">${data.views_count}</span>
                <span>مشاهدة</span>
            </div>
            <div class="modal-stat">
                <i class="fas fa-heart"></i>
                <span class="modal-like-count">${data.likes_count}</span>
                <span>إعجاب</span>
            </div>
            <div class="modal-stat">
                <i class="fas fa-comment"></i>
                <span class="modal-comments-count">${data.comments_count}</span>
                <span>تعليق</span>
            </div>
        </div>
        <div class="modal-actions">
            <button class="modal-action-button like-button ${data.user_liked ? 'liked' : ''}" data-id="${data.id}">
                <i class="fas fa-heart"></i>
                <span>${data.user_liked ? 'إلغاء الإعجاب' : 'أعجبني'}</span>
            </button>
            <button class="modal-action-button comment-button" data-id="${data.id}">
                <i class="fas fa-comment"></i>
                <span>تعليق</span>
            </button>
        </div>
        ${data.link ? `<a href="${data.link}" target="_blank" class="modal-link"><i class="fas fa-external-link-alt"></i> مشاهدة المشروع</a>` : ''}
        <div class="modal-comments-section">
            <h3 class="modal-comments-title">التعليقات (${data.comments_count})</h3>
            <div class="modal-comment-form">
                <textarea class="modal-comment-input" placeholder="أضف تعليقك هنا..." rows="3"></textarea>
                <button class="modal-comment-submit" data-id="${data.id}">إرسال التعليق</button>
            </div>
            <div class="modal-comments-list">
                ${renderComments(data.comments)}
            </div>
        </div>
    `;
    
    modalContent.innerHTML = contentHTML;
    
    // إظهار النافذة المنبثقة
    modalOverlay.classList.add('active');
    
    // إعداد التفاعلات
    setupModalInteractions(data.id);
}

/**
 * إنشاء HTML لعنصر معرض الصور
 * @param {string} mainImage - رابط الصورة الرئيسية
 * @param {Array} carouselImages - مصفوفة روابط الصور الإضافية
 * @returns {string} HTML لعنصر معرض الصور
 */
function createCarouselHTML(mainImage, carouselImages) {
    // دمج الصورة الرئيسية مع الصور الإضافية
    const allImages = [mainImage, ...carouselImages];
    
    // إنشاء شرائح الصور
    let slidesHTML = '';
    allImages.forEach((image, index) => {
        slidesHTML += `
            <div class="carousel-slide ${index === 0 ? 'active' : ''}">
                <img src="${image}" alt="صورة ${index + 1}" class="modal-image">
            </div>
        `;
    });
    
    // إنشاء نقاط التنقل
    let dotsHTML = '';
    allImages.forEach((_, index) => {
        dotsHTML += `<div class="carousel-dot ${index === 0 ? 'active' : ''}" data-index="${index}"></div>`;
    });
    
    // إنشاء HTML كامل لعنصر معرض الصور
    return `
        <div class="carousel-container">
            ${slidesHTML}
            ${allImages.length > 1 ? `
                <button class="carousel-arrow prev"><i class="fas fa-chevron-left"></i></button>
                <button class="carousel-arrow next"><i class="fas fa-chevron-right"></i></button>
                <div class="carousel-dots">
                    ${dotsHTML}
                </div>
            ` : ''}
        </div>
    `;
}

/**
 * إعداد وظائف معرض الصور
 */
function setupCarousel() {
    const carousel = document.querySelector('.carousel-container');
    if (!carousel) return;
    
    const slides = carousel.querySelectorAll('.carousel-slide');
    const dots = carousel.querySelectorAll('.carousel-dot');
    const prevButton = carousel.querySelector('.carousel-arrow.prev');
    const nextButton = carousel.querySelector('.carousel-arrow.next');
    
    if (slides.length <= 1) return;
    
    let currentIndex = 0;
    
    // الانتقال إلى الشريحة المحددة
    function goToSlide(index) {
        // التأكد من أن الفهرس ضمن النطاق
        if (index < 0) index = slides.length - 1;
        if (index >= slides.length) index = 0;
        
        // إزالة الفئة النشطة من جميع الشرائح والنقاط
        slides.forEach(slide => slide.classList.remove('active'));
        dots.forEach(dot => dot.classList.remove('active'));
        
        // تفعيل الشريحة والنقطة المحددة
        slides[index].classList.add('active');
        dots[index].classList.add('active');
        
        // تحديث الفهرس الحالي
        currentIndex = index;
    }
    
    // مستمعي الأحداث للأزرار
    if (prevButton) {
        prevButton.addEventListener('click', () => {
            goToSlide(currentIndex - 1);
        });
    }
    
    if (nextButton) {
        nextButton.addEventListener('click', () => {
            goToSlide(currentIndex + 1);
        });
    }
    
    // مستمعي الأحداث للنقاط
    dots.forEach(dot => {
        dot.addEventListener('click', () => {
            const index = parseInt(dot.getAttribute('data-index'));
            goToSlide(index);
        });
    });
}

/**
 * إعداد التفاعلات في النافذة المنبثقة
 * @param {number} portfolioId - معرف المشروع
 */
function setupModalInteractions(portfolioId) {
    // زر الإعجاب
    const likeButton = document.querySelector('.like-button');
    if (likeButton) {
        likeButton.addEventListener('click', function() {
            toggleLike(portfolioId);
        });
    }
    
    // زر التعليق (للتمرير إلى منطقة التعليق)
    const commentButton = document.querySelector('.comment-button');
    if (commentButton) {
        commentButton.addEventListener('click', function() {
            const commentInput = document.querySelector('.modal-comment-input');
            if (commentInput) {
                commentInput.focus();
                commentInput.scrollIntoView({ behavior: 'smooth' });
            }
        });
    }
    
    // زر إرسال التعليق
    const commentSubmit = document.querySelector('.modal-comment-submit');
    if (commentSubmit) {
        commentSubmit.addEventListener('click', function() {
            addComment(portfolioId);
        });
    }
    
    // إضافة مستمع للضغط على مفتاح Enter في حقل التعليق
    const commentInput = document.querySelector('.modal-comment-input');
    if (commentInput) {
        commentInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                addComment(portfolioId);
            }
        });
    }
    
    // إعداد التفاعلات للتعليقات الموجودة
    setupCommentInteractions();
}

/**
 * تبديل حالة الإعجاب
 * @param {number} portfolioId - معرف المشروع
 */
function toggleLike(portfolioId) {
    fetch(`/restricted/like-portfolio/${portfolioId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // تحديث زر الإعجاب
            const likeButton = document.querySelector('.like-button');
            const likeCountElement = document.querySelector('.modal-like-count');
            
            if (data.liked) {
                likeButton.classList.add('liked');
                likeButton.querySelector('span').textContent = 'إلغاء الإعجاب';
            } else {
                likeButton.classList.remove('liked');
                likeButton.querySelector('span').textContent = 'أعجبني';
            }
            
            // تحديث عدد الإعجابات
            if (likeCountElement) {
                likeCountElement.textContent = data.likes_count;
            }
        }
    })
    .catch(error => {
        console.error('خطأ أثناء تحديث الإعجاب:', error);
    });
}

/**
 * إضافة تعليق جديد
 * @param {number} portfolioId - معرف المشروع
 */
function addComment(portfolioId) {
    const commentInput = document.querySelector('.modal-comment-input');
    const content = commentInput.value.trim();
    
    if (!content) {
        alert('الرجاء كتابة تعليق قبل الإرسال');
        return;
    }
    
    const formData = new FormData();
    formData.append('content', content);
    
    fetch(`/restricted/add-comment/${portfolioId}`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // إفراغ حقل التعليق
            commentInput.value = '';
            
            // تحديث قائمة التعليقات
            const commentsList = document.querySelector('.modal-comments-list');
            if (commentsList) {
                commentsList.innerHTML = renderComments(data.comments);
                
                // إعداد التفاعلات للتعليقات الجديدة
                setupCommentInteractions();
            }
            
            // تحديث عدد التعليقات
            const commentsCountElement = document.querySelector('.modal-comments-count');
            const commentsTitle = document.querySelector('.modal-comments-title');
            if (commentsCountElement) {
                commentsCountElement.textContent = data.comments_count;
            }
            if (commentsTitle) {
                commentsTitle.textContent = `التعليقات (${data.comments_count})`;
            }
            
            // إظهار رسالة نجاح
            if (data.message) {
                const successMessage = document.createElement('div');
                successMessage.className = 'modal-comment-success';
                successMessage.textContent = data.message;
                successMessage.style.color = 'green';
                successMessage.style.marginBottom = '10px';
                
                const commentForm = document.querySelector('.modal-comment-form');
                commentForm.appendChild(successMessage);
                
                // إزالة الرسالة بعد فترة
                setTimeout(() => {
                    successMessage.remove();
                }, 3000);
            }
        } else if (data.error) {
            alert(data.message || 'حدث خطأ أثناء إضافة التعليق');
        }
    })
    .catch(error => {
        console.error('خطأ أثناء إرسال التعليق:', error);
        alert('عذراً، حدث خطأ أثناء إرسال التعليق');
    });
}

/**
 * عرض قائمة التعليقات
 * @param {Array} comments - مصفوفة التعليقات
 * @returns {string} HTML للتعليقات
 */
function renderComments(comments) {
    if (!comments || comments.length === 0) {
        return '<div class="no-comments">لا توجد تعليقات حتى الآن</div>';
    }
    
    let commentsHTML = '';
    
    comments.forEach(comment => {
        commentsHTML += `
            <div class="modal-comment" data-id="${comment.id}">
                <div class="modal-comment-header">
                    <div class="modal-comment-author">${comment.author_name || 'مستخدم'}</div>
                    <div class="modal-comment-date">${formatDate(comment.created_at)}</div>
                </div>
                <div class="modal-comment-content">${comment.content}</div>
                <div class="modal-comment-actions">
                    <button class="modal-comment-action like-comment ${comment.user_liked ? 'liked' : ''}" data-id="${comment.id}">
                        <i class="fas fa-heart"></i>
                        <span class="comment-like-count">${comment.likes_count}</span>
                    </button>
                    <button class="modal-comment-action reply-comment" data-id="${comment.id}">
                        <i class="fas fa-reply"></i>
                        <span>رد</span>
                    </button>
                </div>
            </div>
        `;
    });
    
    return commentsHTML;
}

/**
 * إعداد التفاعلات للتعليقات
 */
function setupCommentInteractions() {
    // أزرار الإعجاب بالتعليقات
    const likeCommentButtons = document.querySelectorAll('.like-comment');
    likeCommentButtons.forEach(button => {
        button.addEventListener('click', function() {
            const commentId = this.getAttribute('data-id');
            toggleCommentLike(commentId, this);
        });
    });
    
    // أزرار الرد على التعليقات (نضيف هذه الميزة لاحقًا)
    const replyCommentButtons = document.querySelectorAll('.reply-comment');
    replyCommentButtons.forEach(button => {
        button.addEventListener('click', function() {
            const commentId = this.getAttribute('data-id');
            // يمكن إضافة وظيفة الرد هنا
            alert('ميزة الرد على التعليقات قيد التطوير.');
        });
    });
}

/**
 * تبديل حالة الإعجاب بالتعليق
 * @param {number} commentId - معرف التعليق
 * @param {Element} button - زر الإعجاب
 */
function toggleCommentLike(commentId, button) {
    fetch(`/restricted/like-comment/${commentId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // تحديث زر الإعجاب بالتعليق
            const likeCountElement = button.querySelector('.comment-like-count');
            
            if (data.liked) {
                button.classList.add('liked');
            } else {
                button.classList.remove('liked');
            }
            
            // تحديث عدد الإعجابات
            if (likeCountElement) {
                likeCountElement.textContent = data.likes_count;
            }
        }
    })
    .catch(error => {
        console.error('خطأ أثناء تحديث الإعجاب بالتعليق:', error);
    });
}

/**
 * تنسيق التاريخ
 * @param {string} dateString - سلسلة التاريخ
 * @returns {string} التاريخ المنسق
 */
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    // إذا كان أقل من دقيقة
    if (diffSec < 60) {
        return 'منذ لحظات';
    }
    // إذا كان أقل من ساعة
    else if (diffMin < 60) {
        return `منذ ${diffMin} دقيقة`;
    }
    // إذا كان أقل من يوم
    else if (diffHour < 24) {
        return `منذ ${diffHour} ساعة`;
    }
    // إذا كان أقل من أسبوع
    else if (diffDay < 7) {
        return `منذ ${diffDay} يوم`;
    }
    // وإلا نعرض التاريخ بالكامل
    else {
        const day = date.getDate();
        const month = date.getMonth() + 1;
        const year = date.getFullYear();
        return `${day}/${month}/${year}`;
    }
}

/**
 * تعامل مع ضغط مفتاح Escape
 * @param {KeyboardEvent} event - حدث المفاتيح
 */
function handleEscapeKey(event) {
    if (event.key === 'Escape') {
        closePortfolioModal();
    }
}

/**
 * إغلاق النافذة المنبثقة
 */
function closePortfolioModal() {
    const modalOverlay = document.querySelector('.portfolio-modal-overlay');
    const modal = document.querySelector('.portfolio-modal');
    
    if (modalOverlay && modal) {
        // تطبيق تأثير الإغلاق التدريجي
        modal.style.transform = 'translateY(60px) scale(0.95)';
        modal.style.opacity = '0';
        
        // انتظار انتهاء التأثير قبل إخفاء النافذة تماماً
        setTimeout(() => {
            modalOverlay.classList.remove('active');
            document.body.style.overflow = ''; // إعادة تفعيل التمرير في الصفحة الخلفية
            
            // إعادة تعيين التنسيقات بعد إغلاق النافذة
            setTimeout(() => {
                modal.style.transform = '';
                modal.style.opacity = '';
            }, 300);
        }, 300); // وقت انتظار أقل من مدة التأثير في CSS لضمان انسيابية الحركة
    }
    
    // إزالة مستمع مفتاح Escape
    document.removeEventListener('keydown', handleEscapeKey);
}