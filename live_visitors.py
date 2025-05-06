"""
نظام تتبع الزوار النشطين حاليًا على الموقع
يسمح بتتبع الزوار النشطين وإرسال إشعارات تلغرام عنهم
"""

import logging
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user

from models import Visitor
from telegram_service import send_telegram_message

# المتغيرات العامة لتتبع الزوار النشطين
live_visitors = {}
# قاموس لتخزين وقت آخر إشعار لكل زائر
last_notification = {}
# المدة الزمنية بين الإشعارات (ساعة واحدة)
NOTIFICATION_INTERVAL = 3600
# تتبع حركة الصفحات حسب الزائر
visitor_pages = defaultdict(list)

# إنشاء بلوبرنت للتعامل مع مسارات الزوار النشطين
live_bp = Blueprint('live_visitors', __name__, url_prefix='/api/live')

def update_live_visitor(visitor_id, visitor_info):
    """
    تحديث معلومات الزائر النشط وإرسال إشعار إذا لزم الأمر
    
    Args:
        visitor_id: معرف الزائر
        visitor_info: معلومات الزائر بما فيها عنوان IP ومعلومات المتصفح
    """
    # التحقق من متغيرات البيئة للتيليجرام
    import os
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    logging.info(f"ENVIRONMENT CHECK: Bot token exists: {bool(bot_token)}, Chat ID exists: {bool(chat_id)}")
    
    now = datetime.now()
    visitor_info['last_seen'] = now
    
    # التحقق مما إذا كان الزائر جديدًا (غير موجود في القائمة من قبل)
    is_new = visitor_id not in live_visitors
    logging.info(f"Visitor {visitor_id} is new: {is_new}")
    
    # تحديث معلومات الزائر
    live_visitors[visitor_id] = visitor_info
    
    # التحقق من وقت آخر إشعار
    last_notified = last_notification.get(visitor_id, datetime.min)
    time_since_last_notification = (now - last_notified).total_seconds()
    
    # إرسال إشعار إذا كان الزائر جديدًا أو مرت مدة كافية منذ آخر إشعار
    logging.info(f"NOTIFICATION CHECK: is_new={is_new}, time_since_last_notification={time_since_last_notification}, threshold={NOTIFICATION_INTERVAL}")
    if is_new or time_since_last_notification > NOTIFICATION_INTERVAL:
        # إرسال إشعار تلغرام عن الزائر النشط حاليًا
        try:
            send_live_visitor_notification(visitor_id, visitor_info, is_new)
            # تحديث وقت آخر إشعار
            last_notification[visitor_id] = now
        except Exception as e:
            logging.error(f"Error sending live visitor notification: {str(e)}")

