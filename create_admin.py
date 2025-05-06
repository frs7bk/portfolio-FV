"""
إنشاء مستخدم مسؤول أو ترقية مستخدم موجود إلى مستوى المسؤول
"""
import os
import sys
from datetime import datetime
from flask import Flask
from werkzeug.security import generate_password_hash
from models import User, UserRole
from database import db

# إعداد التطبيق
app = Flask(__name__)
# الحصول على عنوان قاعدة البيانات من متغير البيئة
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    print("خطأ: لم يتم العثور على عنوان قاعدة البيانات في متغيرات البيئة")
    print("يرجى التأكد من وجود DATABASE_URL في متغيرات البيئة")
    sys.exit(1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

def create_admin_user(username, email, password):
    """إنشاء مستخدم مسؤول جديد"""
    with app.app_context():
        # التحقق مما إذا كان المستخدم موجودًا بالفعل
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            # ترقية المستخدم الموجود إلى مستوى المسؤول
            existing_user.role = UserRole.ADMIN.value
            existing_user.set_password(password)
            existing_user.email_verified = True
            db.session.commit()
            print(f"تم ترقية المستخدم {existing_user.username} إلى مستوى المسؤول")
            return existing_user
        
        # إنشاء مستخدم مسؤول جديد
        new_admin = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=UserRole.ADMIN.value,
            email_verified=True,
            created_at=datetime.now()
        )
        
        db.session.add(new_admin)
        db.session.commit()
        print(f"تم إنشاء مستخدم مسؤول جديد: {new_admin.username}")
        return new_admin

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("الاستخدام: python create_admin.py <username> <email> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    create_admin_user(username, email, password)