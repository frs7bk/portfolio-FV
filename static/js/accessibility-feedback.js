/**
 * نظام ردود الفعل الصوتية والاهتزازية للتفاعلات
 * 
 * هذا الملف يحتوي على وظائف لتوفير تغذية راجعة صوتية واهتزازية 
 * للتفاعلات المختلفة في الموقع (الإعجاب، التعليق، فتح العناصر، إلخ)
 * بهدف تحسين تجربة المستخدم وإمكانية الوصول
 */

// متغيرات عامة
let feedbackEnabled = true;
let soundEnabled = true;
let vibrationEnabled = true;

// أصوات مخزنة مؤقتًا
const audioCache = {};

// تهيئة النظام عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    console.log("تهيئة نظام ردود الفعل الصوتية والاهتزازية...");
    
    // استرجاع إعدادات المستخدم المحفوظة (إن وجدت)
    loadFeedbackSettings();
    
    // إضافة زر التحكم في الإعدادات إلى الصفحة
    addFeedbackSettingsControl();
    
    // تحميل الأصوات مسبقًا لتقليل التأخير
    preloadSounds();
    
    console.log("تم تهيئة نظام ردود الفعل الصوتية والاهتزازية بنجاح");
});

/**
 * تحميل إعدادات التغذية الراجعة من التخزين المحلي
 */
function loadFeedbackSettings() {
    // استرجاع الإعدادات من localStorage
    const settings = localStorage.getItem('accessibilityFeedbackSettings');
    
    if (settings) {
        try {
            const parsedSettings = JSON.parse(settings);
            feedbackEnabled = parsedSettings.enabled !== undefined ? parsedSettings.enabled : true;
            soundEnabled = parsedSettings.sound !== undefined ? parsedSettings.sound : true;
            vibrationEnabled = parsedSettings.vibration !== undefined ? parsedSettings.vibration : true;
            
            console.log("تم تحميل إعدادات التغذية الراجعة:", { feedbackEnabled, soundEnabled, vibrationEnabled });
        } catch (e) {
            console.error("خطأ في تحليل إعدادات التغذية الراجعة:", e);
            // إعادة تعيين الإعدادات الافتراضية
            resetFeedbackSettings();
        }
    } else {
        // تهيئة الإعدادات الافتراضية إذا لم تكن موجودة
        saveFeedbackSettings();
    }
}

/**
 * حفظ إعدادات التغذية الراجعة في التخزين المحلي
 */
function saveFeedbackSettings() {
    const settings = {
        enabled: feedbackEnabled,
        sound: soundEnabled,
        vibration: vibrationEnabled
    };
    
    localStorage.setItem('accessibilityFeedbackSettings', JSON.stringify(settings));
    console.log("تم حفظ إعدادات التغذية الراجعة");
}

/**
 * إعادة تعيين إعدادات التغذية الراجعة إلى القيم الافتراضية
 */
function resetFeedbackSettings() {
    feedbackEnabled = true;
    soundEnabled = true;
    vibrationEnabled = true;
    saveFeedbackSettings();
    
    console.log("تمت إعادة تعيين إعدادات التغذية الراجعة إلى القيم الافتراضية");
    
    // تحديث حالة العناصر في واجهة المستخدم
    updateFeedbackControlUI();
}

/**
 * إضافة زر ولوحة التحكم في إعدادات التغذية الراجعة
 */
