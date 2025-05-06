"""
مسار لاختبار إشعارات تيليجرام
هذا الملف يضيف مساراً بسيطاً لاختبار اتصال تيليجرام
"""

from flask import Blueprint, jsonify, current_app
from datetime import datetime
import os
import logging
import requests

# إنشاء بلوبرنت
telegram_tester = Blueprint('telegram_tester', __name__, url_prefix='/telegram-test')

@telegram_tester.route('/test', methods=['GET'])
def test_telegram():
    """اختبار إرسال رسالة عبر تيليجرام"""
    # إنشاء رسالة اختبار
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"""<b>✅ اختبار الاتصال بتلغرام</b>

<b>الوقت:</b> {now}

هذه رسالة تأكيد للتحقق من أن نظام الإشعارات عبر تلغرام يعمل بشكل صحيح.

تم إرسال هذه الرسالة من خلال مسار اختبار مخصص.

<i>إذا تلقيت هذه الرسالة، فهذا يعني أن إعدادات تلغرام تعمل بشكل صحيح!</i>"""
    
    # محاولة إرسال الرسالة
    try:
        # استرجاع متغيرات البيئة
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        # التحقق من وجود المتغيرات
        if not bot_token or not chat_id:
            return jsonify({
                'success': False,
                'message': 'لم يتم العثور على متغيرات البيئة TELEGRAM_BOT_TOKEN أو TELEGRAM_CHAT_ID'
            })
        
        # تسجيل المعلومات
        current_app.logger.info(f"Bot token exists: {bool(bot_token)}, Chat ID exists: {bool(chat_id)}")
        
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
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                current_app.logger.info("Telegram message sent successfully")
                return jsonify({
                    'success': True,
                    'message': 'تم إرسال رسالة الاختبار بنجاح! تحقق من تطبيق تلغرام لديك.'
                })
            else:
                error_msg = result.get('description', 'خطأ غير معروف')
                current_app.logger.error(f"Failed to send Telegram message: {error_msg}")
                return jsonify({
                    'success': False,
                    'message': f'فشل إرسال رسالة الاختبار: {error_msg}'
                })
        else:
            current_app.logger.error(f"Failed to send Telegram message. Status code: {response.status_code}, Response: {response.text}")
            return jsonify({
                'success': False,
                'message': f'فشل إرسال رسالة الاختبار. رمز الاستجابة: {response.status_code}'
            })
            
    except Exception as e:
        current_app.logger.error(f"Error sending Telegram message: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        })

def init_telegram_tester(app):
    """تسجيل مسارات اختبار تيليجرام"""
    app.register_blueprint(telegram_tester)
    app.logger.info("تم تسجيل مسارات اختبار تيليجرام")