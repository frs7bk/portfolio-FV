/**
 * نظام التعليقات ونافذة إدخال اسم المعلق
 * 
 * هذا الملف يحتوي على الوظائف المسؤولة عن:
 * 1. إدارة التعليقات (إضافة، عرض، إعجاب)
 * 2. إدارة نافذة إدخال اسم المعلق المنبثقة
 * 3. حفظ اسم المعلق في متصفح المستخدم
 */

// متغيرات عامة
let commenterNamePopup = null;
let commenterNameInput = null;
let errorMsg = null;
let isLoggedIn = false; // يتم تعيينها من الصفحة

// تهيئة نافذة اسم المعلق عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    console.log("تهيئة نظام التعليقات ونافذة اسم المعلق...");
    
    // التحقق من حالة تسجيل دخول المستخدم
    isLoggedIn = document.body.getAttribute('data-user-logged-in') === 'true';
    console.log("حالة تسجيل دخول المستخدم:", isLoggedIn);
    
    // إنشاء نافذة إدخال اسم المعلق المنبثقة
    createCommenterNamePopup();
    
    // ربط الأحداث بالعناصر
    bindCommentEvents();
    
    // إضافة زر اختبار في وضع التطوير
    if (window.location.hostname === 'localhost' || window.location.hostname.includes('replit')) {
        addTestButton();
    }
});

/**
 * إنشاء نافذة إدخال اسم المعلق المنبثقة
 */
function createCommenterNamePopup() {
    // إذا كانت النافذة موجودة بالفعل، نخرج من الدالة
    if (document.getElementById('new-commenter-name-popup')) {
        console.log("النافذة المنبثقة موجودة بالفعل");
        return;
    }
    
    console.log("إنشاء نافذة اسم المعلق المنبثقة...");
    
    // إنشاء عناصر النافذة
    commenterNamePopup = document.createElement('div');
    commenterNamePopup.id = 'new-commenter-name-popup';
    commenterNamePopup.className = 'new-popup-overlay';
    
    const popupContent = document.createElement('div');
    popupContent.className = 'new-popup-content';
    
    // ترويسة النافذة
    const header = document.createElement('div');
    header.className = 'new-popup-header';
    
    const title = document.createElement('h3');
    title.textContent = 'أدخل اسمك';
    
    const closeBtn = document.createElement('button');
    closeBtn.className = 'new-popup-close';
    closeBtn.innerHTML = '&times;';
    closeBtn.setAttribute('type', 'button');
    closeBtn.addEventListener('click', closeNamePopup);
    
    header.appendChild(title);
    header.appendChild(closeBtn);
    
    // وصف النافذة
    const description = document.createElement('p');
    description.className = 'new-popup-description';
    description.textContent = 'سيظهر هذا الاسم مع تعليقك ويتم حفظه للمرات القادمة';
    
    // حقل إدخال الاسم
    const inputContainer = document.createElement('div');
    inputContainer.className = 'new-popup-input-container';
    
    const inputLabel = document.createElement('label');
    inputLabel.setAttribute('for', 'new-commenter-name');
    inputLabel.textContent = 'الاسم';
    
    commenterNameInput = document.createElement('input');
    commenterNameInput.id = 'new-commenter-name';
    commenterNameInput.className = 'new-popup-input';
    commenterNameInput.setAttribute('type', 'text');
    commenterNameInput.setAttribute('placeholder', 'أدخل اسمك هنا...');
    commenterNameInput.setAttribute('maxlength', '50');
    commenterNameInput.setAttribute('autocomplete', 'off');
    
    // إضافة مستمع حدث عند الضغط على مفتاح Enter
    commenterNameInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            saveCommenterName();
        }
    });
    
    // إضافة مستمع حدث لإزالة الإشارات المرئية للخطأ عند الكتابة
    commenterNameInput.addEventListener('input', function() {
        this.classList.remove('new-input-error');
        if (errorMsg) {
            errorMsg.style.display = 'none';
        }
    });
    
    // إنشاء عنصر لرسالة الخطأ
    errorMsg = document.createElement('p');
    errorMsg.className = 'new-error-message';
    errorMsg.textContent = 'يرجى إدخال اسمك قبل المتابعة';
    errorMsg.style.display = 'none';
    
    inputContainer.appendChild(inputLabel);
    inputContainer.appendChild(commenterNameInput);
    inputContainer.appendChild(errorMsg);
    
    // أزرار النافذة
    const buttonsContainer = document.createElement('div');
    buttonsContainer.className = 'new-popup-buttons';
    
    const saveBtn = document.createElement('button');
    saveBtn.id = 'new-save-commenter-name';
    saveBtn.className = 'new-popup-save-btn';
    saveBtn.setAttribute('type', 'button');
    saveBtn.textContent = 'حفظ';
    saveBtn.addEventListener('click', saveCommenterName);
    
    const cancelBtn = document.createElement('button');
    cancelBtn.id = 'new-cancel-popup';
    cancelBtn.className = 'new-popup-cancel-btn';
    cancelBtn.setAttribute('type', 'button');
    cancelBtn.textContent = 'إلغاء';
    cancelBtn.addEventListener('click', closeNamePopup);
    
    buttonsContainer.appendChild(saveBtn);
    buttonsContainer.appendChild(cancelBtn);
    
    // تجميع عناصر النافذة
    popupContent.appendChild(header);
    popupContent.appendChild(description);
    popupContent.appendChild(inputContainer);
    popupContent.appendChild(buttonsContainer);
    commenterNamePopup.appendChild(popupContent);
    
    // إضافة مستمع حدث لإغلاق النافذة عند النقر خارجها
    commenterNamePopup.addEventListener('click', function(e) {
        if (e.target === this) {
            closeNamePopup();
        }
    });
    
    // إضافة النافذة إلى الصفحة
    document.body.appendChild(commenterNamePopup);
    
    // إضافة الأنماط CSS الخاصة بالنافذة
    addPopupStyles();
    
    console.log("تم إنشاء نافذة اسم المعلق المنبثقة بنجاح");
}

