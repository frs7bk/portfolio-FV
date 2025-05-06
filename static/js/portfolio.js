/**
 * Portfolio items functionality for viewing, liking, and commenting
 */

document.addEventListener('DOMContentLoaded', function() {
    // إضافة وظيفة البحث في معرض الأعمال
    initializePortfolioSearch();
    
    // تهيئة مكون تفاصيل المشروع
    initializeProjectDetailsModal();
    
    // Handle portfolio item viewing
    const portfolioItems = document.querySelectorAll('.gallery-item');
    if (portfolioItems.length > 0) {
        portfolioItems.forEach(item => {
            item.addEventListener('click', function() {
                const portfolioId = this.dataset.id;
                if (portfolioId) {
                    incrementViewCount(portfolioId);
                    openProjectDetailsModal(portfolioId);
                }
            });
        });
    }
    
    // إضافة مستمعي الأحداث للفلاتر
    const filterButtons = document.querySelectorAll('.filter-item');
    if (filterButtons.length > 0) {
        filterButtons.forEach(button => {
            button.addEventListener('click', function() {
                // إزالة الفئة النشطة من جميع الأزرار
                filterButtons.forEach(btn => btn.classList.remove('active'));
                // إضافة الفئة النشطة للزر المنقر عليه
                this.classList.add('active');
                
                // تطبيق الفلتر على العناصر
                const category = this.textContent.trim() === 'جميع الأعمال' ? 'all' : this.textContent.trim();
                filterPortfolioItems(category);
            });
        });
    }

    // Handle like button clicks
    const likeButtons = document.querySelectorAll('.like-btn');
    if (likeButtons.length > 0) {
        likeButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                const portfolioId = this.dataset.id;
                if (portfolioId) {
                    toggleLike(portfolioId, this);
                }
            });
        });
    }

    // Handle comment button clicks to open comment modal - في حالة وجود أزرار التعليق في الصفحة
    const commentButtons = document.querySelectorAll('.comment-btn');
    const commentModal = document.getElementById('comment-modal');
    
    if (commentButtons && commentButtons.length > 0 && commentModal) {
        commentButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                const portfolioId = this.dataset.id;
                if (portfolioId) {
                    // Set portfolio ID in the modal
                    const portfolioIdInput = document.getElementById('portfolio-id-input');
                    if (portfolioIdInput) {
                        portfolioIdInput.value = portfolioId;
                    }
                    
                    // Open comment modal
                    commentModal.classList.remove('hidden');
                    
                    // Load existing comments for this portfolio item
                    const commentsContainer = document.getElementById('comments-container');
                    if (commentsContainer) {
                        loadComments(portfolioId, commentsContainer);
                    }
                }
            });
        });
    }

    // Close comment modal when close button or overlay is clicked
    const modalCloseBtn = document.querySelector('.modal-close');
    const modalOverlay = document.querySelector('.modal-overlay');
    
    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', function() {
            document.getElementById('comment-modal').classList.add('hidden');
        });
    }
    
    if (modalOverlay) {
        modalOverlay.addEventListener('click', function(e) {
            if (e.target === this) {
                document.getElementById('comment-modal').classList.add('hidden');
            }
        });
    }

    // Handle comment form submission
    const commentForm = document.getElementById('comment-form');
    if (commentForm) {
        commentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const portfolioId = document.getElementById('portfolio-id-input').value;
            submitComment(portfolioId, this);
        });
    }

    // Initialize: update all view counts when page loads
    portfolioItems.forEach(item => {
        const portfolioId = item.dataset.id;
        if (portfolioId) {
            // Get view counts for all portfolio items
            fetch(`/api/portfolio-items/${portfolioId}/view`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const viewCountEl = document.querySelector(`.view-count[data-id="${portfolioId}"]`);
                    if (viewCountEl) {
                        viewCountEl.textContent = data.views_count;
                    }
                }
            })
            .catch(error => console.error('Error updating view count:', error));
        }
    });
});

