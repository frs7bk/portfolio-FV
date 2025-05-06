// نظام عرض الأعمال بتصميم إنستغرام (بدون تعليقات)
document.addEventListener('DOMContentLoaded', function() {
    // العناصر المهمة
    const portfolioModal = document.getElementById('portfolio-modal');
    const modalImage = document.getElementById('modal-image');
    const modalTitle = document.getElementById('modal-title');
    const modalCategory = document.getElementById('modal-category');
    const modalDescription = document.getElementById('modal-description');
    const modalLink = document.getElementById('modal-link');
    const modalLinkContainer = document.getElementById('modal-link-container');
    const modalDate = document.getElementById('modal-date');
    const modalLikes = document.getElementById('modal-likes');
    const modalViews = document.getElementById('modal-views');
    const modalItemId = document.getElementById('modal-item-id');
    const closeModal = document.getElementById('close-modal');
    const likeButton = document.getElementById('like-button');
    
    // أزرار الفلتر
    const filterButtons = document.querySelectorAll('.filter-item');
    
    // حقل البحث
    const searchInput = document.getElementById('search-input');
    const clearSearch = document.getElementById('clear-search');
    const resetSearchButton = document.getElementById('reset-search');
    const searchResultsCounter = document.getElementById('search-results-counter');
    
    // زر تحميل المزيد
    const loadMoreBtn = document.getElementById('load-more-btn');
    
    // ذاكرة مؤقتة للبيانات
    const cachedData = {};
    
    // إعداد البيانات المسبق
    preloadPortfolioData();
    
    // تحميل البيانات مسبقًا للعرض السريع
    function preloadPortfolioData() {
        const items = document.querySelectorAll('.instagram-item');
        console.log('تحميل مسبق لـ ' + items.length + ' مشروع');
        
        items.forEach(item => {
            const id = item.getAttribute('data-id');
            if (id) {
                fetch(`/api/portfolio/item/${id}/detail`)
                    .then(response => response.json())
                    .then(data => {
                        // تخزين البيانات مسبقاً
                        cachedData[id] = data;
                        
                        // تحميل الصورة مسبقاً
                        if (data.image_url) {
                            const preloadImg = new Image();
                            preloadImg.src = data.image_url;
                        }
                    })
                    .catch(err => {
                        console.error('خطأ في تحميل بيانات المشروع:', err);
                    });
            }
        });
    }
    
    // فتح نافذة تفاصيل المشروع
    function openPortfolioDetails(portfolioId) {
        if (cachedData[portfolioId]) {
            displayPortfolioItemData(cachedData[portfolioId]);
            portfolioModal.style.display = 'block';
            document.body.style.overflow = 'hidden'; // منع التمرير
            recordItemView(portfolioId);
            
        } else {
            getPortfolioItemData(portfolioId);
        }
        
        // تحديث المعرف الحالي
        modalItemId.value = portfolioId;
    }
    
    // إغلاق النافذة المنبثقة
    function closePortfolioModal() {
        portfolioModal.style.display = 'none';
        document.body.style.overflow = 'auto'; // إعادة السماح بالتمرير
    }
    
    // جلب بيانات المشروع من الخادم
    function getPortfolioItemData(portfolioId) {
        fetch(`/api/portfolio/item/${portfolioId}/detail`)
            .then(response => response.json())
            .then(data => {
                // تخزين في الذاكرة المؤقتة للاستخدام اللاحق
                cachedData[portfolioId] = data;
                
                // عرض البيانات
                displayPortfolioItemData(data);
                portfolioModal.style.display = 'block';
                document.body.style.overflow = 'hidden'; // منع التمرير
                
                // تسجيل المشاهدة
                recordItemView(portfolioId);
            })
            .catch(err => {
                console.error('خطأ في جلب بيانات المشروع:', err);
                alert('حدث خطأ أثناء تحميل بيانات المشروع. يرجى المحاولة مرة أخرى لاحقًا.');
            });
    }
    
    // عرض بيانات المشروع في النافذة المنبثقة
    function displayPortfolioItemData(data) {
        modalImage.src = data.image_url;
        modalTitle.textContent = data.title;
        modalCategory.textContent = data.category;
        modalDescription.innerHTML = data.description;
        modalDate.textContent = data.created_at;
        modalLikes.textContent = `${data.likes_count} إعجاب`;
        modalViews.textContent = `${data.views_count} مشاهدة`;
        
        // عرض الرابط إذا وجد
        if (data.link && data.link.trim() !== '') {
            modalLinkContainer.style.display = 'block';
            modalLink.href = data.link;
        } else {
            modalLinkContainer.style.display = 'none';
        }
        
        // تحديث حالة زر الإعجاب
        updateLikeButtonState(data.user_has_liked);
        
        // إعداد معرض الصور إذا وجد
        setupImageGallery(data);
    }
    
    // إعداد معرض الصور المتعددة إذا كان المشروع يحتوي على صور متعددة
    function setupImageGallery(data) {
        // يمكن إضافة معرض الصور هنا إذا كان المشروع يحتوي على صور متعددة
    }
    
    // تسجيل مشاهدة للمشروع
    function recordItemView(portfolioId) {
        fetch(`/api/portfolio/${portfolioId}/view`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // تحديث عداد المشاهدات
                modalViews.textContent = `${data.views_count} مشاهدة`;
                
                // تحديث عداد المشاهدات في القائمة
                updateItemStats(portfolioId, 'views', data.views_count);
            }
        })
        .catch(err => {
            console.error('خطأ في تسجيل المشاهدة:', err);
        });
    }
    
    // تحديث حالة زر الإعجاب
    function updateLikeButtonState(isLiked) {
        if (isLiked) {
            likeButton.innerHTML = '<i class="fas fa-heart"></i>';
            likeButton.classList.add('liked');
        } else {
            likeButton.innerHTML = '<i class="far fa-heart"></i>';
            likeButton.classList.remove('liked');
        }
    }
    
    // تصفية العناصر حسب الفئة
    function filterItems(category) {
        const portfolioItems = document.querySelectorAll('.instagram-item');
        let visibleCount = 0;
        
        portfolioItems.forEach(item => {
            const itemCategory = item.getAttribute('data-category');
            
            if (category === 'all' || itemCategory.includes(category)) {
                item.style.display = 'block';
                visibleCount++;
            } else {
                item.style.display = 'none';
            }
        });
        
        // تحديث عداد نتائج البحث
        updateSearchResultsCounter(visibleCount);
        
        // تحديث حالة زر تحميل المزيد
        checkMoreItemsAvailability();
    }
    
    // تحديث عداد نتائج البحث
    function updateSearchResultsCounter(count) {
        if (searchResultsCounter) {
            if (count === 0) {
                searchResultsCounter.textContent = 'لم يتم العثور على نتائج';
                searchResultsCounter.classList.remove('hidden');
            } else {
                searchResultsCounter.textContent = `تم العثور على ${count} مشروع`;
                searchResultsCounter.classList.remove('hidden');
            }
        }
    }
    
    // إعجاب/إلغاء إعجاب بمشروع
    function toggleLike(portfolioId, button) {
        const likeButton = button || likeButton;
        const isLiked = likeButton.classList.contains('liked');
        
        // تحديث واجهة المستخدم فوراً (optimistic update)
        if (isLiked) {
            likeButton.innerHTML = '<i class="far fa-heart"></i>';
            likeButton.classList.remove('liked');
        } else {
            likeButton.innerHTML = '<i class="fas fa-heart"></i>';
            likeButton.classList.add('liked');
            likeButton.classList.add('heart-anim');
            setTimeout(() => {
                likeButton.classList.remove('heart-anim');
            }, 500);
        }
        
        // إرسال الإعجاب للخادم
        fetch(`/api/portfolio/${portfolioId}/like`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // تحديث عداد الإعجابات في النافذة المنبثقة
                if (modalLikes) {
                    modalLikes.textContent = `${data.likes_count} إعجاب`;
                }
                
                // تحديث عداد الإعجابات في القائمة
                updateItemStats(portfolioId, 'likes', data.likes_count);
            } else {
                // إعادة حالة الزر كما كانت في حالة الخطأ
                updateLikeButtonState(!isLiked);
            }
        })
        .catch(err => {
            console.error('خطأ في تبديل حالة الإعجاب:', err);
            // إعادة حالة الزر كما كانت في حالة الخطأ
            updateLikeButtonState(!isLiked);
        });
    }
    
    // إعداد أحداث العناصر والأزرار
    function attachEvents() {
        // فتح تفاصيل المشروع عند النقر على العنصر
        document.querySelectorAll('.instagram-item').forEach(item => {
            item.addEventListener('click', function() {
                const portfolioId = this.getAttribute('data-id');
                openPortfolioDetails(portfolioId);
            });
        });
        
        // أزرار التصفية
        filterButtons.forEach(button => {
            button.addEventListener('click', function() {
                filterButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
                
                const category = this.getAttribute('data-category');
                filterItems(category);
            });
        });
        
        // زر الإعجاب في النافذة المنبثقة
        likeButton.addEventListener('click', function() {
            const portfolioId = modalItemId.value;
            toggleLike(portfolioId);
        });
        
        // زر الإغلاق للنافذة المنبثقة
        closeModal.addEventListener('click', closePortfolioModal);
        
        // زر البحث وحقل البحث
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                if (this.value.trim() !== '') {
                    clearSearch.classList.remove('hidden');
                } else {
                    clearSearch.classList.add('hidden');
                }
            });
            
            searchInput.addEventListener('keyup', function(e) {
                if (e.key === 'Enter') {
                    const query = this.value.trim().toLowerCase();
                    searchItems(query);
                }
            });
        }
        
        // زر مسح البحث
        if (clearSearch) {
            clearSearch.addEventListener('click', function() {
                searchInput.value = '';
                this.classList.add('hidden');
                resetFilters();
            });
        }
        
        // زر إعادة ضبط البحث
        if (resetSearchButton) {
            resetSearchButton.addEventListener('click', resetFilters);
        }
        
        // زر تحميل المزيد
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', function() {
                if (!this.disabled) {
                    loadMoreItems();
                }
            });
        }
        
        // إغلاق النافذة المنبثقة عند النقر خارجها
        portfolioModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closePortfolioModal();
            }
        });
        
        // إغلاق النافذة المنبثقة بمفتاح ESC
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && portfolioModal.style.display === 'block') {
                closePortfolioModal();
            }
        });
    }
    
    // تحميل المزيد من العناصر
    function loadMoreItems(page) {
        if (isLoading) return;
        
        isLoading = true;
        loadMoreBtn.textContent = 'جاري التحميل...';
        loadMoreBtn.disabled = true;
        
        const nextPage = page || currentPage + 1;
        
        fetch(`/api/portfolio/items?page=${nextPage}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.items.length > 0) {
                        // إضافة العناصر الجديدة للصفحة
                        const container = document.querySelector('.instagram-feed');
                        
                        data.items.forEach(item => {
                            const newItem = createPortfolioItem(item);
                            container.appendChild(newItem);
                            
                            // تحميل البيانات المسبق
                            cachedData[item.id] = item;
                        });
                        
                        // تحديث الصفحة الحالية
                        currentPage = nextPage;
                        
                        // استعادة حالة زر التحميل
                        loadMoreBtn.textContent = 'تحميل المزيد';
                        loadMoreBtn.disabled = false;
                        
                        // تحقق من وجود المزيد من العناصر
                        if (data.has_more) {
                            loadMoreBtn.style.display = 'block';
                        } else {
                            loadMoreBtn.style.display = 'none';
                        }
                        
                        // إضافة الأحداث للعناصر الجديدة
                        attachEvents();
                    } else {
                        loadMoreBtn.textContent = 'لا توجد مشاريع أخرى';
                        loadMoreBtn.disabled = true;
                    }
                } else {
                    console.error('خطأ في تحميل العناصر:', data.message);
                    loadMoreBtn.textContent = 'حاول مرة أخرى';
                    loadMoreBtn.disabled = false;
                }
                
                isLoading = false;
            })
            .catch(err => {
                console.error('خطأ في تحميل المزيد من العناصر:', err);
                loadMoreBtn.textContent = 'حاول مرة أخرى';
                loadMoreBtn.disabled = false;
                isLoading = false;
            });
    }
    
    // إنشاء عنصر مشروع جديد في HTML
    function createPortfolioItem(item) {
        const div = document.createElement('div');
        div.className = 'instagram-item';
        div.setAttribute('data-id', item.id);
        div.setAttribute('data-category', item.category);
        div.setAttribute('data-title', item.title);
        div.setAttribute('data-description', item.description);
        
        div.innerHTML = `
            <div class="item-image">
                <img src="${item.image_url}" alt="${item.title}" loading="lazy">
            </div>
            <div class="item-overlay">
                <div class="item-stats">
                    <div class="item-stat"><i class="fas fa-heart"></i> <span>${item.likes_count}</span></div>
                    <div class="item-stat"><i class="fas fa-eye"></i> <span>${item.views_count}</span></div>
                </div>
            </div>
        `;
        
        return div;
    }
    
    // التحقق من وجود المزيد من العناصر
    function checkMoreItemsAvailability() {
        // يمكن إضافة منطق هنا للتحقق من وجود المزيد من العناصر
    }
    
    // تحديث إحصائيات العنصر (الإعجابات، المشاهدات)
    function updateItemStats(itemId, statType, value) {
        const item = document.querySelector(`.instagram-item[data-id="${itemId}"]`);
        if (item) {
            let iconClass;
            switch (statType) {
                case 'likes':
                    iconClass = '.fa-heart';
                    break;
                case 'views':
                    iconClass = '.fa-eye';
                    break;
            }
            
            const statElement = item.querySelector(`.item-stat i${iconClass}`)?.parentNode;
            if (statElement) {
                statElement.querySelector('span').textContent = value;
            }
        }
    }
    
    // إعادة ضبط الفلاتر
    function resetFilters() {
        if (searchInput) searchInput.value = '';
        if (clearSearch) clearSearch.classList.add('hidden');
        if (searchResultsCounter) searchResultsCounter.classList.add('hidden');
        
        // إعادة تفعيل جميع العناصر
        document.querySelectorAll('.instagram-item').forEach(item => {
            item.style.display = 'block';
        });
        
        // إعادة ضبط أزرار التصفية
        filterButtons.forEach(btn => btn.classList.remove('active'));
        filterButtons[0]?.classList.add('active'); // تنشيط الزر الأول (الكل)
    }
    
    // البحث في العناصر
    function searchItems(query) {
        const portfolioItems = document.querySelectorAll('.instagram-item');
        let visibleCount = 0;
        
        if (!query) {
            resetFilters();
            return;
        }
        
        portfolioItems.forEach(item => {
            const title = item.getAttribute('data-title')?.toLowerCase() || '';
            const desc = item.getAttribute('data-description')?.toLowerCase() || '';
            const category = item.getAttribute('data-category')?.toLowerCase() || '';
            
            if (title.includes(query) || desc.includes(query) || category.includes(query)) {
                item.style.display = 'block';
                visibleCount++;
            } else {
                item.style.display = 'none';
            }
        });
        
        // تحديث عداد النتائج
        updateSearchResultsCounter(visibleCount);
    }
    
    // تهيئة الصفحة
    attachEvents();
});