/**
 * إضافة أنماط CSS الخاصة بالنافذة المنبثقة
 */
function addPopupStyles() {
    console.log("إضافة أنماط CSS لنافذة اسم المعلق...");
    
    const style = document.createElement('style');
    style.textContent = `
        /* أنماط النافذة المنبثقة الجديدة */
        .new-popup-overlay {
            display: none;
            position: fixed;
            z-index: 9999;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0, 0, 0, 0.85);
            backdrop-filter: blur(8px);
            animation: newFadeIn 0.3s ease;
        }
        
        .new-popup-content {
            background-color: #1f2937;
            border-radius: 8px;
            border: 2px solid #fbbf24;
            width: 90%;
            max-width: 400px;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            padding: 25px;
            color: #e5e7eb;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4), 0 0 15px rgba(251, 191, 36, 0.3);
            animation: newSlideInUp 0.4s ease-out;
        }
        
        .new-popup-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .new-popup-header h3 {
            color: #fbbf24;
            margin: 0;
            font-size: 1.3rem;
        }
        
        .new-popup-close {
            background: none;
            border: none;
            color: #9ca3af;
            font-size: 24px;
            cursor: pointer;
            padding: 0;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: all 0.2s;
        }
        
        .new-popup-close:hover {
            background-color: rgba(156, 163, 175, 0.2);
            color: #e5e7eb;
        }
        
        .new-popup-description {
            margin-bottom: 20px;
            font-size: 0.9rem;
            color: #9ca3af;
        }
        
        .new-popup-input-container {
            margin-bottom: 20px;
        }
        
        .new-popup-input-container label {
            display: block;
            margin-bottom: 5px;
            color: #ddd;
            font-size: 0.9rem;
        }
        
        .new-popup-input {
            width: 100%;
            padding: 12px;
            background: #374151;
            border: 1px solid #4b5563;
            border-radius: 4px;
            color: #fff;
            font-size: 1rem;
            transition: all 0.2s;
        }
        
        .new-popup-input:focus {
            outline: none;
            border-color: #60a5fa;
            box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.3);
        }
        
        .new-input-error {
            border-color: #ef4444 !important;
            box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.3) !important;
        }
        
        .new-error-message {
            color: #ef4444;
            font-size: 0.85rem;
            margin-top: 5px;
            text-align: right;
        }
        
        .new-popup-buttons {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
        }
        
        .new-popup-save-btn {
            background-color: #fbbf24;
            color: #1f2937;
            border: none;
            padding: 10px 16px;
            border-radius: 4px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .new-popup-save-btn:hover {
            background-color: #f59e0b;
        }
        
        .new-popup-cancel-btn {
            background-color: transparent;
            color: #9ca3af;
            border: 1px solid #4b5563;
            padding: 10px 16px;
            border-radius: 4px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .new-popup-cancel-btn:hover {
            background-color: rgba(75, 85, 99, 0.3);
            color: #e5e7eb;
        }
        
        /* تحركات */
        @keyframes newFadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes newSlideInUp {
            from {
                transform: translate(-50%, -30%);
                opacity: 0;
            }
            to {
                transform: translate(-50%, -50%);
                opacity: 1;
            }
        }
        
        /* زر الاختبار */
        #test-popup-button {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 10px 15px;
            background-color: #fbbf24;
            color: #1f2937;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
            z-index: 9000;
            transition: all 0.2s;
        }
        
        #test-popup-button:hover {
            background-color: #f59e0b;
        }
    `;
    
    document.head.appendChild(style);
    console.log("تمت إضافة أنماط CSS بنجاح");
}

