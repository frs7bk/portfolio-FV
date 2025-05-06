#!/usr/bin/env python3
"""
إنشاء ملف ZIP نظيف يحتوي على قالب الموقع بدون محتوى المستخدم
يمكن استخدام هذا القالب للنشر على منصات مثل Vercel
"""
import os
import zipfile
import datetime
import shutil

# اسم ملف ZIP الناتج
OUTPUT_ZIP = "clean_portfolio_template.zip"

# المجلدات التي يجب الاحتفاظ بها فارغة لكن بدون ملفات المستخدم
EMPTY_DIRS_TO_KEEP = [
    "static/uploads",
    "static/uploads/profile",
    "static/uploads/portfolio",
    "static/uploads/carousel",
    "static/uploads/projects",
    "static/uploads/services",
    "static/uploads/backup_images",
    "instance",
    "tmp"
]

# الملفات والمجلدات التي يجب استبعادها من ملف ZIP
EXCLUDE_PATTERNS = [
    ".git/",
    "__pycache__/",
    ".pyc",
    ".env",
    ".DS_Store",
    "venv/",
    "env/",
    "node_modules/",
    "instance/website.db",
    "static/uploads/",  # استبعاد جميع الملفات المرفوعة
    "instance/",       # استبعاد ملفات قاعدة البيانات
    "tmp/",            # استبعاد الملفات المؤقتة
    ".cache/",         # استبعاد ملفات الكاش
    "uv.lock",
    "attached_assets/", # استبعاد الصور المرفقة في المحادثة
    "__pycache__"
]

# الملفات التي يجب تضمينها فقط (لتسريع عملية الإنشاء)
INCLUDE_FILES_ONLY = [
    "app.py",
    "main.py",
    "models.py",
    "forms.py",
    "database.py",
    "email_service.py",
    "telegram_service.py",
    "direct_telegram_test.py",
    "telegram_test_routes.py",
    "live_visitors.py",
    "analytics.py",
    "auth_routes.py",
    "portfolio_routes.py",
    "fix_modals_register.py",
    "fix_portfolio_modal_routes.py",
    "fix_modals.py",
    "comments_routes.py",
    "messaging_routes.py",
    "portfolio_instagram.py",
    "download_routes.py",
    "carousel_functions.py",
    "requirements.txt",
    "vercel.json",
    "wsgi.py",
    ".env-sample",
    "SETUP_INSTRUCTIONS.md",
    "DEPLOY.md",
    "README.md",
    ".gitignore"
]

# إضافات وملفات إضافية لإضافتها إلى الحزمة
ADDITIONAL_FILES = [
    # ملف .gitignore مع الإعدادات المناسبة
    ".gitignore",
    # ملف requirements.txt الذي يحتوي على المكتبات المطلوبة
    "requirements.txt",
    # ملف vercel.json للنشر على منصة Vercel
    "vercel.json",
    # ملف README.md أو SETUP_INSTRUCTIONS.md للتوثيق
    "README.md",
    "SETUP_INSTRUCTIONS.md"
]

def should_exclude(path):
    """تحديد ما إذا كان المسار يجب استبعاده"""
    for pattern in EXCLUDE_PATTERNS:
        if pattern in path:
            # استثناء: لا تستبعد ملف .gitkeep
            if path.endswith(".gitkeep"):
                return False
            return True
    return False

def create_clean_zip():
    """إنشاء ملف ZIP نظيف مع الحفاظ على هيكل المجلدات"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    temp_dir = f"tmp/export_{timestamp}"
    
    # إنشاء مجلد مؤقت للتصدير
    if not os.path.exists("tmp"):
        os.makedirs("tmp")
    
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    
    os.makedirs(temp_dir)
    
    # نسخ الملفات المحددة فقط
    print("جاري نسخ الملفات الأساسية...")
    for file in INCLUDE_FILES_ONLY:
        if os.path.exists(file):
            dst_path = os.path.join(temp_dir, file)
            # إنشاء المجلد الهدف إذا لم يكن موجوداً
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            
            # نسخ الملف مع معالجة الأخطاء
            try:
                shutil.copy2(file, dst_path)
                print(f"✓ تم نسخ: {file}")
            except (FileNotFoundError, PermissionError, shutil.SameFileError) as e:
                print(f"✗ تخطي الملف: {file} - السبب: {str(e)}")
                continue
    
    # نسخ المجلدات المهمة
    important_folders = [
        "templates",
        "static/css",
        "static/js"
    ]
    
    print("\nجاري نسخ المجلدات المهمة...")
    for folder in important_folders:
        if os.path.exists(folder):
            dst_folder = os.path.join(temp_dir, folder)
            
            # إنشاء المجلد الهدف
            os.makedirs(dst_folder, exist_ok=True)
            
            # نسخ محتويات المجلد
            for root, dirs, files in os.walk(folder):
                # تخطي المجلدات المستبعدة
                dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d) + "/")]
                
                for file in files:
                    src_path = os.path.join(root, file)
                    
                    # تخطي الملفات المستبعدة
                    if should_exclude(src_path):
                        continue
                    
                    # إنشاء مسار النسخ
                    rel_path = os.path.relpath(src_path, ".")
                    dst_path = os.path.join(temp_dir, rel_path)
                    
                    # إنشاء المجلد الهدف إذا لم يكن موجوداً
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    
                    # نسخ الملف مع معالجة الأخطاء
                    try:
                        shutil.copy2(src_path, dst_path)
                    except (FileNotFoundError, PermissionError, shutil.SameFileError) as e:
                        print(f"✗ تخطي الملف: {src_path} - السبب: {str(e)}")
                        continue
            
            print(f"✓ تم نسخ: {folder}")
        else:
            print(f"✗ المجلد غير موجود: {folder}")
    
    # إنشاء المجلدات الفارغة التي يجب الاحتفاظ بها
    for empty_dir in EMPTY_DIRS_TO_KEEP:
        full_path = os.path.join(temp_dir, empty_dir)
        os.makedirs(full_path, exist_ok=True)
        # إضافة ملف .gitkeep للتأكد من إدراج المجلد في Git
        with open(os.path.join(full_path, ".gitkeep"), "w") as f:
            f.write("# This empty file ensures that the directory is included in Git\n")
    
    # إنشاء ملف ZIP
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                src_path = os.path.join(root, file)
                # إضافة الملف إلى ZIP بدون المسار المؤقت
                arc_path = os.path.relpath(src_path, temp_dir)
                zipf.write(src_path, arc_path)
    
    # حذف المجلد المؤقت
    shutil.rmtree(temp_dir)
    
    # طباعة تقرير عن الملف الذي تم إنشاؤه
    zip_size = os.path.getsize(OUTPUT_ZIP) / 1024  # بالكيلوبايت
    
    print(f"\n✅ تم إنشاء ملف ZIP بنجاح: {OUTPUT_ZIP}")
    print(f"📦 حجم الملف: {zip_size:.1f} كيلوبايت")
    print("🔍 يحتوي الملف على قالب نظيف للموقع بدون ملفات المستخدم")
    print("📋 تم الحفاظ على هيكل المجلدات المهمة مع ملفات .gitkeep")
    print("🚀 يمكن استخدام هذا الملف للنشر على منصات استضافة مثل Vercel")

if __name__ == "__main__":
    create_clean_zip()
