import os
import time
from datetime import datetime, timedelta
import json
import random
import string
import base64
import traceback

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort, session, g
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import func, desc, distinct, case, or_
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import logging

from email_service import send_contact_form_notification
from portfolio_routes import portfolio_bp
from auth_routes import auth
# تعطيل استيراد وحدة التعليقات
# from comments_routes import comments
from analytics import analytics
from messaging_routes import messaging_bp
# from portfolio_instagram import portfolio_instagram_bp
from live_visitors import init_live_visitors_tracking
from download_routes import download_bp

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Setup Flask app
from database import db

# الحرص على أن تكون جميع النماذج مستوردة قبل إنشاء الجداول
from models import PortfolioComment, PortfolioItem, User, UserActivity, Service, ContactMessage, SocialMedia, UserRole
csrf = CSRFProtect()
app = Flask(__name__)
# تعيين مفتاح سري من متغيرات البيئة أو استخدام قيمة افتراضية إذا لم يكن متاحًا
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "fb847de58b1dea2efad1f21e6ebe1aa8f62f12cb8e08f82ce9292acf7c3ff0ab")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# تعطيل حماية CSRF للاستجابات API
app.config['WTF_CSRF_CHECK_DEFAULT'] = False
csrf.init_app(app)

# إعداد نظام تسجيل الدخول
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة'
login_manager.login_message_category = 'info'

# تسجيل المسارات
app.register_blueprint(auth)
# تعطيل تسجيل تطبيق التعليقات - حسب طلب المستخدم
# app.register_blueprint(comments)
app.register_blueprint(analytics, url_prefix='/analytics')
app.register_blueprint(messaging_bp)
app.register_blueprint(portfolio_bp)
# app.register_blueprint(portfolio_instagram_bp)
app.register_blueprint(download_bp)

# تهيئة نظام تتبع الزوار النشطين حاليًا
init_live_visitors_tracking(app)

# Security settings
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/admin'):
        return render_template('admin/error.html', error_code=404, error_message="الصفحة غير موجودة"), 404
    return render_template('error.html', error_code=404, error_message="الصفحة غير موجودة"), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    error_details = traceback.format_exc()
    logging.error(f"Internal Server Error: {str(error)}\n{error_details}")
    
    # التقاط معلومات إضافية للتشخيص
    env_vars = {k: '***' if 'key' in k.lower() or 'password' in k.lower() or 'secret' in k.lower() else v 
               for k, v in os.environ.items()}
    
    logging.error(f"Environment variables: {env_vars}")
    logging.error(f"Request path: {request.path}")
    logging.error(f"Request method: {request.method}")
    logging.error(f"Request form keys: {list(request.form.keys()) if request.form else 'No form data'}")
    logging.error(f"Request files keys: {list(request.files.keys()) if request.files else 'No files'}")
    logging.error(f"Referrer: {request.referrer}")
    logging.error(f"=== END DEBUG INFO ===")
    
    error_message = "حدث خطأ في الخادم. لقد تم تسجيل هذا الخطأ وسنعمل على إصلاحه قريبًا."
    
    if request.path.startswith('/admin'):
        return render_template('admin/error.html', error_code=500, error_message=error_message, error_details=str(error) if app.debug else None), 500
    return render_template('error.html', error_code=500, error_message=error_message, error_details=str(error) if app.debug else None), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return render_template('error.html', error_code=413, error_message="حجم الملف كبير جداً. الحد الأقصى هو 50 ميجابايت"), 413

# تعريف دالة للتحقق من صلاحيات المسؤول
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('لا تملك صلاحية الوصول إلى هذه الصفحة', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def init_app(app):
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max-limit
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

init_app(app)

# تحديد لغة المستخدم - استخدام اللغة العربية فقط
def get_preferred_language():
    app.logger.debug(f"Accept-Language header: {request.headers.get('Accept-Language', 'Not provided')}")
    
    # استخدام اللغة العربية دائماً
    session['lang'] = 'ar'
    return 'ar'

# Session validator
@app.before_request
def check_session():
    # تحديد اللغة المفضلة ووضعها في g لاستخدامها في كل الطلبات
    g.lang = get_preferred_language()
    
    # توجيه المستخدم من المسارات الإنجليزية إلى المسارات العربية
    if not request.path.startswith('/static') and not request.path.startswith('/api') and request.method == 'GET':
        if request.path.startswith('/en'):
            # توجيه كل المسارات التي تبدأ بـ /en إلى الصفحة الرئيسية
            return redirect(url_for('index'))
    
    # تتبع الزائر وتسجيل الزيارة (للصفحات العامة فقط، ليس API أو الملفات الثابتة)
    if not request.path.startswith('/static') and not request.path.startswith('/api') and request.method == 'GET':
        # استيراد عند الطلب لتجنب دورة الاستيراد
        from analytics import track_visitor, track_page_visit
        
        try:
            # تتبع الزائر
            visitor = track_visitor(request)
            
            # تسجيل زيارة الصفحة
            track_page_visit(visitor, request)
        except Exception as e:
            app.logger.error(f"Error tracking visitor: {str(e)}", exc_info=True)
            # لا نريد أن نمنع وصول المستخدم إذا فشل التتبع

    # التحقق من صحة الجلسة للمستخدمين المسجلين
    if current_user.is_authenticated:
        if not session.get('_fresh'):
            session.permanent = True
            session.modified = True
            session['_fresh'] = True

        last_active = session.get('last_active')
        if not last_active or datetime.now() - datetime.fromtimestamp(last_active) > timedelta(hours=1):
            logout_user()
            flash('انتهت جلستك. يرجى تسجيل الدخول مرة أخرى.', 'warning')
            return redirect(url_for('admin_login'))

        session['last_active'] = datetime.now().timestamp()

# Database configuration
database_url = os.environ.get("DATABASE_URL")
app.logger.info(f"Database URL: {database_url}")
if database_url is None or database_url == "":
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///website.db"
    app.logger.warning("DATABASE_URL not found, using SQLite database")
else:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.logger.info("Using PostgreSQL database")

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 180,  # تدوير الاتصالات كل 3 دقائق
    "pool_pre_ping": True,  # فحص الاتصال قبل استخدامه
    "pool_size": 10,  # عدد الاتصالات المتزامنة
    "pool_timeout": 30,  # وقت انتهاء مهلة الحصول على اتصال (30 ثانية)
    "max_overflow": 15  # عدد إضافي من الاتصالات فوق حجم المجموعة
}
db.init_app(app)

# Import models
from models import User, Section, Content, Testimonial, Image, PortfolioItem, PortfolioComment, PortfolioLike, CommentLike, PortfolioView, Service, SocialMedia, Carousel, Visitor, PageVisit

# Create all tables
with app.app_context():
    db.create_all()
    app.logger.info("Database tables created")

# Import telegram service
from telegram_service import send_telegram_message, test_telegram_notification, format_contact_message, format_testimonial, format_portfolio_comment, format_order_notification