/**
 * ربط أحداث نظام التعليقات
 */
function bindCommentEvents() {
    // البحث عن نموذج إضافة التعليق
    const commentForms = document.querySelectorAll('.add-comment');
    
    if (commentForms.length === 0) {
        console.log("لم يتم العثور على نماذج التعليقات في الصفحة");
        return;
    }
    
    console.log(`تم العثور على ${commentForms.length} نماذج للتعليقات`);
    
    commentForms.forEach(form => {
        const commentInput = form.querySelector('input[type="text"]');
        const submitBtn = form.querySelector('button');
        
        if (commentInput && submitBtn) {
            // إضافة مستمع حدث للتركيز على حقل التعليق
            commentInput.addEventListener('focus', function() {
                checkCommenterName();
            });
            
            // إضافة مستمع حدث لزر نشر التعليق
            submitBtn.addEventListener('click', function() {
                submitComment(form);
            });
            
            // إضافة مستمع حدث للإرسال بالضغط على Enter
            commentInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    submitComment(form);
                }
            });
        }
    });
    
    console.log("تم ربط أحداث نظام التعليقات بنجاح");
}

/**
 * التحقق من وجود اسم المعلق وعرض النافذة المنبثقة إذا لزم الأمر
 */
function checkCommenterName() {
    console.log("التحقق من اسم المعلق...");
    
    // إذا كان المستخدم مسجل الدخول، لا نحتاج إلى اسم
    if (isLoggedIn) {
        console.log("المستخدم مسجل الدخول - لا حاجة لطلب الاسم");
        return true;
    }
    
    // التحقق من وجود الاسم في localStorage
    const commenterName = localStorage.getItem('commenterName');
    console.log("اسم المعلق المحفوظ:", commenterName);
    
    if (!commenterName) {
        // إذا لم يكن هناك اسم محفوظ، اعرض النافذة المنبثقة
        console.log("لا يوجد اسم محفوظ - عرض النافذة المنبثقة");
        showNamePopup();
        return false;
    }
    
    return true;
}

/**
 * عرض نافذة إدخال اسم المعلق المنبثقة
 */
function showNamePopup() {
    console.log("عرض نافذة اسم المعلق المنبثقة...");
    
    if (!commenterNamePopup) {
        console.error("لم يتم العثور على نافذة اسم المعلق المنبثقة!");
        createCommenterNamePopup();
    }
    
    // إعادة ضبط حقل الإدخال ورسالة الخطأ
    if (commenterNameInput) {
        commenterNameInput.value = '';
        commenterNameInput.classList.remove('new-input-error');
    }
    
    if (errorMsg) {
        errorMsg.style.display = 'none';
    }
    
    // عرض النافذة
    commenterNamePopup.style.display = 'block';
    
    // تركيز حقل الإدخال
    setTimeout(() => {
        if (commenterNameInput) {
            commenterNameInput.focus();
            console.log("تم التركيز على حقل إدخال الاسم");
        }
    }, 100);
}

/**
 * حفظ اسم المعلق
 */