function addFeedbackSettingsControl() {
    // إنشاء زر الإعدادات
    const feedbackControlBtn = document.createElement('button');
    feedbackControlBtn.id = 'accessibility-control-btn';
    feedbackControlBtn.setAttribute('aria-label', 'إعدادات إمكانية الوصول');
    feedbackControlBtn.setAttribute('title', 'إعدادات إمكانية الوصول');
    feedbackControlBtn.innerHTML = '<i class="fas fa-universal-access"></i>';
    
    // إضافة الأنماط للزر
    feedbackControlBtn.style.position = 'fixed';
    feedbackControlBtn.style.bottom = '20px';
    feedbackControlBtn.style.left = '20px';
    feedbackControlBtn.style.zIndex = '9000';
    feedbackControlBtn.style.width = '50px';
    feedbackControlBtn.style.height = '50px';
    feedbackControlBtn.style.borderRadius = '50%';
    feedbackControlBtn.style.backgroundColor = '#3b82f6';
    feedbackControlBtn.style.color = 'white';
    feedbackControlBtn.style.border = 'none';
    feedbackControlBtn.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.2)';
    feedbackControlBtn.style.cursor = 'pointer';
    feedbackControlBtn.style.display = 'flex';
    feedbackControlBtn.style.alignItems = 'center';
    feedbackControlBtn.style.justifyContent = 'center';
    feedbackControlBtn.style.fontSize = '22px';
    
    // إنشاء لوحة الإعدادات
    const settingsPanel = document.createElement('div');
    settingsPanel.id = 'accessibility-settings-panel';
    settingsPanel.setAttribute('aria-hidden', 'true');
    
    // أنماط لوحة الإعدادات
    settingsPanel.style.position = 'fixed';
    settingsPanel.style.bottom = '80px';
    settingsPanel.style.left = '20px';
    settingsPanel.style.zIndex = '8999';
    settingsPanel.style.backgroundColor = '#1f2937';
    settingsPanel.style.width = '280px';
    settingsPanel.style.padding = '15px';
    settingsPanel.style.borderRadius = '8px';
    settingsPanel.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.3)';
    settingsPanel.style.color = 'white';
    settingsPanel.style.display = 'none';
    settingsPanel.style.border = '2px solid #3b82f6';
    settingsPanel.style.direction = 'rtl';
    
    // إنشاء محتوى اللوحة
    settingsPanel.innerHTML = `
        <h3 style="color: #3b82f6; margin-top: 0; text-align: center; font-size: 18px; margin-bottom: 15px;">إعدادات إمكانية الوصول</h3>
        
        <div style="margin-bottom: 12px;">
            <label class="toggle-switch" style="display: flex; justify-content: space-between; align-items: center;">
                <span>تفعيل ردود الفعل</span>
                <div style="position: relative; display: inline-block; width: 50px; height: 24px;">
                    <input type="checkbox" id="feedback-toggle" ${feedbackEnabled ? 'checked' : ''} style="opacity: 0; width: 0; height: 0;">
                    <span style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: ${feedbackEnabled ? '#3b82f6' : '#ccc'}; transition: .4s; border-radius: 24px;">
                        <span style="position: absolute; content: ''; height: 18px; width: 18px; left: 3px; bottom: 3px; background-color: white; transition: .4s; border-radius: 50%; transform: ${feedbackEnabled ? 'translateX(26px)' : 'translateX(0)'}"></span>
                    </span>
                </div>
            </label>
        </div>
        
        <div style="margin-bottom: 12px; ${feedbackEnabled ? '' : 'opacity: 0.5; pointer-events: none;'}">
            <label class="toggle-switch" style="display: flex; justify-content: space-between; align-items: center;">
                <span>الأصوات</span>
                <div style="position: relative; display: inline-block; width: 50px; height: 24px;">
                    <input type="checkbox" id="sound-toggle" ${soundEnabled ? 'checked' : ''} style="opacity: 0; width: 0; height: 0;">
                    <span style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: ${soundEnabled ? '#3b82f6' : '#ccc'}; transition: .4s; border-radius: 24px;">
                        <span style="position: absolute; content: ''; height: 18px; width: 18px; left: 3px; bottom: 3px; background-color: white; transition: .4s; border-radius: 50%; transform: ${soundEnabled ? 'translateX(26px)' : 'translateX(0)'}"></span>
                    </span>
                </div>
            </label>
        </div>
        
        <div style="margin-bottom: 15px; ${feedbackEnabled ? '' : 'opacity: 0.5; pointer-events: none;'}">
            <label class="toggle-switch" style="display: flex; justify-content: space-between; align-items: center;">
                <span>الاهتزاز</span>
                <div style="position: relative; display: inline-block; width: 50px; height: 24px;">
                    <input type="checkbox" id="vibration-toggle" ${vibrationEnabled ? 'checked' : ''} style="opacity: 0; width: 0; height: 0;">
                    <span style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: ${vibrationEnabled ? '#3b82f6' : '#ccc'}; transition: .4s; border-radius: 24px;">
                        <span style="position: absolute; content: ''; height: 18px; width: 18px; left: 3px; bottom: 3px; background-color: white; transition: .4s; border-radius: 50%; transform: ${vibrationEnabled ? 'translateX(26px)' : 'translateX(0)'}"></span>
                    </span>
                </div>
            </label>
        </div>
        
        <button id="reset-feedback-settings" style="background-color: #4b5563; color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; width: 100%; font-size: 14px;">
            إعادة التعيين إلى الإعدادات الافتراضية
        </button>
    `;
    
    // إضافة الأحداث
    feedbackControlBtn.addEventListener('click', function() {
        const panel = document.getElementById('accessibility-settings-panel');
        if (panel.style.display === 'none') {
            panel.style.display = 'block';
            panel.setAttribute('aria-hidden', 'false');
            provideUserFeedback('open');
        } else {
            panel.style.display = 'none';
            panel.setAttribute('aria-hidden', 'true');
            provideUserFeedback('close');
        }
    });
    
    // إضافة العناصر إلى الصفحة
    document.body.appendChild(feedbackControlBtn);
    document.body.appendChild(settingsPanel);
    
    // إضافة مستمعي الأحداث للإعدادات
    document.getElementById('feedback-toggle').addEventListener('change', function() {
        feedbackEnabled = this.checked;
        saveFeedbackSettings();
        updateFeedbackControlUI();
        
        if (feedbackEnabled) {
            provideUserFeedback('toggle-on');
        }
    });
    
    document.getElementById('sound-toggle').addEventListener('change', function() {
        soundEnabled = this.checked;
        saveFeedbackSettings();
        updateFeedbackControlUI();
        
        if (feedbackEnabled && soundEnabled) {
            playSound('toggle');
        }
    });
    
    document.getElementById('vibration-toggle').addEventListener('change', function() {
        vibrationEnabled = this.checked;
        saveFeedbackSettings();
        updateFeedbackControlUI();
        
        if (feedbackEnabled && vibrationEnabled) {
            vibrate(100);
        }
    });
    
    document.getElementById('reset-feedback-settings').addEventListener('click', function() {
        resetFeedbackSettings();
        provideUserFeedback('success');
    });
    
    // إغلاق اللوحة عند النقر خارجها
    document.addEventListener('click', function(e) {
        const panel = document.getElementById('accessibility-settings-panel');
        const button = document.getElementById('accessibility-control-btn');
        
        if (panel && panel.style.display === 'block' && 
            e.target !== panel && 
            e.target !== button && 
            !panel.contains(e.target) && 
            !button.contains(e.target)) {
            panel.style.display = 'none';
            panel.setAttribute('aria-hidden', 'true');
        }
    });
}