# مسار صفحة الزوار النشطين حاليًا
@app.route('/admin/live-visitors')
@login_required
def live_visitors():
    """واجهة عرض الزوار النشطين حاليًا"""
    if not current_user.is_admin():
        flash('لا تملك صلاحية الوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
        
    pending_testimonials = len(Testimonial.query.filter_by(approved=False).all())
    return render_template('admin/live_visitors.html', pending_testimonials=pending_testimonials)

# Google OAuth routes, messaging routes and analytics routes are already registered above
# Login manager setup is already set above, so we don't need to do it again

# Upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'pdf', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max-limit

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def secure_file_save(file, filename, subfolder=''):
    """
    حفظ ملف بشكل آمن في المجلد المحدد
    
    Args:
        file: ملف المُرفق
        filename: اسم الملف
        subfolder: المجلد الفرعي داخل uploads (مثل 'services' أو 'projects')
        
    Returns:
        المسار النسبي للملف المحفوظ
    
    Raises:
        ValueError: إذا كان نوع الملف غير مسموح به
    """
    if not allowed_file(filename):
        raise ValueError('نوع الملف غير مسموح به')

    secure_name = secure_filename(filename)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    final_filename = f"{timestamp}_{secure_name}"

    # إنشاء المجلد الرئيسي للرفع إذا لم يكن موجودًا
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # إذا تم تحديد مجلد فرعي، قم بإنشائه أيضًا
    upload_path = app.config['UPLOAD_FOLDER']
    if subfolder:
        upload_path = os.path.join(upload_path, subfolder)
        os.makedirs(upload_path, exist_ok=True)
        
    file_path = os.path.join(upload_path, final_filename)
    file.save(file_path)
    
    # إرجاع المسار النسبي بالنسبة للملف الرئيسي
    if subfolder:
        relative_path = f"/static/uploads/{subfolder}/{final_filename}"
    else:
        relative_path = f"/static/uploads/{final_filename}"
    app.logger.debug(f"تم حفظ الملف في {file_path}, المسار للـURL: {relative_path}")
    return relative_path

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Default data creation
def create_default_data():
    if User.query.count() == 0:
        default_user = User(
            username='admin',
            email='admin@example.com',
        )
        default_user.set_password('admin123')
        db.session.add(default_user)
        db.session.commit()
        logging.info("Default admin user created")

    if Section.query.count() == 0:
        sections = [
            {"name": "hero", "title": "القسم الرئيسي"},
            {"name": "about", "title": "من أنا"},
            {"name": "services", "title": "الخدمات"},
            {"name": "contact", "title": "اتصل بي"},
            {"name": "footer", "title": "تذييل الصفحة"}
        ]

        for section in sections:
            new_section = Section(name=section["name"], title=section["title"])
            db.session.add(new_section)

        db.session.commit()
        logging.info("Default sections created")

    # إضافة محتوى لقسم الترحيب إذا لم يكن موجودًا
    hero_section = Section.query.filter_by(name="hero").first()
    if hero_section and Content.query.filter_by(section_id=hero_section.id).count() == 0:
        hero_contents = [
            {"key": "title", "value": "مرحباً بك في"},
            {"key": "subtitle", "value": "معرض أعمال فراس"},
            {"key": "description", "value": "خبرة في التصميم الجرافيكي والهوية البصرية مع لمسة من الإبداع والتميّز"},
            {"key": "cta_text", "value": "تصفح أعمالي"},
            {"key": "cta_link", "value": "/portfolio"}
        ]
        
        for content in hero_contents:
            new_content = Content(
                section_id=hero_section.id,
                key=content["key"],
                value=content["value"]
            )
            db.session.add(new_content)
        
        db.session.commit()
        logging.info("Default hero content added")
    
    # إضافة محتوى لقسم من أنا إذا لم يكن موجودًا
    about_section = Section.query.filter_by(name="about").first()
    if about_section:
        # إضافة المحتوى النصي
        if Content.query.filter_by(section_id=about_section.id).count() == 0:
            about_contents = [
                {"key": "name", "value": "فراس"},
                {"key": "description", "value": "مصمم جرافيك جزائري متخصص في تقديم حلول بصرية عالية الاحترافية."},
                {"key": "description2", "value": "أعمل على تصميم الشعارات، الهويات، الفلايرز، أغلفة الكتب وأكثر من ذلك. هدفي هو مساعدتك في إيصال رسالتك بشكل مميز وأنيق."},
                {"key": "cv_text", "value": "تحميل السيرة الذاتية"},
                {"key": "contact_text", "value": "تواصل معي"},
                {"key": "cv_link", "value": "cv-firas.pdf"}
            ]
            
            for content in about_contents:
                new_content = Content(
                    section_id=about_section.id,
                    key=content["key"],
                    value=content["value"]
                )
                db.session.add(new_content)
            
            db.session.commit()
            logging.info("Default about content added")
        
        # إضافة صورة الملف الشخصي
        profile_image = Image.query.filter_by(section_id=about_section.id, key="profile_image").first()
        if not profile_image and os.path.exists("static/uploads/profile.png"):
            default_image = Image(
                section_id=about_section.id,
                key="profile_image",
                filename="profile.png",
                path="/static/uploads/profile.png"
            )
            db.session.add(default_image)
            db.session.commit()
            logging.info("Default profile image added")

    if Service.query.count() == 0:
        services = [
            {
                'service_type': 'social-media',
                'title': 'تصميم منشورات السوشيال ميديا',
                'title_en': 'Social Media Posts Design',
                'subtitle': 'محتوى بصري جذاب ومميز لمنصات التواصل الاجتماعي',
                'subtitle_en': 'Attractive and distinctive visual content for social media platforms',
                'price': '5000 دج - 15000 دج',
                'price_en': '$50 - $150',
                'delivery_time': '24 - 48 ساعة',
                'delivery_time_en': '24 - 48 hours',
                'revisions': 'غير محدودة',
                'revisions_en': 'Unlimited',
                'formats': 'JPG, PNG, PSD',
                'image_url': '/static/uploads/social-media-design.jpg',
                'description': '<p>تعتبر منشورات السوشيال ميديا من أهم الأدوات التسويقية في العصر الحالي، ويمكنها أن تحدث فرقاً كبيراً في نجاح علامتك التجارية عبر المنصات المختلفة مثل فيسبوك وانستغرام وتويتر.</p><p>أقدم لك تصاميم احترافية تجذب انتباه الجمهور المستهدف وتعكس هوية علامتك التجارية بأفضل شكل ممكن. سواء كنت تحتاج إلى منشورات ترويجية، اقتباسات ملهمة، إعلانات، أو أي نوع آخر من المحتوى البصري.</p>',
                'description_en': '<p>Social media posts are one of the most important marketing tools nowadays, and they can make a big difference in the success of your brand across different platforms like Facebook, Instagram, and Twitter.</p><p>I provide you with professional designs that attract the attention of your target audience and reflect your brand identity in the best possible way. Whether you need promotional posts, inspirational quotes, advertisements, or any other type of visual content.</p>',
                'features': 'تصاميم متوافقة مع جميع منصات التواصل الاجتماعي\nاستخدام ألوان وعناصر تتناسب مع هوية العلامة التجارية\nتصميم انفوجرافيك وتصاميم معلوماتية\nتصميم منشورات متسلسلة (كاروسيل)\nتصميم قوالب للستوري والريلز\nتعديلات غير محدودة حتى الوصول للنتيجة المطلوبة',
                'features_en': 'Designs compatible with all social media platforms\nUsing colors and elements that match the brand identity\nInfographic and informational designs\nCarousel post designs\nStory and Reels templates\nUnlimited edits until reaching the desired result',
                'package_includes': 'ملفات بصيغة JPG/PNG جاهزة للنشر\nملفات المصدر بصيغة PSD\nتعديلات غير محدودة\nترخيص تجاري للاستخدام',
                'package_includes_en': 'JPG/PNG files ready for publishing\nPSD source files\nUnlimited revisions\nCommercial license for use',
                'gallery': '[{"image": "/static/uploads/sm-1.jpg", "caption": "تصميم للفيسبوك", "caption_en": "Facebook Design"}, {"image": "/static/uploads/sm-2.jpg", "caption": "تصميم للانستغرام", "caption_en": "Instagram Design"}, {"image": "/static/uploads/sm-3.jpg", "caption": "تصميم للتويتر", "caption_en": "Twitter Design"}, {"image": "/static/uploads/sm-4.jpg", "caption": "انفوجرافيك", "caption_en": "Infographic"}]',
                'related_services': '[{"title": "تصميم الشعارات والهوية البصرية", "short_desc": "شعار مميز وهوية بصرية متكاملة", "url": "/service/logo-brand"}, {"title": "تصميم المطبوعات", "short_desc": "بروشورات، فلايرز، بطاقات عمل وأكثر", "url": "/service/print"}, {"title": "تصميم بصري للمناسبات", "short_desc": "تصاميم للفعاليات والمناسبات الخاصة", "url": "/service/events"}]',
                'related_services_en': '[{"title": "Logo & Brand Identity Design", "short_desc": "Distinctive logo and comprehensive brand identity", "url": "/en/service/logo-brand"}, {"title": "Print Design", "short_desc": "Brochures, flyers, business cards and more", "url": "/en/service/print"}, {"title": "Event Visual Design", "short_desc": "Designs for events and special occasions", "url": "/en/service/events"}]'
            },
            {
                'service_type': 'logo-brand',
                'title': 'تصميم الشعارات والهوية البصرية',
                'title_en': 'Logo & Brand Identity Design',
                'subtitle': 'شعار مميز يعكس روح علامتك التجارية وهوية بصرية متكاملة',
                'subtitle_en': 'A distinctive logo that reflects your brand spirit and comprehensive visual identity',
                'price': '15000 دج - 50000 دج',
                'price_en': '$150 - $500',
                'delivery_time': '3 - 7 أيام',
                'delivery_time_en': '3 - 7 days',
                'revisions': 'غير محدودة',
                'revisions_en': 'Unlimited',
                'formats': 'AI, EPS, SVG, PNG, JPG, PDF',
                'image_url': '/static/uploads/logo-design.jpg',
                'description': '<p>الشعار هو العنصر الأساسي لأي علامة تجارية ناجحة، وهو الانطباع الأول الذي يتركه عملك في أذهان العملاء. أقدم لك تصميماً فريداً يعكس قيم وروح علامتك التجارية ويميزها عن المنافسين.</p><p>خدمة تصميم الشعار والهوية البصرية تشمل تصميم شعار احترافي وكامل عناصر الهوية البصرية مثل ألوان العلامة التجارية، الخطوط، القرطاسية، وأكثر من ذلك.</p>',
                'description_en': '<p>The logo is the essential element of any successful brand, and it\'s the first impression your business leaves in customers\' minds. I offer you a unique design that reflects your brand\'s values and spirit, distinguishing it from competitors.</p><p>The logo and brand identity design service includes designing a professional logo and all visual identity elements such as brand colors, fonts, stationery, and more.</p>',
                'features': 'شعار فريد وحصري 100%\nملفات بصيغ متعددة تناسب جميع الاستخدامات\nدليل استخدام الهوية البصرية\nتصميم القرطاسية (بطاقات العمل، الأوراق الرسمية، الأظرف)\nشعار بألوان وإصدارات متعددة (ملون، أحادي اللون، سالب وموجب)\nتعديلات غير محدودة حتى الرضا الكامل',
                'features_en': '100% unique and exclusive logo\nFiles in multiple formats suitable for all uses\nBrand identity usage guide\nStationery design (business cards, letterheads, envelopes)\nLogo in multiple colors and versions (colored, monochrome, negative and positive)\nUnlimited revisions until complete satisfaction',
                'package_includes': 'شعار بصيغ متعددة (AI, EPS, SVG, PNG, JPG, PDF)\nدليل استخدام الهوية البصرية\nملفات القرطاسية بصيغ قابلة للتعديل\nترخيص تجاري كامل للاستخدام\nتعديلات غير محدودة',
                'package_includes_en': 'Logo in multiple formats (AI, EPS, SVG, PNG, JPG, PDF)\nBrand identity usage guide\nStationery files in editable formats\nFull commercial license for use\nUnlimited revisions',
                'gallery': '[{"image": "/static/uploads/logo-1.jpg", "caption": "شعار لشركة تقنية", "caption_en": "Tech Company Logo"}, {"image": "/static/uploads/logo-2.jpg", "caption": "هوية بصرية لمطعم", "caption_en": "Restaurant Brand Identity"}, {"image": "/static/uploads/logo-3.jpg", "caption": "شعار لعلامة ملابس", "caption_en": "Clothing Brand Logo"}, {"image": "/static/uploads/logo-4.jpg", "caption": "هوية بصرية متكاملة", "caption_en": "Comprehensive Brand Identity"}]',
                'related_services': '[{"title": "تصميم منشورات السوشيال ميديا", "short_desc": "تصاميم جذابة لمنصات التواصل الاجتماعي", "url": "/service/social-media"}, {"title": "تصميم المطبوعات", "short_desc": "بروشورات، فلايرز، بطاقات عمل وأكثر", "url": "/service/print"}, {"title": "تصميم الويب", "short_desc": "واجهات مستخدم جذابة وسهلة الاستخدام", "url": "/service/web-design"}]',
                'related_services_en': '[{"title": "Social Media Posts Design", "short_desc": "Attractive designs for social media platforms", "url": "/en/service/social-media"}, {"title": "Print Design", "short_desc": "Brochures, flyers, business cards and more", "url": "/en/service/print"}, {"title": "Web Design", "short_desc": "Attractive and user-friendly interfaces", "url": "/en/service/web-design"}]'
            }
        ]

        for service_data in services:
            new_service = Service(**service_data)
            db.session.add(new_service)

        db.session.commit()
        logging.info("Default services created")

# Initialize database with default data
with app.app_context():
    db.create_all()
    create_default_data()

@app.route('/')
def index():
    sections = Section.query.all()
    section_data = {}

    for section in sections:
        contents = Content.query.filter_by(section_id=section.id).all()
        images = Image.query.filter_by(section_id=section.id).all()

        content_data = {}
        image_data = {}

        for content in contents:
            content_data[content.key] = content.value

        for image in images:
            image_data[image.key] = image.path

        section_data[section.name] = {
            'title': section.title,
            'contents': content_data,
            'images': image_data
        }

    testimonials = Testimonial.query.filter_by(approved=True).order_by(Testimonial.created_at.desc()).all()
    services = Service.query.all()
    social_media_links = SocialMedia.query.filter_by(active=True).all()
    
    # Get homepage carousel items (showing all active items sorted by order)
    homepage_carousel_items = Carousel.query.filter_by(active=True).order_by(Carousel.order, Carousel.id).all()
    app.logger.info(f"Homepage: Found {len(homepage_carousel_items)} carousel items")
    for idx, item in enumerate(homepage_carousel_items):
        app.logger.info(f"Carousel #{idx+1}: {item.image_filename} (path: {item.image_path})")
    
    # Get portfolio carousel items for the portfolio section
    portfolio_carousel_items = PortfolioItem.query.filter(PortfolioItem.carousel_order > 0).order_by(PortfolioItem.carousel_order).all()
    
    featured_items = PortfolioItem.query.filter_by(featured=True).order_by(PortfolioItem.created_at.desc()).limit(6).all()

    if len(featured_items) < 6:
        additional_items = PortfolioItem.query.filter_by(featured=False).order_by(
            PortfolioItem.created_at.desc()).limit(6 - len(featured_items)).all()
        portfolio_items = featured_items + additional_items
    else:
        portfolio_items = featured_items

    from forms import TestimonialForm
    form = TestimonialForm()
    
    # Get contact information
    contact_info = {}
    contact_section = Section.query.filter_by(name='contact').first()
    if contact_section:
        for content in Content.query.filter_by(section_id=contact_section.id).all():
            contact_info[content.key] = content.value
            
    app.logger.info(f"Contact info: {contact_info}")

    return render_template('index.html',
                         section_data=section_data,
                         testimonials=testimonials,
                         services=services,
                         social_media_links=social_media_links,
                         portfolio_items=portfolio_items,
                         carousel_items=portfolio_carousel_items,
                         homepage_carousel_items=homepage_carousel_items,
                         contact_info=contact_info,
                         form=form)

@app.route('/portfolio')
def portfolio():
    portfolio_items = PortfolioItem.query.order_by(PortfolioItem.created_at.desc()).all()
    categories = set()
    for item in portfolio_items:
        item_categories = [cat.strip() for cat in item.category.split(',')]
        categories.update(item_categories)
    
    # حساب إجمالي الإحصائيات للوحة الإحصائيات بأسلوب انستجرام
    total_views = sum(item.views_count for item in portfolio_items)
    total_likes = sum(item.likes_count for item in portfolio_items)
    total_comments = sum(len(item.comments) for item in portfolio_items)
    
    testimonials = Testimonial.query.filter_by(approved=True).order_by(Testimonial.created_at.desc()).limit(3).all()
    social_media_links = SocialMedia.query.filter_by(active=True).all()
    
    # الحصول على معلومات الملف الشخصي
    user = User.query.filter_by(is_admin=True).first()
    profile = {
        'name': 'فيراس ديزاين',
        'bio': 'استوديو تصميم إبداعي متخصص في التصميم الجرافيكي والهوية البصرية وتطوير الويب.',
        'image_url': user.profile_image if user and user.profile_image else url_for('static', filename='img/default-avatar.png')
    }
    
    # استخدام قالب أسلوب انستجرام الجديد
    return render_template('portfolio_instagram_style.html', 
                           portfolio_items=portfolio_items,
                           categories=sorted(categories),
                           testimonials=testimonials,
                           social_media_links=social_media_links,
                           total_views=total_views,
                           total_likes=total_likes,
                           total_comments=total_comments,
                           profile=profile)

# تمت إزالة مسار الصفحة الرئيسية الإنجليزية

# تمت إزالة مسار معرض الأعمال الإنجليزية

# تمت إزالة مسار تفاصيل الخدمة الإنجليزية

@app.route('/service/<service_type>')
def service_detail(service_type):
    service_obj = Service.query.filter_by(service_type=service_type).first()
    if not service_obj:
        abort(404)
    service = {
        'title': service_obj.title,
        'subtitle': service_obj.subtitle,
        'price': service_obj.price,
        'delivery_time': service_obj.delivery_time,
        'revisions': service_obj.revisions,
        'formats': service_obj.formats,
        'image_url': service_obj.image_url,
        'description': service_obj.description,
        'features': service_obj.get_features(),
        'package_includes': service_obj.get_package_includes(),
        'gallery': service_obj.get_gallery(),
        'related_services': service_obj.get_related_services()
    }
    
    # جلب معلومات التواصل للاستخدام في زر الواتساب
    contact_info = {}
    contact_section = Section.query.filter_by(name='contact').first()
    if contact_section:
        contact_contents = Content.query.filter_by(section_id=contact_section.id).all()
        for content in contact_contents:
            contact_info[content.key] = content.value
    
    return render_template('service_detail.html', service=service, service_type=service_type, contact_info=contact_info)

@app.route('/admin')
def admin_redirect():
    return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user:
            if user.account_locked:
                flash('تم قفل الحساب بسبب محاولات تسجيل دخول متكررة. يرجى المحاولة بعد 30 دقيقة.', 'danger')
                return render_template('admin/login.html')

            if user.check_password(password):
                user.reset_login_attempts()
                login_user(user)
                session['last_active'] = datetime.now().timestamp()
                next_page = request.args.get('next')
                flash('تم تسجيل الدخول بنجاح!', 'success')
                return redirect(next_page or url_for('admin_dashboard'))
            else:
                user.increment_login_attempts()

        flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')

    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin/change-password', methods=['GET', 'POST'])
@login_required
def admin_change_password():
    """تغيير كلمة المرور للمسؤول"""
    if not current_user.is_authenticated or not current_user.role == UserRole.ADMIN.value:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # التحقق من البيانات
        if not current_password or not new_password or not confirm_password:
            flash('جميع الحقول مطلوبة', 'danger')
            return render_template('admin/profile.html", password_change_mode=True')
        
        if new_password != confirm_password:
            flash('كلمات المرور الجديدة غير متطابقة', 'danger')
            return render_template('admin/profile.html', password_change_mode=True)
        
        if len(new_password) < 6:
            flash('يجب أن تتكون كلمة المرور من 6 أحرف على الأقل', 'danger')
            return render_template('admin/profile.html', password_change_mode=True)
        
        # التحقق من كلمة المرور الحالية
        if not current_user.check_password(current_password):
            flash('كلمة المرور الحالية غير صحيحة', 'danger')
            return render_template('admin/profile.html', password_change_mode=True)
        
        # تحديث كلمة المرور
        current_user.set_password(new_password)
        db.session.commit()
        
        # تسجيل نشاط تغيير كلمة المرور
        activity = UserActivity(
            user_id=current_user.id,
            ip_address=request.remote_addr,
            activity_type='password_change',
            resource_type='admin',
            details=json.dumps({
                'user_agent': request.user_agent.string,
                'timestamp': datetime.now().isoformat()
            })
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('✅ تم تحديث كلمة المرور بنجاح', 'success')
        return redirect(url_for('admin_dashboard'))
    
    # إعداد البيانات اللازمة لقالب profile.html
    sections = Section.query.all()
    section_data = {}
    for section in sections:
        contents = Content.query.filter_by(section_id=section.id).all()
        images = Image.query.filter_by(section_id=section.id).all()
        content_data = {}
        image_data = {}
        for content in contents:
            content_data[content.key] = content.value
        for image in images:
            image_data[image.key] = image.path
        section_data[section.name] = {
            "title": section.title,
            "contents": content_data,
            "images": image_data
        }
    pending_testimonials = Testimonial.query.filter_by(approved=False).count()
    pending_portfolio_comments = PortfolioComment.query.filter_by(approved=False).count()
    
    return render_template("admin/profile.html", 
                           password_change_mode=True,
                           section_data=section_data,
                           pending_testimonials=pending_testimonials,
                           pending_portfolio_comments=pending_portfolio_comments)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    sections_count = Section.query.count()
    contents_count = Content.query.count()
    testimonials_count = Testimonial.query.count()
    pending_testimonials = Testimonial.query.filter_by(approved=False).count()
    pending_portfolio_comments = PortfolioComment.query.filter_by(approved=False).count()
    social_media_count = SocialMedia.query.count()
    active_social_media_count = SocialMedia.query.filter_by(active=True).count()
    services_count = Service.query.all()

    services = Service.query.all()
    social_media = SocialMedia.query.filter_by(active=True).all()
    recent_testimonials = Testimonial.query.filter_by(approved=True).order_by(Testimonial.created_at.desc()).limit(5).all()

    home_section = Section.query.filter_by(name='home').first()
    about_section = Section.query.filter_by(name='about').first()
    
    # Check for contact section
    contact_section = Section.query.filter_by(name='contact').first()
    if not contact_section:
        # Create contact section if it doesn't exist
        contact_section = Section(name='contact', title='معلومات التواصل')
        db.session.add(contact_section)
        
        # Add default contact info
        default_email = Content(section_id=contact_section.id, key='email', value='info@firas-designs.com')
        default_phone = Content(section_id=contact_section.id, key='phone', value='+213 770 123 456')
        default_address = Content(section_id=contact_section.id, key='address', value='الجزائر العاصمة، الجزائر')
        default_map = Content(section_id=contact_section.id, key='map_url', value='')
        
        db.session.add_all([default_email, default_phone, default_address, default_map])
        db.session.commit()
        
        app.logger.info("Created contact section with default data")

    home_content = {}
    if home_section:
        for content in Content.query.filter_by(section_id=home_section.id).all():
            home_content[content.key] = content.value

    about_content = {}
    if about_section:
        for content in Content.query.filter_by(section_id=about_section.id).all():
            about_content[content.key] = content.value

    return render_template('admin/dashboard.html', 
                          sections_count=sections_count,
                          contents_count=contents_count,
                          testimonials_count=testimonials_count,
                          pending_testimonials=pending_testimonials,
                          pending_portfolio_comments=pending_portfolio_comments,
                          social_media_count=social_media_count,
                          active_social_media_count=active_social_media_count,
                          services_count=services_count,
                          services=services,
                          social_media=social_media,
                          recent_testimonials=recent_testimonials,
                          home_content=home_content,
                          about_content=about_content)

@app.route('/admin/content')
@login_required
def admin_content():
    sections = Section.query.all()
    return render_template('admin/content.html', sections=sections)

@app.route('/admin/services')
@login_required
def admin_service_content():
    services = Service.query.all()
    return render_template('admin/service_content.html', services=services)

@app.route('/admin/services/<service_type>/edit')
@login_required
def admin_edit_service(service_type):
    service_obj = Service.query.filter_by(service_type=service_type).first()
    if not service_obj:
        flash('الخدمة غير موجودة', 'danger')
        return redirect(url_for('admin_service_content'))
    
    # Make sure services directory exists
    services_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'services')
    os.makedirs(services_dir, exist_ok=True)
    
    # Check if image file exists
    if service_obj.image_filename and not os.path.exists(os.path.join(services_dir, service_obj.image_filename)):
        app.logger.warning(f"Image file not found: {service_obj.image_filename}")
        # If image doesn't exist, use default
        service_obj.image_url = '/static/uploads/services/default-service.svg'
    
    service = {
        'service_type': service_obj.service_type,
        'title': service_obj.title,
        'title_en': service_obj.title_en,
        'subtitle': service_obj.subtitle,
        'subtitle_en': service_obj.subtitle_en,
        'price': service_obj.price,
        'price_en': service_obj.price_en,
        'delivery_time': service_obj.delivery_time,
        'delivery_time_en': service_obj.delivery_time_en,
        'revisions': service_obj.revisions,
        'revisions_en': service_obj.revisions_en,
        'formats': service_obj.formats,
        'image_url': service_obj.image_url,
        'image_filename': service_obj.image_filename,
        'description': service_obj.description,
        'description_en': service_obj.description_en,
        'features': service_obj.get_features(),
        'features_en': service_obj.get_features_en(),
        'package_includes': service_obj.get_package_includes(),
        'package_includes_en': service_obj.get_package_includes_en(),
        'gallery': service_obj.get_gallery(),
        'related_services': service_obj.get_related_services(),
        'related_services_en': service_obj.get_related_services_en()
    }
    return render_template('admin/edit_service.html', service=service, service_type=service_type)

@app.route('/admin/services/add', methods=['GET', 'POST'])
@login_required
def admin_add_service():
    if request.method == 'POST':
        service_type = request.form.get('service_type')
        if not service_type or not service_type.isalnum():
            flash('معرف الخدمة يجب أن يحتوي على أحرف وأرقام فقط', 'danger')
            return redirect(url_for('admin_add_service'))
        existing_service = Service.query.filter_by(service_type=service_type).first()
        if existing_service:
            flash('معرف الخدمة مستخدم بالفعل', 'danger')
            return redirect(url_for('admin_add_service'))
        new_service = Service(
            service_type=service_type,
            title=request.form.get('title', ''),
            subtitle=request.form.get('subtitle', ''),
            price=request.form.get('price', ''),
            delivery_time=request.form.get('delivery_time', ''),
            revisions=request.form.get('revisions', ''),
            formats=request.form.get('formats', ''),
            description=request.form.get('description', '')
        )
        try:
            db.session.add(new_service)
            db.session.commit()
            flash('تم إضافة الخدمة بنجاح', 'success')
            return redirect(url_for('admin_edit_service', service_type=service_type))
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ أثناء إضافة الخدمة', 'danger')
            return redirect(url_for('admin_add_service'))

    return render_template('admin/add_service.html')

@app.route('/admin/services/<service_type>/delete', methods=['POST'])
@login_required
def delete_service(service_type):
    service = Service.query.filter_by(service_type=service_type).first_or_404()
    try:
        # Delete the service's featured image if it exists
        if service.image_filename:
            services_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'services')
            image_path = os.path.join(services_dir, service.image_filename)
            if os.path.exists(image_path):
                os.remove(image_path)
                app.logger.info(f"Deleted service image: {service.image_filename}")
        
        # Delete the service from database
        db.session.delete(service)
        db.session.commit()
        flash('تم حذف الخدمة بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting service: {str(e)}")
        flash('حدث خطأ أثناء حذف الخدمة', 'danger')
    return redirect(url_for('admin_service_content'))

@app.route('/admin/services/<service_type>/update', methods=['POST'])
@login_required
def update_service(service_type):
    service = Service.query.filter_by(service_type=service_type).first()
    if not service:
        flash('الخدمة غير موجودة', 'danger')
        return redirect(url_for('admin_service_content'))
    try:
        # Update basic service details
        service.title = request.form.get('title')
        service.title_en = request.form.get('title_en')
        service.subtitle = request.form.get('subtitle')
        service.subtitle_en = request.form.get('subtitle_en')
        service.price = request.form.get('price')
        service.price_en = request.form.get('price_en')
        service.delivery_time = request.form.get('delivery_time')
        service.delivery_time_en = request.form.get('delivery_time_en')
        service.revisions = request.form.get('revisions')
        service.revisions_en = request.form.get('revisions_en')
        service.formats = request.form.get('formats')
        service.description = request.form.get('description')
        service.description_en = request.form.get('description_en')
        
        # Update features and package details
        features = request.form.getlist('features[]')
        service.features = json.dumps(features) if features else None
        features_en = request.form.getlist('features_en[]')
        service.features_en = json.dumps(features_en) if features_en else None
        package_includes = request.form.getlist('package_includes[]')
        service.package_includes = json.dumps(package_includes) if package_includes else None
        package_includes_en = request.form.getlist('package_includes_en[]')
        service.package_includes_en = json.dumps(package_includes_en) if package_includes_en else None
        
        # Create services directory if it doesn't exist
        services_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'services')
        os.makedirs(services_dir, exist_ok=True)
        
        # Handle image removal if requested
        remove_image = request.form.get('remove_image') == '1'
        if remove_image:
            # Delete the image file if it exists
            if service.image_filename and os.path.exists(os.path.join(services_dir, service.image_filename)):
                try:
                    os.remove(os.path.join(services_dir, service.image_filename))
                    app.logger.info(f"Deleted service image: {service.image_filename}")
                except Exception as e:
                    app.logger.error(f"Error deleting image: {str(e)}")
            
            # Reset image fields in the database
            service.image_filename = None
            service.image_url = "/static/uploads/services/default-service.svg"
            app.logger.info("Reset service image to default")
        
        # Handle image upload if a new file is provided    
        elif 'featured_image' in request.files:
            file = request.files['featured_image']
            if file and file.filename and file.filename.strip() != '':
                if allowed_file(file.filename):
                    # Generate secure filename with timestamp
                    secure_name = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    final_filename = f"{timestamp}_{secure_name}"
                    
                    # Delete old file if exists
                    if service.image_filename and os.path.exists(os.path.join(services_dir, service.image_filename)):
                        try:
                            os.remove(os.path.join(services_dir, service.image_filename))
                        except Exception as e:
                            app.logger.error(f"Error deleting old image: {str(e)}")
                    
                    # Save new file
                    file_path = os.path.join(services_dir, final_filename)
                    file.save(file_path)
                    
                    # Update database
                    service.image_filename = final_filename
                    service.image_url = f"/static/uploads/services/{final_filename}"
                    app.logger.info(f"Saved service image: {service.image_url}")
                else:
                    # If file format is not allowed, log the error but continue with other updates
                    app.logger.warning(f"Invalid file format for service image: {file.filename}")
                    flash('تم تحديث الخدمة، لكن صيغة الصورة غير مدعومة', 'warning')
        gallery_images = request.form.getlist('gallery_images[]')
        gallery_captions = request.form.getlist('gallery_captions[]')
        gallery = []
        
        # إنشاء مجلد للمعرض إذا لم يكن موجودًا
        services_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'services')
        gallery_dir = os.path.join(services_dir, 'gallery')
        os.makedirs(gallery_dir, exist_ok=True)
        
        for img, caption in zip(gallery_images, gallery_captions):
            # التحقق مما إذا كانت الصورة بصيغة base64 (تم رفعها للتو)
            if img.startswith('data:image'):
                try:
                    # استخراج نوع الصورة وبياناتها من base64
                    format_info, encoded_data = img.split(',', 1)
                    image_format = format_info.split(';')[0].split('/')[1]
                    
                    # فك ترميز البيانات
                    decoded_data = base64.b64decode(encoded_data)
                    
                    # إنشاء اسم ملف فريد
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
                    filename = f"gallery_{timestamp}_{random_str}.{image_format}"
                    
                    # حفظ الملف
                    file_path = os.path.join(gallery_dir, filename)
                    with open(file_path, 'wb') as f:
                        f.write(decoded_data)
                    
                    # تخزين الرابط النسبي للصورة
                    image_url = f"/static/uploads/services/gallery/{filename}"
                    gallery.append({
                        'image': image_url,
                        'caption': caption
                    })
                    app.logger.info(f"حفظ صورة معرض جديدة: {image_url}")
                except Exception as e:
                    app.logger.error(f"خطأ في معالجة صورة المعرض: {str(e)}")
                    # في حالة الخطأ، الاحتفاظ بالصورة الأصلية كما هي
                    gallery.append({
                        'image': img,
                        'caption': caption
                    })
            else:
                # إذا لم تكن الصورة بصيغة base64، فقم بتخزينها كما هي
                gallery.append({
                    'image': img,
                    'caption': caption
                })
        
        service.gallery = json.dumps(gallery) if gallery else None
        related_titles = request.form.getlist('related_titles[]')
        related_descs = request.form.getlist('related_descs[]')
        related_urls = request.form.getlist('related_urls[]')
        related_services = []
        for title, desc, url in zip(related_titles, related_descs, related_urls):
            related_services.append({
                'title': title,
                'short_desc': desc,
                'url': url
            })
        service.related_services = json.dumps(related_services) if related_services else None
        db.session.commit()
        flash('تم تحديث الخدمة بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating service: {str(e)}")
        flash('حدث خطأ أثناء تحديث الخدمة', 'danger')
    return redirect(url_for('admin_edit_service', service_type=service_type))

@app.route('/admin/content/<int:section_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_content(section_id):
    section = Section.query.get_or_404(section_id)
    if request.method == 'POST':
        try:
            # Log the incoming form data for debugging
            app.logger.info(f"Incoming form data: {request.form}")
            
            for key, value in request.form.items():
                if key.startswith('content_'):
                    content_key = key.replace('content_', '')
                    content = Content.query.filter_by(section_id=section_id, key=content_key).first()
                    
                    if content:
                        app.logger.info(f"Updating existing content: {content_key} = {value}")
                        content.value = value
                    else:
                        app.logger.info(f"Creating new content: {content_key} = {value}")
                        new_content = Content(section_id=section_id, key=content_key, value=value)
                        db.session.add(new_content)
            
            db.session.commit()
            db.session.refresh(section)  # Refresh the section object
            
            # Verify the changes
            updated_contents = Content.query.filter_by(section_id=section_id).all()
            app.logger.info("Updated contents:")
            for content in updated_contents:
                app.logger.info(f"{content.key}: {content.value}")
            
            flash('تم حفظ التغييرات بنجاح', 'success')
            return redirect(url_for('admin_content'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error saving content: {str(e)}")
            flash(f'حدث خطأ أثناء حفظ التغييرات: {str(e)}', 'danger')
            return redirect(url_for('admin_edit_content', section_id=section_id))
            
    contents = Content.query.filter_by(section_id=section_id).all()
    content_dict = {content.key: content.value for content in contents}
    return render_template('admin/edit_content.html', section=section, contents=content_dict)

@app.route('/admin/testimonials')
@login_required
def admin_testimonials():
    testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).all()
    return render_template('admin/testimonials.html', testimonials=testimonials)

@app.route('/admin/testimonials/<int:testimonial_id>/approve', methods=['GET', 'POST'])
@login_required
def approve_testimonial(testimonial_id):
    try:
        testimonial = Testimonial.query.get(testimonial_id)
        
        if not testimonial:
            flash('لم يتم العثور على التقييم المطلوب', 'danger')
            return redirect(url_for('admin_testimonials'))
            
        # Toggle approval status
        testimonial.approved = not testimonial.approved
        db.session.commit()
        
        # Show appropriate success message
        if testimonial.approved:
            flash(f'تم اعتماد التقييم من "{testimonial.name}" بنجاح وسيظهر الآن على الموقع', 'success')
        else:
            flash(f'تم إلغاء اعتماد التقييم من "{testimonial.name}" بنجاح ولن يظهر على الموقع', 'warning')
            
        return redirect(url_for('admin_testimonials'))
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error approving testimonial: {str(e)}")
        flash('حدث خطأ أثناء محاولة تحديث حالة التقييم. الرجاء المحاولة مرة أخرى.', 'danger')
        return redirect(url_for('admin_testimonials'))

@app.route('/admin/testimonials/<int:testimonial_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_testimonial(testimonial_id):
    try:
        testimonial = Testimonial.query.get(testimonial_id)
        
        if not testimonial:
            flash('لم يتم العثور على التقييم المطلوب', 'danger')
            return redirect(url_for('admin_testimonials'))
        
        # Store name for the success message
        name = testimonial.name
        
        # Delete from database
        db.session.delete(testimonial)
        db.session.commit()
        
        flash(f'تم حذف التقييم من "{name}" بنجاح', 'success')
        return redirect(url_for('admin_testimonials'))
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting testimonial: {str(e)}")
        flash('حدث خطأ أثناء محاولة حذف التقييم. الرجاء المحاولة مرة أخرى.', 'danger')
        return redirect(url_for('admin_testimonials'))

@app.route('/admin/profile')
@login_required
def admin_profile():
    from forms import ProfileForm
    form = ProfileForm()
    form.email.data = current_user.email
    sections = Section.query.all()
    section_data = {}
    for section in sections:
        contents = Content.query.filter_by(section_id=section.id).all()
        images = Image.query.filter_by(section_id=section.id).all()
        content_data = {}
        image_data = {}
        for content in contents:
            content_data[content.key] = content.value
        for image in images:
            image_data[image.key] = image.path
        section_data[section.name] = {
            'title': section.title,
            'contents': content_data,
            'images': image_data
        }
    pending_testimonials = Testimonial.query.filter_by(approved=False).count()
    pending_portfolio_comments = PortfolioComment.query.filter_by(approved=False).count()
    return render_template('admin/profile.html', 
                          form=form, 
                          section_data=section_data,
                          pending_testimonials=pending_testimonials,
                          pending_portfolio_comments=pending_portfolio_comments)

@app.route('/admin/social-media')
@login_required
def admin_social_media():
    social_media_links = SocialMedia.query.order_by(SocialMedia.platform).all()
    services_count = Service.query.count()
    testimonials_count = Testimonial.query.count()
    pending_testimonials = Testimonial.query.filter_by(approved=False).count()
    portfolio_count = PortfolioItem.query.count()
    pending_portfolio_comments = PortfolioComment.query.filter_by(approved=False).count()
    social_media_count = SocialMedia.query.count()
    active_social_media_count = SocialMedia.query.filter_by(active=True).count()
    
    return render_template('admin/social_media.html', 
                          social_media_links=social_media_links,
                          services_count=services_count,
                          testimonials_count=testimonials_count,
                          pending_testimonials=pending_testimonials,
                          portfolio_count=portfolio_count,
                          pending_portfolio_comments=pending_portfolio_comments,
                          social_media_count=social_media_count,
                          active_social_media_count=active_social_media_count)

@app.route('/admin/contact-info')
@login_required
def admin_contact_info():
    """عرض واجهة تعديل معلومات التواصل"""

@app.route('/admin/telegram-settings', methods=['GET'])
@login_required
@admin_required
def telegram_settings():
    """إعدادات إشعارات تيليجرام واختبار الاتصال"""
    # التحقق من وجود متغيرات البيئة لتيليجرام
    telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    return render_template('admin/telegram_settings.html', 
                           telegram_token=telegram_token, 
                           telegram_chat_id=telegram_chat_id)

@app.route('/admin/test-telegram', methods=['POST'])
@login_required
@admin_required
def test_telegram_connection():
    """اختبار الاتصال بتيليجرام وإرسال رسالة تجريبية"""
    success, message = test_telegram_notification()
    return jsonify({'success': success, 'message': message})
    
def admin_contact_info():
    """عرض واجهة تعديل معلومات التواصل"""
    contact_section = Section.query.filter_by(name='contact').first()
    if not contact_section:
        # Create contact section if it doesn't exist
        contact_section = Section(name='contact', title='معلومات التواصل')
        db.session.add(contact_section)
        
        # Add default contact info
        default_email = Content(section_id=contact_section.id, key='email', value='info@firas-designs.com')
        default_phone = Content(section_id=contact_section.id, key='phone', value='+213 770 123 456')
        default_address = Content(section_id=contact_section.id, key='address', value='الجزائر العاصمة، الجزائر')
        default_map = Content(section_id=contact_section.id, key='map_url', value='')
        
        db.session.add_all([default_email, default_phone, default_address, default_map])
        db.session.commit()
        
        app.logger.info("Created contact section with default data")
    
    # Get contact content
    email = ""
    phone = ""
    address = ""
    map_url = ""
    
    for content in Content.query.filter_by(section_id=contact_section.id).all():
        if content.key == 'email':
            email = content.value
        elif content.key == 'phone':
            phone = content.value
        elif content.key == 'address':
            address = content.value
        elif content.key == 'map_url':
            map_url = content.value
    
    # Create a dictionary for easier template usage
    contact_info = {
        'email': email,
        'phone': phone,
        'address': address,
        'map_url': map_url
    }
    
    return render_template('admin/contact_info.html', contact_info=contact_info)

@app.route('/admin/contact-info/update', methods=['POST'])
@login_required
def admin_update_contact():
    """تحديث معلومات التواصل"""
    email = request.form.get('email', '')
    phone = request.form.get('phone', '')
    address = request.form.get('address', '')
    map_url = request.form.get('map_url', '')
    
    contact_section = Section.query.filter_by(name='contact').first()
    if not contact_section:
        # Create contact section if it doesn't exist
        contact_section = Section(name='contact', title='معلومات التواصل')
        db.session.add(contact_section)
        db.session.commit()
    
    # Update or create email content
    email_content = Content.query.filter_by(section_id=contact_section.id, key='email').first()
    if email_content:
        email_content.value = email
    else:
        email_content = Content(section_id=contact_section.id, key='email', value=email)
        db.session.add(email_content)
    
    # Update or create phone content
    phone_content = Content.query.filter_by(section_id=contact_section.id, key='phone').first()
    if phone_content:
        phone_content.value = phone
    else:
        phone_content = Content(section_id=contact_section.id, key='phone', value=phone)
        db.session.add(phone_content)
    
    # Update or create address content
    address_content = Content.query.filter_by(section_id=contact_section.id, key='address').first()
    if address_content:
        address_content.value = address
    else:
        address_content = Content(section_id=contact_section.id, key='address', value=address)
        db.session.add(address_content)
    
    # Update or create map_url content
    map_content = Content.query.filter_by(section_id=contact_section.id, key='map_url').first()
    if map_content:
        map_content.value = map_url
    else:
        map_content = Content(section_id=contact_section.id, key='map_url', value=map_url)
        db.session.add(map_content)
    
    try:
        db.session.commit()
        app.logger.info("Contact information updated successfully")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': '✅ تم تحديث معلومات التواصل بنجاح'
            })
        
        flash('✅ تم تحديث معلومات التواصل بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating contact info: {str(e)}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': 'حدث خطأ أثناء تحديث معلومات التواصل'
            })
        
        flash('حدث خطأ أثناء تحديث معلومات التواصل', 'danger')
    
    return redirect(url_for('admin_contact_info'))

@app.route('/admin/social-media/add', methods=['POST'])
@login_required
def add_social_media():
    """إضافة رابط تواصل اجتماعي جديد"""
    # سجل معلومات الطلب للتصحيح
    app.logger.info(f"=== DEBUG INFO ===")
    app.logger.info(f"Request method: {request.method}")
    app.logger.info(f"Content type: {request.content_type}")
    app.logger.info(f"Request form keys: {list(request.form.keys()) if request.form else 'No form data'}")
    app.logger.info(f"=== END DEBUG INFO ===")
    
    # التحقق من وجود البيانات المطلوبة
    platform = request.form.get('platform')
    name = request.form.get('name')
    url = request.form.get('url')
    icon = request.form.get('icon')
    
    if not platform or not name or not url or not icon:
        flash('❌ جميع الحقول مطلوبة', 'danger')
        app.logger.warning(f"Missing required fields: Platform: {platform}, Name: {name}, URL: {url}, Icon: {icon}")
        return redirect(url_for('admin_social_media'))
    
    # تأكد من أن الرابط يبدأ بـ http:// أو https://
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # إنشاء كائن وسائل التواصل الاجتماعي الجديد
    social_media = SocialMedia(
        platform=platform,
        name=name,
        url=url,
        icon=icon,
        active=True
    )
    
    try:
        db.session.add(social_media)
        db.session.commit()
        app.logger.info(f"Social media link added successfully: {platform} - {name}")
        flash('✅ تم إضافة رابط التواصل بنجاح', 'success')
        
        # إذا كان الطلب من AJAX، أرجع استجابة JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': '✅ تم إضافة رابط التواصل بنجاح'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding social media link: {str(e)}")
        app.logger.error(traceback.format_exc())
        flash(f'❌ حدث خطأ: {str(e)}', 'danger')
        
        # إذا كان الطلب من AJAX، أرجع استجابة JSON مع الخطأ
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': f'❌ حدث خطأ: {str(e)}'}), 500
    
    return redirect(url_for('admin_social_media'))

@app.route('/admin/social-media/update', methods=['POST'])
@login_required
def update_social_media():
    """تحديث بيانات رابط التواصل الاجتماعي"""
    # سجل معلومات الطلب للتصحيح
    app.logger.info(f"=== DEBUG INFO ===")
    app.logger.info(f"Request method: {request.method}")
    app.logger.info(f"Content type: {request.content_type}")
    app.logger.info(f"Request form keys: {list(request.form.keys()) if request.form else 'No form data'}")
    app.logger.info(f"=== END DEBUG INFO ===")
    
    # التحقق من وجود البيانات المطلوبة
    social_id = request.form.get('social_id')
    platform = request.form.get('platform')
    name = request.form.get('name')
    url = request.form.get('url')
    icon = request.form.get('icon')
    active = bool(request.form.get('active'))
    
    if not social_id or not platform or not name or not url or not icon:
        flash('❌ جميع الحقول مطلوبة', 'danger')
        app.logger.warning(f"Missing required fields in update: ID: {social_id}, Platform: {platform}, Name: {name}, URL: {url}, Icon: {icon}")
        return redirect(url_for('admin_social_media'))
    
    # البحث عن الرابط في قاعدة البيانات
    social_media = SocialMedia.query.get_or_404(social_id)
    
    # تأكد من أن الرابط يبدأ بـ http:// أو https://
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # تحديث البيانات
    social_media.platform = platform
    social_media.name = name
    social_media.url = url
    social_media.icon = icon
    social_media.active = active
    
    try:
        db.session.commit()
        app.logger.info(f"Social media link updated successfully: ID={social_id}, Platform={platform}")
        flash('✅ تم تحديث رابط التواصل بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating social media link: {str(e)}")
        app.logger.error(traceback.format_exc())
        flash(f'❌ حدث خطأ أثناء تحديث رابط التواصل: {str(e)}', 'danger')
    
    return redirect(url_for('admin_social_media'))

@app.route('/admin/social-media/toggle/<int:social_id>', methods=['GET', 'POST'])
@login_required
def toggle_social_media(social_id):
    """تبديل حالة رابط التواصل الاجتماعي (نشط/غير نشط)"""
    social_media = SocialMedia.query.get_or_404(social_id)
    social_media.active = not social_media.active
    
    try:
        db.session.commit()
        app.logger.info(f"Social media link status toggled: ID={social_id}, New status: {'active' if social_media.active else 'inactive'}")
        
        if social_media.active:
            flash('✅ تم تفعيل رابط التواصل بنجاح', 'success')
        else:
            flash('✅ تم تعطيل رابط التواصل بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error toggling social media: {str(e)}")
        app.logger.error(traceback.format_exc())
        flash(f'❌ حدث خطأ أثناء تغيير حالة الرابط: {str(e)}', 'danger')
    
    return redirect(url_for('admin_social_media'))

@app.route('/admin/social-media/delete/<int:social_id>', methods=['GET', 'POST'])
@login_required
def delete_social_media(social_id):
    """حذف رابط التواصل الاجتماعي"""
    social_media = SocialMedia.query.get_or_404(social_id)
    platform = social_media.platform
    name = social_media.name
    
    try:
        db.session.delete(social_media)
        db.session.commit()
        app.logger.info(f"Social media link deleted: ID={social_id}, Platform={platform}, Name={name}")
        flash('✅ تم حذف رابط التواصل بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting social media: {str(e)}")
        app.logger.error(traceback.format_exc())
        flash(f'❌ حدث خطأ أثناء حذف رابط التواصل: {str(e)}', 'danger')
    
    return redirect(url_for('admin_social_media'))

@app.route('/admin/profile/update', methods=['POST'])
@login_required
def update_profile():
    from forms import ProfileForm
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.email = form.email.data
        if form.current_password.data and form.new_password.data:
            if check_password_hash(current_user.password_hash, form.current_password.data):
                if form.new_password.data == form.confirm_password.data:
                    current_user.set_password(form.new_password.data)
                    flash('تم تحديث كلمة المرور بنجاح', 'success')
                else:
                    flash('كلمة المرور الجديدة وتأكيدها غير متطابقين', 'danger')
                    return redirect(url_for('admin_profile'))
            else:
                flash('كلمة المرور الحالية غير صحيحة', 'danger')
                return redirect(url_for('admin_profile'))
        db.session.commit()
        flash('تم تحديث الملف الشخصي بنجاح', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')
    return redirect(url_for('admin_profile'))


@app.route('/admin/upload-profile-image', methods=['POST'])
@login_required
def upload_profile_image():
    """رفع وتحديث صورة الملف الشخصي"""
    if 'profile_image' not in request.files:
        return jsonify({'success': False, 'message': 'لم يتم اختيار ملف'}), 400
    
    file = request.files['profile_image']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'لم يتم اختيار ملف'}), 400
    
    # التحقق من نوع الملف
    if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        return jsonify({'success': False, 'message': 'يرجى اختيار صورة بتنسيق JPG أو PNG فقط'}), 400
    
    try:
        # إنشاء مجلد profile إذا لم يكن موجودًا
        profile_dir = os.path.join('static', 'uploads', 'profile')
        os.makedirs(profile_dir, exist_ok=True)
        
        # تنظيف اسم الملف وحفظه مع إضافة طابع زمني
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename_parts = os.path.splitext(secure_filename(file.filename))
        secure_filename_with_timestamp = f"{timestamp}_{filename_parts[0]}{filename_parts[1]}"
        file_path = os.path.join(profile_dir, secure_filename_with_timestamp)
        relative_path = f"/static/uploads/profile/{secure_filename_with_timestamp}"
        
        # حفظ الملف
        file.save(file_path)
        
        # البحث عن قسم "about" أو إنشاؤه إذا لم يكن موجودًا
        about_section = Section.query.filter_by(name='about').first()
        if not about_section:
            about_section = Section(name='about', title='من أنا')
            db.session.add(about_section)
            db.session.flush()
        
        # تحديث أو إنشاء سجل الصورة
        existing_image = Image.query.filter_by(section_id=about_section.id, key='profile_image').first()
        if existing_image:
            existing_image.filename = secure_filename_with_timestamp
            existing_image.path = relative_path
        else:
            new_image = Image(
                section_id=about_section.id,
                key='profile_image',
                filename=secure_filename_with_timestamp,
                path=relative_path
            )
            db.session.add(new_image)
        
        db.session.commit()
        app.logger.info(f"Profile image updated successfully: {relative_path}")
        
        return jsonify({
            'success': True,
            'message': '✅ تم تحديث صورة الملف الشخصي بنجاح',
            'image_path': relative_path
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error uploading profile image: {str(e)}")
        return jsonify({'success': False, 'message': f'حدث خطأ أثناء رفع الصورة: {str(e)}'}), 500

@app.route('/add-testimonial', methods=['POST'])
def add_testimonial():
    from forms import TestimonialForm
    form = TestimonialForm()
    
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.best == 'application/json'
    
    # Log form data for debugging
    app.logger.debug(f"Testimonial form submitted: {request.form}")
    
    if form.validate_on_submit():
        try:
            # Create new testimonial object
            testimonial = Testimonial(
                name=form.name.data,
                company=form.company.data,
                content=form.content.data,
                rating=form.rating.data,
                approved=False
            )
            
            # Add to database and commit
            db.session.add(testimonial)
            db.session.commit()
            
            # Log successful submission
            app.logger.info(f"Testimonial submitted successfully by {form.name.data}")
            
            # Prevent spam by adding session flag
            session['testimonial_submitted'] = True
            session['testimonial_time'] = datetime.now().timestamp()
            
            # Return different responses based on request type
            if is_ajax:
                return jsonify({
                    'success': True,
                    'message': 'شكراً لك! تم استلام توصيتك بنجاح وستتم مراجعتها قريباً.'
                })
            else:
                flash('شكراً لك! تم استلام توصيتك بنجاح وستتم مراجعتها قريباً.', 'success')
                return redirect(url_for('index') + '#testimonials')
                
        except Exception as e:
            # Roll back transaction on error
            db.session.rollback()
            
            # Log the detailed error
            app.logger.error(f"Error submitting testimonial: {str(e)}")
            
            # Return user-friendly error message
            if is_ajax:
                return jsonify({
                    'success': False,
                    'message': 'حدث خطأ أثناء حفظ تقييمك. الرجاء المحاولة مرة أخرى.'
                }), 500
            else:
                flash('حدث خطأ أثناء حفظ تقييمك. الرجاء المحاولة مرة أخرى.', 'danger')
                return redirect(url_for('index') + '#testimonials')
    else:
        # Form validation failed
        error_messages = []
        for field, errors in form.errors.items():
            for error in errors:
                field_label = getattr(form, field).label.text
                error_msg = f"{field_label}: {error}"
                error_messages.append(error_msg)
                app.logger.warning(f"Form validation error: {error_msg}")
        
        error_summary = ', '.join(error_messages)
        app.logger.warning(f"Testimonial form validation failed: {error_summary}")
        
        # Return validation errors to user
        if is_ajax:
            return jsonify({
                'success': False,
                'message': 'هناك خطأ في البيانات المدخلة',
                'errors': error_messages
            }), 400
        else:
            for msg in error_messages:
                flash(msg, 'danger')
            return redirect(url_for('index') + '#testimonials')

@app.route('/api/section/<section_name>/content')
def get_section_content(section_name):
    section = Section.query.filter_by(name=section_name).first()
    if not section:
        return jsonify({'error': 'Section not found'}), 404
    contents = Content.query.filter_by(section_id=section.id).all()
    content_data = {content.key: content.value for content in contents}
    return jsonify({
        'id': section.id,
        'name': section.name,
        'title': section.title,
        'contents': content_data
    })

@app.route('/api/content/update', methods=['POST'])
@login_required
def update_content():
    data = request.json
    section_id = data.get('section_id')
    key = data.get('key')
    value = data.get('value')
    if not section_id or not key:
        return jsonify({'error': 'Missing required fields'}), 400
    content = Content.query.filter_by(section_id=section_id, key=key).first()
    if content:
        content.value = value
    else:
        content = Content(section_id=section_id, key=key, value=value)
        db.session.add(content)
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/section/update', methods=['POST'])
@login_required
def update_section():
    data = request.json
    section_id = data.get('section_id')
    title = data.get('title')
    if not section_id or not title:
        return jsonify({'error': 'Missing required fields'}), 400
    section = Section.query.get(section_id)
    if not section:
        return jsonify({'error': 'Section not found'}), 404
    section.title = title
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-image', methods=['POST'])
@login_required
def upload_image():
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'لم يتم اختيار ملف'}), 400
    file = request.files['image']
    section = request.form.get('section')
    key = request.form.get('key')
    if file.filename == '':
        return jsonify({'success': False, 'message': 'لم يتم اختيار ملف'}), 400
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'نوع الملف غير مسموح به'}), 400
    try:
        filename = secure_file_save(file, file.filename)
        section_obj = None
        if section.isdigit():
            section_obj = Section.query.get(int(section))
        else:
            section_obj = Section.query.filter_by(name=section).first()
        if not section_obj:
            return jsonify({'success': False, 'message': 'القسم غير موجود'}), 404
        existing_image = Image.query.filter_by(section_id=section_obj.id, key=key).first()
        if existing_image:
            existing_image.filename = os.path.basename(filename)
            existing_image.path = filename
        else:
            new_image = Image(
                section_id=section_obj.id,
                key=key,
                filename=os.path.basename(filename),
                path=filename
            )
            db.session.add(new_image)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'تم رفع الصورة بنجاح',
            'path': filename,
            'url': filename
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'لم يتم اختيار ملف'}), 400
    file = request.files['image']
    section = request.form.get('section')
    key = request.form.get('key')
    if file.filename == '':
        return jsonify({'success': False, 'message': 'لم يتم اختيار ملف'}), 400
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'نوع الملف غير مسموح به'}), 400
    try:
        filename = secure_file_save(file, file.filename)
        section_obj = None
        if section.isdigit():
            section_obj = Section.query.get(int(section))
        else:
            section_obj = Section.query.filter_by(name=section).first()
        if not section_obj:
            return jsonify({'success': False, 'message': 'القسم غير موجود'}), 404
        existing_image = Image.query.filter_by(section_id=section_obj.id, key=key).first()
        if existing_image:
            existing_image.filename = os.path.basename(filename)
            existing_image.path = filename
        else:
            new_image = Image(
                section_id=section_obj.id,
                key=key,
                filename=os.path.basename(filename),
                path=filename
            )
            db.session.add(new_image)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'تم رفع الصورة بنجاح',
            'path': filename
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'لم يتم اختيار ملف', 'message': 'لم يتم اختيار ملف'}), 400
    file = request.files['image']
    section_identifier = request.form.get('section')
    key = request.form.get('key')
    caption = request.form.get('caption', '')
    alt_text = request.form.get('alt_text', '')
    if file.filename == '':
        return jsonify({'success': False, 'error': 'لم يتم اختيار ملف', 'message': 'لم يتم اختيار ملف'}), 400
    if not section_identifier:
        return jsonify({'success': False, 'error': 'يجب تحديد القسم', 'message': 'يجب تحديد القسم'}), 400
    if not key:
        return jsonify({'success': False, 'error': 'يجب تحديد مفتاح للصورة', 'message': 'يجب تحديد مفتاح للصورة'}), 400
    try:
        file_path = secure_file_save(file, file.filename)
        file_basename = os.path.basename(file_path)
        section_obj = None
        if str(section_identifier).isdigit():
            section_id = int(section_identifier)
            section_obj = Section.query.get(section_id)
        else:
            section_obj = Section.query.filter_by(name=section_identifier).first()
        if not section_obj:
            app.logger.error(f"القسم غير موجود: {section_identifier}")
            if not str(section_identifier).isdigit():
                section_obj = Section(
                    name=section_identifier,
                    title=section_identifier.capitalize()
                )
                db.session.add(section_obj)
                db.session.flush()
                app.logger.info(f"تم إنشاء قسم جديد: {section_identifier} (ID: {section_obj.id})")
            else:
                return jsonify({
                    'success': False, 
                    'error': f'القسم غير موجود: {section_identifier}', 
                    'message': f'القسم غير موجود: {section_identifier}'
                }), 404
        section_id = section_obj.id
        existing_image = Image.query.filter_by(section_id=section_id, key=key).first()
        if existing_image:
            if existing_image.filename != file_basename:
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], existing_image.filename)
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                        app.logger.info(f"تم حذف الصورة القديمة: {old_path}")
                    except Exception as e:
                        app.logger.warning(f"خطأ في حذف الصورة القديمة: {str(e)}")
            existing_image.filename = file_basename
            existing_image.path = file_path
        else:
            new_image = Image(
                section_id=section_id,
                key=key,
                filename=file_basename,
                path=file_path
            )
            db.session.add(new_image)
        db.session.commit()
        app.logger.info(f"تم رفع/تحديث الصورة بنجاح: {file_path}")
        return jsonify({
            'success': True,
            'message': 'تم تحديث الصورة بنجاح',
            'path': file_path,
            'url': file_path,
            'section': section_obj.name,
            'section_id': section_obj.id,
            'key': key,
            'filename': file_basename
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error uploading image: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'حدث خطأ أثناء رفع الصورة: {str(e)}'
        }), 500
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'لم يتم اختيار ملف'}), 400
    file = request.files['image']
    section = request.form.get('section')
    key = request.form.get('key')
    if file.filename == '':
        return jsonify({'success': False, 'message': 'لم يتم اختيار ملف'}), 400
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'نوع الملف غير مسموح به'}), 400
    try:
        filename = secure_file_save(file, file.filename)
        section_obj = None
        if section.isdigit():
            section_obj = Section.query.get(int(section))
        else:
            section_obj = Section.query.filter_by(name=section).first()
        if not section_obj:
            return jsonify({'success': False, 'message': 'القسم غير موجود'}), 404
        existing_image = Image.query.filter_by(section_id=section_obj.id, key=key).first()
        if existing_image:
            existing_image.filename = os.path.basename(filename)
            existing_image.path = filename
        else:
            new_image = Image(
                section_id=section_obj.id,
                key=key,
                filename=os.path.basename(filename),
                path=filename
            )
            db.session.add(new_image)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'تم رفع الصورة بنجاح',
            'path': filename
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    data = request.json
    if not data or not data.get('image'):
        return jsonify({'success': False, 'message': 'لم يتم تحديد الصورة'}), 400
    section_identifier = data.get('section')
    key = data.get('key')
    caption = data.get('caption', '')
    alt_text = data.get('alt_text', '')
    if not section_identifier or not key:
        return jsonify({'success': False, 'message': 'المعلومات المطلوبة غير مكتملة'}), 400
    try:
        img_parts = data.get('image').split(';base64,')
        if len(img_parts) != 2:
            return jsonify({'success': False, 'message': 'تنسيق الصورة غير صحيح'}), 400
        content_type = img_parts[0].split(':')[1]
        ext = 'jpg'
        if 'png' in content_type:
            ext = 'png'
        elif 'jpeg' in content_type or 'jpg' in content_type:
            ext = 'jpg'
        elif 'gif' in content_type:
            ext = 'gif'
        elif 'webp' in content_type:
            ext = 'webp'
        elif 'svg' in content_type:
            ext = 'svg'
        img_data = img_parts[1]
        img_bytes = base64.b64decode(img_data)
        section_obj = None
        if str(section_identifier).isdigit():
            section_id = int(section_identifier)
            section_obj = Section.query.get(section_id)
        else:
            section_obj = Section.query.filter_by(name=section_identifier).first()
        if not section_obj:
            app.logger.error(f"القسم غير موجود: {section_identifier}")
            if not str(section_identifier).isdigit():
                section_obj = Section(
                    name=section_identifier,
                    title=section_identifier.capitalize()
                )
                db.session.add(section_obj)
                db.session.flush()
                app.logger.info(f"تم إنشاء قسم جديد: {section_identifier} (ID: {section_obj.id})")
            else:
                return jsonify({
                    'success': False, 
                    'error': f'القسم غير موجود: {section_identifier}', 
                    'message': f'القسم غير موجود: {section_identifier}'
                }), 404
        section_id = section_obj.id
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{timestamp}_{key}.{ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(file_path, 'wb') as f:
            f.write(img_bytes)
        relative_path = f"/static/uploads/{filename}"
        app.logger.debug(f"تم حفظ الصورة في: {file_path}, المسار: {relative_path}")
        existing_image = Image.query.filter_by(section_id=section_id, key=key).first()
        if existing_image:
            old_path = os.path.join(app.config['UPLOAD_FOLDER'], existing_image.filename)
            if os.path.exists(old_path) and old_path != file_path:
                try:
                    os.remove(old_path)
                    app.logger.info(f"تم حذف الصورة القديمة: {old_path}")
                except Exception as e:
                    app.logger.warning(f"خطأ في حذف الصورة القديمة: {str(e)}")
            existing_image.filename = filename
            existing_image.path = relative_path
        else:
            new_image = Image(
                section_id=section_id,
                key=key,
                filename=filename,
                path=relative_path
            )
            db.session.add(new_image)
        db.session.commit()
        app.logger.info(f"تم رفع/تحديث الصورة بنجاح: {relative_path}")
        return jsonify({
            'success': True,
            'message': 'تم تحديث الصورة بنجاح',
            'path': relative_path,
            'url': relative_path,
            'section': section_obj.name,
            'section_id': section_obj.id,
            'key': key,
            'filename': filename
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"خطأ في معالجة الصورة: {str(e)}")
        return jsonify({
            'success': False, 
            'error': str(e), 
            'message': f'حدث خطأ أثناء معالجة الصورة: {str(e)}'
        }), 500

@app.route('/api/portfolio-items')
def get_portfolio_items():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    category = request.args.get('category')
    query = PortfolioItem.query
    if category:
        query = query.filter_by(category=category)
    items = query.order_by(PortfolioItem.created_at.desc()).paginate(page=page, per_page=per_page)
    result = {
        'items': [{
            'id': item.id,
            'title': item.title,
            'title_en': item.title_en,
            'description': item.description,
            'description_en': item.description_en,
            'image_url': item.image_url,
            'carousel_images': item.get_carousel_images() if item.carousel_images else [],
            'category': item.category,
            'year': item.year,
            'views_count': item.views_count,
            'likes_count': item.likes_count,
            'comments_count': item.comments.filter_by(approved=True).count()
        } for item in items.items],
        'total':items.total,
        'pages': items.pages,
        'current_page': page
    }
    return jsonify(result)

@app.route('/api/portfolio-items/<int:portfolio_id>')
@csrf.exempt
def get_portfolio_item_detail(portfolio_id):
    """الحصول على تفاصيل عنصر واحد من معرض الأعمال"""
    try:
        item = PortfolioItem.query.get_or_404(portfolio_id)
        result = {
            'status': 'success',
            'item': {
                'id': item.id,
                'title': item.title,
                'title_en': item.title_en,
                'description': item.description,
                'description_en': item.description_en,
                'image_url': item.image_url,
                'carousel_images': item.get_carousel_images(),
                'category': item.category,
                'external_url': item.link,
                'views_count': item.views_count,
                'likes_count': item.likes_count,
                'comments_count': item.comments.filter_by(approved=True).count(),
                'created_at': item.created_at.strftime('%Y-%m-%d'),
                'user_liked': False  # Placeholder, can be implemented with session tracking
            }
        }
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error fetching portfolio item details: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/portfolio-items/<int:portfolio_id>/view', methods=['POST'])
@csrf.exempt
def view_portfolio_item(portfolio_id):
    """زيادة عدد مشاهدات عنصر معرض الأعمال بطريقة دقيقة واحترافية"""
    try:
        # البحث عن عنصر المعرض
        item = PortfolioItem.query.get_or_404(portfolio_id)
        
        # الحصول على معلومات المستخدم/الزائر
        user_id = current_user.id if current_user.is_authenticated else None
        visitor_id = session.get('visitor_id')
        session_id = session.get('session_id', request.cookies.get('session'))
        ip_address = request.remote_addr
        user_agent = request.user_agent.string if request.user_agent else None
        fingerprint = request.cookies.get('browser_fingerprint') # إذا كان موجودًا
        referrer = request.referrer
        
        # التحقق مما إذا كان المستخدم/الزائر قد شاهد هذا العنصر من قبل
        existing_view = PortfolioView.query.filter(
            PortfolioView.portfolio_id == portfolio_id
        ).filter(
            # البحث عن المستخدم المسجل أو الزائر أو الجلسة
            db.or_(
                db.and_(PortfolioView.user_id == user_id, user_id != None),
                db.and_(PortfolioView.visitor_id == visitor_id, visitor_id != None),
                db.and_(PortfolioView.session_id == session_id, session_id != None),
                # تحقق من عنوان IP كملاذ أخير
                db.and_(PortfolioView.ip_address == ip_address, ip_address != None)
            )
        ).first()
        
        if existing_view:
            # تحديث سجل المشاهدة القائم
            existing_view.last_viewed_at = datetime.now()
            existing_view.view_count += 1
            # تحديث معلومات إضافية إذا تغيرت
            if user_id and not existing_view.user_id:
                existing_view.user_id = user_id
            if visitor_id and not existing_view.visitor_id:
                existing_view.visitor_id = visitor_id
            app.logger.info(f"Repeated view for portfolio item {portfolio_id} by the same user/visitor")
        else:
            # إنشاء سجل مشاهدة جديد
            new_view = PortfolioView(
                portfolio_id=portfolio_id,
                user_id=user_id,
                visitor_id=visitor_id,
                session_id=session_id,
                ip_address=ip_address,
                fingerprint=fingerprint,
                user_agent=user_agent,
                referrer=referrer
            )
            db.session.add(new_view)
            # زيادة العداد فقط للمشاهدات الجديدة
            item.views_count = item.views_count + 1 if item.views_count else 1
            app.logger.info(f"New view recorded for portfolio item {portfolio_id}, count: {item.views_count}")
        
        db.session.commit()
        return jsonify({'success': True, 'views_count': item.views_count})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error incrementing view count: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/portfolio-items/<int:portfolio_id>/like', methods=['POST'])
@csrf.exempt
def like_portfolio_item(portfolio_id):
    """تبديل حالة الإعجاب لعنصر معرض الأعمال (إضافة أو إزالة)"""
    try:
        # التحقق من وجود العنصر
        item = PortfolioItem.query.get_or_404(portfolio_id)
        
        # الحصول على عنوان IP للمستخدم الحالي
        user_ip = request.remote_addr
        if not user_ip:
            # استخدام X-Forwarded-For إذا كان هناك وسيط
            user_ip = request.headers.get('X-Forwarded-For', '127.0.0.1')
            
        # البحث عن إعجاب موجود
        existing_like = PortfolioLike.query.filter_by(
            portfolio_id=portfolio_id,
            user_ip=user_ip
        ).first()
        
        # إزالة الإعجاب إذا كان موجوداً، وإلا إضافة إعجاب جديد
        if existing_like:
            db.session.delete(existing_like)
            liked = False
            app.logger.info(f"Like removed for portfolio item {portfolio_id} from IP {user_ip}")
        else:
            new_like = PortfolioLike(portfolio_id=portfolio_id, user_ip=user_ip)
            db.session.add(new_like)
            liked = True
            app.logger.info(f"Like added for portfolio item {portfolio_id} from IP {user_ip}")
        
        # تحديث عدد الإعجابات وحفظ التغييرات
        item.likes_count = PortfolioLike.query.filter_by(portfolio_id=portfolio_id).count()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'likes_count': item.likes_count,
            'liked': liked
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error toggling like: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/portfolio-items/<int:portfolio_id>/comments')
def get_portfolio_comments(portfolio_id):
    comments = PortfolioComment.query.filter_by(
        portfolio_id=portfolio_id,
        approved=True
    ).order_by(PortfolioComment.created_at.desc()).all()
    result = [{
        'id': comment.id,
        'name': comment.name,
        'content': comment.content,
        'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
    } for comment in comments]
    return jsonify(result)

@app.route('/api/portfolio-items/<int:portfolio_id>/comments', methods=['POST'])
@csrf.exempt
def add_portfolio_comment(portfolio_id):
    data = request.json
    if not data or not data.get('name') or not data.get('content'):
        return jsonify({'error': 'Name and content are required'}), 400
    
    # Verify portfolio exists
    portfolio = PortfolioItem.query.get_or_404(portfolio_id)
    
    comment = PortfolioComment(
        portfolio_id=portfolio_id,
        name=data.get('name'),
        email=data.get('email'),
        content=data.get('content'),
        approved=False
    )
    try:
        db.session.add(comment)
        db.session.commit()
        
        # استخراج البريد الإلكتروني للمسؤول
        admin = User.query.first()
        admin_email = admin.email if admin else None
        
        # إرسال إشعار للمسؤول عن وجود تعليق جديد (إذا كانت الوظيفة موجودة)
        if 'send_testimonial_notification' in globals() and admin_email:
            try:
                send_testimonial_notification(
                    name=data.get('name'),
                    company="",
                    rating=5,
                    content=data.get('content'),
                    admin_email=admin_email
                )
            except Exception as e:
                # لا نريد أن نفشل في إضافة التعليق إذا فشل إرسال الإشعار
                app.logger.error(f"Failed to send notification email: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': 'تم إرسال تعليقك بنجاح وهو قيد المراجعة الآن'
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding comment: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/portfolio-comments')
@login_required
def admin_portfolio_comments():
    comments = PortfolioComment.query.order_by(PortfolioComment.created_at.desc()).all()
    pending_comments = [comment for comment in comments if not comment.approved]
    approved_comments = [comment for comment in comments if comment.approved]
    pending_testimonials = Testimonial.query.filter_by(approved=False).count()
    pending_portfolio_comments = PortfolioComment.query.filter_by(approved=False).count()
    return render_template('admin/portfolio_comments.html', 
                           pending_comments=pending_comments,
                           approved_comments=approved_comments,
                           pending_testimonials=pending_testimonials,
                           pending_portfolio_comments=pending_portfolio_comments)

@app.route('/admin/portfolio-comments/<int:comment_id>/approve', methods=['POST'])
@login_required
def approve_portfolio_comment(comment_id):
    comment = PortfolioComment.query.get_or_404(comment_id)
    comment.approved = True
    db.session.commit()
    flash('تم اعتماد التعليق بنجاح', 'success')
    return redirect(url_for('admin_portfolio_comments'))

@app.route('/admin/portfolio-comments/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_portfolio_comment(comment_id):
    comment = PortfolioComment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash('تم حذف التعليق بنجاح', 'success')
    return redirect(url_for('admin_portfolio_comments'))

@app.route('/api/contact', methods=['POST'])
@csrf.exempt
def contact_form():
    try:
        data = request.json
        required_fields = ['name', 'email', 'message']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            app.logger.warning(f"Missing contact form fields: {', '.join(missing_fields)}")
            return jsonify({
                'success': False,
                'error': 'جميع الحقول مطلوبة',
                'missing_fields': missing_fields
            }), 400
        name = data.get('name')
        email = data.get('email')
        subject = data.get('subject', 'رسالة جديدة من الموقع')
        message = data.get('message')
        phone = data.get('phone', '')
        app.logger.info(f"Contact form submission from {name} ({email})")
        
        # حفظ الرسالة في قاعدة البيانات
        try:
            new_message = ContactMessage(
                name=name,
                email=email,
                subject=subject,
                message=message,
                phone=phone,
                ip_address=request.remote_addr
            )
            db.session.add(new_message)
            db.session.commit()
            app.logger.info(f"Contact message saved to database with ID: {new_message.id}")
            
            # إرسال إشعار تيليجرام
            formatted_message = format_contact_message(name, email, message, subject)
            telegram_success = send_telegram_message(formatted_message)
            
            if telegram_success:
                new_message.telegram_sent = True
                db.session.commit()
                app.logger.info(f"Telegram notification sent for contact message ID {new_message.id}")
            else:
                app.logger.warning(f"Failed to send Telegram notification for contact message ID {new_message.id}")
                
        except Exception as db_error:
            app.logger.error(f"Error saving contact message to database: {str(db_error)}")
            # استمر بإرسال البريد حتى لو فشل حفظ الرسالة
        
        # إرسال بريد إلكتروني للإدارة
        admin_user = User.query.first()
        admin_email = admin_user.email if admin_user else os.environ.get('ADMIN_EMAIL', 'admin@example.com')
        email_sent = send_contact_form_notification(name, email, subject, message, admin_email)
        
        if email_sent:
            app.logger.info(f"Contact email sent successfully to {admin_email}")
            
            # تحديث حالة إرسال البريد إذا تم حفظ الرسالة
            try:
                if 'new_message' in locals() and new_message.id:
                    new_message.email_sent = True
                    db.session.commit()
            except Exception as e:
                app.logger.error(f"Error updating email_sent status: {str(e)}")
                
            return jsonify({
                'success': True,
                'message': 'تم إرسال رسالتك بنجاح، سنتواصل معك قريباً'
            })
        else:
            app.logger.error("Failed to send contact email")
            return jsonify({
                'success': False,
                'error': 'حدث خطأ أثناء إرسال الرسالة، يرجى المحاولة مرة أخرى لاحقاً'
            }), 500
    except Exception as e:
        app.logger.error(f"Contact form error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'حدث خطأ غير متوقع، يرجى المحاولة مرة أخرى لاحقاً'
        }), 500

@app.route('/admin/add-portfolio-item', methods=['GET', 'POST'])
@login_required
def add_portfolio_item():
    """إضافة عنصر جديد إلى معرض الأعمال"""
    # تسجيل معلومات للمساعدة في تصحيح أخطاء الإرسال
    app.logger.info("=== DEBUG INFO - ADD PORTFOLIO ITEM ===")
    app.logger.info(f"Request method: {request.method}")
    app.logger.info(f"Content type: {request.content_type}")
    app.logger.info(f"Request form keys: {list(request.form.keys()) if request.form else 'No form data'}")
    app.logger.info(f"Request files keys: {list(request.files.keys()) if request.files else 'No files'}")
    app.logger.info(f"Referrer: {request.referrer}")
    if 'image' in request.files:
        app.logger.info(f"Main image filename: {request.files['image'].filename}")
    if 'carousel_images[]' in request.files:
        app.logger.info(f"Carousel array files: {[f.filename for f in request.files.getlist('carousel_images[]')]}")
    elif 'carousel_images' in request.files:
        app.logger.info(f"Regular carousel files: {[f.filename for f in request.files.getlist('carousel_images')]}")
    app.logger.info("=== END DEBUG INFO ===")
    
    # إذا كان الطلب بطريقة GET، سنعرض نموذج إضافة المشروع
    if request.method == 'GET':
        # نهيئ نموذج فارغ ونعرض الصفحة
        form = {
            'title': None,
            'title_en': None,
            'description': None,
            'description_en': None,
            'category': None,
            'year': None,
            'featured': False,
            'carousel_order': 0,
            'csrf_token': None
        }
        
        # نرسل البيانات إلى قالب صفحة إضافة المشروع
        all_items = PortfolioItem.query.all()
        categories = set()
        for item in all_items:
            item_categories = [cat.strip() for cat in item.category.split(',') if cat.strip()]
            categories.update(item_categories)
            
        pending_testimonials = Testimonial.query.filter_by(approved=False).count()
        pending_portfolio_comments = PortfolioComment.query.filter_by(approved=False).count()
        
        return render_template('admin/portfolio_add.html',
                            categories=sorted(categories),
                            pending_testimonials=pending_testimonials,
                            pending_portfolio_comments=pending_portfolio_comments)
    
    # إذا كان الطلب بطريقة POST، سنتحقق من البيانات ونضيف المشروع
    try:
        # تسجيل بيانات النموذج للتصحيح بشكل مفصل
        app.logger.info("=== بدء إضافة مشروع جديد ===")
        app.logger.info(f"Request method: {request.method}")
        app.logger.info(f"Content type: {request.content_type}")
        app.logger.info(f"Form data keys: {list(request.form.keys())}")
        app.logger.info(f"CSRF Token: {request.form.get('csrf_token', 'NOT FOUND')}")
        app.logger.info(f"Title: {request.form.get('title', 'NOT FOUND')}")
        app.logger.info(f"Description length: {len(request.form.get('description', '')) if request.form.get('description') else 'NOT FOUND'}")
        app.logger.info(f"Category: {request.form.get('category', 'NOT FOUND')}")
        app.logger.info(f"Year: {request.form.get('year', 'NOT FOUND')}")
        app.logger.info(f"Featured: {'featured' in request.form}")
        app.logger.info(f"Carousel order: {request.form.get('carousel_order', 'NOT FOUND')}")
        app.logger.info(f"Files keys: {list(request.files.keys())}")
        
        if 'image' in request.files:
            app.logger.info(f"Main image filename: {request.files['image'].filename}")
            app.logger.info(f"Main image content type: {request.files['image'].content_type}")
        
        # تحديد طريقة جلب صور الكاروسيل (من الصيغة المفردة أو المصفوفة)
        if 'carousel_images[]' in request.files:
            carousel_files = request.files.getlist('carousel_images[]')
            app.logger.info(f"Using carousel_images[] array format, found {len(carousel_files)} files")
        else:
            carousel_files = request.files.getlist('carousel_images')
            app.logger.info(f"Using carousel_images format, found {len(carousel_files)} files")
            
        for i, file in enumerate(carousel_files):
            if file.filename:
                app.logger.info(f"Carousel image {i+1}: {file.filename}, {file.content_type}")
        
        # التحقق من الحقول المطلوبة
        if not request.form.get('title'):
            app.logger.error("Title is missing")
            flash('❌ الرجاء إدخال عنوان للمشروع', 'danger')
            # نعيد التوجيه إلى صفحة إضافة المشروع بدلاً من قائمة المشاريع
            return redirect(url_for('add_portfolio_item'))
            
        if not request.form.get('description'):
            app.logger.error("Description is missing")
            flash('❌ الرجاء إدخال وصف للمشروع', 'danger')
            return redirect(url_for('add_portfolio_item'))
            
        if not request.form.get('category'):
            app.logger.error("Category is missing")
            flash('❌ الرجاء إدخال فئة للمشروع', 'danger')
            return redirect(url_for('add_portfolio_item'))
        
        # التحقق من وجود الصورة الرئيسية
        app.logger.info("Checking for main image file...")
        if 'image' not in request.files:
            app.logger.error("No image field in request.files")
            flash('❌ يجب تحميل صورة رئيسية للعمل', 'danger')
            return redirect(url_for('add_portfolio_item'))

        file = request.files['image']
        app.logger.info(f"Image filename: {file.filename}")
        if file.filename == '':
            app.logger.error("Image filename is empty")
            flash('❌ لم يتم اختيار ملف للصورة الرئيسية', 'danger')
            return redirect(url_for('add_portfolio_item'))

        # التحقق من نوع الملف
        if not allowed_file(file.filename):
            app.logger.error(f"File type not allowed: {file.filename}")
            flash(f'❌ نوع الملف غير مسموح به. الأنواع المسموح بها هي: {", ".join(ALLOWED_EXTENSIONS)}', 'danger')
            return redirect(url_for('add_portfolio_item'))
        
        # إنشاء مجلد المشاريع إذا لم يكن موجودًا
        projects_folder = 'projects'
        projects_path = os.path.join(app.config['UPLOAD_FOLDER'], projects_folder)
        os.makedirs(projects_path, exist_ok=True)
        app.logger.info(f"Projects folder created at: {projects_path}")
        
        # حفظ الصورة الرئيسية
        try:
            app.logger.info("Saving main image...")
            filename = secure_file_save(file, file.filename, subfolder=projects_folder)
            image_filename = os.path.basename(filename)
            app.logger.info(f"Main image saved successfully: {filename}")
        except Exception as e:
            app.logger.error(f"Error saving main image: {str(e)}", exc_info=True)
            flash(f'❌ حدث خطأ أثناء حفظ الصورة الرئيسية: {str(e)}', 'danger')
            return redirect(url_for('add_portfolio_item'))
        
        # جمع بيانات النموذج
        title = request.form.get('title')
        title_en = request.form.get('title_en')
        description = request.form.get('description')
        description_en = request.form.get('description_en')
        category = request.form.get('category')
        
        # معالجة الحقول الرقمية بشكل آمن
        try:
            year = int(request.form.get('year')) if request.form.get('year') else None
        except ValueError:
            app.logger.warning(f"Invalid year value: {request.form.get('year')}")
            year = None
            
        try:
            carousel_order = int(request.form.get('carousel_order', 0))
            carousel_order = max(0, min(10, carousel_order))  # تقييد القيمة بين 0 و 10
        except ValueError:
            app.logger.warning(f"Invalid carousel_order value: {request.form.get('carousel_order')}")
            carousel_order = 0
            
        featured = 'featured' in request.form
        app.logger.info(f"Featured: {featured}")
        
        # معالجة صور الكاروسيل المتعددة (إذا وجدت)
        carousel_images = []
        
        # تحقق من وجود ملفات كاروسيل بالتنسيقين المختلفين
        carousel_files = []
        if 'carousel_images[]' in request.files:
            carousel_files = request.files.getlist('carousel_images[]')
            app.logger.info(f"Processing carousel_images[] array: {len(carousel_files)} files")
        elif 'carousel_images' in request.files:
            carousel_files = request.files.getlist('carousel_images') 
            app.logger.info(f"Processing carousel_images: {len(carousel_files)} files")
        
        for i, carousel_file in enumerate(carousel_files):
            # فقط معالجة الملفات التي تحتوي على اسم (أي أنها غير فارغة)
            if carousel_file and carousel_file.filename and carousel_file.filename != '':
                app.logger.info(f"Checking carousel image {i+1}: {carousel_file.filename}")
                
                if allowed_file(carousel_file.filename):
                    try:
                        app.logger.info(f"Saving carousel image {i+1}: {carousel_file.filename}")
                        carousel_filename = secure_file_save(carousel_file, carousel_file.filename, subfolder=projects_folder)
                        carousel_images.append(carousel_filename)
                        app.logger.info(f"Carousel image {i+1} saved successfully as: {carousel_filename}")
                    except Exception as e:
                        app.logger.error(f"Error saving carousel image {i+1}: {str(e)}", exc_info=True)
                        flash(f'⚠️ تم تخطي صورة الكاروسيل {i+1} بسبب خطأ في الحفظ: {str(e)}', 'warning')
                else:
                    app.logger.warning(f"Carousel image {i+1} has invalid file type: {carousel_file.filename}")
                    flash(f'⚠️ تم تخطي صورة الكاروسيل {i+1} بسبب نوع ملف غير مسموح به: {carousel_file.filename}', 'warning')
        
        # إنشاء عنصر معرض الأعمال
        try:
            app.logger.info("Creating new PortfolioItem...")
            # إنشاء عنصر جديد فقط بالحقول الموجودة في النموذج
            # تسجيل محتويات النموذج للمساعدة في تصحيح الأخطاء
            app.logger.info(f"المقولات المقبولة: title, title_en, description, description_en, image_url, category, link, featured, carousel_order")
            
            new_item = PortfolioItem(
                title=title,
                title_en=title_en,
                description=description,
                description_en=description_en,
                image_url=filename,  # يستخدم المسار الكامل المحفوظ للصورة
                category=category,
                link=request.form.get('link'),
                featured=featured,
                carousel_order=carousel_order
            )
            
            # تسجيل معلومات عن الكائن المنشأ
            app.logger.info(f"Created new PortfolioItem with title: {title}, image_url: {filename}")
            
            # إضافة العنصر الجديد إلى قاعدة البيانات
            app.logger.info("Adding to database session...")
            db.session.add(new_item)
            app.logger.info("Committing to database...")
            db.session.commit()
            
            app.logger.info(f"Portfolio item added successfully with ID: {new_item.id}")
            # إضافة رسالة نجاح واضحة مع تفاصيل
            flash(f'✅ تم إضافة المشروع "{title}" بنجاح. يمكنك الآن مشاهدته في معرض الأعمال.', 'success')
            # حفظ رسالة نجاح في الجلسة لعرضها في الصفحة التالية بشكل واضح
            if 'flash_messages' not in session:
                session['flash_messages'] = []
            session['flash_messages'].append({
                'message': f'✅ تم إضافة المشروع "{title}" بنجاح.',
                'category': 'success'
            })
            # تحويل المستخدم إلى صفحة إدارة المشاريع مع تحديد القسم
            return redirect(url_for('admin_portfolio_management'))
        except Exception as e:
            app.logger.error(f"Error creating or saving portfolio item: {str(e)}", exc_info=True)
            db.session.rollback()
            flash(f'❌ حدث خطأ أثناء حفظ المشروع في قاعدة البيانات: {str(e)}', 'danger')
            return redirect(url_for('add_portfolio_item'))
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"خطأ في إضافة عنصر المشروع: {str(e)}", exc_info=True)
        flash(f'❌ حدث خطأ أثناء إضافة العمل: {str(e)}', 'danger')
        return redirect(url_for('add_portfolio_item'))

@app.route('/admin/portfolio')
@login_required
def admin_portfolio_management():
    search_query = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    featured_filter = request.args.get('featured', '')
    query = PortfolioItem.query
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            db.or_(
                PortfolioItem.title.ilike(search_term),
                PortfolioItem.title_en.ilike(search_term),
                PortfolioItem.description.ilike(search_term),
                PortfolioItem.category.ilike(search_term)
            )
        )
    if category_filter:
        query = query.filter(PortfolioItem.category.ilike(f"%{category_filter}%"))
    if featured_filter == 'featured':
        query = query.filter(PortfolioItem.featured == True)
    elif featured_filter == 'not_featured':
        query = query.filter(PortfolioItem.featured == False)
    elif featured_filter == 'carousel':
        query = query.filter(PortfolioItem.carousel_order > 0)
    if sort_by == 'title':
        order_column = PortfolioItem.title
    elif sort_by == 'views':
        order_column = PortfolioItem.views_count
    elif sort_by == 'likes':
        order_column = PortfolioItem.likes_count
    elif sort_by == 'carousel_order':
        order_column = PortfolioItem.carousel_order
    else:
        order_column = PortfolioItem.created_at
    if sort_order == 'asc':
        query = query.order_by(order_column.asc())
    else:
        query = query.order_by(order_column.desc())
    portfolio_items = query.all()
    all_items = PortfolioItem.query.all()
    categories = set()
    for item in all_items:
        item_categories = [cat.strip() for cat in item.category.split(',') if cat.strip()]
        categories.update(item_categories)
    total_views = sum(item.views_count or 0 for item in all_items)
    total_likes = sum(item.likes_count or 0 for item in all_items)
    total_comments = PortfolioComment.query.count()
    featured_count = PortfolioItem.query.filter_by(featured=True).count()
    carousel_count = PortfolioItem.query.filter(PortfolioItem.carousel_order > 0).count()
    pending_testimonials = Testimonial.query.filter_by(approved=False).count()
    pending_portfolio_comments = PortfolioComment.query.filter_by(approved=False).count()
    return render_template('admin/portfolio_management.html', 
                          portfolio_items=portfolio_items,
                          categories=sorted(categories),
                          total_views=total_views,
                          total_likes=total_likes,
                          total_comments=total_comments,
                          pending_testimonials=pending_testimonials,
                          pending_portfolio_comments=pending_portfolio_comments,
                          featured_count=featured_count,
                          carousel_count=carousel_count,
                          search_query=search_query,
                          category_filter=category_filter,
                          sort_by=sort_by,
                          sort_order=sort_order,
                          featured_filter=featured_filter)

@app.route('/admin/portfolio/<int:portfolio_id>/update', methods=['GET', 'POST'])
@login_required
def update_portfolio_item(portfolio_id):
    try:
        item = PortfolioItem.query.get_or_404(portfolio_id)
        
        # إذا كان طلب GET، اعرض صفحة التعديل
        if request.method == 'GET':
            # الحصول على جميع الفئات الموجودة
            all_portfolio_items = PortfolioItem.query.all()
            categories = set()
            for portfolio_item in all_portfolio_items:
                if portfolio_item.category:
                    item_categories = [cat.strip() for cat in portfolio_item.category.split(',')]
                    categories.update(item_categories)
            
            # تجهيز صور الكاروسيل
            carousel_images = item.get_carousel_images()
            
            return render_template('admin/edit_portfolio_item.html', 
                                  item=item,
                                  categories=sorted(categories),
                                  carousel_images=carousel_images)
        
        # تسجيل بيانات التحديث للتصحيح
        app.logger.info(f"تحديث العنصر {portfolio_id}. الحقول المتاحة: title, title_en, description, description_en, category, link, featured, carousel_order")
        
        # تحديث البيانات
        item.title = request.form.get('title')
        item.title_en = request.form.get('title_en')
        item.description = request.form.get('description')
        item.description_en = request.form.get('description_en')
        item.category = request.form.get('category')
        item.link = request.form.get('link')
        item.featured = 'featured' in request.form
        carousel_order = request.form.get('carousel_order', type=int, default=0)
        item.carousel_order = max(0, min(10, carousel_order))
        
        # إنشاء مجلد المشاريع إذا لم يكن موجودًا
        projects_folder = 'projects'
        projects_path = os.path.join(app.config['UPLOAD_FOLDER'], projects_folder)
        os.makedirs(projects_path, exist_ok=True)
        
        # تحديث الصورة الرئيسية إذا تم تقديم صورة جديدة
        if 'image' in request.files and request.files['image'].filename != '':
            file = request.files['image']
            if allowed_file(file.filename):
                try:
                    # حفظ الصورة الجديدة في مجلد المشاريع
                    new_image_path = secure_file_save(file, file.filename, subfolder=projects_folder)
                    new_image_filename = os.path.basename(new_image_path)
                    
                    # حذف الصورة القديمة إذا كانت موجودة
                    if item.image_url:
                        old_filename = os.path.basename(item.image_url)
                        # تحديد المسار بناءً على ما إذا كانت الصورة في المجلد الفرعي أم لا
                        if 'projects/' in item.image_url:
                            old_path = os.path.join(projects_path, old_filename)
                        else:
                            old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_filename)
                            
                        if os.path.exists(old_path):
                            try:
                                os.remove(old_path)
                                app.logger.info(f"تم حذف الصورة القديمة: {old_path}")
                            except Exception as e:
                                app.logger.error(f"خطأ في حذف صورة المشروع القديمة: {str(e)}")
                    
                    # تحديث مسار الصورة في قاعدة البيانات
                    item.image_url = new_image_path
                    app.logger.info(f"Updated portfolio item image to: {new_image_path}")
                    
                except Exception as e:
                    app.logger.error(f"خطأ في حفظ صورة المشروع المحدثة: {str(e)}")
                    flash(f'حدث خطأ أثناء حفظ الصورة: {str(e)}', 'warning')
            else:
                flash('نوع الملف غير مسموح به. الأنواع المسموح بها هي: ' + ', '.join(ALLOWED_EXTENSIONS), 'warning')
        
        # معالجة صور الكاروسيل المتعددة (إذا وجدت)
        carousel_files = []
        if 'carousel_images[]' in request.files:
            carousel_files = request.files.getlist('carousel_images[]')
            app.logger.info(f"Edit: Using carousel_images[] array format, found {len(carousel_files)} files")
        elif 'carousel_images' in request.files:
            carousel_files = request.files.getlist('carousel_images') 
            app.logger.info(f"Edit: Using carousel_images format, found {len(carousel_files)} files")
            
        if carousel_files and any(file.filename != '' for file in carousel_files):
            # الحصول على قائمة الصور الحالية
            current_carousel_images = item.get_carousel_images()
            app.logger.info(f"Current carousel images: {len(current_carousel_images)}")
            
            # إضافة صور جديدة إلى القائمة
            for i, carousel_file in enumerate(carousel_files):
                if carousel_file.filename != '' and allowed_file(carousel_file.filename):
                    try:
                        app.logger.info(f"Saving edit carousel image {i+1}: {carousel_file.filename}")
                        carousel_filename = secure_file_save(carousel_file, carousel_file.filename, subfolder=projects_folder)
                        current_carousel_images.append(carousel_filename)
                        app.logger.info(f"Carousel image saved as: {carousel_filename}")
                    except Exception as e:
                        app.logger.error(f"خطأ في حفظ صورة الكاروسيل: {str(e)}", exc_info=True)
            
            # تحديث القائمة في قاعدة البيانات
            item.carousel_images = json.dumps(current_carousel_images)
        
        # حذف صور الكاروسيل التي تم تحديدها للحذف
        carousel_images_to_remove = request.form.getlist('remove_carousel_images')
        if carousel_images_to_remove:
            current_carousel_images = item.get_carousel_images()
            updated_carousel_images = []
            
            for img_url in current_carousel_images:
                if img_url not in carousel_images_to_remove:
                    updated_carousel_images.append(img_url)
                else:
                    # حذف الملف من القرص
                    try:
                        img_filename = os.path.basename(img_url)
                        if 'projects/' in img_url:
                            img_path = os.path.join(projects_path, img_filename)
                        else:
                            img_path = os.path.join(app.config['UPLOAD_FOLDER'], img_filename)
                            
                        if os.path.exists(img_path):
                            os.remove(img_path)
                            app.logger.info(f"تم حذف صورة الكاروسيل: {img_url}")
                    except Exception as e:
                        app.logger.error(f"خطأ في حذف صورة الكاروسيل: {str(e)}")
            
            item.carousel_images = json.dumps(updated_carousel_images) if updated_carousel_images else None
        
        db.session.commit()
        flash('تم تحديث العمل بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"خطأ في تحديث عنصر المحفظة: {str(e)}")
        flash(f'حدث خطأ أثناء تحديث العمل: {str(e)}', 'danger')
    return redirect(url_for('admin_portfolio_management'))

@app.route('/admin/portfolio/<int:portfolio_id>/delete', methods=['POST'])
@login_required
def delete_portfolio_item(portfolio_id):
    try:
        portfolio_item = PortfolioItem.query.get_or_404(portfolio_id)
        projects_folder = 'projects'
        projects_path = os.path.join(app.config['UPLOAD_FOLDER'], projects_folder)
        
        # حذف الصورة الرئيسية
        if portfolio_item.image_url:
            filename = os.path.basename(portfolio_item.image_url)
            # تحديد المسار بناءً على ما إذا كانت الصورة في المجلد الفرعي أم لا
            if 'projects/' in portfolio_item.image_url:
                image_path = os.path.join(projects_path, filename)
            else:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    app.logger.info(f"تم حذف الصورة الرئيسية للمشروع: {image_path}")
                except Exception as e:
                    app.logger.error(f"خطأ في حذف صورة المشروع: {str(e)}")
        
        # حذف صور الكاروسيل
        carousel_images = portfolio_item.get_carousel_images()
        for img_url in carousel_images:
            img_filename = os.path.basename(img_url)
            if 'projects/' in img_url:
                img_path = os.path.join(projects_path, img_filename)
            else:
                img_path = os.path.join(app.config['UPLOAD_FOLDER'], img_filename)
                
            if os.path.exists(img_path):
                try:
                    os.remove(img_path)
                    app.logger.info(f"تم حذف صورة الكاروسيل: {img_path}")
                except Exception as e:
                    app.logger.error(f"خطأ في حذف صورة الكاروسيل: {str(e)}")
        
        # حذف سجلات المشاهدات المرتبطة بهذا العنصر
        try:
            views = PortfolioView.query.filter_by(portfolio_id=portfolio_id).all()
            for view in views:
                db.session.delete(view)
            app.logger.info(f"تم حذف {len(views)} سجل مشاهدة مرتبط بالعنصر")
        except Exception as e:
            app.logger.error(f"خطأ في حذف سجلات المشاهدات: {str(e)}")
            
        # حذف سجلات الإعجابات المرتبطة بهذا العنصر
        try:
            likes = PortfolioLike.query.filter_by(portfolio_id=portfolio_id).all()
            for like in likes:
                db.session.delete(like)
            app.logger.info(f"تم حذف {len(likes)} سجل إعجاب مرتبط بالعنصر")
        except Exception as e:
            app.logger.error(f"خطأ في حذف سجلات الإعجابات: {str(e)}")
            
        # حذف التعليقات المرتبطة بهذا العنصر
        try:
            comments = PortfolioComment.query.filter_by(portfolio_id=portfolio_id).all()
            for comment in comments:
                # حذف الإعجابات بالتعليقات أولاً
                comment_likes = CommentLike.query.filter_by(comment_id=comment.id).all()
                for comment_like in comment_likes:
                    db.session.delete(comment_like)
                db.session.delete(comment)
            app.logger.info(f"تم حذف {len(comments)} تعليق مرتبط بالعنصر")
        except Exception as e:
            app.logger.error(f"خطأ في حذف التعليقات: {str(e)}")
        
        item_id = portfolio_item.id
        item_title = portfolio_item.title
        
        # حذف العنصر نفسه
        db.session.delete(portfolio_item)
        db.session.commit()
        flash('تم حذف العمل بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"خطأ في حذف عنصر المحفظة: {str(e)}")
        flash(f'حدث خطأ أثناء حذف العمل: {str(e)}', 'danger')
    return redirect(url_for('admin_portfolio_management'))

@app.route('/admin/carousel-management')
@login_required
def admin_carousel_management():
    # Portfolio Carousel Items
    portfolio_carousel_items = PortfolioItem.query.filter(PortfolioItem.carousel_order > 0).order_by(PortfolioItem.carousel_order).all()
    portfolio_items = PortfolioItem.query.order_by(PortfolioItem.created_at.desc()).all()
    featured_items = PortfolioItem.query.filter_by(featured=True).all()
    
    # Homepage Carousel Items
    homepage_carousel_items = Carousel.query.order_by(Carousel.order).all()
    
    # Notification counts
    pending_testimonials = Testimonial.query.filter_by(approved=False).count()
    pending_portfolio_comments = PortfolioComment.query.filter_by(approved=False).count()
    
    return render_template('admin/carousel_management.html',
                          carousel_items=portfolio_carousel_items,
                          portfolio_items=portfolio_items,
                          featured_items=featured_items,
                          homepage_carousel_items=homepage_carousel_items,
                          pending_testimonials=pending_testimonials,
                          pending_portfolio_comments=pending_portfolio_comments)

@app.route('/admin/api/homepage-carousel/<int:carousel_id>')
@login_required
def get_homepage_carousel_item(carousel_id):
    """الحصول على بيانات عنصر الكاروسيل للصفحة الرئيسية"""
    carousel_item = Carousel.query.get_or_404(carousel_id)
    
    return jsonify({
        'id': carousel_item.id,
        'title': carousel_item.title,
        'title_en': carousel_item.title_en,
        'caption': carousel_item.caption,
        'caption_en': carousel_item.caption_en,
        'image_path': carousel_item.image_path,
        'image_filename': carousel_item.image_filename,
        'active': carousel_item.active,
        'order': carousel_item.order
    })

@app.route('/admin/homepage-carousel/add', methods=['POST'])
@login_required
def add_homepage_carousel_item():
    """إضافة عنصر جديد لكاروسيل الصفحة الرئيسية"""
    try:
        # Check if the post request has the file part
        if 'image' not in request.files:
            flash('يجب تحميل صورة للشريحة', 'danger')
            return redirect(url_for('admin_carousel_management'))
        
        image = request.files['image']
        
        # If user does not select file, browser also
        # submits an empty part without filename
        if image.filename == '':
            flash('يجب اختيار صورة للشريحة', 'danger')
            return redirect(url_for('admin_carousel_management'))
        
        # Check if the file type is allowed
        if not allowed_file(image.filename):
            flash('نوع الملف غير مسموح به. يجب أن تكون الصورة بتنسيق JPG، JPEG، PNG، أو GIF', 'danger')
            return redirect(url_for('admin_carousel_management'))
        
        # Save the file securely using our helper function instead of custom code
        try:
            relative_path = secure_file_save(image, image.filename, subfolder='carousel')
            # Extract just the filename from the path
            filename = os.path.basename(relative_path)
            
            # Log successful image upload
            app.logger.info(f"Carousel image uploaded successfully: {relative_path}")
            
            # Create new carousel item in database
            carousel_item = Carousel(
                title=request.form.get('title'),
                title_en=request.form.get('title_en'),
                caption=request.form.get('caption'),
                caption_en=request.form.get('caption_en'),
                image_filename=filename,
                image_path=relative_path,
                active='active' in request.form,
                order=request.form.get('order', 0, type=int)
            )
            
            # Save to database
            db.session.add(carousel_item)
            db.session.commit()
            
            # Success message
            flash('تمت إضافة الشريحة بنجاح', 'success')
            return redirect(url_for('admin_carousel_management'))
            
        except ValueError as ve:
            # Handle file type validation error
            flash(f'خطأ: {str(ve)}', 'danger')
            return redirect(url_for('admin_carousel_management'))
            
    except Exception as e:
        # Handle any other errors
        db.session.rollback()
        app.logger.error(f"خطأ في إضافة شريحة الكاروسيل: {str(e)}")
        flash('حدث خطأ أثناء إضافة الشريحة. الرجاء المحاولة مرة أخرى.', 'danger')
        return redirect(url_for('admin_carousel_management'))

@app.route('/admin/homepage-carousel/<int:carousel_id>/edit', methods=['POST'])
@login_required
def edit_homepage_carousel_item(carousel_id):
    """تعديل عنصر كاروسيل الصفحة الرئيسية"""
    try:
        carousel_item = Carousel.query.get_or_404(carousel_id)
        
        carousel_item.title = request.form.get('title')
        carousel_item.title_en = request.form.get('title_en')
        carousel_item.caption = request.form.get('caption')
        carousel_item.caption_en = request.form.get('caption_en')
        carousel_item.active = 'active' in request.form
        carousel_item.order = request.form.get('order', 0, type=int)
        
        # تحديث الصورة إذا تم تحميل واحدة جديدة
        if 'image' in request.files and request.files['image'].filename:
            image = request.files['image']
            
            if not allowed_file(image.filename):
                flash('نوع الملف غير مسموح به. يجب أن تكون الصورة بتنسيق JPG، JPEG، PNG، أو GIF', 'danger')
                return redirect(url_for('admin_carousel_management'))
            
            try:
                # Save the new image securely
                relative_path = secure_file_save(image, image.filename, subfolder='carousel')
                # Extract just the filename from the path
                filename = os.path.basename(relative_path)
                
                # Log successful image upload
                app.logger.info(f"Updated carousel image uploaded successfully: {relative_path}")
                
                # تحديث البيانات
                carousel_item.image_filename = filename
                carousel_item.image_path = relative_path
                
            except ValueError as ve:
                flash(f'خطأ: {str(ve)}', 'danger')
                return redirect(url_for('admin_carousel_management'))
        
        carousel_item.updated_at = datetime.now()
        db.session.commit()
        
        flash('تم تحديث الشريحة بنجاح', 'success')
        return redirect(url_for('admin_carousel_management'))
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"خطأ في تعديل شريحة الكاروسيل: {str(e)}")
        flash(f'حدث خطأ أثناء تعديل الشريحة: {str(e)}', 'danger')
        return redirect(url_for('admin_carousel_management'))

@app.route('/admin/homepage-carousel/<int:carousel_id>/delete', methods=['POST'])
@login_required
def delete_homepage_carousel_item(carousel_id):
    """حذف عنصر كاروسيل الصفحة الرئيسية"""
    try:
        carousel_item = Carousel.query.get_or_404(carousel_id)
        
        # حذف الصورة من المجلد
        image_path = os.path.join(app.static_folder, 'uploads', 'carousel', carousel_item.image_filename)
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as e:
                app.logger.error(f"خطأ في حذف الصورة: {str(e)}")
        
        # حذف العنصر من قاعدة البيانات
        db.session.delete(carousel_item)
        db.session.commit()
        
        flash('تم حذف الشريحة بنجاح', 'success')
        return redirect(url_for('admin_carousel_management'))
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"خطأ في حذف شريحة الكاروسيل: {str(e)}")
        flash(f'حدث خطأ أثناء حذف الشريحة: {str(e)}', 'danger')
        return redirect(url_for('admin_carousel_management'))

@app.route('/admin/homepage-carousel/save-order', methods=['POST'])
@login_required
def save_homepage_carousel_order():
    """حفظ ترتيب شرائح الكاروسيل للصفحة الرئيسية"""
    try:
        data = request.json
        items = data.get('items', [])
        
        for item in items:
            carousel_id = item.get('id')
            order = item.get('order')
            
            carousel_item = Carousel.query.get(carousel_id)
            if carousel_item:
                carousel_item.order = order
        
        db.session.commit()
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"خطأ في حفظ ترتيب شرائح الكاروسيل: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/portfolio/update-carousel', methods=['POST'])
@login_required
def update_portfolio_carousel():
    try:
        portfolio_id = request.form.get('portfolio_id', type=int)
        if not portfolio_id:
            flash('معرف العنصر مطلوب', 'danger')
            return redirect(url_for('admin_carousel_management'))
        portfolio_item = PortfolioItem.query.get_or_404(portfolio_id)
        carousel_order = request.form.get('carousel_order', type=int, default=0)
        portfolio_item.carousel_order = max(0, min(10, carousel_order))
        portfolio_item.featured = 'featured' in request.form
        db.session.commit()
        flash('تم تحديث إعدادات الكاروسيل والعناصر البارزة بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"خطأ في تحديث إعدادات الكاروسيل: {str(e)}")
        flash(f'حدث خطأ أثناء تحديث إعدادات الكاروسيل: {str(e)}', 'danger')
    return redirect(url_for('admin_carousel_management'))

@app.route('/admin/carousel/save-order', methods=['POST'])
@login_required
def save_carousel_order():
    try:
        if request.is_json:
            data = request.get_json()
            items = data.get('items', [])
            if not items:
                return jsonify({'success': False, 'message': 'لا توجد عناصر للتحديث'})
            for index, item in enumerate(items, start=1):
                item_id = item.get('id')
                if item_id:
                    portfolio_item = PortfolioItem.query.get(item_id)
                    if portfolio_item:
                        portfolio_item.carousel_order = index
            db.session.commit()
            return jsonify({'success': True, 'message': 'تم تحديث ترتيب الكاروسيل بنجاح'})
        return jsonify({'success': False, 'message': 'البيانات غير صالحة'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"خطأ في حفظ ترتيب الكاروسيل: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/carousel/<int:item_id>/get-data')
@login_required
def get_carousel_item_data(item_id):
    """الحصول على بيانات عنصر الكاروسيل (للمحفظة) للتعديل"""
    item = PortfolioItem.query.get_or_404(item_id)
    
    data = {
        'id': item.id,
        'title': item.title,
        'title_en': item.title_en,
        'description': item.description,
        'description_en': item.description_en,
        'order': item.carousel_order,
        'active': item.featured,
        'image_path': item.image_url,
        'category': item.category,
        'year': item.year
    }
    
    return jsonify(data)

@app.route('/admin/carousel/update-order', methods=['POST'])
@login_required
def update_carousel_order():
    """تحديث ترتيب عنصر في الكاروسيل"""
    data = request.json
    try:
        carousel_id = data.get('carousel_id')
        new_order = data.get('order')
        
        item = PortfolioItem.query.get_or_404(carousel_id)
        item.carousel_order = new_order
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/carousel/toggle-status', methods=['POST'])
@login_required
def toggle_carousel_status():
    """تبديل حالة عنصر في الكاروسيل (نشط/غير نشط)"""
    data = request.json
    try:
        carousel_id = data.get('carousel_id')
        active = data.get('active')
        
        item = PortfolioItem.query.get_or_404(carousel_id)
        item.featured = active
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/carousel/<int:item_id>/update', methods=['POST'])
@login_required
def update_carousel_item(item_id):
    try:
        item = PortfolioItem.query.get_or_404(item_id)
        if 'title' in request.form:
            item.title = request.form['title']
        if 'description' in request.form:
            item.description = request.form['description']
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_file_save(file, file.filename)
                item.image_url = filename
        db.session.commit()
        flash('تم تحديث عنصر الكاروسيل بنجاح', 'success')
        return redirect(url_for('admin_carousel_management'))
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء تحديث عنصر الكاروسيل: {str(e)}', 'danger')
        return redirect(url_for('admin_carousel_management'))


# محلل المشاهدات المتطور واحترافي جدًا
@app.route('/admin/analytics/views')
@login_required
def views_analytics():
    """صفحة تحليل المشاهدات المتطورة واحترافية جدًا"""
    try:
        # التحقق من صلاحيات المستخدم
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
            return redirect(url_for('index'))
        
        # الحصول على معلمات التصفية
        days = request.args.get('days', 30, type=int)
        portfolio_id = request.args.get('portfolio_id', None, type=int)
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # تحديد الفترة الزمنية
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # الحصول على إجمالي المشاهدات
        try:
            total_views_query = db.session.query(func.sum(PortfolioItem.views_count))
            if days:
                # لا نستطيع تصفية حسب التاريخ لأن الحقل views_count هو إجمالي فقط
                pass
            total_views = total_views_query.scalar() or 0
        except Exception as e:
            app.logger.error(f"Error getting total views: {str(e)}")
            total_views = 0
            
        # الحصول على المشاهدات الفريدة (من portfolio_view)
        try:
            unique_views_query = db.session.query(func.count(distinct(PortfolioView.id)))
            if days:
                unique_views_query = unique_views_query.filter(PortfolioView.created_at >= start_date)
            unique_views = unique_views_query.scalar() or 0
        except Exception as e:
            app.logger.error(f"Error getting unique views: {str(e)}")
            unique_views = 0
            
        # الحصول على توزيع الأجهزة
        try:
            device_stats_query = db.session.query(
                Visitor.device,
                func.count(Visitor.id).label('count')
            ).group_by(Visitor.device)
            
            if days:
                device_stats_query = device_stats_query.filter(Visitor.first_visit >= start_date)
                
            device_stats_result = device_stats_query.all()
            
            device_stats = {
                'labels': [],
                'values': []
            }
            
            for device, count in device_stats_result:
                if device:  # تجنب القيم الفارغة
                    device_stats['labels'].append(device)
                    device_stats['values'].append(count)
        except Exception as e:
            app.logger.error(f"Error getting device stats: {str(e)}")
            device_stats = {
                'labels': ['كمبيوتر', 'هاتف', 'تابلت', 'أخرى'],
                'values': [1, 1, 1, 1]
            }
            
        # بيانات الاتجاه على مدار الفترة المحددة (7 أيام ماضية كحد أقصى)
        trend_days = min(days, 7)  # لعرض أحدث 7 أيام فقط لتبسيط الرسم البياني
        
        trend_data = {
            'labels': [],
            'total': [],
            'unique': []
        }
        
        # توليد بيانات الاتجاه يوميًا
        for i in range(trend_days, 0, -1):
            current_date = end_date - timedelta(days=i)
            next_date = current_date + timedelta(days=1)
            date_str = current_date.strftime('%Y-%m-%d')
            
            # إضافة التاريخ إلى التسميات
            trend_data['labels'].append(date_str)
            
            try:
                # عدد زيارات الصفحات في هذا اليوم
                day_visits = db.session.query(func.count(PageVisit.id)).filter(
                    PageVisit.visited_at >= current_date,
                    PageVisit.visited_at < next_date
                ).scalar() or 0
                
                # عدد الزوار الفريدين في هذا اليوم
                day_visitors = db.session.query(func.count(func.distinct(PageVisit.visitor_id))).filter(
                    PageVisit.visited_at >= current_date,
                    PageVisit.visited_at < next_date
                ).scalar() or 0
                
                trend_data['total'].append(day_visits)
                trend_data['unique'].append(day_visitors)
            except Exception as e:
                app.logger.error(f"Error getting trend data for {date_str}: {str(e)}")
                trend_data['total'].append(0)
                trend_data['unique'].append(0)
        
        # الحصول على إحصائيات المشاريع
        try:
            projects_query = db.session.query(
                PortfolioItem.id,
                PortfolioItem.title,
                PortfolioItem.views_count
            ).order_by(desc(PortfolioItem.views_count)).limit(5)
            
            projects_result = projects_query.all()
            
            top_projects = {
                'labels': [],
                'values': []
            }
            
            for project_id, title, views in projects_result:
                top_projects['labels'].append(title)
                top_projects['values'].append(views)
                
        except Exception as e:
            app.logger.error(f"Error getting top projects: {str(e)}")
            top_projects = {
                'labels': ['لا توجد بيانات'],
                'values': [0]
            }
            
        # إحصائيات المتابعة
        engagement_stats = {
            'avg_duration': 0,
            'bounce_rate': 0
        }
        
        try:
            # متوسط مدة المشاهدة
            avg_duration_query = db.session.query(func.avg(PortfolioView.duration))
            if days:
                avg_duration_query = avg_duration_query.filter(PortfolioView.created_at >= start_date)
            avg_duration = avg_duration_query.scalar() or 0
            
            engagement_stats['avg_duration'] = int(avg_duration)
            
            # نسبة الارتداد
            # تصحيح استخدام case() في SQLAlchemy
            bounced_query = db.session.query(func.sum(
                case((PortfolioView.bounced == True, 1), else_=0)
            ))
            total_query = db.session.query(func.count(PortfolioView.id))
            
            if days:
                bounced_query = bounced_query.filter(PortfolioView.created_at >= start_date)
                total_query = total_query.filter(PortfolioView.created_at >= start_date)
                
            bounced = bounced_query.scalar() or 0
            total = total_query.scalar() or 1  # لتجنب القسمة على صفر
            
            bounce_rate = (bounced / total) * 100 if total > 0 else 0
            engagement_stats['bounce_rate'] = int(bounce_rate)
            
        except Exception as e:
            app.logger.error(f"Error getting engagement stats: {str(e)}")
            
        # تحضير البيانات التفصيلية للمشاريع
        detailed_stats = []
        
        try:
            detailed_query = db.session.query(
                PortfolioItem.id,
                PortfolioItem.title,
                PortfolioItem.views_count,
                func.count(distinct(PortfolioView.id)).label('unique_views'),
                func.avg(PortfolioView.duration).label('avg_duration')
            ).outerjoin(
                PortfolioView, PortfolioView.portfolio_id == PortfolioItem.id
            ).group_by(
                PortfolioItem.id
            ).order_by(
                desc(PortfolioItem.views_count)
            )
            
            if days:
                detailed_query = detailed_query.filter(or_(
                    PortfolioView.created_at >= start_date,
                    PortfolioView.created_at == None
                ))
                
            # تطبيق الترقيم
            total_count = detailed_query.count()
            detailed_query = detailed_query.offset((page - 1) * per_page).limit(per_page)
            detailed_result = detailed_query.all()
            
            for item_id, title, views, unique_views, avg_duration in detailed_result:
                # حساب معدل التفاعل
                if avg_duration is None:
                    avg_duration = 0
                    
                engagement = min(int(avg_duration / 60) * 5, 100) if avg_duration else 0
                
                detailed_stats.append({
                    'id': item_id,
                    'title': title,
                    'views': views,
                    'unique_views': unique_views or 0,
                    'avg_duration': int(avg_duration or 0),
                    'engagement': engagement
                })
                
            # حساب إجمالي عدد الصفحات
            total_pages = (total_count + per_page - 1) // per_page
            
        except Exception as e:
            app.logger.error(f"Error getting detailed stats: {str(e)}")
            total_pages = 1
        
        # إحصائيات بسيطة
        # تغيير الطريقة لتحديد المتغير المسبب للمشكلة
        
        # إنشاء قاموس بالمتغيرات والتحقق من كل متغير على حدة
        # المتغيرات التي سيتم تمريرها إلى القالب
        template_vars = {}
        
        # إضافة كل متغير بشكل منفصل مع التحقق من نوعه
        try:
            template_vars['days'] = days
            app.logger.debug('days added successfully')
            
            template_vars['total_views'] = total_views
            app.logger.debug('total_views added successfully')
            
            template_vars['unique_views'] = unique_views
            app.logger.debug('unique_views added successfully')
            
            # التحقق من بيانات الاتجاه
            if isinstance(trend_data, dict) and 'labels' in trend_data and 'total' in trend_data and 'unique' in trend_data:
                template_vars['views_trend'] = trend_data
                app.logger.debug('views_trend added successfully')
            else:
                template_vars['views_trend'] = {'labels': [], 'total': [], 'unique': []}
                app.logger.warning('views_trend reset to default')
            
            # التحقق من إحصائيات الأجهزة
            if isinstance(device_stats, dict) and 'labels' in device_stats and 'values' in device_stats:
                template_vars['device_stats'] = device_stats
                app.logger.debug('device_stats added successfully')
            else:
                template_vars['device_stats'] = {'labels': [], 'values': []}
                app.logger.warning('device_stats reset to default')
            
            # التحقق من إحصائيات المشاريع
            if isinstance(top_projects, dict) and 'labels' in top_projects and 'values' in top_projects:
                template_vars['top_projects'] = top_projects
                app.logger.debug('top_projects added successfully')
            else:
                template_vars['top_projects'] = {'labels': [], 'values': []}
                app.logger.warning('top_projects reset to default')
            
            # التحقق من إحصائيات المشاركة
            if isinstance(engagement_stats, dict) and 'avg_duration' in engagement_stats and 'bounce_rate' in engagement_stats:
                template_vars['engagement_stats'] = engagement_stats
                app.logger.debug('engagement_stats added successfully')
            else:
                template_vars['engagement_stats'] = {'avg_duration': 0, 'bounce_rate': 0}
                app.logger.warning('engagement_stats reset to default')
            
            # التحقق من إحصائيات تفصيلية
            if isinstance(detailed_stats, list):
                template_vars['detailed_stats'] = detailed_stats
                app.logger.debug('detailed_stats added successfully')
            else:
                template_vars['detailed_stats'] = []
                app.logger.warning('detailed_stats reset to default')
            
            template_vars['page'] = page
            app.logger.debug('page added successfully')
            
            template_vars['total_pages'] = total_pages
            app.logger.debug('total_pages added successfully')
            
            template_vars['portfolio_id'] = portfolio_id
            app.logger.debug('portfolio_id added successfully')
            
        except Exception as e:
            app.logger.error(f"Error preparing template variables: {str(e)}")
            # إنشاء متغيرات افتراضية في حالة الخطأ
            template_vars = {
                'days': days if isinstance(days, int) else 30,
                'total_views': total_views if isinstance(total_views, int) else 0,
                'unique_views': unique_views if isinstance(unique_views, int) else 0,
                'views_trend': {'labels': [], 'total': [], 'unique': []},
                'device_stats': {'labels': [], 'values': []},
                'top_projects': {'labels': [], 'values': []},
                'engagement_stats': {'avg_duration': 0, 'bounce_rate': 0},
                'detailed_stats': [],
                'page': 1,
                'total_pages': 1,
                'portfolio_id': None
            }
        
        # ريندر القالب باستخدام المتغيرات المتحقق منها
        return render_template('admin/views_analytics.html', **template_vars)
                               
    except Exception as e:
        app.logger.error(f"Error in views_analytics: {str(e)}")
        flash(f'حدث خطأ: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))


# إضافة مسار صفحة التشخيص
@app.route('/system-diagnostic')
@admin_required
def system_diagnostic():
    """صفحة تشخيص النظام وقاعدة البيانات للمسؤول فقط"""
    from diagnostics import run_diagnostics
    results = run_diagnostics()
    return render_template('diagnostic.html', results=results)

# End of implementation

if __name__ == '__main__':
    app.run(debug=True)