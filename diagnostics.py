"""
أداة تشخيص للتحقق من صحة التثبيت والإعدادات
"""
import os
import sys
import logging
import platform
import importlib
from sqlalchemy import create_engine, text, inspect
import traceback

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """التحقق من إعدادات البيئة"""
    logger.info("جاري التحقق من إعدادات البيئة...")
    
    results = {
        "system": {
            "os": f"{platform.system()} {platform.release()}",
            "python_version": platform.python_version(),
            "working_directory": os.getcwd()
        },
        "environment_variables": {
            "database_url_exists": bool(os.environ.get("DATABASE_URL")),
            "flask_secret_key_exists": bool(os.environ.get("FLASK_SECRET_KEY")),
            "session_secret_exists": bool(os.environ.get("SESSION_SECRET")),
            "sendgrid_api_key_exists": bool(os.environ.get("SENDGRID_API_KEY")),
            "telegram_bot_token_exists": bool(os.environ.get("TELEGRAM_BOT_TOKEN")),
            "telegram_chat_id_exists": bool(os.environ.get("TELEGRAM_CHAT_ID")),
        },
        "directories": {}
    }
    
    # فحص المجلدات المطلوبة
    required_dirs = [
        "static",
        "static/uploads",
        "static/uploads/profile",
        "static/uploads/portfolio",
        "static/uploads/carousel",
        "static/uploads/services",
        "static/uploads/projects",
        "templates",
        "instance"
    ]
    
    for directory in required_dirs:
        results["directories"][directory] = os.path.exists(directory)
    
    return results

def check_database():
    """التحقق من قاعدة البيانات"""
    logger.info("جاري التحقق من قاعدة البيانات...")
    
    results = {
        "connected": False,
        "tables": [],
        "admin_user_exists": False,
        "error": None
    }
    
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        results["error"] = "DATABASE_URL غير موجود في متغيرات البيئة"
        return results
    
    # تحويل postgres:// إلى postgresql:// إذا لزم الأمر
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    try:
        # إنشاء محرك قاعدة البيانات
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={"connect_timeout": 10}
        )
        
        # اختبار الاتصال
        with engine.connect() as connection:
            # التحقق من أن الاتصال يعمل
            connection.execute(text("SELECT 1"))
            results["connected"] = True
            
            # الحصول على قائمة الجداول
            inspector = inspect(engine)
            results["tables"] = inspector.get_table_names()
            
            # التحقق من وجود مستخدم مسؤول
            if "user" in results["tables"]:
                try:
                    admin_query = connection.execute(text("SELECT COUNT(*) FROM \"user\" WHERE role = 'admin'"))
                    admin_count = admin_query.fetchone()[0]
                    results["admin_user_exists"] = admin_count > 0
                    results["admin_count"] = admin_count
                except Exception as e:
                    results["admin_check_error"] = str(e)
            
    except Exception as e:
        results["error"] = str(e)
        results["traceback"] = traceback.format_exc()
    
    return results

def check_installed_packages():
    """التحقق من المكتبات المثبتة"""
    logger.info("جاري التحقق من المكتبات المثبتة...")
    
    required_packages = [
        "flask",
        "flask_login",
        "flask_sqlalchemy",
        "flask_wtf",
        "sqlalchemy",
        "werkzeug",
        "gunicorn",
        "sendgrid"
    ]
    
    results = {}
    for package in required_packages:
        try:
            module = importlib.import_module(package)
            results[package] = {
                "installed": True,
                "version": getattr(module, "__version__", "غير معروف")
            }
        except ImportError:
            results[package] = {
                "installed": False
            }
    
    return results

def check_files():
    """التحقق من الملفات الأساسية"""
    logger.info("جاري التحقق من الملفات الأساسية...")
    
    required_files = [
        "main.py",
        "app.py",
        "models.py",
        "forms.py",
        "database.py",
        "render.yaml",
        "render_setup.py",
        "test_database_connection.py",
        "templates/index.html",
        "templates/admin/login.html"
    ]
    
    results = {}
    for file_path in required_files:
        results[file_path] = os.path.exists(file_path)
    
    return results

def run_diagnostics():
    """تشغيل التشخيص الكامل"""
    logger.info("بدء تشخيص المشروع...")
    
    results = {
        "environment": check_environment(),
        "database": check_database(),
        "packages": check_installed_packages(),
        "files": check_files()
    }
    
    logger.info("اكتمل التشخيص")
    return results

if __name__ == "__main__":
    results = run_diagnostics()
    print(results)