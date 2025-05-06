/**
 * توليد الأصوات ديناميكيًا باستخدام Web Audio API
 * 
 * هذا الملف يحتوي على دوال لتوليد الأصوات المختلفة المستخدمة في نظام التغذية الراجعة
 * بدلاً من الاعتماد على ملفات صوتية خارجية
 */

// إنشاء سياق الصوت
let audioContext = null;

// تهيئة سياق الصوت عند أول استخدام
function initAudioContext() {
    try {
        if (!audioContext) {
            window.AudioContext = window.AudioContext || window.webkitAudioContext;
            audioContext = new AudioContext();
            console.log("تم تهيئة سياق الصوت بنجاح");
        }
        return audioContext;
    } catch (e) {
        console.error("فشل إنشاء سياق الصوت:", e);
        return null;
    }
}

/**
 * توليد نغمة بتردد ومدة محددة
 * 
 * @param {number} frequency - تردد النغمة (بالهرتز)
 * @param {number} duration - مدة النغمة (بالثواني)
 * @param {string} type - نوع الموجة ('sine', 'square', 'sawtooth', 'triangle')
 * @param {number} volume - مستوى الصوت (0 إلى 1)
 * @param {number} fadeOut - مدة التلاشي في نهاية النغمة (بالثواني)
 */
function generateTone(frequency, duration, type = 'sine', volume = 0.5, fadeOut = 0.1) {
    const context = initAudioContext();
    if (!context) return;
    
    try {
        // استئناف السياق إذا كان معلقًا (متطلب من المتصفحات الحديثة)
        if (context.state === 'suspended') {
            context.resume();
        }
        
        // إنشاء مذبذب (oscillator)
        const oscillator = context.createOscillator();
        const gainNode = context.createGain();
        
        // ضبط خصائص المذبذب
        oscillator.type = type;
        oscillator.frequency.value = frequency;
        
        // ضبط مستوى الصوت
        gainNode.gain.value = volume;
        
        // تلاشي الصوت في النهاية
        const fadeOutTime = context.currentTime + duration - fadeOut;
        gainNode.gain.setValueAtTime(volume, context.currentTime);
        gainNode.gain.linearRampToValueAtTime(0, context.currentTime + duration);
        
        // توصيل المذبذب بعقدة التحكم بالصوت ثم بالخرج
        oscillator.connect(gainNode);
        gainNode.connect(context.destination);
        
        // بدء وإيقاف المذبذب
        oscillator.start(context.currentTime);
        oscillator.stop(context.currentTime + duration);
        
        return oscillator;
    } catch (e) {
        console.error("خطأ في توليد النغمة:", e);
    }
}

/**
 * توليد سلسلة من النغمات المتتالية
 * 
 * @param {Array} noteSequence - مصفوفة من النغمات، كل نغمة عبارة عن كائن يحتوي على التردد والمدة والنوع والصوت
 * @param {number} delay - التأخير بين النغمات (بالثواني)
 */
function generateSequence(noteSequence, delay = 0.05) {
    const context = initAudioContext();
    if (!context) return;
    
    try {
        // استئناف السياق إذا كان معلقًا
        if (context.state === 'suspended') {
            context.resume();
        }
        
        let currentTime = context.currentTime;
        
        noteSequence.forEach((note, index) => {
            const { frequency, duration, type = 'sine', volume = 0.5, fadeOut = 0.1 } = note;
            
            setTimeout(() => {
                generateTone(frequency, duration, type, volume, fadeOut);
            }, (index * delay) * 1000);
        });
    } catch (e) {
        console.error("خطأ في توليد سلسلة النغمات:", e);
    }
}

// دوال لتوليد الأصوات المختلفة المستخدمة في التطبيق

/**
 * صوت النقر (للأزرار العامة)
 */
function generateClickSound() {
    generateTone(800, 0.1, 'sine', 0.3, 0.05);
}

/**
 * صوت النجاح (للعمليات الناجحة)
 */
function generateSuccessSound() {
    generateSequence([
        { frequency: 600, duration: 0.1, type: 'sine', volume: 0.3 },
        { frequency: 800, duration: 0.1, type: 'sine', volume: 0.4 },
        { frequency: 1000, duration: 0.15, type: 'sine', volume: 0.5 }
    ], 0.08);
}

/**
 * صوت الخطأ (للعمليات الفاشلة)
 */
function generateErrorSound() {
    generateSequence([
        { frequency: 400, duration: 0.15, type: 'square', volume: 0.3 },
        { frequency: 300, duration: 0.2, type: 'square', volume: 0.4 }
    ], 0.1);
}

/**
 * صوت التبديل (للمفاتيح والإعدادات)
 */
function generateToggleSound() {
    generateTone(500, 0.08, 'sine', 0.3, 0.03);
}

/**
 * صوت الإعجاب
 */
function generateLikeSound() {
    generateSequence([
        { frequency: 700, duration: 0.08, type: 'sine', volume: 0.3 },
        { frequency: 900, duration: 0.1, type: 'sine', volume: 0.4 }
    ], 0.06);
}

/**
 * صوت التعليق
 */
function generateCommentSound() {
    generateSequence([
        { frequency: 600, duration: 0.1, type: 'sine', volume: 0.3 },
        { frequency: 500, duration: 0.1, type: 'sine', volume: 0.3 }
    ], 0.1);
}

/**
 * صوت الفتح (للنوافذ المنبثقة والعناصر المتوسعة)
 */
function generateOpenSound() {
    generateTone(600, 0.15, 'sine', 0.3, 0.1);
}

/**
 * صوت الإغلاق (للنوافذ المنبثقة والعناصر المتوسعة)
 */
function generateCloseSound() {
    generateTone(400, 0.12, 'sine', 0.3, 0.08);
}

/**
 * صوت الإشعار
 */
function generateNotificationSound() {
    generateSequence([
        { frequency: 800, duration: 0.08, type: 'sine', volume: 0.3 },
        { frequency: 1000, duration: 0.1, type: 'sine', volume: 0.4 },
        { frequency: 800, duration: 0.08, type: 'sine', volume: 0.3 }
    ], 0.08);
}

// تصدير الدوال للاستخدام في ملفات JavaScript أخرى
window.soundGenerator = {
    generateTone,
    generateSequence,
    generateClickSound,
    generateSuccessSound,
    generateErrorSound,
    generateToggleSound,
    generateLikeSound,
    generateCommentSound,
    generateOpenSound,
    generateCloseSound,
    generateNotificationSound
};