/**
 * Increment the view count for a portfolio item
 * @param {number} portfolioId - Portfolio item ID
 */
function incrementViewCount(portfolioId) {
    fetch(`/api/portfolio-items/${portfolioId}/view`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const viewCountEl = document.querySelector(`.view-count[data-id="${portfolioId}"]`);
            if (viewCountEl) {
                viewCountEl.textContent = data.views_count;
            }
        }
    })
    .catch(error => console.error('Error updating view count:', error));
}

/**
 * Toggle like for a portfolio item
 * @param {number} portfolioId - Portfolio item ID
 * @param {HTMLElement} button - The like button element
 */
function toggleLike(portfolioId, button) {
    fetch(`/api/portfolio-items/${portfolioId}/like`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const likeCountEl = document.querySelector(`.like-count[data-id="${portfolioId}"]`);
            if (likeCountEl) {
                likeCountEl.textContent = data.likes_count;
            }
            
            // Update like button appearance
            if (data.liked) {
                button.classList.add('liked');
                button.querySelector('i').classList.remove('far');
                button.querySelector('i').classList.add('fas');
            } else {
                button.classList.remove('liked');
                button.querySelector('i').classList.remove('fas');
                button.querySelector('i').classList.add('far');
            }
        }
    })
    .catch(error => console.error('Error updating like status:', error));
}

/**
 * Load comments for a portfolio item
 * @param {number} portfolioId - Portfolio item ID
 * @param {HTMLElement} container - Comment container element
 */
function loadComments(portfolioId, container) {
    const commentsContainer = document.getElementById('comments-list');
    if (!commentsContainer) return;
    
    fetch(`/api/portfolio-items/${portfolioId}/comments`)
    .then(response => response.json())
    .then(data => {
        // API يمكن أن يرجع مباشرة مصفوفة التعليقات أو كائن يحتوي عليها
        const comments = Array.isArray(data) ? data : (data.comments || []);
            
        if (comments.length === 0) {
            commentsContainer.innerHTML = '<div class="text-center p-4 text-gray-400">لا توجد تعليقات بعد. كن أول من يعلق!</div>';
            return;
        }
        
        commentsContainer.innerHTML = '';
        comments.forEach(comment => {
                const commentEl = document.createElement('div');
                commentEl.className = 'border-b border-gray-700 p-4 last:border-0';
                commentEl.innerHTML = `
                    <div class="flex justify-between mb-2">
                        <strong class="font-bold text-white">${comment.name}</strong>
                        <span class="text-gray-400 text-sm">${comment.created_at}</span>
                    </div>
                    <div class="text-gray-300">${comment.content}</div>
                `;
                commentsContainer.appendChild(commentEl);
            });
            
            // Update comment count
        const commentCountEl = document.querySelector(`.comment-count[data-id="${portfolioId}"]`);
        if (commentCountEl) {
            commentCountEl.textContent = comments.length;
        }
    })
    .catch(error => console.error('Error loading comments:', error));
}

/**
 * Submit a new comment
 * @param {number} portfolioId - Portfolio item ID
 * @param {HTMLFormElement} form - Comment form element
 */