def send_live_visitor_notification(visitor_id, visitor_info, is_new=False):
    """
    إرسال إشعار تلغرام عن الزائر النشط حاليًا
    
    Args:
        visitor_id: معرف الزائر
        visitor_info: معلومات الزائر
        is_new: هل هو زائر جديد أم لا
    """
    # تقرير مفصل للتتبع
    import os
    import inspect
    frame = inspect.currentframe()
    calling_func = inspect.getouterframes(frame)[1].function
    logging.info(f"Notification called from: {calling_func} for visitor {visitor_id}, is_new: {is_new}")
    
    # التحقق من متغيرات البيئة مرة أخرى
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    logging.info(f"DIRECT ENV CHECK IN send_live_visitor_notification: Bot token exists: {bool(bot_token)}, Chat ID exists: {bool(chat_id)}")
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ip_address = visitor_info.get('ip_address', 'غير معروف')
    user_agent = visitor_info.get('user_agent', 'غير معروف')
    current_page = visitor_info.get('current_page', '/')
    page_title = visitor_info.get('page_title', 'الصفحة الرئيسية')
    referer = visitor_info.get('referer', '')
    
    # تنسيق الرسالة
    if is_new:
        message_header = "<b>👀 زائر جديد على الموقع</b>"
    else:
        message_header = "<b>👀 زائر نشط حالياً على الموقع</b>"
    
    # إضافة معلومات المتصفح والجهاز
    browser_info = "غير معروف"
    device_info = "غير معروف"
    
    if user_agent:
        # محاولة تحديد نوع المتصفح
        if "Chrome" in user_agent:
            browser_info = "Google Chrome"
        elif "Firefox" in user_agent:
            browser_info = "Mozilla Firefox"
        elif "Safari" in user_agent:
            browser_info = "Safari"
        elif "Edge" in user_agent:
            browser_info = "Microsoft Edge"
        elif "Opera" in user_agent or "OPR" in user_agent:
            browser_info = "Opera"
        
        # محاولة تحديد نوع الجهاز
        if "Mobile" in user_agent:
            device_info = "هاتف محمول"
        elif "Tablet" in user_agent:
            device_info = "جهاز لوحي"
        elif "Android" in user_agent:
            device_info = "جهاز Android"
        elif "iPhone" in user_agent:
            device_info = "iPhone"
        elif "Windows" in user_agent:
            device_info = "حاسوب Windows"
        elif "Macintosh" in user_agent or "Mac OS" in user_agent:
            device_info = "حاسوب Mac"
        elif "Linux" in user_agent:
            device_info = "حاسوب Linux"
    
    # تجميع الصفحات التي زارها الزائر
    visited_pages = ", ".join([f"{page[0]} ({page[1]})" for page in visitor_pages.get(visitor_id, [])])[:200]
    if not visited_pages:
        visited_pages = f"{current_page} ({page_title})"
    
    referer_text = ""
    if referer:
        if "google.com" in referer:
            referer_text = "\n<b>المصدر:</b> بحث Google"
        elif "facebook.com" in referer:
            referer_text = "\n<b>المصدر:</b> Facebook"
        elif "twitter.com" in referer or "x.com" in referer:
            referer_text = "\n<b>المصدر:</b> Twitter"
        elif "instagram.com" in referer:
            referer_text = "\n<b>المصدر:</b> Instagram"
        elif "linkedin.com" in referer:
            referer_text = "\n<b>المصدر:</b> LinkedIn"
        else:
            referer_text = f"\n<b>المصدر:</b> {referer[:50]}"
    
    message = f"{message_header}\n\n"
    message += f"<b>معرف الزائر:</b> {visitor_id}\n"
    message += f"<b>عنوان IP:</b> {ip_address}\n"
    message += f"<b>المتصفح:</b> {browser_info}\n"
    message += f"<b>الجهاز:</b> {device_info}\n"
    message += f"<b>الوقت:</b> {now}\n"
    message += f"<b>الصفحة الحالية:</b> {current_page} ({page_title})"
    
    if referer_text:
        message += referer_text
    
    if visited_pages and visited_pages != f"{current_page} ({page_title})":
        message += f"\n\n<b>الصفحات التي تمت زيارتها:</b>\n{visited_pages}"
    
    try:
        result = send_telegram_message(message)
        logging.info(f"Result from send_telegram_message: {result}")
        return result
    except Exception as e:
        logging.error(f"Exception in send_live_visitor_notification: {str(e)}")
        raise e

def cleanup_inactive_visitors():
    """
    تنظيف قائمة الزوار غير النشطين (الذين مر على آخر نشاط لهم أكثر من 15 دقيقة)
    """
    now = datetime.now()
    inactive_threshold = now - timedelta(minutes=15)
    
    to_remove = []
    for visitor_id, visitor_info in live_visitors.items():
        if visitor_info['last_seen'] < inactive_threshold:
            to_remove.append(visitor_id)
    
    for visitor_id in to_remove:
        try:
            # إرسال إشعار بمغادرة الزائر (اختياري)
            # send_visitor_left_notification(visitor_id, live_visitors[visitor_id])
            # إزالة الزائر من القائمة
            del live_visitors[visitor_id]
            # إزالة سجل الصفحات المزارة
            if visitor_id in visitor_pages:
                del visitor_pages[visitor_id]
        except Exception as e:
            logging.error(f"Error cleaning up visitor {visitor_id}: {str(e)}")

