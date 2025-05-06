"""
مسار مباشر لاختبار اتصال تلغرام
"""

from flask import Blueprint, jsonify, request, render_template, current_app, redirect, url_for, flash, session
from datetime import datetime
import os
import logging
import requests

from telegram_service import (
    send_telegram_message, 
    format_contact_message, 
    format_comment_notification, 
    format_portfolio_comment, 
    format_testimonial, 
    format_order_notification, 
    format_like_notification, 
    format_user_registration
)

# إنشاء بلوبرنت
direct_telegram = Blueprint('direct_telegram', __name__, url_prefix='/direct-telegram')

@direct_telegram.route('/', methods=['GET'])
def test_page():
    """صفحة اختبار التلغرام"""
    return render_template('direct_telegram_test.html')
    
@direct_telegram.route('/status', methods=['GET'])
def telegram_status():
    """التحقق من حالة اتصال تلغرام"""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    return jsonify({
        'bot_token_exists': bool(bot_token),
        'chat_id_exists': bool(chat_id)
    })

@direct_telegram.route('/test', methods=['GET'])
def test_telegram():
    """اختبار إرسال رسالة عبر تلغرام"""
    # إنشاء رسالة اختبار
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"""<b>✅ اختبار الاتصال بتلغرام</b>

<b>الوقت:</b> {now}

هذه رسالة تأكيد للتحقق من أن نظام الإشعارات عبر تلغرام يعمل بشكل صحيح.

تم طلب هذا الاختبار من لوحة التحكم.

<i>إذا تلقيت هذه الرسالة، فهذا يعني أن إعدادات تلغرام تعمل بشكل صحيح!</i>"""
    
    # محاولة إرسال الرسالة
    try:
        # استرجاع متغيرات البيئة
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        # طباعة المتغيرات للتصحيح (مع إخفاء التوكن)
        if bot_token:
            masked_token = bot_token[:4] + "..." + bot_token[-4:]
            current_app.logger.info(f"Using bot token: {masked_token}")
        current_app.logger.info(f"Using chat ID: {chat_id}")
        
        # التحقق من وجود المتغيرات
        if not bot_token or not chat_id:
            flash('لم يتم العثور على متغيرات البيئة المطلوبة (TELEGRAM_BOT_TOKEN أو TELEGRAM_CHAT_ID)', 'danger')
            return jsonify({
                'success': False,
                'message': 'لم يتم العثور على متغيرات البيئة TELEGRAM_BOT_TOKEN أو TELEGRAM_CHAT_ID'
            })
        
        # إرسال الرسالة
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        current_app.logger.info("Sending Telegram message...")
        response = requests.post(url, json=payload, timeout=10)
        current_app.logger.info(f"Telegram API response status: {response.status_code}")
        current_app.logger.info(f"Telegram API response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                flash('تم إرسال رسالة الاختبار بنجاح! تحقق من تطبيق تلغرام لديك.', 'success')
                return jsonify({
                    'success': True,
                    'message': 'تم إرسال رسالة الاختبار بنجاح! تحقق من تطبيق تلغرام لديك.'
                })
            else:
                error_msg = result.get('description', 'خطأ غير معروف')
                flash(f'فشل إرسال رسالة الاختبار: {error_msg}', 'danger')
                return jsonify({
                    'success': False,
                    'message': f'فشل إرسال رسالة الاختبار: {error_msg}'
                })
        else:
            flash(f'فشل إرسال رسالة الاختبار. رمز الاستجابة: {response.status_code}، النص: {response.text}', 'danger')
            return jsonify({
                'success': False,
                'message': f'فشل إرسال رسالة الاختبار. رمز الاستجابة: {response.status_code}'
            })
            
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'danger')
        return jsonify({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        })

@direct_telegram.route('/test-contact', methods=['GET'])
def test_contact_message():
    """اختبار إرسال إشعار رسالة تواصل"""
    formatted_message = format_contact_message(
        name="زائر جديد",
        email="visitor@example.com",
        message="هذه رسالة اختبار لنظام الإشعارات. أرغب في الاستفسار عن خدماتكم.",
        subject="استفسار عن الخدمات"
    )
    
    success = send_telegram_message(formatted_message)
    
    return jsonify({
        'success': success,
        'message': 'تم إرسال إشعار رسالة التواصل بنجاح' if success else 'فشل إرسال إشعار رسالة التواصل'
    })

@direct_telegram.route('/test-comment', methods=['GET'])
def test_comment():
    """اختبار إرسال إشعار تعليق جديد"""
    formatted_message = format_comment_notification(
        user_info="Ahmed Mohamed",
        portfolio_title="تصميم موقع متجر إلكتروني",
        comment_text="تصميم رائع وألوان متناسقة وسرعة تحميل ممتازة!"
    )
    
    success = send_telegram_message(formatted_message)
    
    return jsonify({
        'success': success,
        'message': 'تم إرسال إشعار التعليق بنجاح' if success else 'فشل إرسال إشعار التعليق'
    })

@direct_telegram.route('/test-testimonial', methods=['GET'])
def test_testimonial():
    """اختبار إرسال إشعار تقييم جديد"""
    formatted_message = format_testimonial(
        name="سارة أحمد",
        company="شركة المستقبل",
        content="تجربة رائعة مع الفريق. العمل احترافي والتسليم في الموعد المحدد. سأتعامل معهم مرة أخرى بكل تأكيد.",
        rating=5
    )
    
    success = send_telegram_message(formatted_message)
    
    return jsonify({
        'success': success,
        'message': 'تم إرسال إشعار التقييم بنجاح' if success else 'فشل إرسال إشعار التقييم'
    })

@direct_telegram.route('/test-service', methods=['GET'])
def test_service_request():
    """اختبار إرسال إشعار طلب خدمة"""
    formatted_message = format_order_notification(
        name="محمد علي",
        service="تصميم وبرمجة موقع شركة",
        details="أحتاج إلى موقع لشركتي يحتوي على نظام حجز ودفع إلكتروني",
        email="mohamed@example.com",
        phone="+2010000000"
    )
    
    success = send_telegram_message(formatted_message)
    
    return jsonify({
        'success': success,
        'message': 'تم إرسال إشعار طلب الخدمة بنجاح' if success else 'فشل إرسال إشعار طلب الخدمة'
    })

@direct_telegram.route('/test-like', methods=['GET'])
def test_like():
    """اختبار إرسال إشعار إعجاب جديد"""
    formatted_message = format_like_notification(
        user_info="زائر (غير مسجل)",
        content_type="مشروع",
        content_title="تطبيق إدارة المهام"
    )
    
    success = send_telegram_message(formatted_message)
    
    return jsonify({
        'success': success,
        'message': 'تم إرسال إشعار الإعجاب بنجاح' if success else 'فشل إرسال إشعار الإعجاب'
    })

@direct_telegram.route('/test-registration', methods=['GET'])
def test_registration():
    """اختبار إرسال إشعار تسجيل مستخدم جديد"""
    formatted_message = format_user_registration(
        username="new_user",
        email="newuser@example.com",
        display_name="مستخدم جديد"
    )
    
    success = send_telegram_message(formatted_message)
    
    return jsonify({
        'success': success,
        'message': 'تم إرسال إشعار تسجيل المستخدم بنجاح' if success else 'فشل إرسال إشعار تسجيل المستخدم'
    })
        
def init_direct_telegram(app):
    """تسجيل مسارات اختبار تلغرام المباشرة"""
    app.register_blueprint(direct_telegram)
    app.logger.info("تم تسجيل مسارات اختبار تلغرام المباشرة")