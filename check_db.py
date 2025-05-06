"""
التحقق من وجود الجداول في قاعدة البيانات وإنشاء الجداول المفقودة
"""
import os
import logging
from sqlalchemy import create_engine, inspect, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# نموذج قاعدة البيانات
Base = declarative_base()

# استيراد نماذج قاعدة البيانات
from models import User, UserActivity, PortfolioComment, PortfolioLike, CommentLike

def check_tables():
    """التحقق من وجود الجداول في قاعدة البيانات"""
    
    # الاتصال بقاعدة البيانات
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        logger.error("DATABASE_URL not found in environment variables")
        return False
    
    # تحويل عنوان postgres:// إلى postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    try:
        # إنشاء محرك الاتصال بقاعدة البيانات
        engine = create_engine(database_url)
        
        # إنشاء مفتش لفحص قاعدة البيانات
        inspector = inspect(engine)
        
        # قائمة بالجداول المطلوبة
        required_tables = [
            'user',
            'user_activity',
            'portfolio_comment',
            'portfolio_like',
            'comment_like'
        ]
        
        # التحقق من وجود كل جدول
        missing_tables = []
        for table in required_tables:
            if not inspector.has_table(table):
                missing_tables.append(table)
                logger.info(f"Table {table} does not exist")
        
        if missing_tables:
            logger.info(f"Missing tables: {missing_tables}")
            return False, missing_tables
        else:
            logger.info("All required tables exist")
            return True, []
    
    except Exception as e:
        logger.error(f"Error checking tables: {str(e)}")
        return False, []

def create_tables():
    """إنشاء الجداول في قاعدة البيانات"""
    
    # الاتصال بقاعدة البيانات
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        logger.error("DATABASE_URL not found in environment variables")
        return False
    
    # تحويل عنوان postgres:// إلى postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    try:
        # إنشاء محرك الاتصال بقاعدة البيانات
        engine = create_engine(database_url)
        
        # إنشاء الجداول
        Base.metadata.create_all(engine)
        
        logger.info("Tables created successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        return False

if __name__ == "__main__":
    tables_exist, missing_tables = check_tables()
    
    if not tables_exist:
        logger.info("Creating missing tables...")
        if create_tables():
            print("Tables created successfully!")
        else:
            print("Failed to create tables. Check logs for details.")
    else:
        print("All required tables already exist!")