/**
 * تحديث واجهة المستخدم لعناصر التحكم في التغذية الراجعة
 */
function updateFeedbackControlUI() {
    const feedbackToggle = document.getElementById('feedback-toggle');
    const soundToggle = document.getElementById('sound-toggle');
    const vibrationToggle = document.getElementById('vibration-toggle');
    
    if (feedbackToggle) {
        feedbackToggle.checked = feedbackEnabled;
        feedbackToggle.parentNode.style.backgroundColor = feedbackEnabled ? '#3b82f6' : '#ccc';
        feedbackToggle.nextElementSibling.lastElementChild.style.transform = feedbackEnabled ? 'translateX(26px)' : 'translateX(0)';
    }
    
    if (soundToggle) {
        soundToggle.checked = soundEnabled;
        soundToggle.parentNode.style.backgroundColor = soundEnabled ? '#3b82f6' : '#ccc';
        soundToggle.nextElementSibling.lastElementChild.style.transform = soundEnabled ? 'translateX(26px)' : 'translateX(0)';
        soundToggle.closest('div').style.opacity = feedbackEnabled ? '1' : '0.5';
        soundToggle.closest('div').style.pointerEvents = feedbackEnabled ? 'auto' : 'none';
    }
    
    if (vibrationToggle) {
        vibrationToggle.checked = vibrationEnabled;
        vibrationToggle.parentNode.style.backgroundColor = vibrationEnabled ? '#3b82f6' : '#ccc';
        vibrationToggle.nextElementSibling.lastElementChild.style.transform = vibrationEnabled ? 'translateX(26px)' : 'translateX(0)';
        vibrationToggle.closest('div').style.opacity = feedbackEnabled ? '1' : '0.5';
        vibrationToggle.closest('div').style.pointerEvents = feedbackEnabled ? 'auto' : 'none';
    }
}

/**
 * تهيئة نظام الأصوات
 */
