"""
خدمة التيليجرام لإرسال الإشعارات والتنبيهات عن النماذج والطلبات الجديدة والتعليقات وتفاعلات المستخدمين
وأيضاً لتوفير المصادقة الثنائية
"""

import os
import json
import logging
import requests
import secrets
import time
from datetime import datetime, timedelta
from flask import flash

def send_telegram_message(message):
    """
    إرسال رسالة إلى بوت التيليجرام
    
    Args:
        message (str): نص الرسالة المراد إرسالها
        
    Returns:
        bool: True إذا تم الإرسال بنجاح، False إذا فشل الإرسال
    """
    logging.info(f"Going to send Telegram message: {message[:50]}...")
    
    # استخدام متغيرات البيئة فقط
    try:
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        # طباعة المتغيرات البيئية المتاحة للتصحيح
        all_env_vars = {key: '***' if key in ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID'] else value[:10] + '...' if isinstance(value, str) and len(value) > 10 else value 
                       for key, value in os.environ.items()}
        logging.info(f"Available env vars: {all_env_vars}")
    except Exception as e:
        logging.error(f"Error accessing environment variables: {str(e)}")
        bot_token = None
        chat_id = None
    
    logging.info(f"Bot token exists: {bool(bot_token)}, Chat ID exists: {bool(chat_id)}")
    
    if not bot_token or not chat_id:
        logging.warning("Telegram configuration missing: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not found in environment variables.")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        # طباعة قيم المتغيرات للتصحيح (مع تعتيم التوكن)
        if bot_token:
            masked_token = bot_token[:5] + "..." + bot_token[-5:]
            logging.info(f"Using bot token: {masked_token}")
        logging.info(f"Using chat ID: {chat_id}")
        
        logging.info("Sending Telegram message...")
        response = requests.post(url, json=payload, timeout=10)
        logging.info(f"Telegram API response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                logging.info("Telegram message sent successfully")
                return True
            else:
                logging.error(f"Failed to send Telegram message: {result.get('description')}")
                return False
        else:
            logging.error(f"Failed to send Telegram message. Status code: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"Error sending Telegram message: {str(e)}")
        return False


def format_contact_message(name, email, message, subject=None):
    """
    تنسيق رسالة تواصل جديدة لإرسالها عبر التيليجرام
    
    Args:
        name (str): اسم المرسل
        email (str): البريد الإلكتروني للمرسل
        message (str): نص الرسالة
        subject (str, optional): موضوع الرسالة إذا كان متاحاً
        
    Returns:
        str: رسالة منسقة
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # تقصير الرسالة إذا كانت طويلة جداً
    if len(message) > 500:
        message = message[:497] + "..."
        
    formatted_message = f"""<b>🔔 رسالة جديدة من نموذج التواصل 📩</b>

<b>الاسم:</b> {name}
<b>البريد الإلكتروني:</b> {email}"""

    if subject:
        formatted_message += f"\n<b>الموضوع:</b> {subject}"
        
    formatted_message += f"""
<b>التاريخ:</b> {now}

<b>نص الرسالة:</b>
{message}

<i>يمكنك الرد على هذه الرسالة من لوحة التحكم.</i>"""

    return formatted_message


def format_portfolio_comment(name, portfolio_item, comment, rating=None):
    """
    تنسيق تعليق جديد على مشروع في معرض الأعمال
    
    Args:
        name (str): اسم المعلق
        portfolio_item (str): عنوان المشروع
        comment (str): نص التعليق
        rating (int, optional): تقييم المشروع إذا كان متاحاً
        
    Returns:
        str: رسالة منسقة
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # تقصير التعليق إذا كان طويلاً جداً
    if len(comment) > 500:
        comment = comment[:497] + "..."
        
    formatted_message = f"""<b>💬 تعليق جديد على معرض الأعمال 📊</b>

<b>الاسم:</b> {name}
<b>المشروع:</b> {portfolio_item}"""

    if rating:
        formatted_message += f"\n<b>التقييم:</b> {'⭐' * rating}"
        
    formatted_message += f"""
<b>التاريخ:</b> {now}

<b>نص التعليق:</b>
{comment}

<i>يمكنك مراجعة التعليق من لوحة التحكم.</i>"""

    return formatted_message


def format_testimonial(name, company, content, rating):
    """
    تنسيق شهادة جديدة من العملاء
    
    Args:
        name (str): اسم العميل
        company (str): اسم الشركة
        content (str): نص الشهادة
        rating (int): تقييم العميل
        
    Returns:
        str: رسالة منسقة
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # تقصير النص إذا كان طويلاً جداً
    if len(content) > 500:
        content = content[:497] + "..."
        
    formatted_message = f"""<b>🌟 شهادة جديدة من عميل 👤</b>

<b>الاسم:</b> {name}"""

    if company:
        formatted_message += f"\n<b>الشركة:</b> {company}"
        
    formatted_message += f"""
<b>التقييم:</b> {'⭐' * rating}
<b>التاريخ:</b> {now}

<b>نص الشهادة:</b>
{content}

<i>يمكنك مراجعة الشهادة من لوحة التحكم.</i>"""

    return formatted_message


def format_order_notification(name, service, details, email=None, phone=None):
    """
    تنسيق طلب خدمة جديد
    
    Args:
        name (str): اسم العميل
        service (str): نوع الخدمة المطلوبة
        details (str): تفاصيل الطلب
        email (str, optional): البريد الإلكتروني للعميل
        phone (str, optional): رقم هاتف العميل
        
    Returns:
        str: رسالة منسقة
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # تقصير التفاصيل إذا كانت طويلة جداً
    if len(details) > 500:
        details = details[:497] + "..."
        
    formatted_message = f"""<b>🔔 طلب خدمة جديد 📋</b>

<b>الاسم:</b> {name}
<b>الخدمة المطلوبة:</b> {service}"""

    if email:
        formatted_message += f"\n<b>البريد الإلكتروني:</b> {email}"
        
    if phone:
        formatted_message += f"\n<b>رقم الهاتف:</b> {phone}"
        
    formatted_message += f"""
<b>التاريخ:</b> {now}

<b>تفاصيل الطلب:</b>
{details}

<i>يمكنك إدارة هذا الطلب من لوحة التحكم.</i>"""

    return formatted_message


def format_user_registration(username, email, display_name=None):
    """
    تنسيق إشعار تسجيل مستخدم جديد
    
    Args:
        username (str): اسم المستخدم
        email (str): البريد الإلكتروني
        display_name (str, optional): الاسم الظاهر للمستخدم
        
    Returns:
        str: رسالة منسقة
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    formatted_message = f"""<b>👤 تسجيل مستخدم جديد ✅</b>

<b>اسم المستخدم:</b> {username}
<b>البريد الإلكتروني:</b> {email}"""

    if display_name:
        formatted_message += f"\n<b>الاسم الظاهر:</b> {display_name}"
        
    formatted_message += f"""
<b>التاريخ:</b> {now}

<i>يمكنك إدارة المستخدمين من لوحة التحكم.</i>"""

    return formatted_message


def format_comment_notification(user_info, portfolio_title, comment_text, is_reply=False, parent_comment=None):
    """
    تنسيق إشعار تعليق جديد أو رد على تعليق
    
    Args:
        user_info (str): معلومات المستخدم (اسم المستخدم أو اسم الزائر)
        portfolio_title (str): عنوان المشروع
        comment_text (str): نص التعليق
        is_reply (bool, optional): هل هو رد على تعليق آخر
        parent_comment (str, optional): نص التعليق الأصلي إذا كان رداً
        
    Returns:
        str: رسالة منسقة
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # تقصير نص التعليق إذا كان طويلاً جداً
    if len(comment_text) > 500:
        comment_text = comment_text[:497] + "..."
    
    if is_reply and parent_comment:
        # تقصير نص التعليق الأصلي إذا كان طويلاً جداً
        if len(parent_comment) > 200:
            parent_comment = parent_comment[:197] + "..."
            
        formatted_message = f"""<b>💬 رد جديد على تعليق 📝</b>

<b>المستخدم:</b> {user_info}
<b>المشروع:</b> {portfolio_title}
<b>التاريخ:</b> {now}

<b>التعليق الأصلي:</b>
{parent_comment}

<b>الرد:</b>
{comment_text}

<i>يمكنك إدارة التعليقات من لوحة التحكم.</i>"""
    else:
        formatted_message = f"""<b>💬 تعليق جديد 📝</b>

<b>المستخدم:</b> {user_info}
<b>المشروع:</b> {portfolio_title}
<b>التاريخ:</b> {now}

<b>التعليق:</b>
{comment_text}

<i>يمكنك إدارة التعليقات من لوحة التحكم.</i>"""

    return formatted_message


def format_like_notification(user_info, content_type, content_title):
    """
    تنسيق إشعار إعجاب جديد
    
    Args:
        user_info (str): معلومات المستخدم (اسم المستخدم أو "زائر")
        content_type (str): نوع المحتوى (مشروع، تعليق، إلخ)
        content_title (str): عنوان المحتوى
        
    Returns:
        str: رسالة منسقة
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    formatted_message = f"""<b>❤️ إعجاب جديد 👍</b>

<b>المستخدم:</b> {user_info}
<b>المحتوى:</b> {content_type}
<b>العنوان:</b> {content_title}
<b>التاريخ:</b> {now}

<i>يمكنك مشاهدة الإعجابات من لوحة التحكم.</i>"""

    return formatted_message


# ===== وظائف المصادقة الثنائية =====

def generate_2fa_code(user_id, email):
    """
    إنشاء رمز المصادقة الثنائية وإرساله عبر تليجرام
    
    Args:
        user_id (int): معرف المستخدم
        email (str): البريد الإلكتروني للمستخدم
        
    Returns:
        str: رمز المصادقة الثنائية المولد
    """
    # إنشاء رمز مكون من 6 أرقام
    two_factor_code = ''.join(secrets.choice('0123456789') for _ in range(6))
    
    # إرسال الرمز عبر تليجرام
    message = f"""<b>🔐 رمز المصادقة الثنائية 🔐</b>

<b>المستخدم:</b> {email}
<b>الرمز:</b> <code>{two_factor_code}</code>

<i>هذا الرمز صالح لمدة 10 دقائق فقط. لا تشاركه مع أي شخص.</i>"""

    # إرسال الرسالة
    send_telegram_message(message)
    
    # إرجاع الرمز لتخزينه مؤقتًا
    return two_factor_code


def test_telegram_notification():
    """
    إرسال إشعار تجريبي للتحقق من أن إعدادات تيليجرام تعمل بشكل صحيح
    
    Returns:
        tuple: (نجاح العملية, رسالة للمستخدم)
    """
    try:
        # التحقق من وجود متغيرات البيئة
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            return False, "لم يتم العثور على متغيرات البيئة TELEGRAM_BOT_TOKEN أو TELEGRAM_CHAT_ID"
        
        # إنشاء رسالة اختبار
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"""<b>✅ رسالة اختبار من موقعك</b>

<b>الوقت:</b> {now}

تم إرسال هذه الرسالة من صفحة إعدادات تيليجرام في لوحة التحكم للتحقق من أن الإعدادات تعمل بشكل صحيح.

إذا كنت ترى هذه الرسالة، فهذا يعني أن إعدادات تيليجرام تعمل بشكل صحيح! 🎉"""
        
        # محاولة إرسال الرسالة
        success = send_telegram_message(message)
        
        if success:
            return True, "تم إرسال رسالة الاختبار بنجاح! تحقق من تطبيق تيليجرام لديك."
        else:
            return False, "فشل إرسال رسالة الاختبار. تحقق من أن متغيرات البيئة صحيحة."
    
    except Exception as e:
        logging.error(f"Error in test_telegram_notification: {str(e)}")
        return False, f"حدث خطأ أثناء اختبار الاتصال: {str(e)}"


def format_security_alert(email, action, ip_address, user_agent=None, location=None):
    """
    تنسيق تنبيه أمني وإرساله عبر تليجرام
    
    Args:
        email (str): البريد الإلكتروني للمستخدم
        action (str): نوع العملية (تسجيل دخول، تغيير كلمة المرور، إلخ)
        ip_address (str): عنوان IP
        user_agent (str, optional): معلومات المتصفح
        location (str, optional): الموقع الجغرافي (إذا كان متاحًا)
        
    Returns:
        bool: نجاح أو فشل إرسال التنبيه
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    formatted_message = f"""<b>🚨 تنبيه أمني 🚨</b>

<b>الحساب:</b> {email}
<b>العملية:</b> {action}
<b>الوقت:</b> {now}
<b>عنوان IP:</b> {ip_address}"""

    if user_agent:
        formatted_message += f"\n<b>المتصفح:</b> {user_agent}"
        
    if location:
        formatted_message += f"\n<b>الموقع:</b> {location}"
        
    formatted_message += "\n\n<i>إذا لم تكن أنت من قام بهذه العملية، يرجى تغيير كلمة المرور فوراً.</i>"

    # إرسال التنبيه
    return send_telegram_message(formatted_message)


def verify_telegram_chat(verification_code, expected_code):
    """
    التحقق من رمز ربط حساب تليجرام
    
    Args:
        verification_code (str): الرمز المدخل من قبل المستخدم
        expected_code (str): الرمز المتوقع
        
    Returns:
        bool: صحة الرمز
    """
    return verification_code == expected_code


def setup_telegram_2fa(user_id, username, email):
    """
    إعداد المصادقة الثنائية عبر تليجرام لمستخدم جديد
    
    Args:
        user_id (int): معرف المستخدم
        username (str): اسم المستخدم
        email (str): البريد الإلكتروني
        
    Returns:
        str: رمز التحقق لربط الحساب
    """
    # إنشاء رمز فريد لربط الحساب
    verification_code = ''.join(secrets.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(8))
    
    # إرسال رسالة الترحيب والتعليمات
    message = f"""<b>👋 مرحباً بك في نظام المصادقة الثنائية</b>

<b>المستخدم:</b> {username}
<b>البريد الإلكتروني:</b> {email}

لربط حسابك مع بوت التليجرام وتفعيل المصادقة الثنائية، يرجى إرسال الرمز التالي للبوت:

<code>{verification_code}</code>

<i>هذا الرمز صالح لمدة 24 ساعة. لا تشاركه مع أي شخص.</i>"""

    # إرسال الرسالة
    send_telegram_message(message)
    
    # إرجاع الرمز للتحقق لاحقًا
    return verification_code


def format_visit_notification(user_info, project_title, ip_address, user_agent):
    """
    تنسيق إشعار زيارة جديدة لمشروع
    
    Args:
        user_info (str): معلومات المستخدم أو الزائر
        project_title (str): عنوان المشروع
        ip_address (str): عنوان IP للزائر
        user_agent (str): معلومات متصفح الزائر
        
    Returns:
        str: رسالة الإشعار المنسقة
    """
    # استخراج معلومات المتصفح والجهاز من User-Agent
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
        elif "MSIE" in user_agent or "Trident" in user_agent:
            browser_info = "Internet Explorer"
            
        # محاولة تحديد نوع الجهاز
        if "Mobile" in user_agent:
            device_info = "هاتف محمول"
        elif "Tablet" in user_agent:
            device_info = "جهاز لوحي"
        elif "Android" in user_agent:
            device_info = "جهاز Android"
        elif "iPhone" in user_agent:
            device_info = "iPhone"
        elif "iPad" in user_agent:
            device_info = "iPad"
        elif "Windows" in user_agent:
            device_info = "حاسوب Windows"
        elif "Macintosh" in user_agent or "Mac OS" in user_agent:
            device_info = "حاسوب Mac"
        elif "Linux" in user_agent:
            device_info = "حاسوب Linux"
    
    # الوقت الحالي
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # تنسيق الرسالة
    message = f"""<b>👁️ مشاهدة جديدة لمشروع</b>

<b>الزائر:</b> {user_info}
<b>المشروع:</b> "{project_title}"
<b>عنوان IP:</b> {ip_address}
<b>المتصفح:</b> {browser_info}
<b>الجهاز:</b> {device_info}
<b>التاريخ:</b> {now}

<i>تمت مشاهدة المشروع لأول مرة من هذا الزائر.</i>
"""
    
    return message