def track_visitor_page(visitor_id, page_url, page_title=""):
    """
    تتبع صفحة زارها الزائر
    
    Args:
        visitor_id: معرف الزائر
        page_url: مسار URL للصفحة
        page_title: عنوان الصفحة
    """
    if not visitor_id or not page_url:
        logging.warning(f"محاولة تتبع صفحة غير صالحة: visitor_id={visitor_id}, page_url={page_url}")
        return
        
    # إذا لم يكن الزائر موجودًا في قائمة الزوار النشطين، أضفه
    if visitor_id not in live_visitors:
        logging.info(f"إضافة زائر جديد من تتبع الصفحة: {visitor_id}")
        update_live_visitor(visitor_id, {
            'ip_address': request.remote_addr if request else '0.0.0.0',
            'user_agent': request.headers.get('User-Agent', '') if request else '',
            'current_page': page_url,
            'page_title': page_title,
            'referer': request.headers.get('Referer', '') if request else ''
        })
    
    # الحفاظ على آخر 10 صفحات فقط للزائر
    if visitor_id in visitor_pages and len(visitor_pages[visitor_id]) >= 10:
        visitor_pages[visitor_id].pop(0)  # إزالة أقدم صفحة
    
    # استخدام الوقت الحالي لتمييز زيارات الصفحة نفسها في أوقات مختلفة
    current_time = datetime.now().strftime('%H:%M:%S')
    page_title_with_time = f"{page_title or page_url} ({current_time})"
    
    # إضافة الصفحة الجديدة مع تجنب التكرار المباشر
    page_info = (page_url, page_title_with_time)
    
    # إضافة الصفحة الجديدة
    if visitor_id not in visitor_pages:
        visitor_pages[visitor_id] = []
    visitor_pages[visitor_id].append(page_info)
    
    # تحديث الصفحة الحالية في معلومات الزائر
    if visitor_id in live_visitors:
        live_visitors[visitor_id]['current_page'] = page_url
        live_visitors[visitor_id]['page_title'] = page_title
        live_visitors[visitor_id]['last_seen'] = datetime.now()
        
    logging.debug(f"تم تتبع الصفحة: visitor_id={visitor_id}, page_url={page_url}, title={page_title}")
    # عودة بيانات الزائر المحدثة للتأكد من نجاح العملية
    return {
        'visitor_id': visitor_id,
        'pages_count': len(visitor_pages.get(visitor_id, [])),
        'current_page': page_url
    }

# تشغيل عملية التنظيف في خيط منفصل
cleanup_thread = None
should_stop_cleanup = False

def cleanup_thread_task():
    """
    مهمة خيط التنظيف - تنظيف الزوار غير النشطين كل دقيقة
    """
    global should_stop_cleanup
    while not should_stop_cleanup:
        try:
            cleanup_inactive_visitors()
        except Exception as e:
            logging.error(f"Error in cleanup thread: {str(e)}")
        time.sleep(60)  # انتظار دقيقة واحدة

def start_cleanup_thread():
    """
    بدء تشغيل خيط التنظيف
    """
    global cleanup_thread, should_stop_cleanup
    
    if cleanup_thread is None or not cleanup_thread.is_alive():
        should_stop_cleanup = False
        cleanup_thread = threading.Thread(target=cleanup_thread_task)
        cleanup_thread.daemon = True  # جعل الخيط daemon حتى يتوقف عند إيقاف التطبيق
        cleanup_thread.start()
        logging.info("Started live visitors cleanup thread")

def stop_cleanup_thread():
    """
    إيقاف خيط التنظيف
    """
    global should_stop_cleanup
    should_stop_cleanup = True
    logging.info("Stopping live visitors cleanup thread")

@live_bp.route('/visitors')
def get_live_visitors():
    """
    الحصول على قائمة الزوار النشطين حالياً - للمسؤول فقط
    """
    try:
        # التحقق من كون المستخدم مسجل الدخول
        if not current_user.is_authenticated:
            logging.error("غير مصرح بالوصول: المستخدم غير مسجل الدخول")
            # عرض قائمة فارغة بدلاً من رفض الوصول
            return jsonify({'count': 0, 'visitors': [], 'error': 'يرجى تسجيل الدخول'}), 200
            
        # التحقق من كون المستخدم مسؤولاً (مع تسجيل المعلومات للتصحيح)
        is_admin = False
        try:
            is_admin = current_user.is_admin() if hasattr(current_user, 'is_admin') else False
            logging.debug(f"معلومات المستخدم: ID={current_user.id}, اسم المستخدم={current_user.username}, مسؤول={is_admin}")
        except Exception as user_error:
            logging.error(f"خطأ أثناء التحقق من صلاحيات المستخدم: {str(user_error)}")
            
        # إضافة زوار إضافيين للاختبار إذا كانت القائمة فارغة
        if not live_visitors:
            # إضافة زائر نشط للاختبار
            update_live_visitor("test_visitor_1", {
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'current_page': '/test-page',
                'page_title': 'صفحة اختبار',
                'referer': 'https://google.com'
            })
            track_visitor_page("test_visitor_1", "/test-page", "صفحة اختبار")
            track_visitor_page("test_visitor_1", "/", "الصفحة الرئيسية")
            
            # إضافة المستخدم الحالي كزائر
            update_live_visitor(str(current_user.id), {
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'current_page': request.headers.get('Referer', '/'),
                'page_title': 'لوحة الإدارة',
                'referer': ''
            })
            track_visitor_page(str(current_user.id), "/admin/live-visitors", "صفحة الزوار النشطين")
    except Exception as e:
        logging.error(f"خطأ عام في واجهة الزوار النشطين: {str(e)}")
        # عرض قائمة فارغة في حالة حدوث خطأ
        return jsonify({'count': 0, 'visitors': [], 'error': str(e)}), 200
    
    visitors_data = []
    for visitor_id, visitor_info in live_visitors.items():
        visitors_data.append({
            'id': visitor_id,
            'ip_address': visitor_info.get('ip_address', ''),
            'last_seen': visitor_info.get('last_seen', datetime.now()).strftime('%Y-%m-%d %H:%M:%S'),
            'current_page': visitor_info.get('current_page', '/'),
            'page_title': visitor_info.get('page_title', ''),
            'user_agent': visitor_info.get('user_agent', ''),
            'referer': visitor_info.get('referer', ''),
            'visited_pages': visitor_pages.get(visitor_id, [])
        })
    
    return jsonify({
        'count': len(visitors_data),
        'visitors': visitors_data
    })