function preloadSounds() {
    console.log("تهيئة نظام توليد الأصوات...");
    
    // التحقق من وجود مولد الأصوات
    if (!window.soundGenerator) {
        console.warn("لم يتم العثور على مولد الأصوات. تأكد من تضمين ملف sound-generator.js");
    } else {
        console.log("تم العثور على مولد الأصوات وتهيئته بنجاح");
    }
}

/**
 * تشغيل صوت محدد
 * @param {string} soundName - اسم الصوت المراد تشغيله
 */
function playSound(soundName) {
    if (!feedbackEnabled || !soundEnabled) return;
    
    try {
        // التحقق من وجود مولد الأصوات
        if (!window.soundGenerator) {
            console.warn('لم يتم العثور على مولد الأصوات');
            return;
        }
        
        // استدعاء الدالة المناسبة من مولد الأصوات
        switch (soundName) {
            case 'click':
                window.soundGenerator.generateClickSound();
                break;
            case 'success':
                window.soundGenerator.generateSuccessSound();
                break;
            case 'error':
                window.soundGenerator.generateErrorSound();
                break;
            case 'toggle':
                window.soundGenerator.generateToggleSound();
                break;
            case 'like':
                window.soundGenerator.generateLikeSound();
                break;
            case 'comment':
                window.soundGenerator.generateCommentSound();
                break;
            case 'open':
                window.soundGenerator.generateOpenSound();
                break;
            case 'close':
                window.soundGenerator.generateCloseSound();
                break;
            case 'notification':
                window.soundGenerator.generateNotificationSound();
                break;
            default:
                window.soundGenerator.generateClickSound();
                break;
        }
    } catch (error) {
        console.error('خطأ في تشغيل الصوت:', error);
    }
}

/**
 * تشغيل اهتزاز لفترة محددة
 * @param {number|number[]} pattern - فترة الاهتزاز بالميلي ثانية أو نمط من فترات الاهتزاز والتوقف
 */
function vibrate(pattern) {
    if (!feedbackEnabled || !vibrationEnabled) return;
    
    try {
        // التحقق من دعم الاهتزاز في المتصفح
        if ('vibrate' in navigator) {
            navigator.vibrate(pattern);
        } else {
            console.warn('المتصفح لا يدعم واجهة برمجة الاهتزاز (Vibration API)');
        }
    } catch (error) {
        console.error('خطأ في تشغيل الاهتزاز:', error);
    }
}

/**
 * توفير تغذية راجعة مركبة للمستخدم (صوت واهتزاز) بناءً على نوع التفاعل
 * @param {string} interactionType - نوع التفاعل
 */
function provideUserFeedback(interactionType) {
    if (!feedbackEnabled) return;
    
    switch (interactionType) {
        case 'click':
            if (soundEnabled) playSound('click');
            if (vibrationEnabled) vibrate(50);
            break;
        
        case 'like':
            if (soundEnabled) playSound('like');
            if (vibrationEnabled) vibrate([50, 30, 50]);
            break;
        
        case 'comment':
            if (soundEnabled) playSound('comment');
            if (vibrationEnabled) vibrate(100);
            break;
        
        case 'success':
            if (soundEnabled) playSound('success');
            if (vibrationEnabled) vibrate([50, 30, 100, 30, 50]);
            break;
        
        case 'error':
            if (soundEnabled) playSound('error');
            if (vibrationEnabled) vibrate([100, 50, 100]);
            break;
        
        case 'open':
            if (soundEnabled) playSound('open');
            if (vibrationEnabled) vibrate(70);
            break;
        
        case 'close':
            if (soundEnabled) playSound('close');
            if (vibrationEnabled) vibrate(40);
            break;
            
        case 'notification':
            if (soundEnabled) playSound('notification');
            if (vibrationEnabled) vibrate([50, 50, 50, 50, 100]);
            break;
            
        case 'toggle-on':
            if (soundEnabled) playSound('toggle');
            if (vibrationEnabled) vibrate([30, 20, 30]);
            break;
            
        case 'toggle-off':
            if (soundEnabled) playSound('toggle');
            if (vibrationEnabled) vibrate(30);
            break;
            
        default:
            if (soundEnabled) playSound('click');
            if (vibrationEnabled) vibrate(50);
            break;
    }
}

// تصدير الدوال للاستخدام من ملفات JavaScript أخرى
window.accessibilityFeedback = {
    playSound,
    vibrate,
    provideUserFeedback
};