function submitComment(portfolioId, form) {
    const nameInput = form.querySelector('input[name="name"]');
    const emailInput = form.querySelector('input[name="email"]');
    const contentInput = form.querySelector('textarea[name="content"]');
    const submitButton = form.querySelector('button[type="submit"]');
    
    if (!nameInput || !contentInput) return;
    
    const name = nameInput.value.trim();
    const email = emailInput ? emailInput.value.trim() : '';
    const content = contentInput.value.trim();
    
    if (!name || !content) {
        showFormMessage(form, 'يرجى تعبئة جميع الحقول المطلوبة', 'error');
        return;
    }
    
    // تعطيل زر الإرسال
    if (submitButton) {
        submitButton.disabled = true;
    }
    
    fetch(`/api/portfolio-items/${portfolioId}/comments`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
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
            // Clear form
            nameInput.value = '';
            if (emailInput) emailInput.value = '';
            contentInput.value = '';
            
            // إظهار صندوق نجاح متميز
            const modalBody = form.closest('.modal-content').querySelector('.modal-body');
            if (modalBody) {
                // حفظ المحتوى الأصلي
                const originalContent = modalBody.innerHTML;
                
                // إنشاء رسالة النجاح
                modalBody.innerHTML = `
                    <div class="text-center p-4">
                        <div class="mb-4">
                            <i class="fas fa-check-circle text-green-500 text-5xl"></i>
                        </div>
                        <h4 class="text-xl font-bold mb-3">تم إرسال تعليقك بنجاح!</h4>
                        <p class="mb-4">${data.message || 'تم إرسال تعليقك بنجاح وهو قيد المراجعة الآن'}</p>
                    </div>
                `;
                
                // إعادة المحتوى الأصلي بعد 4 ثوان وإغلاق النافذة
                setTimeout(() => {
                    modalBody.innerHTML = originalContent;
                    document.getElementById('comment-modal').classList.add('hidden');
                    // إعادة تمكين الزر
                    if (submitButton) {
                        submitButton.disabled = false;
                        submitButton.innerHTML = 'إرسال التعليق';
                    }
                }, 4000);
            } else {
                // عرض رسالة النجاح العادية إذا لم نتمكن من تغيير المودال
                showFormMessage(form, data.message || 'تم إرسال تعليقك بنجاح وهو قيد المراجعة الآن', 'success');
                
                // إخفاء النافذة المنبثقة بعد ٣ ثوان
                setTimeout(() => {
                    document.getElementById('comment-modal').classList.add('hidden');
                    // إعادة تمكين الزر
                    if (submitButton) {
                        submitButton.disabled = false;
                        submitButton.innerHTML = 'إرسال التعليق';
                    }
                }, 3000);
            }
        } else {
            // استعادة حالة الزر
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = 'إرسال التعليق';
            }
            showFormMessage(form, data.message || 'حدث خطأ أثناء إرسال التعليق', 'error');
        }
    })
    .catch(error => {
        console.error('Error submitting comment:', error);
        // استعادة حالة الزر
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.innerHTML = 'إرسال التعليق';
        }
        showFormMessage(form, 'حدث خطأ في النظام، يرجى المحاولة مرة أخرى', 'error');
    });
}

/**
 * Show a message in the form
 * @param {HTMLFormElement} form - Comment form element
 * @param {string} message - Message to display
 * @param {string} type - Message type: 'success' or 'error'
 */
function showFormMessage(form, message, type) {
    const formMessage = document.getElementById('form-message');
    if (!formMessage) return;
    
    formMessage.textContent = message;
    formMessage.className = `mt-4 p-2 rounded ${type === 'success' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}`;
    
    // Make sure form message is visible
    formMessage.classList.remove('hidden');
    
    // Clear message after a delay for success messages
    if (type === 'success') {
        setTimeout(() => {
            formMessage.textContent = '';
            formMessage.classList.add('hidden');
        }, 5000);
    }
}

/**
 * تهيئة مكون عرض تفاصيل المشروع
 */