function saveCommenterName() {
    console.log("محاولة حفظ اسم المعلق...");
    
    if (!commenterNameInput) {
        console.error("لم يتم العثور على حقل إدخال الاسم!");
        return;
    }
    
    const name = commenterNameInput.value.trim();
    
    if (name) {
        console.log("تم حفظ الاسم:", name);
        
        // حفظ الاسم في localStorage
        localStorage.setItem('commenterName', name);
        
        // إغلاق النافذة
        closeNamePopup();
        
        // تركيز حقل التعليق بعد إغلاق النافذة
        setTimeout(() => {
            const commentField = document.querySelector('.add-comment input[type="text"]');
            if (commentField) {
                commentField.focus();
                console.log("تم التركيز على حقل التعليق");
            }
        }, 300);
        
        return true;
    } else {
        console.log("حقل الاسم فارغ - عرض رسالة خطأ");
        
        // عرض رسالة الخطأ
        commenterNameInput.classList.add('new-input-error');
        
        if (errorMsg) {
            errorMsg.style.display = 'block';
        }
        
        // تركيز الحقل
        commenterNameInput.focus();
        
        return false;
    }
}

/**
 * إغلاق نافذة اسم المعلق المنبثقة
 */
function closeNamePopup() {
    console.log("إغلاق نافذة اسم المعلق المنبثقة...");
    
    if (commenterNamePopup) {
        commenterNamePopup.style.display = 'none';
    }
}

/**
 * إرسال تعليق جديد
 */
function submitComment(form) {
    console.log("محاولة إرسال تعليق جديد...");
    
    // التحقق من وجود اسم المعلق إذا لم يكن المستخدم مسجلاً
    if (!isLoggedIn) {
        const hasName = checkCommenterName();
        if (!hasName) {
            console.log("لا يمكن إرسال التعليق بدون اسم");
            return;
        }
    }
    
    // البحث عن الحقول اللازمة في النموذج
    const commentInput = form.querySelector('input[type="text"]');
    const portfolioIdInput = form.querySelector('input[id="comment-portfolio-id"]');
    const parentCommentIdInput = form.querySelector('input[id="parent-comment-id"]');
    
    if (!commentInput || !portfolioIdInput) {
        console.error("لم يتم العثور على الحقول اللازمة في النموذج!");
        return;
    }
    
    const content = commentInput.value.trim();
    const portfolioId = portfolioIdInput.value;
    const parentCommentId = parentCommentIdInput ? parentCommentIdInput.value : '';
    
    if (!content) {
        console.log("محتوى التعليق فارغ");
        commentInput.classList.add('new-input-error');
        return;
    }
    
    // الحصول على اسم المعلق من localStorage
    const commenterName = localStorage.getItem('commenterName') || '';
    
    console.log("إرسال التعليق:", {
        content,
        portfolioId,
        parentCommentId,
        commenterName
    });
    
    // إرسال التعليق إلى الخادم باستخدام Fetch API
    fetch(`/api/portfolio/${portfolioId}/comment`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
        },
        body: JSON.stringify({
            content: content,
            parent_id: parentCommentId,
            commenter_name: commenterName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log("تم إرسال التعليق بنجاح:", data);
            
            // إعادة تحميل التعليقات
            if (typeof loadComments === 'function') {
                loadComments(portfolioId);
            }
            
            // مسح حقل التعليق
            commentInput.value = '';
            
            // إعادة ضبط parentCommentId إذا كان موجوداً
            if (parentCommentIdInput) {
                parentCommentIdInput.value = '';
            }
            
            // إزالة نمط الرد إذا كان موجوداً
            form.classList.remove('replying');
            
            // إزالة زر إلغاء الرد إذا كان موجوداً
            const cancelReplyBtn = form.querySelector('.cancel-reply-btn');
            if (cancelReplyBtn) {
                cancelReplyBtn.remove();
            }
        } else {
            console.error("فشل إرسال التعليق:", data.error);
            alert("حدث خطأ أثناء إرسال التعليق. يرجى المحاولة مرة أخرى.");
        }
    })
    .catch(error => {
        console.error("خطأ في إرسال التعليق:", error);
        alert("حدث خطأ أثناء إرسال التعليق. يرجى المحاولة مرة أخرى.");
    });
}

/**
 * إضافة زر اختبار النافذة المنبثقة (فقط في وضع التطوير)
 */
function addTestButton() {
    console.log("إضافة زر اختبار النافذة المنبثقة...");
    
    const testBtn = document.createElement('button');
    testBtn.id = 'test-popup-button';
    testBtn.textContent = 'اختبار النافذة المنبثقة';
    testBtn.addEventListener('click', function() {
        showNamePopup();
    });
    
    document.body.appendChild(testBtn);
    console.log("تم إضافة زر الاختبار بنجاح");
}