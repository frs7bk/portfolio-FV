#!/usr/bin/env python3
"""
إنشاء حزمة ملفات جاهزة للنشر على Render
يقوم بتجميع جميع الملفات الضرورية في ملف ZIP واحد
"""
import os
import zipfile
import datetime

# اسم ملف ZIP الناتج
OUTPUT_ZIP = "render_deployment_package.zip"

# الملفات الأساسية للنشر على Render
RENDER_FILES = [
    "render.yaml",
    "render-requirements.txt",
    "render_setup.py",
    "test_database_connection.py",
    ".gitignore",
    "RENDER_DEPLOYMENT.md"
]

def create_render_package():
    """إنشاء حزمة ملفات النشر على Render"""
    print("جاري إنشاء حزمة ملفات النشر على Render...")
    
    # التحقق من وجود جميع الملفات المطلوبة
    missing_files = []
    for file in RENDER_FILES:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"⚠️ الملفات التالية مفقودة: {', '.join(missing_files)}")
        return False
    
    # إنشاء ملف ZIP
    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # إضافة ملفات Render
        for file in RENDER_FILES:
            zipf.write(file)
            print(f"✓ تمت إضافة: {file}")
    
    # طباعة معلومات عن الملف المنشأ
    file_size = os.path.getsize(OUTPUT_ZIP) / 1024  # بالكيلوبايت
    print(f"\n✅ تم إنشاء ملف الحزمة بنجاح: {OUTPUT_ZIP}")
    print(f"📦 حجم الملف: {file_size:.1f} كيلوبايت")
    
    return True

if __name__ == "__main__":
    if create_render_package():
        print("\n📝 تعليمات الاستخدام:")
        print("1. قم بتنزيل ملف الحزمة من مشروعك")
        print("2. قم بفك ضغط الملف على جهازك")
        print("3. انسخ الملفات المستخرجة إلى مجلد مشروعك")
        print("4. اتبع التعليمات في ملف RENDER_DEPLOYMENT.md للنشر على Render")