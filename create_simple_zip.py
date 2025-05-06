#!/usr/bin/env python3
"""
إنشاء ملف ZIP مبسط للموقع
"""
import os
import zipfile
import datetime
import shutil

# اسم ملف ZIP الناتج
OUTPUT_ZIP = "clean_portfolio_template.zip"

# الملفات والمجلدات الرئيسية التي يجب تضمينها
ESSENTIAL_FILES = [
    "main.py",
    "app.py",
    "models.py",
    "database.py",
    "auth_routes.py",
    "portfolio_routes.py",
    "fix_portfolio_modal_routes.py",
    "fix_modals.py",
    "fix_modals_register.py",
    "analytics.py",
    "email_service.py",
    "comments_routes.py",
    "carousel_functions.py",
    "download_routes.py",
    "forms.py",
    "requirements.txt",
    "vercel.json",
    "README.md",
    "SETUP_INSTRUCTIONS.md"
]

# المجلدات التي يجب نسخها بالكامل
ESSENTIAL_DIRS = [
    "templates",
    "static/css",
    "static/js"
]

# المجلدات الفارغة التي يجب إنشاؤها
EMPTY_DIRS = [
    "static/uploads",
    "static/uploads/portfolio",
    "static/uploads/profile",
    "static/uploads/carousel",
    "static/uploads/projects",
    "static/uploads/services",
    "instance"
]

def create_simple_zip():
    """إنشاء ملف ZIP مبسط يحتوي على الملفات الأساسية فقط"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    temp_dir = f"tmp_export_{timestamp}"
    
    # إنشاء مجلد مؤقت للتصدير
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    
    os.makedirs(temp_dir)
    
    # نسخ الملفات الرئيسية
    for file in ESSENTIAL_FILES:
        if os.path.exists(file):
            try:
                # إنشاء المجلد الهدف إذا لم يكن موجوداً
                os.makedirs(os.path.dirname(os.path.join(temp_dir, file)), exist_ok=True)
                # نسخ الملف
                shutil.copy2(file, os.path.join(temp_dir, file))
                print(f"تم نسخ الملف: {file}")
            except Exception as e:
                print(f"خطأ في نسخ الملف {file}: {str(e)}")
    
    # نسخ المجلدات الرئيسية بالكامل
    for directory in ESSENTIAL_DIRS:
        if os.path.exists(directory):
            try:
                # نسخ المجلد بكامل محتوياته
                shutil.copytree(directory, os.path.join(temp_dir, directory))
                print(f"تم نسخ المجلد: {directory}")
            except Exception as e:
                print(f"خطأ في نسخ المجلد {directory}: {str(e)}")
    
    # إنشاء المجلدات الفارغة
    for empty_dir in EMPTY_DIRS:
        try:
            # إنشاء المجلد الفارغ
            os.makedirs(os.path.join(temp_dir, empty_dir), exist_ok=True)
            # إضافة ملف .gitkeep
            with open(os.path.join(temp_dir, empty_dir, ".gitkeep"), "w") as f:
                f.write("# This empty file ensures the directory is included in Git\n")
            print(f"تم إنشاء المجلد الفارغ: {empty_dir}")
        except Exception as e:
            print(f"خطأ في إنشاء المجلد الفارغ {empty_dir}: {str(e)}")
    
    # إنشاء ملف ZIP
    try:
        with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    # مسار الملف المصدر
                    src_file = os.path.join(root, file)
                    # مسار الملف داخل الأرشيف
                    arc_name = os.path.relpath(src_file, temp_dir)
                    # إضافة الملف إلى الأرشيف
                    zipf.write(src_file, arc_name)
        
        # طباعة معلومات عن الملف
        zip_size = os.path.getsize(OUTPUT_ZIP) / 1024  # بالكيلوبايت
        print(f"\n✅ تم إنشاء ملف ZIP بنجاح: {OUTPUT_ZIP}")
        print(f"📦 حجم الملف: {zip_size:.1f} كيلوبايت")
    except Exception as e:
        print(f"خطأ في إنشاء ملف ZIP: {str(e)}")
    
    # حذف المجلد المؤقت
    try:
        shutil.rmtree(temp_dir)
        print("تم حذف المجلد المؤقت")
    except Exception as e:
        print(f"خطأ في حذف المجلد المؤقت: {str(e)}")

if __name__ == "__main__":
    create_simple_zip()