function initializeProjectDetailsModal() {
    const modal = document.getElementById('project-details-modal');
    const closeBtn = document.getElementById('close-project-modal');
    const backdrop = document.getElementById('project-modal-backdrop');
    const commentBtn = document.getElementById('project-comment-btn');
    const likeBtn = document.getElementById('project-like-btn');
    
    if (!modal || !closeBtn) return;
    
    // إغلاق المودال عند النقر على زر الإغلاق
    closeBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
    });
    
    // إغلاق المودال عند النقر على الخلفية
    if (backdrop) {
        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) {
                modal.classList.add('hidden');
            }
        });
    }
    
    // إضافة حدث النقر على زر التعليق في المودال
    if (commentBtn) {
        commentBtn.addEventListener('click', () => {
            const portfolioId = commentBtn.dataset.id;
            if (portfolioId) {
                // إغلاق مودال التفاصيل
                modal.classList.add('hidden');
                
                // فتح مودال التعليق
                const commentModal = document.getElementById('comment-modal');
                const portfolioIdInput = document.getElementById('portfolio-id-input');
                
                if (commentModal && portfolioIdInput) {
                    portfolioIdInput.value = portfolioId;
                    commentModal.classList.remove('hidden');
                    
                    // تحميل التعليقات الحالية
                    const commentsContainer = document.getElementById('comments-container');
                    if (commentsContainer) {
                        loadComments(portfolioId, commentsContainer);
                    }
                }
            }
        });
    }
    
    // إضافة حدث النقر على زر الإعجاب في المودال
    if (likeBtn) {
        likeBtn.addEventListener('click', () => {
            const portfolioId = likeBtn.dataset.id;
            if (portfolioId) {
                toggleLike(portfolioId, likeBtn);
            }
        });
    }
}

/**
 * فتح مودال تفاصيل المشروع وعرض البيانات
 * @param {number} portfolioId - معرف المشروع
 */
function openProjectDetailsModal(portfolioId) {
    const modal = document.getElementById('project-details-modal');
    
    if (!modal || !portfolioId) return;
    
    // احضار بيانات المشروع من الخادم
    fetch(`/api/portfolio-items/${portfolioId}`)
        .then(response => response.json())
        .then(data => {
            // تحديث بيانات المودال
            updateProjectDetailsModal(data);
            
            // إظهار المودال
            modal.classList.remove('hidden');
        })
        .catch(error => {
            console.error('Error loading project details:', error);
        });
}

/**
 * تحديث بيانات مودال تفاصيل المشروع
 * @param {Object} project - بيانات المشروع
 */
