#!/usr/bin/env python3
"""
إنشاء ملف ZIP جاهز للتشغيل المحلي - نسخة مبسطة
"""
import os
import zipfile
import datetime
import shutil
import glob

# اسم ملف ZIP الناتج
OUTPUT_ZIP = "portfolio_ready_to_run.zip"

# الملفات الأساسية التي يجب تضمينها بالأولوية
ESSENTIAL_FILES = [
    "app.py",
    "main.py",
    "models.py",
    "forms.py",
    "database.py",
    "check_db.py",
    "setup_local.py",
    ".env-sample",
    "requirements.txt",
    "LOCAL_SETUP_INSTRUCTIONS.md"
]

# المجلدات الأساسية
ESSENTIAL_DIRS = [
    "templates",
    "static/css",
    "static/js"
]

# المجلدات التي يجب تضمينها فارغة
EMPTY_DIRS = [
    "static/uploads/profile",
    "static/uploads/portfolio",
    "static/uploads/carousel",
    "static/uploads/projects",
    "static/uploads/services",
    "instance"
]

# الملفات والمجلدات التي يجب استبعادها
EXCLUDE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    ".env",
    ".DS_Store",
    "venv",
    "env",
    "node_modules",
    "*.db",
    "tmp",
    ".cache",
    ".git"
]

def should_exclude(path):
    """تحديد ما إذا كان المسار يجب استبعاده"""
    for pattern in EXCLUDE_PATTERNS:
        if pattern in path:
            return True
    return False

def create_simple_zip():
    """إنشاء ملف ZIP مبسط وسريع"""
    # إنشاء ملف ZIP مباشرة
    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # إضافة الملفات الأساسية
        print("إضافة الملفات الأساسية...")
        for file in ESSENTIAL_FILES:
            if os.path.exists(file):
                zipf.write(file)
                print(f"✓ تمت إضافة: {file}")
        
        # إضافة جميع ملفات .py في المجلد الرئيسي
        print("إضافة ملفات Python...")
        for py_file in glob.glob("*.py"):
            if not should_exclude(py_file) and py_file not in ESSENTIAL_FILES:
                zipf.write(py_file)
                print(f"✓ تمت إضافة: {py_file}")
        
        # إضافة المجلدات الأساسية
        print("إضافة المجلدات الأساسية...")
        for directory in ESSENTIAL_DIRS:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    if not should_exclude(file_path):
                        zipf.write(file_path)
        
        # إنشاء المجلدات الفارغة
        print("إنشاء المجلدات الفارغة...")
        for empty_dir in EMPTY_DIRS:
            empty_file = os.path.join(empty_dir, ".gitkeep")
            os.makedirs(os.path.dirname(empty_file), exist_ok=True)
            
            # إنشاء ملف .gitkeep مؤقت
            if not os.path.exists(empty_file):
                with open(empty_file, 'w') as f:
                    pass
            
            # إضافة الملف إلى ZIP
            zipf.write(empty_file)
            
            # حذف الملف المؤقت إذا تم إنشاؤه
            if not os.path.exists(empty_file + ".original"):
                os.remove(empty_file)
    
    print(f"\n✓ تم إنشاء ملف ZIP بنجاح: {OUTPUT_ZIP}")
    print(f"حجم الملف: {os.path.getsize(OUTPUT_ZIP) / (1024*1024):.2f} MB")
    
    return OUTPUT_ZIP

if __name__ == "__main__":
    print("جاري إنشاء ملف ZIP جاهز للتشغيل...")
    zip_path = create_simple_zip()
    print(f"تم الانتهاء! يمكنك تحميل الملف: {zip_path}")