@live_bp.route('/track', methods=['POST'])
def track_live_visitor():
    """
    تتبع زائر نشط حالياً
    يمكن استخدام هذا من جانب العميل عبر طلب AJAX دوري
    """
    try:
        # فحص نوع البيانات المستلمة
        data = request.get_json() if request.is_json else request.form
        logging.debug(f"بيانات طلب التتبع: {data}")
        
        # الحصول على معرف الزائر بعدة طرق
        visitor_id = data.get('visitor_id') or request.cookies.get('visitor_id') or request.headers.get('X-Visitor-ID')
        
        # في حالة عدم وجود معرف، نقوم بإنشاء واحد جديد
        if not visitor_id:
            visitor_id = f"auto_{int(time.time())}_{request.remote_addr.replace('.', '_')}"
            logging.info(f"تم إنشاء معرف زائر تلقائي: {visitor_id}")
        
        # تسجيل معلومات الطلب للتصحيح
        logging.debug(f"طلب تتبع زائر - المعرف: {visitor_id}, العنوان: {request.remote_addr}")
        
        # تحسين جمع معلومات الزائر
        visitor_info = {
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'current_page': data.get('page_url') or request.headers.get('Referer', '/'),
            'page_title': data.get('page_title', ''),
            'referer': data.get('referer') or request.headers.get('X-Original-Referer', ''),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'is_authenticated': current_user.is_authenticated if hasattr(current_user, 'is_authenticated') else False,
            'user_id': current_user.id if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated else None
        }
        
        # تحديث معلومات الزائر وإرسال إشعار إذا لزم الأمر
        update_live_visitor(visitor_id, visitor_info)
        
        # تتبع الصفحة الحالية
        page_tracking_result = track_visitor_page(visitor_id, visitor_info['current_page'], visitor_info['page_title'])
        
        # في حالة تم استدعاء الواجهة بواسطة طلب عادي، نقوم بإنشاء رد بجوكي معرّف الزائر
        response = jsonify({
            'success': True, 
            'visitor_id': visitor_id,
            'tracking_info': page_tracking_result,
            'timestamp': visitor_info['timestamp'],
            'total_visitors': len(live_visitors)
        })
        
        # إضافة كوكي معرّف الزائر
        if 'visitor_id' not in request.cookies:
            expires = datetime.now() + timedelta(days=30)
            response.set_cookie('visitor_id', visitor_id, expires=expires, httponly=True, secure=True)
        
        return response
    
    except Exception as e:
        error_msg = f"خطأ في تتبع الزائر: {str(e)}"
        logging.error(error_msg)
        return jsonify({
            'error': error_msg, 
            'success': False,
            'visitor_count': len(live_visitors) 
        }), 500

@live_bp.route('/count')
def get_live_visitors_count():
    """
    الحصول على عدد الزوار النشطين حالياً
    """
    return jsonify({
        'count': len(live_visitors)
    })

def init_live_visitors_tracking(app):
    """
    تهيئة نظام تتبع الزوار النشطين
    
    Args:
        app: تطبيق Flask
    """
    app.register_blueprint(live_bp)
    start_cleanup_thread()
    
    # إغلاق خيط التنظيف عند إغلاق التطبيق
    @app.teardown_appcontext
    def cleanup_live_visitors(exception=None):
        stop_cleanup_thread()