function updateProjectDetailsModal(project) {
    // العناصر الأساسية في المودال
    const mainImage = document.getElementById('project-main-image');
    const title = document.getElementById('project-title');
    const description = document.getElementById('project-description');
    const categories = document.getElementById('project-categories');
    const year = document.getElementById('project-year');
    const views = document.getElementById('project-views');
    const likes = document.getElementById('project-likes');
    const likeBtn = document.getElementById('project-like-btn');
    const commentBtn = document.getElementById('project-comment-btn');
    const carouselContainer = document.getElementById('project-carousel-container');
    const carouselGallery = document.getElementById('project-carousel-gallery');
    
    // تحديث العناصر بالبيانات
    if (mainImage) mainImage.src = project.image_url;
    if (mainImage) mainImage.alt = project.title;
    if (title) title.textContent = project.title;
    if (description) description.textContent = project.description;
    if (year) year.textContent = project.year || '';
    if (views) views.textContent = project.views_count || 0;
    if (likes) likes.textContent = project.likes_count || 0;
    
    // تحديث التصنيفات
    if (categories) {
        categories.innerHTML = '';
        const cats = project.category ? project.category.split(',') : [];
        cats.forEach(cat => {
            const span = document.createElement('span');
            span.className = 'bg-gray-700 text-yellow-400 px-3 py-1 rounded-full text-sm';
            span.textContent = cat.trim();
            categories.appendChild(span);
        });
    }
    
    // تحديث أزرار التفاعل
    if (likeBtn) likeBtn.dataset.id = project.id;
    if (commentBtn) commentBtn.dataset.id = project.id;
    
    // تحديث معرض الصور (الكاروسيل)
    if (carouselGallery) {
        carouselGallery.innerHTML = '';
        
        // إضافة الصورة الرئيسية كأول صورة
        const mainImageThumb = document.createElement('div');
        mainImageThumb.className = 'cursor-pointer rounded-lg overflow-hidden border-2 border-yellow-500';
        mainImageThumb.innerHTML = `<img src="${project.image_url}" alt="${project.title}" class="w-full h-16 object-cover">`;
        carouselGallery.appendChild(mainImageThumb);
        
        // عند النقر على الصورة الرئيسية المصغرة
        mainImageThumb.addEventListener('click', () => {
            if (mainImage) {
                mainImage.src = project.image_url;
                mainImage.alt = project.title;
                
                // إزالة التحديد من كل الصور
                const allThumbs = carouselGallery.querySelectorAll('div');
                allThumbs.forEach(thumb => thumb.classList.remove('border-yellow-500'));
                
                // تحديد الصورة الحالية
                mainImageThumb.classList.add('border-yellow-500');
            }
        });
        
        // إضافة صور الكاروسيل إذا كانت موجودة
        if (project.carousel_images) {
            let carouselImages = project.carousel_images;
            
            // تحويل من سلسلة JSON إلى مصفوفة إذا كانت سلسلة
            if (typeof project.carousel_images === 'string') {
                try {
                    carouselImages = JSON.parse(project.carousel_images);
                } catch (e) {
                    console.error('Error parsing carousel images:', e);
                }
            }
            
            if (Array.isArray(carouselImages) && carouselImages.length > 0) {
                carouselImages.forEach(image => {
                    // التعامل مع الصور بتنسيقين مختلفين (كائن مع url أو مسار مباشر)
                    const imageSrc = image.url || image;
                    if (!imageSrc) return;
                    
                    const imageThumb = document.createElement('div');
                    imageThumb.className = 'cursor-pointer rounded-lg overflow-hidden border-2 border-transparent';
                    imageThumb.innerHTML = `<img src="${imageSrc}" alt="${(image.caption || project.title)}" class="w-full h-16 object-cover">`;
                    carouselGallery.appendChild(imageThumb);
                    
                    // عند النقر على صورة مصغرة من الكاروسيل
                    imageThumb.addEventListener('click', () => {
                        if (mainImage) {
                            mainImage.src = imageSrc;
                            mainImage.alt = (image.caption || project.title);
                            
                            // إزالة التحديد من كل الصور
                            const allThumbs = carouselGallery.querySelectorAll('div');
                            allThumbs.forEach(thumb => thumb.classList.remove('border-yellow-500'));
                            
                            // تحديد الصورة الحالية
                            imageThumb.classList.add('border-yellow-500');
                        }
                    });
                });
                
                // إظهار قسم الكاروسيل
                if (carouselContainer) {
                    carouselContainer.classList.remove('hidden');
                }
            } else {
                // إخفاء قسم الكاروسيل إذا لم تكن هناك صور
                if (carouselContainer) {
                    carouselContainer.classList.add('hidden');
                }
            }
        } else {
            // إخفاء قسم الكاروسيل إذا لم تكن هناك صور
            if (carouselContainer) {
                carouselContainer.classList.add('hidden');
            }
        }
    }
}

/**
 * تهيئة وظيفة البحث في مشاريع البورتفوليو
 */
function initializePortfolioSearch() {
    const searchInput = document.getElementById('portfolio-search');
    const clearSearchBtn = document.getElementById('clear-search');
    const searchButton = document.getElementById('search-button');
    const yearFilter = document.getElementById('year-filter');
    const searchResultsCounter = document.getElementById('search-results-counter');
    const resetSearchBtn = document.getElementById('reset-search');
    const noResultsMessage = document.getElementById('no-results-message');
    
    if (!searchInput || !clearSearchBtn || !searchButton) return;
    
    // إضافة مستمع الحدث لزر البحث
    searchButton.addEventListener('click', function() {
        const searchTerm = searchInput.value.trim();
        const selectedYear = yearFilter.value;
        searchPortfolioItems(searchTerm, selectedYear);
    });
    
    // إضافة مستمع الحدث لمفتاح الإدخال في حقل البحث
    searchInput.addEventListener('keyup', function(e) {
        // تنفيذ البحث عند الضغط على Enter
        if (e.key === 'Enter') {
            const searchTerm = searchInput.value.trim();
            const selectedYear = yearFilter.value;
            searchPortfolioItems(searchTerm, selectedYear);
        }
        
        // إظهار أو إخفاء زر المسح بناءً على وجود نص في حقل البحث
        if (searchInput.value.trim() !== '') {
            clearSearchBtn.classList.remove('hidden');
        } else {
            clearSearchBtn.classList.add('hidden');
        }
    });
    
    // إضافة مستمع الحدث لزر مسح البحث
    clearSearchBtn.addEventListener('click', function() {
        searchInput.value = '';
        clearSearchBtn.classList.add('hidden');
        resetSearch();
    });
    
    // إضافة مستمع الحدث لزر إعادة ضبط البحث
    if (resetSearchBtn) {
        resetSearchBtn.addEventListener('click', resetSearch);
    }
}

