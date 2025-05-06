/**
 * نظام التعرف التلقائي على أيقونات وسائل التواصل الاجتماعي والمواقع الشهيرة
 * Auto Icon Detector for social media platforms and popular websites
 */

document.addEventListener('DOMContentLoaded', function() {
    // نظام تعرف تلقائي للأيقونات حسب اسم الموقع أو رابطه
    initAutoIconDetection();
    
    // دعم التكامل مع صفحة وسائل التواصل الاجتماعي
    const platformSelection = document.getElementById('platform');
    if (platformSelection) {
        platformSelection.addEventListener('change', updateIconBasedOnPlatform);
    }
    
    // دعم التكامل مع صفحة تعديل وسائل التواصل الاجتماعي
    const editPlatformSelection = document.getElementById('edit-platform');
    if (editPlatformSelection) {
        editPlatformSelection.addEventListener('change', function() {
            updateIconBasedOnPlatformForEdit();
        });
    }
    
    // دعم الإدخال اليدوي لاسم الموقع
    const nameInput = document.getElementById('name');
    if (nameInput) {
        nameInput.addEventListener('input', function() {
            detectIconFromName(this.value);
        });
    }
    
    // دعم الإدخال اليدوي لرابط الموقع
    const urlInput = document.getElementById('url');
    if (urlInput) {
        urlInput.addEventListener('input', function() {
            detectIconFromUrl(this.value);
        });
    }
});

/**
 * قائمة شاملة للمنصات والمواقع الشائعة مع أيقوناتها في Font Awesome
 */
const platformIcons = {
    // وسائل التواصل الاجتماعي
    'facebook': 'fab fa-facebook',
    'twitter': 'fab fa-twitter',
    'x': 'fab fa-x-twitter',
    'instagram': 'fab fa-instagram',
    'linkedin': 'fab fa-linkedin',
    'youtube': 'fab fa-youtube',
    'pinterest': 'fab fa-pinterest',
    'snapchat': 'fab fa-snapchat',
    'tiktok': 'fab fa-tiktok',
    'whatsapp': 'fab fa-whatsapp',
    'telegram': 'fab fa-telegram',
    'discord': 'fab fa-discord',
    'reddit': 'fab fa-reddit',
    'twitch': 'fab fa-twitch',
    'vimeo': 'fab fa-vimeo',
    'medium': 'fab fa-medium',
    'quora': 'fab fa-quora',
    'mastodon': 'fab fa-mastodon',
    'threads': 'fab fa-threads',
    'slack': 'fab fa-slack',
    'skype': 'fab fa-skype',
    'tumblr': 'fab fa-tumblr',
    'flickr': 'fab fa-flickr',
    'vk': 'fab fa-vk',
    
    // منصات استضافة الكود والتطوير
    'github': 'fab fa-github',
    'gitlab': 'fab fa-gitlab',
    'bitbucket': 'fab fa-bitbucket',
    'stack overflow': 'fab fa-stack-overflow',
    'stackoverflow': 'fab fa-stack-overflow',
    'codepen': 'fab fa-codepen',
    'jsfiddle': 'fab fa-jsfiddle',
    
    // منصات الفن والتصميم
    'behance': 'fab fa-behance',
    'dribbble': 'fab fa-dribbble',
    'deviantart': 'fab fa-deviantart',
    
    // منصات التسوق
    'amazon': 'fab fa-amazon',
    'etsy': 'fab fa-etsy',
    'shopify': 'fab fa-shopify',
    
    // مواقع شهيرة أخرى
    'google': 'fab fa-google',
    'apple': 'fab fa-apple',
    'microsoft': 'fab fa-microsoft',
    'windows': 'fab fa-windows',
    'android': 'fab fa-android',
    'linux': 'fab fa-linux',
    'ubuntu': 'fab fa-ubuntu',
    'firefox': 'fab fa-firefox',
    'chrome': 'fab fa-chrome',
    'safari': 'fab fa-safari',
    'opera': 'fab fa-opera',
    'edge': 'fab fa-edge',
    'internet explorer': 'fab fa-internet-explorer',
    
    // منصات الموسيقى
    'spotify': 'fab fa-spotify',
    'soundcloud': 'fab fa-soundcloud',
    'itunes': 'fab fa-itunes',
    'apple music': 'fab fa-apple',
    
    // تطبيقات الدفع
    'paypal': 'fab fa-paypal',
    'stripe': 'fab fa-stripe',
    'bitcoin': 'fab fa-bitcoin',
    'ethereum': 'fab fa-ethereum',
    
    // أخرى
    'wordpress': 'fab fa-wordpress',
    'joomla': 'fab fa-joomla',
    'drupal': 'fab fa-drupal',
    'magento': 'fab fa-magento',
    'wix': 'fab fa-wix'
};

/**
 * تهيئة نظام الكشف التلقائي عن الأيقونات
 */
