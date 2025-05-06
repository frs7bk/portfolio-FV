// ملف JavaScript لمعرض الأعمال بأسلوب انستجرام

document.addEventListener('DOMContentLoaded', function() {
    // لا نقوم بمعالجة إرسال التعليق هنا، يتم معالجتها في comment-popup.js
    console.log('تم تحميل ملف instagram-gallery-modal.js');
    
    // تهيئة المتغيرات
    const galleryItems = document.querySelectorAll('.instagram-item');
    const filterButtons = document.querySelectorAll('.filter-item');
    const searchInput = document.getElementById('portfolio-search');
    const searchButton = document.getElementById('search-button');
    const clearSearch = document.getElementById('clear-search');
    const noResultsMessage = document.getElementById('no-results-message');
    const resetSearchButton = document.getElementById('reset-search');
    const searchResultsCounter = document.getElementById('search-results-counter');
    
    // تحميل عداد الإعجابات من الخادم عند البدء
    updateLikeCounts();
    
    // إضافة استماع لأحداث النقر للإعجاب
    document.querySelectorAll('.like-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const portfolioId = this.getAttribute('data-id');
            toggleLike(portfolioId, this);
        });
    });
    
    // إضافة استماع لأحداث النقر لعرض التعليقات
    document.querySelectorAll('.comment-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const portfolioId = this.getAttribute('data-id');
            openCommentsModal(portfolioId);
        });
    });

    // تحديث الفلتر النشط عند النقر
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // إزالة الفئة النشطة من جميع الأزرار
            filterButtons.forEach(btn => btn.classList.remove('active'));
            
            // إضافة الفئة النشطة للزر المحدد
            this.classList.add('active');
            
            // الحصول على الفئة المحددة
            const category = this.textContent.trim();
            
            // تطبيق الفلتر
            filterItems(category);
        });
    });

    // وظيفة الفلترة حسب الفئة
    function filterItems(category) {
        let visibleCount = 0;
        
        galleryItems.forEach(item => {
            const itemCategories = item.getAttribute('data-category').split(',');
            const searchValue = searchInput ? searchInput.value.toLowerCase() : '';
            const itemTitle = item.querySelector('img').getAttribute('alt').toLowerCase();
            
            // التحقق مما إذا كان العنصر يطابق فئة الفلتر وقيمة البحث (إن وجدت)
            let matchesCategory = (category === 'جميع الأعمال' || itemCategories.some(cat => cat.trim() === category));
            let matchesSearch = searchValue === '' || itemTitle.includes(searchValue);
            
            if (matchesCategory && matchesSearch) {
                item.classList.remove('hidden');
                visibleCount++;
            } else {
                item.classList.add('hidden');
            }
        });
        
        // إظهار رسالة "لا توجد نتائج" إذا لزم الأمر
        if (noResultsMessage) {
            if (visibleCount === 0) {
                noResultsMessage.classList.remove('hidden');
            } else {
                noResultsMessage.classList.add('hidden');
            }
        }
        
        // تحديث عداد نتائج البحث
        updateSearchResultsCounter(visibleCount);
    }

    // وظيفة البحث
    function searchItems() {
        if (!searchInput) return;
        
        const searchValue = searchInput.value.toLowerCase();
        
        // إظهار زر مسح البحث إذا كان هناك نص بحث
        if (clearSearch) {
            if (searchValue) {
                clearSearch.classList.remove('hidden');
            } else {
                clearSearch.classList.add('hidden');
            }
        }
        
        // الحصول على الفئة النشطة حاليًا
        const activeCategory = document.querySelector('.filter-item.active');
        if (activeCategory) {
            // إعادة تطبيق الفلتر مع البحث
            filterItems(activeCategory.textContent.trim());
        }
    }

    // أحداث البحث
    if (searchButton) {
        searchButton.addEventListener('click', searchItems);
    }
    
    if (searchInput) {
        searchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                searchItems();
            }
            
            // إظهار/إخفاء زر المسح حسب محتوى البحث
            if (clearSearch) {
                if (this.value) {
                    clearSearch.classList.remove('hidden');
                } else {
                    clearSearch.classList.add('hidden');
                    // إعادة تطبيق الفلتر بدون بحث
                    const activeCategory = document.querySelector('.filter-item.active');
                    if (activeCategory) {
                        filterItems(activeCategory.textContent.trim());
                    }
                }
            }
        });
    }
    
    // مسح البحث
    if (clearSearch) {
        clearSearch.addEventListener('click', function() {
            if (searchInput) {
                searchInput.value = '';
                clearSearch.classList.add('hidden');
                
                // إعادة تطبيق الفلتر بدون بحث
                const activeCategory = document.querySelector('.filter-item.active');
                if (activeCategory) {
                    filterItems(activeCategory.textContent.trim());
                }
            }
        });
    }
    
    // إعادة ضبط البحث
    if (resetSearchButton) {
        resetSearchButton.addEventListener('click', function() {
            if (searchInput) {
                searchInput.value = '';
            }
            
            if (clearSearch) {
                clearSearch.classList.add('hidden');
            }
            
            // إعادة تحديد "جميع الأعمال" كفئة نشطة
            if (filterButtons && filterButtons.length > 0) {
                filterButtons.forEach(btn => btn.classList.remove('active'));
                filterButtons[0].classList.add('active');
                
                // إعادة تطبيق الفلتر
                filterItems('جميع الأعمال');
            }
        });
    }

    // تحديث عداد نتائج البحث
    function updateSearchResultsCounter(count) {
        if (searchResultsCounter && searchInput) {
            if (count > 0 && searchInput.value) {
                searchResultsCounter.textContent = `تم العثور على ${count} نتيجة`;
                searchResultsCounter.classList.remove('hidden');
            } else {
                searchResultsCounter.classList.add('hidden');
            }
        }
    }

    // إضافة أو إزالة إعجاب لعنصر المحفظة
    function toggleLike(portfolioId, button) {
        fetch(`/portfolio/like/${portfolioId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const countElement = button.querySelector('.like-count');
                if (countElement) {
                    countElement.textContent = data.likes_count;
                }
                
                // تغيير أيقونة القلب حسب حالة الإعجاب
                const icon = button.querySelector('i');
                if (icon) {
                    if (data.action === 'added') {
                        icon.classList.remove('far');
                        icon.classList.add('fas');
                        icon.classList.add('text-red-500');
                    } else {
                        icon.classList.remove('fas');
                        icon.classList.remove('text-red-500');
                        icon.classList.add('far');
                    }
                }
            }
        })
        .catch(error => console.error('Error:', error));
    }

    // عرض صندوق حوار التعليقات
    function openCommentsModal(portfolioId) {
        const modalComments = document.getElementById('modal-comments');
        const modalCommentPortfolioId = document.getElementById('modal-comment-portfolio-id');
        const commentPortfolioId = document.getElementById('comment-portfolio-id');
        const modalItemId = document.getElementById('modal-item-id');
        
        // تعيين قيمة المعرف في النموذج الرئيسي
        if (modalCommentPortfolioId) {
            modalCommentPortfolioId.value = portfolioId;
        }
        
        // تعيين القيمة في نموذج التعليق المنبثق
        if (commentPortfolioId) {
            commentPortfolioId.value = portfolioId;
        }
        
        if (modalItemId) {
            modalItemId.value = portfolioId;
        }
        
        // تم إزالة كود جلب التعليقات لأن خاصية التعليقات تم إزالتها من التطبيق
        }
    }

    // تنسيق التاريخ للعرض
    function formatDate(dateString) {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('ar-SA', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(date);
    }

    // تحديث عدادات الإعجاب
    function updateLikeCounts() {
        const likeButtons = document.querySelectorAll('.like-btn');
        if (likeButtons.length === 0) return;
        
        // الحصول على معرفات جميع عناصر المحفظة
        const portfolioIds = Array.from(likeButtons).map(btn => btn.getAttribute('data-id'));
        
        // طلب عدادات الإعجاب والحالة للمستخدم الحالي
        fetch('/api/portfolio/likes-status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ ids: portfolioIds })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // تحديث كل زر إعجاب بالعدد والحالة
                likeButtons.forEach(btn => {
                    const portfolioId = btn.getAttribute('data-id');
                    const itemData = data.items[portfolioId];
                    
                    if (itemData) {
                        // تحديث النص
                        const countElement = btn.querySelector('.like-count');
                        if (countElement) {
                            countElement.textContent = itemData.count;
                        }
                        
                        // تحديث الأيقونة
                        const icon = btn.querySelector('i');
                        if (icon) {
                            if (itemData.liked) {
                                icon.classList.remove('far');
                                icon.classList.add('fas');
                                icon.classList.add('text-red-500');
                            } else {
                                icon.classList.remove('fas');
                                icon.classList.remove('text-red-500');
                                icon.classList.add('far');
                            }
                        }
                    }
                });
            }
        })
        .catch(error => console.error('Error updating like counts:', error));
    }

    // تحميل المزيد من العناصر
    const loadMoreBtn = document.getElementById('load-more-btn');
    let currentPage = 1;
    
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', function() {
            currentPage++;
            loadMoreItems(currentPage);
        });
        
        // التحقق إذا كان هناك صفحات أخرى
        checkMoreItemsAvailability();
    }
    
    // تحديث عدد العناصر في الإحصائيات
    const postsCountElement = document.getElementById('posts-count');
    if (postsCountElement) {
        postsCountElement.textContent = document.querySelectorAll('.instagram-item').length;
    }
    
    // تحميل المزيد من العناصر من الخادم
    function loadMoreItems(page) {
        loadMoreBtn.disabled = true;
        loadMoreBtn.textContent = 'جاري التحميل...';
        
        fetch(`/api/portfolio/items?page=${page}`)
            .then(response => response.json())
            .then(data => {
                if (data.items && data.items.length > 0) {
                    const feed = document.querySelector('.instagram-feed');
                    
                    // إضافة العناصر الجديدة إلى المعرض
                    data.items.forEach(item => {
                        const itemElement = createPortfolioItem(item);
                        feed.appendChild(itemElement);
                    });
                    
                    // تحديث عدد العناصر
                    if (postsCountElement) {
                        postsCountElement.textContent = document.querySelectorAll('.instagram-item').length;
                    }
                    
                    // إعادة تطبيق الفلتر النشط
                    const activeCategory = document.querySelector('.filter-item.active');
                    if (activeCategory) {
                        filterItems(activeCategory.textContent.trim());
                    }
                    
                    // إضافة أحداث للإعجاب والتعليقات
                    attachEvents();
                    
                    // التحقق من وجود صفحات إضافية
                    if (data.has_more) {
                        loadMoreBtn.disabled = false;
                        loadMoreBtn.textContent = 'تحميل المزيد';
                    } else {
                        loadMoreBtn.style.display = 'none';
                    }
                } else {
                    loadMoreBtn.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                loadMoreBtn.disabled = false;
                loadMoreBtn.textContent = 'حاول مرة أخرى';
            });
    }
    
    // إنشاء عنصر معرض جديد
    function createPortfolioItem(item) {
        const div = document.createElement('div');
        div.className = 'instagram-item';
        div.setAttribute('data-id', item.id);
        div.setAttribute('data-category', item.category);
        
        div.innerHTML = `
            <div class="instagram-image">
                <img src="${item.image_url}" alt="${item.title}">
                <div class="instagram-overlay">
                    <div class="overlay-content">
                        <div class="stats">
                            <span><i class="fas fa-heart"></i> ${item.likes_count}</span>
                            <span><i class="fas fa-eye"></i> ${item.views_count}</span>
                        </div>
                        <a href="#" class="view-details" data-id="${item.id}">عرض التفاصيل</a>
                    </div>
                </div>
            </div>
            <div class="instagram-caption">
                <h4>${item.title}</h4>
                <p class="category">${item.category}</p>
                <div class="actions">
                    <button class="like-btn" data-id="${item.id}">
                        <i class="far fa-heart"></i>
                        <span class="like-count">${item.likes_count}</span>
                    </button>
                </div>
            </div>
        `;
        
        return div;
    }
    
    // إرفاق الأحداث بعناصر المعرض
    function attachEvents() {
        // إضافة استماع لأحداث النقر للإعجاب
        document.querySelectorAll('.like-btn').forEach(btn => {
            if (!btn.hasEventListener) {
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    const portfolioId = this.getAttribute('data-id');
                    toggleLike(portfolioId, this);
                });
                btn.hasEventListener = true;
            }
        });
        
        // تم إزالة معالج الحدث لأزرار التعليقات
        
        // إضافة استماع لأحداث النقر لعرض التفاصيل
        document.querySelectorAll('.view-details').forEach(link => {
            if (!link.hasEventListener) {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    const portfolioId = this.getAttribute('data-id');
                    openPortfolioDetails(portfolioId);
                });
                link.hasEventListener = true;
            }
        });
    }
    
    // التحقق من وجود صفحات إضافية
    function checkMoreItemsAvailability() {
        fetch('/api/portfolio/has-more-items')
            .then(response => response.json())
            .then(data => {
                if (data.has_more) {
                    loadMoreBtn.disabled = false;
                } else {
                    loadMoreBtn.style.display = 'none';
                }
            })
            .catch(error => console.error('Error:', error));
    }
});