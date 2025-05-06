// نظام التعليقات المنبثق بتصميم جديد
document.addEventListener('DOMContentLoaded', function() {
    console.log('تم بدء تحميل نظام التعليقات الجديد');
    
    // نموذج الإدخال
    const commentForm = document.querySelector('#comment-form');
    
    // زر الإرسال
    const submitBtn = document.querySelector('#comment-submit');
    
    // زر إغلاق النموذج
    const closeModalBtns = document.querySelectorAll('.comment-modal-close');
    
    // زر إلغاء
    const cancelBtn = document.querySelector('#comment-cancel');
    
    // زر فتح النافذة
    const openCommentBtn = document.querySelector('#open-comment-modal-btn');
    
    // حقل التعليق الوهمي للنقر
    const commentPlaceholder = document.querySelector('#comment-placeholder');
    
    // الحقول داخل النموذج
    const nameField = document.querySelector('#comment-author');
    const emailField = document.querySelector('#comment-email');
    const contentField = document.querySelector('#comment-content');
    const portfolioIdField = document.querySelector('#comment-portfolio-id');
    
    // نافذة التعليقات
    const commentModal = document.querySelector('#comment-modal');
    
    // عنصر الرسائل
    const messageEl = document.querySelector('#comment-message');
    
    console.log('عناصر النموذج المكتشفة:', {
        form: !!commentForm,
        submitBtn: !!submitBtn,
        nameField: !!nameField,
        emailField: !!emailField,
        contentField: !!contentField,
        portfolioIdField: !!portfolioIdField
    });
    
    // إضافة مستمع أحداث النقر على زر فتح النافذة
    if (openCommentBtn) {
        openCommentBtn.addEventListener('click', function() {
            openCommentModal();
        });
    }
    
    // إضافة مستمع أحداث النقر على حقل التعليق الوهمي
    if (commentPlaceholder) {
        commentPlaceholder.addEventListener('click', function() {
            openCommentModal();
        });
    }
    
    // إضافة مستمع أحداث لأزرار إغلاق النافذة
    if (closeModalBtns) {
        closeModalBtns.forEach(function(btn) {
            btn.addEventListener('click', function() {
                closeCommentModal();
            });
        });
    }
    
    // إضافة مستمع أحداث لزر الإلغاء
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            closeCommentModal();
        });
    }
    
    // إضافة مستمع أحداث لزر إرسال النموذج
    if (submitBtn) {
        submitBtn.addEventListener('click', function(e) {
            e.preventDefault();
            submitForm();
        });
    }
    
    // إضافة مستمع أحداث لإرسال النموذج
    if (commentForm) {
        commentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitForm();
        });
    }
    
    /**
     * فتح نافذة التعليق
     */
    function openCommentModal() {
        if (!commentModal) return;
        
        // الحصول على معرف المشروع
        const portfolioId = document.querySelector('#modal-item-id')?.value;
        console.log('فتح نافذة التعليق للمشروع:', portfolioId);
        
        // تعيين معرف المشروع في النموذج
        if (portfolioIdField) {
            portfolioIdField.value = portfolioId;
        }
        
        // مسح الحقول
        if (nameField) nameField.value = '';
        if (emailField) emailField.value = '';
        if (contentField) contentField.value = '';
        
        // إخفاء أية رسائل خطأ
        if (messageEl) messageEl.style.display = 'none';
        
        // عرض النافذة
        commentModal.style.display = 'flex';
    }
    
    /**
     * إغلاق نافذة التعليق
     */
    function closeCommentModal() {
        if (commentModal) {
            commentModal.style.display = 'none';
        }
    }
    
    /**
     * إرسال نموذج التعليق
     * يتحقق من البيانات ثم يرسلها باستخدام Ajax
     */
    function submitForm() {
        console.log('محاولة إرسال التعليق...');
        
        // التحقق من الحقول
        if (!nameField || !emailField || !contentField || !portfolioIdField) {
            console.error('حقول النموذج غير موجودة');
            return;
        }
        
        // الحصول على القيم
        const author = nameField.value.trim();
        const email = emailField.value.trim();
        const content = contentField.value.trim();
        const portfolioId = portfolioIdField.value;
        
        // طباعة القيم للتشخيص
        console.log('بيانات النموذج:', {
            author: author,
            email: email,
            content: content ? content.substring(0, 20) + '...' : '', // طباعة جزء من المحتوى فقط
            portfolioId: portfolioId
        });
        
        // التحقق من اكتمال البيانات
        if (!author) {
            showMessage('يرجى إدخال اسمك', 'error');
            nameField.focus();
            return;
        }
        
        if (!email) {
            showMessage('يرجى إدخال بريدك الإلكتروني', 'error');
            emailField.focus();
            return;
        }
        
        if (!isValidEmail(email)) {
            showMessage('يرجى إدخال بريد إلكتروني صحيح', 'error');
            emailField.focus();
            return;
        }
        
        if (!content) {
            showMessage('يرجى إدخال التعليق', 'error');
            contentField.focus();
            return;
        }
        
        if (!portfolioId) {
            showMessage('لم يتم تحديد المشروع', 'error');
            return;
        }
        
        // إعداد بيانات النموذج
        const formData = new FormData();
        formData.append('name', author);
        formData.append('email', email);
        formData.append('content', content);
        formData.append('portfolio_id', portfolioId);
        
        // إظهار رسالة الانتظار
        showMessage('جاري إرسال التعليق...', 'info');
        
        // إرسال البيانات إلى الخادم
        console.log('إرسال التعليق للخادم...');
        
        fetch('/api/portfolio/comment/add', {
            method: 'POST',
            body: formData
        })
        .then(function(response) {
            if (!response.ok) {
                throw new Error('فشل الاتصال بالخادم: ' + response.status);
            }
            return response.json();
        })
        .then(function(data) {
            console.log('رد الخادم:', data);
            
            if (data.success) {
                // تم إرسال التعليق بنجاح
                showMessage('تم استلام تعليقك وسيتم مراجعته قبل النشر', 'success');
                
                // مسح حقل المحتوى
                contentField.value = '';
                
                // إغلاق النافذة تلقائيًا بعد 3 ثوان
                setTimeout(function() {
                    closeCommentModal();
                }, 3000);
            } else {
                // حدث خطأ في معالجة التعليق
                showMessage(data.message || 'حدث خطأ في معالجة التعليق', 'error');
            }
        })
        .catch(function(error) {
            console.error('خطأ في إرسال التعليق:', error);
            showMessage('حدث خطأ في الاتصال بالخادم', 'error');
        });
    }
    
    /**
     * التحقق من صحة البريد الإلكتروني
     */
    function isValidEmail(email) {
        const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(String(email).toLowerCase());
    }
    
    /**
     * عرض رسالة في النموذج
     */
    function showMessage(text, type) {
        if (!messageEl) return;
        
        // تعيين نص الرسالة
        messageEl.textContent = text;
        
        // تعيين نوع الرسالة
        messageEl.className = 'comment-message ' + type;
        
        // إظهار الرسالة
        messageEl.style.display = 'block';
    }
});