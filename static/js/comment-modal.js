/**
 * نظام التعليقات المنبثق
 * هذا الملف يحتوي على وظائف JavaScript الخاصة بنظام التعليقات المنبثق
 */

// دالة للتحقق من صحة البريد الإلكتروني
function validateEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('تهيئة نظام التعليقات المنبثق');
    
    // عناصر نافذة التعليقات المنبثقة
    const commentModal = document.getElementById('comment-modal');
    const commentButton = document.getElementById('comment-button');
    const openCommentBtn = document.getElementById('open-comment-modal-btn');
    const commentPlaceholder = document.getElementById('comment-placeholder');
    const closeButtons = document.querySelector('.comment-modal-close');
    const cancelButton = document.getElementById('comment-cancel');
    const submitButton = document.getElementById('comment-submit');
    
    // إضافة مستمع لزر التعليق في شاشة تفاصيل المشروع
    if (commentButton) {
        commentButton.addEventListener('click', function() {
            console.log('تم النقر على زر التعليق');
            openCommentForm();
        });
    }
    
    // إضافة مستمع لزر النشر في حقل التعليق المصغر
    if (openCommentBtn) {
        openCommentBtn.addEventListener('click', function() {
            console.log('تم النقر على زر نشر التعليق');
            openCommentForm();
        });
    }
    
    // إضافة مستمع لحقل التعليق المصغر (النص)
    if (commentPlaceholder) {
        commentPlaceholder.addEventListener('click', function() {
            console.log('تم النقر على حقل التعليق');
            openCommentForm();
        });
    }
    
    // إضافة مستمع لزر الإغلاق
    if (closeButtons) {
        closeButtons.addEventListener('click', closeCommentForm);
    }
    
    // إضافة مستمع لزر الإلغاء
    if (cancelButton) {
        cancelButton.addEventListener('click', closeCommentForm);
    }
    
    // إضافة مستمع لزر إرسال التعليق
    if (submitButton) {
        submitButton.addEventListener('click', submitComment);
    }
    
    // فتح نافذة التعليق
    function openCommentForm() {
        // التأكد من وجود معرف المشروع
        const portfolioId = document.getElementById('modal-item-id').value;
        
        if (!portfolioId) {
            console.error('خطأ: معرف المشروع غير موجود');
            return;
        }
        
        console.log(`فتح نافذة التعليق للمشروع رقم: ${portfolioId}`);
        
        // تحديث معرف المشروع في نموذج التعليق
        document.getElementById('comment-portfolio-id').value = portfolioId;
        
        // مسح البيانات السابقة من النموذج
        document.getElementById('comment-author').value = '';
        document.getElementById('comment-email').value = '';
        document.getElementById('comment-content').value = '';
        
        // إخفاء رسائل الخطأ السابقة
        const messageElement = document.getElementById('comment-message');
        messageElement.className = 'comment-message';
        messageElement.style.display = 'none';
        
        // إظهار النافذة المنبثقة
        commentModal.classList.add('active');
    }
    
    // إغلاق نافذة التعليق
    function closeCommentForm() {
        console.log('إغلاق نافذة التعليق');
        commentModal.classList.remove('active');
    }
    
    // إرسال التعليق
    function submitComment() {
        console.log('محاولة إرسال تعليق جديد');
        
        const portfolioId = document.getElementById('comment-portfolio-id').value;
        const authorName = document.getElementById('comment-author').value.trim();
        const authorEmail = document.getElementById('comment-email').value.trim();
        const commentContent = document.getElementById('comment-content').value.trim();
        
        // التحقق من البيانات المدخلة
        if (!authorName) {
            showMessage('يرجى إدخال اسمك', 'error');
            return;
        }
        
        // التحقق من البريد الإلكتروني إذا تم إدخاله
        if (authorEmail && !validateEmail(authorEmail)) {
            showMessage('يرجى إدخال بريد إلكتروني صحيح', 'error');
            return;
        }
        
        // التحقق من محتوى التعليق
        if (!commentContent) {
            showMessage('يرجى إدخال نص التعليق', 'error');
            return;
        }
        
        // إظهار رسالة انتظار
        showMessage('جاري إرسال التعليق...', 'info');
        
        // إعداد البيانات
        const formData = new FormData();
        formData.append('name', authorName);
        formData.append('email', authorEmail);
        formData.append('content', commentContent);
        
        // الاتصال بالخادم
        fetch(`/portfolio/comment/${portfolioId}`, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            console.log('استجابة الخادم:', response.status);
            if (!response.ok) {
                throw new Error(`خطأ في الاتصال: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('بيانات الاستجابة:', data);
            
            if (data.success) {
                // نجاح إرسال التعليق
                showMessage('تم استلام تعليقك وسيتم مراجعته قبل النشر', 'success');
                
                // مسح محتوى التعليق
                document.getElementById('comment-content').value = '';
                
                // إغلاق النافذة بعد فترة
                setTimeout(() => {
                    closeCommentForm();
                }, 3000);
            } else {
                // فشل إرسال التعليق
                showMessage(data.message || 'حدث خطأ في إرسال التعليق', 'error');
            }
        })
        .catch(error => {
            console.error('خطأ:', error);
            showMessage('حدث خطأ في الاتصال بالخادم، يرجى المحاولة لاحقاً', 'error');
        });
    }
    
    // عرض رسالة للمستخدم
    function showMessage(message, type) {
        console.log(`عرض رسالة: ${message} (${type})`);
        
        const messageElement = document.getElementById('comment-message');
        messageElement.textContent = message;
        messageElement.className = 'comment-message';
        
        if (type === 'error') {
            messageElement.classList.add('error');
        } else if (type === 'success') {
            messageElement.classList.add('success');
        } else {
            messageElement.classList.add('info');
        }
        
        messageElement.style.display = 'block';
    }
});