#!/usr/bin/env python3
"""
أداة مساعدة لإعداد المشروع محليًا
تقوم هذه الأداة بإنشاء ملف .env وإعداد قاعدة البيانات وإنشاء مستخدم مسؤول
"""
import os
import sys
import secrets
import subprocess
import getpass
from sqlalchemy import create_engine, inspect
from database import Base
import logging
import time

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_secret_key():
    """إنشاء مفتاح سري عشوائي"""
    return secrets.token_hex(16)

def create_env_file():
    """إنشاء ملف .env مع المتغيرات اللازمة"""
    if os.path.exists(".env"):
        overwrite = input("ملف .env موجود بالفعل. هل ترغب في استبداله؟ (نعم/لا): ").lower()
        if overwrite != "نعم" and overwrite != "yes":
            logger.info("تم إلغاء إنشاء ملف .env")
            return False
    
    print("\nإدخال بيانات قاعدة البيانات:")
    db_user = input("اسم مستخدم قاعدة البيانات PostgreSQL: ") or "postgres"
    db_password = getpass.getpass("كلمة مرور قاعدة البيانات: ")
    db_host = input("مضيف قاعدة البيانات (localhost): ") or "localhost"
    db_port = input("منفذ قاعدة البيانات (5432): ") or "5432"
    db_name = input("اسم قاعدة البيانات: ") or "portfolio"
    
    flask_secret_key = generate_secret_key()
    session_secret = generate_secret_key()
    
    with open(".env", "w") as env_file:
        env_file.write(f"DATABASE_URL=postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}\n")
        env_file.write(f"FLASK_SECRET_KEY={flask_secret_key}\n")
        env_file.write(f"SESSION_SECRET={session_secret}\n")
    
    logger.info("تم إنشاء ملف .env بنجاح")
    
    # تحميل المتغيرات البيئية
    os.environ['DATABASE_URL'] = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    os.environ['FLASK_SECRET_KEY'] = flask_secret_key
    os.environ['SESSION_SECRET'] = session_secret
    
    return True

def create_database():
    """إنشاء قاعدة البيانات إذا لم تكن موجودة"""
    from models import User, UserActivity, PortfolioComment, PortfolioLike, CommentLike
    
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL غير موجود في متغيرات البيئة")
        return False
    
    # تحويل عنوان postgres:// إلى postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    try:
        # إنشاء محرك الاتصال بقاعدة البيانات
        engine = create_engine(database_url)
        
        # إنشاء الجداول
        Base.metadata.create_all(engine)
        
        logger.info("تم إنشاء جداول قاعدة البيانات بنجاح")
        return True
    
    except Exception as e:
        logger.error(f"خطأ في إنشاء قاعدة البيانات: {str(e)}")
        return False

def create_admin_user():
    """إنشاء مستخدم مسؤول"""
    from app import app, db
    from models import User
    from werkzeug.security import generate_password_hash
    
    with app.app_context():
        admin_exists = User.query.filter_by(is_admin=True).first()
        if admin_exists:
            overwrite = input("يوجد مستخدم مسؤول بالفعل. هل ترغب في إنشاء مستخدم مسؤول جديد؟ (نعم/لا): ").lower()
            if overwrite != "نعم" and overwrite != "yes":
                logger.info("تم إلغاء إنشاء مستخدم مسؤول جديد")
                return False
        
        username = input("اسم المستخدم للمسؤول: ")
        email = input("البريد الإلكتروني للمسؤول: ")
        password = getpass.getpass("كلمة المرور للمسؤول: ")
        
        new_admin = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=True,
            email_confirmed=True
        )
        
        db.session.add(new_admin)
        db.session.commit()
        
        logger.info(f"تم إنشاء مستخدم مسؤول جديد بنجاح: {username}")
        return True

def install_requirements():
    """تثبيت المتطلبات من ملف requirements.txt"""
    try:
        logger.info("جاري تثبيت المتطلبات...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        logger.info("تم تثبيت المتطلبات بنجاح")
        return True
    except Exception as e:
        logger.error(f"خطأ في تثبيت المتطلبات: {str(e)}")
        return False

def create_default_directories():
    """إنشاء المجلدات الافتراضية اللازمة"""
    directories = [
        "static/uploads",
        "static/uploads/profile",
        "static/uploads/portfolio",
        "static/uploads/carousel",
        "static/uploads/projects",
        "static/uploads/services",
        "instance"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"تم إنشاء المجلد: {directory}")
    
    return True

def run_setup():
    """تشغيل عملية الإعداد بالكامل"""
    logger.info("بدء عملية إعداد المشروع محليًا...")
    
    # التحقق من وجود Python
    logger.info(f"إصدار Python: {sys.version}")
    
    # إنشاء ملف .env
    if not create_env_file():
        return False
    
    # تثبيت المتطلبات
    if not install_requirements():
        return False
    
    # إنشاء المجلدات الافتراضية
    if not create_default_directories():
        return False
    
    # إنشاء قاعدة البيانات
    if not create_database():
        return False
    
    # إنشاء مستخدم مسؤول
    if not create_admin_user():
        return False
    
    logger.info("تم إكمال عملية الإعداد بنجاح!")
    logger.info("يمكنك الآن تشغيل التطبيق باستخدام: python main.py")
    
    return True

if __name__ == "__main__":
    run_setup()