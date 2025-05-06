
from app import app
import logging
import os
from flask import jsonify
from fix_modals_register import register_fix_modals
from fix_portfolio_modal_routes import init_portfolio_modal_fix
from telegram_test_routes import init_telegram_test_routes
from direct_telegram_test import init_direct_telegram

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تسجيل مسارات إصلاح النوافذ المنبثقة
app = register_fix_modals(app)
logger.info("تم تسجيل مسارات إصلاح النوافذ المنبثقة")

# تسجيل مسارات النافذة المنبثقة بنمط إنستغرام
app = init_portfolio_modal_fix(app)
logger.info("تم تسجيل مسارات النافذة المنبثقة بنمط إنستغرام")

# تسجيل مسارات اختبار تيليجرام
init_telegram_test_routes(app)
logger.info("تم تسجيل مسارات اختبار تيليجرام")

# تسجيل مسارات اختبار تلغرام المباشر
init_direct_telegram(app)
logger.info("تم تسجيل مسارات اختبار تلغرام المباشر")

# إضافة مسار فحص حالة التطبيق لـ Vercel
@app.route('/api/status')
def vercel_status_check():
    """مسار لفحص حالة التطبيق وإعداداته في Vercel"""
    env_vars = {
        "DATABASE_URL": os.environ.get("DATABASE_URL", "").split('@')[0] + '@[HIDDEN]' if os.environ.get("DATABASE_URL") else None,
        "SESSION_SECRET": "***" if os.environ.get("SESSION_SECRET") else None,
        "TELEGRAM_BOT_TOKEN": "***" if os.environ.get("TELEGRAM_BOT_TOKEN") else None,
        "TELEGRAM_CHAT_ID": "***" if os.environ.get("TELEGRAM_CHAT_ID") else None,
        "FLASK_SECRET_KEY": "***" if os.environ.get("FLASK_SECRET_KEY") else None,
        "SENDGRID_API_KEY": "***" if os.environ.get("SENDGRID_API_KEY") else None,
    }
    
    return jsonify({
        "status": "running",
        "environment": os.environ.get("VERCEL_ENV", os.environ.get("FLASK_ENV", "development")),
        "version": "1.0.0",
        "env_vars_status": env_vars
    })

if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0')
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise
