"""
مصادقة Google OAuth للموقع
"""
import json
import os

import requests
from flask import Blueprint, redirect, request, url_for, flash, session
from flask_login import login_required, login_user, logout_user

from app import db
from models import User
from oauthlib.oauth2 import WebApplicationClient
import logging

# تكوين Google OAuth client
GOOGLE_CLIENT_ID = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_OAUTH_CLIENT_SECRET"]
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# احصل على معلومات الخادم من متغيرات البيئة
SERVER_DOMAIN = os.environ.get("REPLIT_DEV_DOMAIN", "localhost:5000")
SERVER_PROTOCOL = "https" if "REPLIT_DEV_DOMAIN" in os.environ else "http"

# عنوان إعادة التوجيه للمصادقة
REDIRECT_URL = f"{SERVER_PROTOCOL}://{SERVER_DOMAIN}/google_login/callback"

# طباعة معلومات الإعداد لتسهيل التثبيت
print(f"""
لتفعيل المصادقة عبر Google:
1. الذهاب إلى https://console.cloud.google.com/apis/credentials
2. إنشاء OAuth 2.0 Client ID جديد
3. إضافة {REDIRECT_URL} إلى Authorized redirect URIs

للحصول على تعليمات مفصلة، انظر:
https://docs.replit.com/additional-resources/google-auth-in-flask#set-up-your-oauth-app--client
""")

# إنشاء عميل OAuth
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# إنشاء Blueprint لمسارات المصادقة
google_auth = Blueprint("google_auth", __name__)


@google_auth.route("/google_login")
def login():
    """بدء عملية تسجيل الدخول عبر Google"""
    # التحقق من وجود عنوان العودة 
    next_url = request.args.get('next', '/')
    session['next_url'] = next_url
    
    # الحصول على معلومات Google OAuth Provider
    try:
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        # إعداد عنوان الطلب للمصادقة
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            # التأكد من استخدام بروتوكول https للوصول إلى مسار إعادة التوجيه
            redirect_uri=request.base_url.replace("http://", "https://") + "/callback",
            scope=["openid", "email", "profile"],
        )
        return redirect(request_uri)
    except Exception as e:
        logging.error(f"خطأ في بدء مصادقة Google: {str(e)}")
        flash("حدث خطأ أثناء الاتصال بخدمات Google. الرجاء المحاولة مرة أخرى.", "danger")
        return redirect("/")


@google_auth.route("/google_login/callback")
def callback():
    """التعامل مع استجابة Google بعد المصادقة"""
    # التحقق من وجود خطأ في الرد
    if 'error' in request.args:
        flash("فشل تسجيل الدخول عبر Google. الرجاء المحاولة مرة أخرى.", "danger")
        return redirect("/")
    
    # الحصول على رمز التفويض (code)
    code = request.args.get("code")
    if not code:
        flash("لم يتم توفير رمز التفويض من Google.", "danger")
        return redirect("/")
    
    try:
        # الحصول على معلومات Google OAuth Provider
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]

        # إعداد طلب الحصول على الرمز
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            # التأكد من استخدام بروتوكول https
            authorization_response=request.url.replace("http://", "https://"),
            redirect_url=request.base_url.replace("http://", "https://"),
            code=code,
        )
        
        # إرسال طلب الحصول على الرمز
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )

        # تحليل استجابة الرمز
        client.parse_request_body_response(json.dumps(token_response.json()))

        # الحصول على معلومات المستخدم
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        # استخراج معلومات المستخدم
        userinfo = userinfo_response.json()
        
        # التحقق من صحة البريد الإلكتروني
        if not userinfo.get("email_verified"):
            flash("البريد الإلكتروني غير مصادق عليه من قبل Google.", "danger")
            return redirect("/")
            
        # استخراج معلومات المستخدم
        user_email = userinfo["email"]
        user_name = userinfo.get("given_name") or userinfo.get("name", "مستخدم")
        user_picture = userinfo.get("picture")

        # البحث عن المستخدم في قاعدة البيانات
        user = User.query.filter_by(email=user_email).first()
        
        # إنشاء مستخدم جديد إذا لم يكن موجودًا
        if not user:
            user = User(
                username=user_email.split('@')[0],  # استخدام جزء من البريد الإلكتروني كاسم مستخدم
                email=user_email,
                display_name=user_name,
                avatar_url=user_picture,
                email_verified=True  # تأكيد البريد الإلكتروني تلقائيًا للمستخدمين من Google
            )
            # إنشاء كلمة مرور عشوائية
            import secrets
            random_password = secrets.token_hex(16)
            user.set_password(random_password)
            
            db.session.add(user)
            db.session.commit()
            logging.info(f"تم إنشاء مستخدم جديد عبر Google: {user_email}")

        # تسجيل الدخول للمستخدم
        login_user(user)
        user.reset_login_attempts()  # إعادة تعيين محاولات تسجيل الدخول الفاشلة
        
        # توجيه المستخدم إلى الصفحة التي كان يحاول الوصول إليها
        next_url = session.pop('next_url', '/')
        
        flash(f"مرحبًا {user.display_name or user.username}! تم تسجيل دخولك بنجاح.", "success")
        return redirect(next_url)
        
    except Exception as e:
        logging.error(f"خطأ في معالجة استجابة Google: {str(e)}")
        flash("حدث خطأ أثناء محاولة التحقق من هويتك. الرجاء المحاولة مرة أخرى.", "danger")
        return redirect("/")


@google_auth.route("/google_logout")
@login_required
def logout():
    """تسجيل الخروج من الحساب المرتبط بـ Google"""
    logout_user()
    flash("تم تسجيل خروجك بنجاح.", "info")
    return redirect("/")