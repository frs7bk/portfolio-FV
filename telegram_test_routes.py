#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
مسارات اختبار إشعارات تيليجرام
الصفحة متاحة فقط للمسؤول
"""

import os
from datetime import datetime
from flask import Blueprint, render_template, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from telegram_service import send_telegram_message, format_contact_message, format_like_notification
from functools import wraps

# دالة التحقق من صلاحيات المسؤول
def admin_access_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('يجب تسجيل الدخول أولاً', 'danger')
            return redirect(url_for('auth.login'))
            
        if not current_user.is_admin():
            flash('لا تملك صلاحية الوصول إلى هذه الصفحة', 'danger')
            return redirect(url_for('index'))
            
        return f(*args, **kwargs)
    return decorated_function

# إنشاء بلوبرنت لمسارات اختبار تيليجرام
telegram_test = Blueprint('telegram_test', __name__, url_prefix='/telegram')

@telegram_test.route('/test', methods=['GET'])
@login_required
@admin_access_required
def telegram_test_page():
    """صفحة اختبار إشعارات تيليجرام"""
    # التحقق من وجود متغيرات البيئة لتيليجرام
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    return render_template('test_telegram.html', 
                          bot_token_exists=bool(bot_token), 
                          chat_id_exists=bool(chat_id))

@telegram_test.route('/test-notification', methods=['POST'])
@login_required
@admin_access_required
def send_test_notification():
    """إرسال إشعار اختباري عبر تيليجرام"""
    try:
        # إنشاء رسالة اختبار
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"""<b>✅ رسالة اختبار</b>

<b>الوقت:</b> {now}

تم إرسال هذه الرسالة من صفحة اختبار تيليجرام للتحقق من أن الإعدادات تعمل بشكل صحيح.

<i>إذا كنت ترى هذه الرسالة، فهذا يعني أن إعدادات تيليجرام تعمل بشكل صحيح! 🎉</i>"""
        
        # إرسال الرسالة
        success = send_telegram_message(message)
        
        if success:
            flash('تم إرسال رسالة الاختبار بنجاح! تحقق من تطبيق تيليجرام لديك.', 'success')
        else:
            flash('فشل إرسال رسالة الاختبار. تحقق من رموز الوصول لتيليجرام.', 'danger')
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'danger')
    
    return redirect(url_for('telegram_test.telegram_test_page'))

@telegram_test.route('/simulate-like', methods=['POST'])
@login_required
@admin_access_required
def simulate_like_notification():
    """محاكاة إشعار إعجاب بمشروع"""
    try:
        # معلومات المستخدم الافتراضية
        user_info = 'زائر - اختبار'
        
        # إنشاء الرسالة
        message = format_like_notification(user_info, 'مشروع', 'مشروع اختباري')
        
        # إرسال الرسالة
        success = send_telegram_message(message)
        
        if success:
            flash('تم إرسال إشعار الإعجاب بنجاح! تحقق من تطبيق تيليجرام لديك.', 'success')
        else:
            flash('فشل إرسال إشعار الإعجاب. تحقق من رموز الوصول لتيليجرام.', 'danger')
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'danger')
    
    return redirect(url_for('telegram_test.telegram_test_page'))

@telegram_test.route('/simulate-contact', methods=['POST'])
@login_required
@admin_access_required
def simulate_contact_notification():
    """محاكاة إشعار رسالة تواصل"""
    try:
        # معلومات الرسالة الافتراضية
        name = 'مستخدم اختباري'
        email = 'test@example.com'
        subject = 'اختبار الإشعارات'
        message_content = 'هذه رسالة اختبارية للتحقق من عمل نظام الإشعارات عبر تيليجرام. شكراً لكم.'
        
        # إنشاء الرسالة
        message = format_contact_message(name, email, message_content, subject)
        
        # إرسال الرسالة
        success = send_telegram_message(message)
        
        if success:
            flash('تم إرسال إشعار رسالة التواصل بنجاح! تحقق من تطبيق تيليجرام لديك.', 'success')
        else:
            flash('فشل إرسال إشعار رسالة التواصل. تحقق من رموز الوصول لتيليجرام.', 'danger')
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'danger')
    
    return redirect(url_for('telegram_test.telegram_test_page'))

# دالة لتسجيل البلوبرنت في تطبيق Flask
def init_telegram_test_routes(app):
    app.register_blueprint(telegram_test)