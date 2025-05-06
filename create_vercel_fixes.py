#!/usr/bin/env python3
"""
إنشاء ملف ZIP يحتوي على الإصلاحات الخاصة بالنشر على Vercel
"""
import os
import zipfile
import datetime

# اسم ملف ZIP الناتج
OUTPUT_ZIP = "vercel_fixes.zip"

# الملفات التي تم تعديلها وتحديثها لدعم Vercel
VERCEL_FIXES = [
    "wsgi.py",
    "vercel.json",
    "main.py",
    "app.py",
    "DEPLOY.md"
]

def create_vercel_fixes_zip():
    """إنشاء ملف ZIP مع الإصلاحات الخاصة بـ Vercel"""
    # إنشاء ملف ZIP
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in VERCEL_FIXES:
            if os.path.exists(file):
                zipf.write(file)
                print(f"✓ تم إضافة: {file}")
            else:
                print(f"✗ الملف غير موجود: {file}")
    
    # طباعة تقرير عن الملف الذي تم إنشاؤه
    zip_size = os.path.getsize(OUTPUT_ZIP) / 1024  # بالكيلوبايت
    
    print(f"\n✅ تم إنشاء ملف ZIP بنجاح: {OUTPUT_ZIP}")
    print(f"📦 حجم الملف: {zip_size:.1f} كيلوبايت")
    print("🔧 يحتوي الملف على الإصلاحات الخاصة بـ Vercel")
    print("🚀 قم بدمج هذه الملفات مع مشروعك الأصلي قبل النشر على Vercel")

if __name__ == "__main__":
    create_vercel_fixes_zip()