/**
 * البحث في مشاريع البورتفوليو
 * @param {string} searchTerm - نص البحث
 * @param {string} year - السنة المحددة للفلترة
 */
function searchPortfolioItems(searchTerm, year) {
    const portfolioItems = document.querySelectorAll('.gallery-item');
    const searchResultsCounter = document.getElementById('search-results-counter');
    const noResultsMessage = document.getElementById('no-results-message');
    
    if (!portfolioItems.length) return;
    
    searchTerm = searchTerm.toLowerCase();
    let matchCount = 0;
    
    portfolioItems.forEach(item => {
        const title = item.querySelector('h3')?.textContent.toLowerCase() || '';
        const description = item.querySelector('p')?.textContent.toLowerCase() || '';
        const tags = Array.from(item.querySelectorAll('.tag')).map(tag => tag.textContent.toLowerCase());
        const itemYear = item.querySelector('.text-yellow-400.text-sm')?.textContent.trim() || '';
        
        // تحقق مما إذا كان العنصر يطابق معايير البحث
        const matchesSearch = searchTerm === '' || 
            title.includes(searchTerm) || 
            description.includes(searchTerm) || 
            tags.some(tag => tag.includes(searchTerm));
            
        // تحقق مما إذا كان العنصر يطابق فلتر السنة
        const matchesYear = year === '' || itemYear === year;
        
        // إخفاء أو إظهار العنصر بناءً على نتائج البحث
        if (matchesSearch && matchesYear) {
            item.classList.remove('hidden');
            matchCount++;
        } else {
            item.classList.add('hidden');
        }
    });
    
    // تحديث عداد نتائج البحث
    if (searchResultsCounter) {
        if (searchTerm !== '' || year !== '') {
            searchResultsCounter.classList.remove('hidden');
            searchResultsCounter.textContent = `تم العثور على ${matchCount} مشروع`;
        } else {
            searchResultsCounter.classList.add('hidden');
        }
    }
    
    // إظهار رسالة عدم وجود نتائج إذا لم يتم العثور على تطابقات
    if (noResultsMessage) {
        if (matchCount === 0 && (searchTerm !== '' || year !== '')) {
            noResultsMessage.classList.remove('hidden');
        } else {
            noResultsMessage.classList.add('hidden');
        }
    }
}

/**
 * إعادة ضبط البحث وإظهار جميع المشاريع
 */
function resetSearch() {
    const searchInput = document.getElementById('portfolio-search');
    const yearFilter = document.getElementById('year-filter');
    const searchResultsCounter = document.getElementById('search-results-counter');
    const noResultsMessage = document.getElementById('no-results-message');
    const portfolioItems = document.querySelectorAll('.gallery-item');
    
    // إعادة ضبط قيم حقول البحث
    if (searchInput) searchInput.value = '';
    if (yearFilter) yearFilter.value = '';
    
    // إخفاء عداد نتائج البحث ورسالة عدم وجود نتائج
    if (searchResultsCounter) searchResultsCounter.classList.add('hidden');
    if (noResultsMessage) noResultsMessage.classList.add('hidden');
    
    // إظهار جميع العناصر
    portfolioItems.forEach(item => {
        item.classList.remove('hidden');
    });
}

