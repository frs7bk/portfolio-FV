#!/usr/bin/env python3
"""
اختبار الاتصال بقاعدة البيانات
استخدم هذا السكربت للتحقق من إمكانية الاتصال بقاعدة البيانات
"""
import os
import sys
import logging
from sqlalchemy import create_engine, text
import time

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_database_connection(max_retries=5, retry_delay=5):
    """
    اختبار الاتصال بقاعدة البيانات مع إعادة المحاولة
    
    Args:
        max_retries (int): عدد محاولات إعادة الاتصال
        retry_delay (int): الفاصل الزمني بين المحاولات بالثواني
        
    Returns:
        bool: True إذا كان الاتصال ناجحًا، False في حالة الفشل
    """
    database_url = os.environ.get("DATABASE_URL")
    
    # فحص وجود رابط قاعدة البيانات
    if not database_url:
        logger.error("متغير DATABASE_URL غير محدد في البيئة")
        # طباعة متغيرات البيئة المتاحة (مع إخفاء المعلومات الحساسة)
        env_vars = {k: v[:3] + "..." if any(s in k.lower() for s in ["key", "password", "secret", "token"]) else v 
                   for k, v in os.environ.items() if k.startswith(("PG", "DATABASE"))}
        logger.info(f"المتغيرات البيئية المتعلقة بقاعدة البيانات: {env_vars}")
        return False
    
    # تحويل postgres:// إلى postgresql:// إذا لزم الأمر
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        logger.info("تم تعديل رابط قاعدة البيانات لاستخدام postgresql://")
    
    # إخفاء كلمة المرور في السجلات
    safe_db_url = database_url
    if "@" in safe_db_url and ":" in safe_db_url:
        parts = safe_db_url.split("@")
        auth_parts = parts[0].split(":")
        if len(auth_parts) > 2:
            auth_parts[2] = "****"  # إخفاء كلمة المرور
            parts[0] = ":".join(auth_parts)
            safe_db_url = "@".join(parts)
    
    logger.info(f"جاري محاولة الاتصال بقاعدة البيانات: {safe_db_url}")
    
    # محاولة الاتصال بقاعدة البيانات مع إعادة المحاولة
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"محاولة الاتصال بقاعدة البيانات ({attempt}/{max_retries})...")
            
            # إنشاء محرك قاعدة البيانات مع إعدادات مناسبة
            engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_recycle=300,
                pool_timeout=30,
                pool_size=5,
                max_overflow=10,
                connect_args={
                    "connect_timeout": 10,
                    "application_name": "portfolio_app_render",
                    "keepalives": 1,
                    "keepalives_idle": 30,
                    "keepalives_interval": 10,
                    "keepalives_count": 5
                }
            )
            
            # اختبار الاتصال باستخدام استعلام بسيط
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                logger.info(f"تم الاتصال بنجاح! نتيجة الاستعلام: {result.fetchone()}")
                
                # اختبار إضافي للتحقق من وجود جداول أساسية
                try:
                    tables_result = connection.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"))
                    tables_count = tables_result.fetchone()[0]
                    logger.info(f"تم العثور على {tables_count} جدول في قاعدة البيانات")
                    
                    if tables_count > 0:
                        user_table_result = connection.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'user'"))
                        if user_table_result.fetchone()[0] > 0:
                            logger.info("جدول المستخدمين موجود")
                        else:
                            logger.warning("جدول المستخدمين غير موجود! سيتم إنشاؤه عند بدء التطبيق")
                except Exception as table_error:
                    logger.warning(f"لم يتم التحقق من جداول قاعدة البيانات: {str(table_error)}")
            
            # إذا وصلنا إلى هنا، فإن الاتصال ناجح
            return True
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"فشل الاتصال بقاعدة البيانات: {str(e)}\n{error_details}")
            
            if attempt < max_retries:
                logger.info(f"إعادة المحاولة بعد {retry_delay} ثوانٍ...")
                time.sleep(retry_delay)
            else:
                logger.error("استنفدت جميع محاولات الاتصال. تعذر الوصول إلى قاعدة البيانات.")
                return False

if __name__ == "__main__":
    success = test_database_connection()
    if success:
        logger.info("✅ تم الاتصال بقاعدة البيانات بنجاح!")
        sys.exit(0)
    else:
        logger.error("❌ فشل الاتصال بقاعدة البيانات!")
        sys.exit(1)