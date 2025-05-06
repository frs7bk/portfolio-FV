#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
سكربت اختبار الاتصال بتيليجرام
"""

import os
import requests
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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
        
        if not bot_token or not chat_id:
            logging.warning("Telegram configuration missing: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not found in environment variables.")
            return False
        
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

def main():
    # إنشاء رسالة اختبار
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"""<b>✅ رسالة اختبار من سكربت test_telegram.py</b>

<b>الوقت:</b> {now}

تم إرسال هذه الرسالة من سكربت test_telegram.py للتحقق من أن إعدادات تيليجرام تعمل بشكل صحيح.

<i>إذا كنت ترى هذه الرسالة، فهذا يعني أن إعدادات تيليجرام تعمل بشكل صحيح! 🎉</i>"""
    
    # محاولة إرسال الرسالة
    success = send_telegram_message(message)
    
    if success:
        print("✅ تم إرسال رسالة الاختبار بنجاح! تحقق من تطبيق تيليجرام لديك.")
        return True
    else:
        print("❌ فشل إرسال رسالة الاختبار. تحقق من رموز الوصول لتيليجرام.")
        print("تأكد من وجود المتغيرات البيئية TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID")
        return False

if __name__ == "__main__":
    main()
