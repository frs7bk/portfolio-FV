#!/usr/bin/env python3
"""
سكربت لإعادة تعيين كلمة المرور للمستخدم المسؤول
هذا السكربت يسمح بإعادة تعيين كلمة المرور لأي مستخدم، ويمكن استخدامه خصيصًا لإعادة تعيين
كلمة المرور للمسؤول عندما تنسى كلمة المرور الحالية.
"""

import os
import sys
from getpass import getpass

# استيراد الموديلات اللازمة
try:
    from database import db
    from models import User, UserRole
except ImportError:
    print("خطأ في استيراد الموديلات. تأكد من تشغيل السكربت من المجلد الرئيسي للتطبيق.")
    sys.exit(1)

# تهيئة قاعدة البيانات باستخدام قيمة البيئة
def init_db():
    """
    تهيئة اتصال قاعدة البيانات باستخدام متغير البيئة DATABASE_URL
    """
    try:
        from flask import Flask
        app = Flask(__name__)
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("تحذير: متغير البيئة DATABASE_URL غير موجود. استخدام المسار الافتراضي لقاعدة البيانات.")
            database_url = 'sqlite:///website.db'  # مسار افتراضي
        
        print(f"استخدام قاعدة البيانات: {database_url}")
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)
        return app
    except Exception as e:
        print(f"خطأ في تهيئة قاعدة البيانات: {str(e)}")
        sys.exit(1)

def reset_password(username, new_password):
    """
    إعادة تعيين كلمة المرور للمستخدم
    
    Args:
        username: اسم المستخدم
        new_password: كلمة المرور الجديدة
    
    Returns:
        bool: نجاح العملية أم لا
    """
    app = init_db()
    
    with app.app_context():
        # البحث عن المستخدم
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"❌ المستخدم {username} غير موجود في قاعدة البيانات.")
            return False
        
        # إعادة تعيين كلمة المرور
        user.set_password(new_password)
        
        # إعادة تعيين محاولات تسجيل الدخول وفتح الحساب إذا كان مقفلًا
        user.login_attempts = 0
        user.account_locked = False
        
        # التأكد من أن المستخدم له دور المسؤول
        if user.role != UserRole.ADMIN.value:
            print(f"ملاحظة: دور المستخدم الحالي هو '{user.role}'. تغيير الدور إلى 'admin'...")
            user.role = UserRole.ADMIN.value
        
        try:
            db.session.commit()
            print(f"✅ تم تحديث كلمة المرور للمستخدم {username} بنجاح.")
            print(f"✅ دور المستخدم هو: {user.role}")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ حدث خطأ أثناء تحديث كلمة المرور: {str(e)}")
            return False

def main():
    print("=== أداة إعادة تعيين كلمة المرور للمسؤول ===")
    
    # الحصول على اسم المستخدم
    username = input("أدخل اسم المستخدم: ").strip()
    if not username:
        print("❌ اسم المستخدم مطلوب.")
        return
    
    # الحصول على كلمة المرور الجديدة (مخفية عند الكتابة)
    new_password = getpass("أدخل كلمة المرور الجديدة: ")
    if not new_password:
        print("❌ كلمة المرور مطلوبة.")
        return
    
    # تأكيد كلمة المرور
    confirm_password = getpass("تأكيد كلمة المرور الجديدة: ")
    if new_password != confirm_password:
        print("❌ كلمات المرور غير متطابقة.")
        return
    
    # تطبيق التغييرات
    reset_password(username, new_password)

if __name__ == "__main__":
    main()
