/**
 * نظام تتبع المشاهدات المتطور للغاية
 * يوفر قياسات تفاعل متقدمة وتحليلات احترافية لمشاهدات المشاريع
 * 
 * الميزات:
 * - قياس مدة المشاهدة الدقيقة
 * - تتبع مستوى التفاعل (التمرير، النقرات، الوقت المنقضي)
 * - تسجيل البيانات الوصفية للمشاهدة (الجهاز، المتصفح، الشاشة)
 * - إرسال البيانات بشكل دوري للخادم للتحليل
 * - التحليل في الوقت الفعلي لسلوك المستخدم
 */

// نطاق عام للوصول المباشر من خارج الملف
const AdvancedViewsTracking = (() => {
    // متغيرات خاصة
    let _isInitialized = false;
    let _currentItemId = null;
    let _viewStartTime = null;
    let _lastInteractionTime = null;
    let _interactionEvents = 0;
    let _scrollDepth = 0;
    let _totalTimeSpent = 0;
    let _isVisible = false;
    let _viewData = {};
    let _sendInterval = null;
    let _isUserActive = true;
    let _periodicUpdateInterval = 10000; // 10 ثوانٍ للتحديثات الدورية
    let _viewTimerInterval = null;
    let _idleTimeout = null;
    let _idleThreshold = 60000; // مهلة الخمول: 60 ثانية

    // الدوال الخاصة
    const _logMessage = (message) => {
        console.log(`[تتبع المشاهدات المتطور]: ${message}`);
    };

    // جمع معلومات عن متصفح وجهاز المستخدم
    const _collectDeviceInfo = () => {
        const screenWidth = window.screen.width;
        const screenHeight = window.screen.height;
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        const pixelRatio = window.devicePixelRatio || 1;
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        const isTablet = /(iPad|tablet|Tablet)/i.test(navigator.userAgent);
        
        return {
            userAgent: navigator.userAgent,
            screenSize: `${screenWidth}x${screenHeight}`,
            viewportSize: `${viewportWidth}x${viewportHeight}`,
            pixelRatio: pixelRatio,
            deviceType: isMobile ? 'mobile' : (isTablet ? 'tablet' : 'desktop'),
            browserName: _getBrowserName(),
            os: _getOperatingSystem()
        };
    };

    // حساب اسم المتصفح
    const _getBrowserName = () => {
        const agent = navigator.userAgent;
        if (agent.indexOf("Chrome") > -1) return "Chrome";
        if (agent.indexOf("Safari") > -1) return "Safari";
        if (agent.indexOf("Firefox") > -1) return "Firefox";
        if (agent.indexOf("MSIE") > -1 || agent.indexOf("Trident") > -1) return "Internet Explorer";
        if (agent.indexOf("Edge") > -1) return "Edge";
        if (agent.indexOf("Opera") > -1) return "Opera";
        return "Unknown";
    };

    // حساب نظام التشغيل
    const _getOperatingSystem = () => {
        const agent = navigator.userAgent;
        if (agent.indexOf("Windows") > -1) return "Windows";
        if (agent.indexOf("Mac") > -1) return "MacOS";
        if (agent.indexOf("Android") > -1) return "Android";
        if (agent.indexOf("iOS") > -1 || agent.indexOf("iPhone") > -1 || agent.indexOf("iPad") > -1) return "iOS";
        if (agent.indexOf("Linux") > -1) return "Linux";
        return "Unknown";
    };

    // تحليل مستوى التفاعل للمستخدم
    const _calculateEngagementScore = () => {
        // حساب درجة التفاعل استنادًا إلى:
        // 1. المدة الزمنية
        const durationScore = Math.min(_totalTimeSpent / 10000, 5); // درجة أقصاها 5 نقاط للمدة
        
        // 2. عدد التفاعلات
        const interactionScore = Math.min(_interactionEvents / 5, 3); // درجة أقصاها 3 نقاط للتفاعلات
        
        // 3. عمق التمرير
        const scrollScore = Math.min(_scrollDepth / 20, 2); // درجة أقصاها 2 نقاط لعمق التمرير
        
        // إجمالي درجة التفاعل (من 10 نقاط)
        return Math.round((durationScore + interactionScore + scrollScore) * 10) / 10;
    };

    // إضافة حدث تفاعل وتحديث وقت آخر تفاعل
    const _updateInteraction = () => {
        _lastInteractionTime = Date.now();
        _interactionEvents++;
        _resetIdleTimeout();
    };

    // حساب عمق التمرير الحالي
    const _updateScrollDepth = () => {
        const documentHeight = Math.max(
            document.body.scrollHeight,
            document.body.offsetHeight,
            document.documentElement.clientHeight,
            document.documentElement.scrollHeight,
            document.documentElement.offsetHeight
        );
        
        const windowHeight = window.innerHeight;
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
        const trackLength = documentHeight - windowHeight;
        
        // حساب النسبة المئوية للتمرير
        const scrollPercentage = Math.floor((scrollTop / trackLength) * 100);
        
        // تحديث عمق التمرير إذا كان أعلى من القيمة الحالية
        if (scrollPercentage > _scrollDepth) {
            _scrollDepth = scrollPercentage;
        }
    };

    // تحديث حالة رؤية العنصر
    const _updateVisibility = () => {
        if (_currentItemId === null) return;
        
        // إذا كان المودال مفتوحًا، فإن العنصر مرئي
        const modalElement = document.getElementById('portfolio-modal');
        if (modalElement && modalElement.style.display === 'block') {
            if (!_isVisible) {
                _isVisible = true;
                _viewStartTime = Date.now();
                _startViewTimer();
                _logMessage(`بدء تتبع وقت المشاهدة للعنصر: ${_currentItemId}`);
            }
        } else {
            if (_isVisible) {
                _isVisible = false;
                _stopViewTimer();
                _logMessage(`توقف تتبع وقت المشاهدة للعنصر: ${_currentItemId}`);
            }
        }
    };

    // بدء مؤقت المشاهدة
    const _startViewTimer = () => {
        if (_viewTimerInterval) clearInterval(_viewTimerInterval);
        
        _viewTimerInterval = setInterval(() => {
            if (_isVisible && _isUserActive) {
                _totalTimeSpent += 1000; // إضافة ثانية واحدة
            }
        }, 1000);
    };

    // إيقاف مؤقت المشاهدة
    const _stopViewTimer = () => {
        if (_viewTimerInterval) {
            clearInterval(_viewTimerInterval);
            _viewTimerInterval = null;
        }
    };

    // إعادة ضبط مهلة الخمول
    const _resetIdleTimeout = () => {
        _isUserActive = true;
        
        if (_idleTimeout) {
            clearTimeout(_idleTimeout);
        }
        
        _idleTimeout = setTimeout(() => {
            _logMessage('اكتشاف خمول المستخدم - توقف مؤقت عن حساب وقت المشاهدة');
            _isUserActive = false;
        }, _idleThreshold);
    };

    // إرسال بيانات المشاهدة إلى الخادم
    const _sendViewData = (isFinalUpdate = false) => {
        if (_currentItemId === null) return;
        
        // تجميع بيانات المشاهدة الحالية
        const viewData = {
            itemId: _currentItemId,
            duration: _totalTimeSpent,
            interactionCount: _interactionEvents,
            scrollDepth: _scrollDepth,
            engagementScore: _calculateEngagementScore(),
            viewedAt: _viewStartTime ? new Date(_viewStartTime).toISOString() : null,
            deviceInfo: _viewData.deviceInfo || _collectDeviceInfo(),
            referrer: document.referrer || null,
            finalUpdate: isFinalUpdate
        };
        
        // إرسال البيانات إلى الخادم
        fetch(`/instagram/api/portfolio/${_currentItemId}/view`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(viewData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                _logMessage(`تم تحديث بيانات المشاهدة للعنصر ${_currentItemId} - المدة: ${_totalTimeSpent}ms، التفاعل: ${_interactionEvents}`);
            } else {
                console.error('فشل في تحديث بيانات المشاهدة:', data.error);
            }
        })
        .catch(error => {
            console.error('خطأ في إرسال بيانات المشاهدة:', error);
        });
    };

    // بدء التحديثات الدورية لبيانات المشاهدة
    const _startPeriodicUpdates = () => {
        if (_sendInterval) clearInterval(_sendInterval);
        
        _sendInterval = setInterval(() => {
            _sendViewData(false);
        }, _periodicUpdateInterval);
    };

    // إيقاف التحديثات الدورية
    const _stopPeriodicUpdates = () => {
        if (_sendInterval) {
            clearInterval(_sendInterval);
            _sendInterval = null;
        }
    };

    // تهيئة مستمعي الأحداث
    const _setupEventListeners = () => {
        // مستمع لفتح النافذة المنبثقة
        document.addEventListener('modalOpened', (event) => {
            const itemId = event.detail.itemId;
            if (itemId) {
                _trackItemView(itemId);
            }
        });
        
        // مستمع لإغلاق النافذة المنبثقة
        document.getElementById('close-modal').addEventListener('click', () => {
            _stopTracking();
        });
        
        // مستمعات لأحداث التفاعل
        const interactionEvents = ['click', 'touchstart', 'scroll', 'keypress', 'mousemove'];
        interactionEvents.forEach(eventType => {
            document.addEventListener(eventType, _updateInteraction, { passive: true });
        });
        
        // مستمع خاص للتمرير لتحديث عمق التمرير
        document.addEventListener('scroll', _updateScrollDepth, { passive: true });
        
        // مستمعات لمغادرة الصفحة
        window.addEventListener('beforeunload', () => {
            if (_currentItemId) {
                _sendViewData(true);
            }
        });
        
        // إضافة فحص الرؤية دوريًا
        setInterval(_updateVisibility, 1000);
    };

    // بدء تتبع مشاهدة عنصر
    const _trackItemView = (itemId) => {
        // إذا كان المستخدم يشاهد بالفعل عنصرًا، توقف عن تتبعه أولاً
        if (_currentItemId) {
            _stopTracking();
        }
        
        _currentItemId = itemId;
        _viewStartTime = Date.now();
        _lastInteractionTime = Date.now();
        _interactionEvents = 0;
        _scrollDepth = 0;
        _totalTimeSpent = 0;
        _isVisible = true;
        _isUserActive = true;
        
        // جمع معلومات الجهاز
        _viewData = {
            deviceInfo: _collectDeviceInfo()
        };
        
        _logMessage(`بدء تتبع المشاهدة للعنصر: ${itemId}`);
        
        // تسجيل المشاهدة الأولية
        _sendViewData(false);
        
        // بدء التتبع المستمر
        _startViewTimer();
        _startPeriodicUpdates();
        _resetIdleTimeout();
    };

    // إيقاف التتبع الحالي
    const _stopTracking = () => {
        if (!_currentItemId) return;
        
        _stopViewTimer();
        _stopPeriodicUpdates();
        
        // إرسال التحديث النهائي
        _sendViewData(true);
        
        _logMessage(`إيقاف تتبع المشاهدة للعنصر: ${_currentItemId} - المدة الإجمالية: ${_totalTimeSpent}ms`);
        
        // إعادة ضبط الحالة
        _currentItemId = null;
        _viewStartTime = null;
        _lastInteractionTime = null;
        _interactionEvents = 0;
        _scrollDepth = 0;
        _totalTimeSpent = 0;
        _isVisible = false;
        _viewData = {};
    };

    // الواجهة العامة
    return {
        // تهيئة نظام التتبع
        init: () => {
            if (_isInitialized) return;
            
            _logMessage('جاري تهيئة نظام تتبع المشاهدات المتطور...');
            
            _setupEventListeners();
            _isInitialized = true;
            
            _logMessage('تم تهيئة نظام تتبع المشاهدات المتطور بنجاح!');
        },
        
        // بدء تتبع مشاهدة مشروع محدد
        trackView: (itemId) => {
            _trackItemView(itemId);
        },
        
        // إيقاف التتبع
        stopTracking: () => {
            _stopTracking();
        },
        
        // الحصول على إحصائيات التتبع الحالية
        getStats: () => {
            return {
                itemId: _currentItemId,
                duration: _totalTimeSpent,
                interactionEvents: _interactionEvents,
                scrollDepth: _scrollDepth,
                engagementScore: _calculateEngagementScore(),
                isVisible: _isVisible,
                isUserActive: _isUserActive
            };
        }
    };
})();

// تلقائيًا عند تضمين هذا الملف، سيتم تنفيذ:
console.log('تم تحميل نظام تتبع المشاهدات المتطور');