function initAutoIconDetection() {
    // تحديث الأيقونات بناءً على القيم الأولية
    const platformSelection = document.getElementById('platform');
    if (platformSelection && platformSelection.value) {
        updateIconBasedOnPlatform();
    }
    
    const editPlatformSelection = document.getElementById('edit-platform');
    if (editPlatformSelection && editPlatformSelection.value) {
        updateIconBasedOnPlatformForEdit();
    }
    
    const nameInput = document.getElementById('name');
    if (nameInput && nameInput.value) {
        detectIconFromName(nameInput.value);
    }
    
    const urlInput = document.getElementById('url');
    if (urlInput && urlInput.value) {
        detectIconFromUrl(urlInput.value);
    }
}

/**
 * تحديث حقل الأيقونة بناءً على المنصة المختارة
 */
function updateIconBasedOnPlatform() {
    const platform = document.getElementById('platform').value;
    const iconInput = document.getElementById('icon');
    
    if (platform && platformIcons[platform] && iconInput) {
        iconInput.value = platformIcons[platform];
        // عرض معاينة للأيقونة
        showIconPreview(platformIcons[platform], iconInput);
    }
}

/**
 * تحديث حقل الأيقونة في نموذج التعديل بناءً على المنصة المختارة
 */
function updateIconBasedOnPlatformForEdit() {
    const platform = document.getElementById('edit-platform').value;
    const iconInput = document.getElementById('edit-icon');
    
    if (platform && platformIcons[platform] && iconInput) {
        iconInput.value = platformIcons[platform];
        // عرض معاينة للأيقونة
        showIconPreview(platformIcons[platform], iconInput);
    }
}

/**
 * الكشف عن الأيقونة المناسبة من اسم الموقع
 * @param {string} name - اسم الموقع
 */
function detectIconFromName(name) {
    if (!name) return;
    
    const iconInput = document.getElementById('icon') || document.getElementById('edit-icon');
    if (!iconInput) return;
    
    // إذا كان الحقل قد تم تعديله يدويًا، لا تقم بالتغيير التلقائي
    if (iconInput.dataset.manuallyChanged === 'true') return;
    
    name = name.toLowerCase();
    
    // البحث عن تطابق دقيق أو جزئي
    let matchedIcon = null;
    
    // أولاً البحث عن تطابق دقيق
    if (platformIcons[name]) {
        matchedIcon = platformIcons[name];
    } else {
        // البحث عن تطابق جزئي إذا لم يتم العثور على تطابق دقيق
        for (const platform in platformIcons) {
            if (name.includes(platform) || platform.includes(name)) {
                matchedIcon = platformIcons[platform];
                break;
            }
        }
    }
    
    // تطبيق الأيقونة إذا تم العثور عليها
    if (matchedIcon) {
        iconInput.value = matchedIcon;
        showIconPreview(matchedIcon, iconInput);
    }
}

/**
 * الكشف عن الأيقونة المناسبة من رابط الموقع
 * @param {string} url - رابط الموقع
 */
function detectIconFromUrl(url) {
    if (!url) return;
    
    const iconInput = document.getElementById('icon') || document.getElementById('edit-icon');
    if (!iconInput) return;
    
    // إذا كان الحقل قد تم تعديله يدويًا، لا تقم بالتغيير التلقائي
    if (iconInput.dataset.manuallyChanged === 'true') return;
    
    try {
        // استخراج اسم النطاق من الرابط
        let domain = '';
        if (url.indexOf('://') > -1) {
            domain = url.split('/')[2];
        } else {
            domain = url.split('/')[0];
        }
        
        // إزالة www. والحصول على اسم النطاق الرئيسي
        domain = domain.replace('www.', '');
        domain = domain.split('.')[0];
        
        // البحث عن تطابق
        if (domain) {
            detectIconFromName(domain);
        }
    } catch (e) {
        console.log('خطأ في استخراج النطاق:', e);
    }
}

/**
 * عرض معاينة للأيقونة بجانب حقل الإدخال
 * @param {string} iconClass - اسم كلاس الأيقونة
 * @param {HTMLElement} inputElement - عنصر حقل الإدخال
 */
function showIconPreview(iconClass, inputElement) {
    if (!inputElement) return;
    
    // إزالة المعاينة السابقة إن وجدت
    const parentElement = inputElement.parentElement;
    const existingPreview = parentElement.querySelector('.icon-preview');
    if (existingPreview) {
        existingPreview.remove();
    }
    
    // إنشاء عنصر معاينة جديد
    const previewElement = document.createElement('div');
    previewElement.className = 'icon-preview d-flex align-items-center mt-2';
    previewElement.innerHTML = `
        <i class="${iconClass} mr-2" style="font-size: 1.5rem;"></i>
        <small class="text-muted">معاينة الأيقونة</small>
    `;
    
    // إضافة المعاينة بعد حقل الإدخال
    inputElement.after(previewElement);
}

// إضافة مستمع حدث للتعديل اليدوي على حقل الأيقونة
document.addEventListener('DOMContentLoaded', function() {
    const iconInputs = document.querySelectorAll('input[name="icon"], #edit-icon');
    iconInputs.forEach(input => {
        input.addEventListener('input', function() {
            // تمييز الحقل بأنه تم تعديله يدويًا
            this.dataset.manuallyChanged = 'true';
            
            // تحديث المعاينة
            if (this.value) {
                showIconPreview(this.value, this);
            }
        });
    });
});