/**
 * فلترة مشاريع البورتفوليو حسب الفئة مع تأثيرات انتقالية محسنة
 * @param {string} category - فئة المشاريع المراد عرضها
 */
function filterPortfolioItems(category) {
    const portfolioItems = document.querySelectorAll('.gallery-item, .portfolio-item');
    const container = document.querySelector('.portfolio-grid') || document.getElementById('gallery-container');
    let visibleCount = 0;
    
    // تعليم الكونتينر لمنع تفاعلات المستخدم أثناء الانتقال
    if (container) {
        container.style.pointerEvents = 'none';
    }
    
    // تحديد العناصر التي ستظهر/تختفي أولاً
    const itemsToShow = [];
    const itemsToHide = [];
    
    // فرز العناصر حسب الرؤية
    portfolioItems.forEach(item => {
        if (category === 'all') {
            itemsToShow.push(item);
        } else {
            const itemCategory = item.dataset.category || '';
            const tagsText = Array.from(item.querySelectorAll('.tag'))
                .map(tag => tag.textContent.toLowerCase())
                .join(' ');
                
            // تحقق من وجود الفئة في عنوان العنصر أو الوسوم
            const title = item.querySelector('h3')?.textContent.toLowerCase() || '';
            const matchesCategory = 
                itemCategory === category.toLowerCase() || 
                tagsText.includes(category.toLowerCase()) ||
                title.includes(category.toLowerCase());
                
            if (matchesCategory) {
                itemsToShow.push(item);
            } else {
                itemsToHide.push(item);
            }
        }
    });
    
    // تطبيق تأثير التلاشي على العناصر المخفية أولاً
    itemsToHide.forEach(item => {
        // إضافة فئة تلاشي مع تغيير في translateY
        item.style.opacity = '1';
        item.style.transform = 'translateY(0)';
        
        setTimeout(() => {
            item.style.opacity = '0';
            item.style.transform = 'translateY(20px)';
            
            // بعد انتهاء الانتقال، إضافة hidden
            setTimeout(() => {
                item.classList.add('hidden');
                item.style.opacity = '';
                item.style.transform = '';
            }, 200);
        }, 10);
    });
    
    // الانتظار قليلاً ثم إظهار العناصر المطلوبة
    setTimeout(() => {
        // تأخير قصير ثم إظهار العناصر الجديدة بتأثير انتقالي
        itemsToShow.forEach((item, index) => {
            // إعادة تعيين الستايل أولاً
            item.style.opacity = '0';
            item.style.transform = 'translateY(20px)';
            item.classList.remove('hidden');
            
            // تأخير تدريجي للعناصر لتحقيق تأثير متتالي
            setTimeout(() => {
                item.style.opacity = '1';
                item.style.transform = 'translateY(0)';
                visibleCount++;
                
                // بعد انتهاء الانتقال، إزالة ستايل الانتقال
                setTimeout(() => {
                    item.style.opacity = '';
                    item.style.transform = '';
                    
                    // تفعيل التفاعل مع الكونتينر بعد انتهاء آخر عنصر
                    if (index === itemsToShow.length - 1 && container) {
                        container.style.pointerEvents = '';
                    }
                }, 300);
            }, index * 50); // تأخير تدريجي بين كل عنصر
        });
    }, 250);
    
    // إعادة ضبط نص البحث والفلاتر الأخرى
    const searchInput = document.getElementById('portfolio-search');
    const yearFilter = document.getElementById('year-filter');
    const searchResultsCounter = document.getElementById('search-results-counter');
    
    if (searchInput) searchInput.value = '';
    if (yearFilter) yearFilter.value = '';
    if (searchResultsCounter) searchResultsCounter.classList.add('hidden');
}