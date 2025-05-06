"""
اختبار الاتصال بتلغرام
هذا السكربت يختبر اتصال تلغرام فوراً
"""

import os
import logging
from datetime import datetime
import requests

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_telegram_message(message):
    """
    إرسال رسالة إلى بوت التيليجرام
    
    Args:
        message (str): نص الرسالة المراد إرسالها
        
    Returns:
        bool: True إذا تم الإرسال بنجاح، False إذا فشل الإرسال
    """
    logging.info(f"Going to send Telegram message: {message[:50]}...")
    
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

def send_test_message():
    """إرسال رسالة اختبارية"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"""<b>✅ اختبار الاتصال بتلغرام</b>

<b>الوقت:</b> {now}

هذه رسالة تأكيد للتحقق من أن نظام الإشعارات عبر تلغرام يعمل بشكل صحيح.

تم إرسال هذه الرسالة بواسطة سكربت الاختبار.

<i>إذا تلقيت هذه الرسالة، فهذا يعني أن إعدادات تلغرام تعمل بشكل صحيح!</i>"""
    
    # إرسال الرسالة
    result = send_telegram_message(message)
    
    if result:
        logging.info("تم إرسال رسالة الاختبار بنجاح!")
        return True, "تم إرسال رسالة الاختبار بنجاح! تحقق من تطبيق تلغرام لديك."
    else:
        logging.error("فشل في إرسال رسالة الاختبار!")
        return False, "فشل في إرسال رسالة الاختبار! تحقق من صحة التوكن وآيدي المحادثة."

if __name__ == "__main__":
    # التحقق من وجود المتغيرات البيئية
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("خطأ: لم يتم العثور على متغيرات البيئة TELEGRAM_BOT_TOKEN أو TELEGRAM_CHAT_ID")
        exit(1)
    
    print("جاري إرسال رسالة اختبارية إلى تلغرام...")
    success, message = send_test_message()
    print(message)
    
    if success:
        print("تم الاختبار بنجاح! يمكنك الآن استخدام خدمة الإشعارات عبر تلغرام.")
    else:
        print("فشل الاختبار! يرجى التحقق من التوكن وآيدي المحادثة.")