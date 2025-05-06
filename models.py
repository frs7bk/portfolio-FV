from datetime import datetime, timedelta
import json
import enum
import ipaddress
from flask_login import UserMixin
from database import db
from werkzeug.security import generate_password_hash, check_password_hash

class UserRole(enum.Enum):
    ADMIN = 'admin'
    VISITOR = 'visitor' # مستخدم عادي للتعليق والإعجاب

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(100), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True) # رابط الصورة الشخصية
    bio = db.Column(db.Text, nullable=True) # نبذة عن المستخدم
    role = db.Column(db.String(20), default=UserRole.VISITOR.value)
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_login = db.Column(db.DateTime)
    login_attempts = db.Column(db.Integer, default=0)
    account_locked = db.Column(db.Boolean, default=False)
    
    # حقول المصادقة الثنائية
    two_factor_enabled = db.Column(db.Boolean, default=False)  # هل المصادقة الثنائية مفعلة
    telegram_chat_id = db.Column(db.String(100), nullable=True)  # معرف محادثة تليجرام للمستخدم
    telegram_verified = db.Column(db.Boolean, default=False)  # هل تم التحقق من ربط التليجرام
    telegram_verification_code = db.Column(db.String(20), nullable=True)  # رمز التحقق للربط
    telegram_code_expiry = db.Column(db.DateTime, nullable=True)  # تاريخ انتهاء صلاحية رمز الربط
    two_factor_method = db.Column(db.String(20), default='telegram')  # طريقة المصادقة الثنائية (telegram, email, etc)
    two_factor_secret = db.Column(db.String(100), nullable=True)  # سر المصادقة الثنائية (للطرق الأخرى مثل TOTP)
    
    # معلومات لتسجيل الدخول عبر Google
    google_id = db.Column(db.String(100), nullable=True, unique=True)  # معرف Google للمستخدم
    from_google = db.Column(db.Boolean, default=False)  # هل تم إنشاء الحساب من خلال Google
    
    # العلاقات
    comments = db.relationship('PortfolioComment', 
                             foreign_keys='PortfolioComment.user_id',
                             backref='user', lazy=True)
    likes = db.relationship('PortfolioLike', 
                          foreign_keys='PortfolioLike.user_id',
                          backref='user', lazy=True)
    comment_likes = db.relationship('CommentLike', 
                                  foreign_keys='CommentLike.user_id',
                                  backref='user', lazy=True)
    activities = db.relationship('UserActivity', 
                               foreign_keys='UserActivity.user_id',
                               backref='user', lazy=True)

    def increment_login_attempts(self):
        self.login_attempts += 1
        if self.login_attempts >= 5:
            self.account_locked = True
        db.session.commit()

    def reset_login_attempts(self):
        self.login_attempts = 0
        self.account_locked = False
        self.last_login = datetime.now()
        db.session.commit()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def generate_verification_token(self):
        import secrets
        self.verification_token = secrets.token_urlsafe(32)
        self.token_expiry = datetime.now() + timedelta(hours=24)
        return self.verification_token
        
    def verify_email(self, token):
        if self.verification_token == token and self.token_expiry and self.token_expiry > datetime.now():
            self.email_verified = True
            self.verification_token = None
            self.token_expiry = None
            return True
        return False
    
    def generate_telegram_verification_code(self):
        """إنشاء رمز للتحقق من ربط حساب تليجرام"""
        import secrets
        self.telegram_verification_code = ''.join(secrets.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(8))
        self.telegram_code_expiry = datetime.now() + timedelta(days=1)
        return self.telegram_verification_code
    
    def verify_telegram(self, code):
        """التحقق من رمز ربط حساب تليجرام"""
        if (self.telegram_verification_code == code and 
            self.telegram_code_expiry and 
            self.telegram_code_expiry > datetime.now()):
            self.telegram_verified = True
            self.telegram_verification_code = None
            self.telegram_code_expiry = None
            return True
        return False
    
    def needs_two_factor_auth(self):
        """التحقق مما إذا كان المستخدم يحتاج إلى المصادقة الثنائية"""
        return self.two_factor_enabled and self.telegram_verified
        
    def is_admin(self):
        return self.role == UserRole.ADMIN.value

    def __repr__(self):
        return f'<User {self.username}>'
        
class UserActivity(db.Model):
    """نموذج لتسجيل نشاطات المستخدمين"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # يمكن أن يكون النشاط لمستخدم غير مسجل
    ip_address = db.Column(db.String(45), nullable=True)
    activity_type = db.Column(db.String(50), nullable=False) # view, like, comment, login, register, etc.
    resource_type = db.Column(db.String(50), nullable=True) # portfolio_item, page, etc.
    resource_id = db.Column(db.Integer, nullable=True) # معرف المورد إذا كان موجوداً
    details = db.Column(db.Text, nullable=True) # تفاصيل إضافية عن النشاط بتنسيق JSON
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<UserActivity {self.activity_type}>'

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)

    contents = db.relationship('Content', backref='section', lazy=True, cascade="all, delete-orphan")
    images = db.relationship('Image', backref='section', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Section {self.name}>'

class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Text, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('section_id', 'key', name='uix_content_section_key'),
    )

    def __repr__(self):
        return f'<Content {self.section.name}.{self.key}>'

class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=5)
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Testimonial by {self.name}>'

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    key = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Image {self.filename}>'

class PortfolioView(db.Model):
    """نموذج متطور لتتبع مشاهدات عناصر المعرض بشكل احترافي"""
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio_item.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # للمستخدم المسجل
    visitor_id = db.Column(db.Integer, db.ForeignKey('visitor.id'), nullable=True)  # للزائر غير المسجل
    session_id = db.Column(db.Text, nullable=True)  # معرف الجلسة
    ip_address = db.Column(db.String(45), nullable=True)  # عنوان IP
    fingerprint = db.Column(db.String(255), nullable=True)  # بصمة المتصفح
    created_at = db.Column(db.DateTime, default=datetime.now)  # وقت المشاهدة الأولى
    last_viewed_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # وقت آخر مشاهدة
    view_count = db.Column(db.Integer, default=1)  # عدد مرات المشاهدة من نفس المستخدم/الزائر
    duration = db.Column(db.Integer, default=0)  # مدة المشاهدة بالثواني (تقديرية)
    user_agent = db.Column(db.Text, nullable=True)  # معلومات متصفح المستخدم
    referrer = db.Column(db.Text, nullable=True)  # الصفحة المحيلة
    country = db.Column(db.String(100), nullable=True)  # الدولة المقدرة للزائر
    city = db.Column(db.String(100), nullable=True)  # المدينة المقدرة للزائر
    device_type = db.Column(db.String(50), nullable=True)  # نوع الجهاز (حاسوب، جوال، لوحي)
    bounced = db.Column(db.Boolean, default=True)  # هل غادر الزائر سريعاً؟
    
    # علاقة لتسهيل الوصول إلى بيانات العنصر
    portfolio_item = db.relationship('PortfolioItem', backref='views')
    
    # خصائص محسوبة وإحصائيات متقدمة
    @property
    def last_view(self):
        """الحصول على وقت آخر مشاهدة"""
        return self.last_viewed_at
    
    @property
    def engagement_score(self):
        """حساب مؤشر تفاعل المستخدم مع العنصر (0-100%)"""
        # حساب المؤشر بناءً على عدد المشاهدات والمدة والتفاعلات الأخرى
        base_score = min(self.view_count * 10, 40)  # حد أقصى 40% للمشاهدات
        duration_score = min(self.duration // 30, 60)  # حد أقصى 60% للمدة (كل 30 ثانية = 1 نقطة)
        return min(base_score + duration_score, 100)
    
    @property
    def is_returning_visitor(self):
        """تحديد ما إذا كان زائر عائد"""
        return self.view_count > 1
    
    @property
    def estimated_read_percentage(self):
        """نسبة تقديرية لقراءة المحتوى استناداً على المدة"""
        # افتراض 200 كلمة في الدقيقة كمتوسط قراءة
        avg_read_time = 60  # افتراضي: يستغرق قراءة المشروع 60 ثانية
        if self.duration <= 0:
            return 0
        read_percentage = min((self.duration / avg_read_time) * 100, 100)
        return int(read_percentage)
    
    # قيود فريدة لمنع تكرار السجلات
    __table_args__ = (
        # ضمان عدم تكرار المشاهدة من نفس الزائر أو المستخدم لنفس المشروع
        db.UniqueConstraint('portfolio_id', 'user_id', name='uix_view_portfolio_user'),
        db.UniqueConstraint('portfolio_id', 'visitor_id', name='uix_view_portfolio_visitor'),
        db.UniqueConstraint('portfolio_id', 'fingerprint', name='uix_view_portfolio_fingerprint'),
    )
    
    def __repr__(self):
        return f'<PortfolioView {self.id}: portfolio={self.portfolio_id}, views={self.view_count}>'
    
    # تحديث معلومات المشاهدة الحالية
    def update_view(self, duration=None, referrer=None):
        """تحديث معلومات المشاهدة الحالية"""
        # زيادة عداد المشاهدات
        self.view_count += 1
        # تحديث وقت آخر مشاهدة تلقائياً من خلال onupdate
        
        # تحديث المدة إذا تم توفيرها
        if duration is not None and duration > 0:
            # نستخدم المتوسط المرجح للمدة للحصول على تقدير أفضل
            if self.duration > 0:
                self.duration = int((self.duration * 0.7) + (duration * 0.3))
            else:
                self.duration = duration
        
        # تحديث المرجع إذا تم توفيره
        if referrer:
            self.referrer = referrer
        
        # تحديث حالة المغادرة السريعة إذا شاهد الصفحة أكثر من مرة أو بقي لفترة
        if self.view_count > 1 or (duration and duration >= 30):
            self.bounced = False
        
        return self
    
    @classmethod
    def get_view(cls, portfolio_id, user_id=None, session_id=None, fingerprint=None, visitor_id=None):
        """الحصول على سجل المشاهدة الحالي إن وجد"""
        query = cls.query.filter_by(portfolio_id=portfolio_id)
        
        if user_id:
            return query.filter_by(user_id=user_id).first()
        elif session_id:
            return query.filter_by(session_id=session_id).first()
        elif fingerprint:
            return query.filter_by(fingerprint=fingerprint).first()
        elif visitor_id:
            return query.filter_by(visitor_id=visitor_id).first()
            
        return None
    
    @classmethod
    def get_analytics(cls, portfolio_id=None, days=30):
        """الحصول على إحصائيات متقدمة للمشاهدات"""
        from sqlalchemy import func, and_, distinct
        from datetime import datetime, timedelta
        
        # تاريخ البداية للتحليل
        start_date = datetime.now() - timedelta(days=days)
        
        # الاستعلام الأساسي
        query = db.session.query(cls)
        
        # تطبيق فلترة حسب العنصر إذا تم تحديده
        if portfolio_id:
            query = query.filter(cls.portfolio_id == portfolio_id)
        
        # تطبيق فلترة التاريخ
        query = query.filter(cls.created_at >= start_date)
        
        # إحصائيات متنوعة
        total_views = query.count()
        unique_views = db.session.query(func.count(distinct(cls.ip_address))).filter(
            cls.created_at >= start_date
        ).scalar()
        
        returning_views = query.filter(cls.view_count > 1).count()
        avg_duration = query.with_entities(func.avg(cls.duration)).scalar() or 0
        
        # التحليل حسب الجهاز (تلخيص)
        device_stats = {}
        for view in query.all():
            device = view.device_type or 'unknown'
            if device not in device_stats:
                device_stats[device] = 0
            device_stats[device] += 1
        
        # نسبة المشاهدات المرتدة
        bounce_rate = 0
        if total_views > 0:
            bounce_rate = (query.filter(cls.bounced == True).count() / total_views) * 100
            
        return {
            'total_views': total_views,
            'unique_views': unique_views,
            'returning_views': returning_views,
            'avg_duration': int(avg_duration),
            'bounce_rate': round(bounce_rate, 2),
            'device_stats': device_stats
        }

class PortfolioItem(db.Model):
    """نموذج لعنصر في معرض الأعمال"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=False)
    description_en = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=False)  # المسار النسبي للصورة
    category = db.Column(db.String(100), nullable=False, default="")
    link = db.Column(db.String(255), nullable=True)  # رابط المشروع (اختياري)
    carousel_images = db.Column(db.Text, nullable=True)  # صور إضافية مخزنة كـ JSON
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # إضافة الحقول المطلوبة للحفاظ على التوافق مع الكود القديم
    featured = db.Column(db.Boolean, default=False)  # هل المشروع مميز في الصفحة الرئيسية؟
    carousel_order = db.Column(db.Integer, default=0)  # ترتيب العرض في الكاروسيل (0 = لا يظهر)
    views_count = db.Column(db.Integer, default=0)  # عدد المشاهدات
    likes_count_value = db.Column(db.Integer, default=0)  # عدد الإعجابات
    
    @property
    def likes_count(self):
        """للحفاظ على التوافق مع الكود القديم"""
        return self.likes_count_value
    
    # المحافظة على العلاقات الموجودة سابقاً
    comments = db.relationship('PortfolioComment', backref='portfolio_item', lazy=True, cascade="all, delete-orphan")
    likes = db.relationship('PortfolioLike', backref='portfolio_item', lazy=True, cascade="all, delete-orphan")

    def increment_views(self):
        """زيادة عدد مشاهدات المشروع"""
        if self.views_count is None:
            self.views_count = 1
        else:
            self.views_count += 1
        return self.views_count
    
    def update_views_count(self):
        """تحديث عدد المشاهدات بناءً على عدد السجلات الفريدة"""
        from sqlalchemy import func
        count = db.session.query(func.count(PortfolioView.id)).filter(PortfolioView.portfolio_id == self.id).scalar()
        self.views_count = count
        return self.views_count
        
    def get_carousel_images(self):
        """الحصول على قائمة بمسارات صور الكاروسيل"""
        if self.carousel_images:
            try:
                return json.loads(self.carousel_images)
            except:
                return []
        return []
    
    def get_likes_count(self):
        """الحصول على عدد الإعجابات من قاعدة البيانات"""
        return len(self.likes)

    def __repr__(self):
        return f'<PortfolioItem {self.id}: {self.title}>'

class PortfolioComment(db.Model):
    """نموذج لتعليق على عنصر في معرض الأعمال"""
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio_item.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # مستخدم مسجل
    session_id = db.Column(db.Text, nullable=True)  # معرف الجلسة للمستخدم الغير مسجل
    author_name = db.Column(db.String(100), nullable=True)  # اسم المعلق (للزوار)
    author_email = db.Column(db.String(120), nullable=True)  # البريد الإلكتروني للمعلق (للزوار)
    content = db.Column(db.Text, nullable=False)
    approved = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='pending')  # حالة التعليق (pending, approved, rejected, spam)
    likes_count = db.Column(db.Integer, default=0)  # عدد الإعجابات
    ip_address = db.Column(db.String(45), nullable=True)  # عنوان IP للمعلق (يدعم IPv6)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # العلاقات
    parent_id = db.Column(db.Integer, db.ForeignKey('portfolio_comment.id'), nullable=True)  # للردود على التعليقات
    replies = db.relationship('PortfolioComment',
                             backref=db.backref('parent', remote_side=[id]),
                             lazy='dynamic')
    likes = db.relationship('CommentLike', backref='comment', lazy=True, cascade="all, delete-orphan")
    
    @property
    def replies_count(self):
        return self.replies.count()
    
    def to_dict(self):
        """تحويل التعليق إلى قاموس"""
        # الحصول على اسم ومعلومات المستخدم
        author = None
        avatar = None
        if self.user_id:
            user = User.query.get(self.user_id)
            if user:
                author = user.display_name or user.username
                avatar = user.avatar_url
        
        # إرجاع بيانات التعليق
        return {
            'id': self.id,
            'author_name': author or self.author_name or 'زائر',
            'avatar': avatar,
            'content': self.content,
            'likes_count': self.likes_count,
            'replies_count': self.replies_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'parent_id': self.parent_id
        }
        
    def __repr__(self):
        return f'<PortfolioComment {self.id}>'

class CommentLike(db.Model):
    """نموذج للإعجاب بالتعليقات"""
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('portfolio_comment.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # للمستخدم المسجل
    session_id = db.Column(db.Text, nullable=True)  # معرف الجلسة للمستخدم الغير مسجل
    ip_address = db.Column(db.String(45), nullable=True)  # عنوان IP للمستخدم
    fingerprint = db.Column(db.String(255), nullable=True)  # بصمة المتصفح
    user_ip = db.Column(db.String(50), nullable=True)  # عنوان IP للمستخدم (قديم)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<CommentLike {self.id}>'

class PortfolioLike(db.Model):
    """نموذج للإعجاب بعنصر في معرض الأعمال"""
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio_item.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # للمستخدم المسجل
    session_id = db.Column(db.Text, nullable=True)  # معرف الجلسة للمستخدم الغير مسجل
    ip_address = db.Column(db.String(45), nullable=True)  # عنوان IP للمستخدم
    fingerprint = db.Column(db.String(255), nullable=True)  # بصمة المتصفح
    user_ip = db.Column(db.String(50), nullable=True)  # عنوان IP للمستخدم (قديم)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<PortfolioLike {self.id}>'

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_type = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200), nullable=True)
    subtitle = db.Column(db.String(255), nullable=False)
    subtitle_en = db.Column(db.String(255), nullable=True)
    price = db.Column(db.String(100), nullable=False)
    price_en = db.Column(db.String(100), nullable=True)
    delivery_time = db.Column(db.String(100), nullable=False)
    delivery_time_en = db.Column(db.String(100), nullable=True)
    revisions = db.Column(db.String(100), nullable=False)
    revisions_en = db.Column(db.String(100), nullable=True)
    formats = db.Column(db.String(200), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    image_filename = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=False)
    description_en = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Store lists as JSON
    features = db.Column(db.Text, nullable=True)
    features_en = db.Column(db.Text, nullable=True)
    package_includes = db.Column(db.Text, nullable=True)
    package_includes_en = db.Column(db.Text, nullable=True)
    gallery = db.Column(db.Text, nullable=True)
    related_services = db.Column(db.Text, nullable=True)
    related_services_en = db.Column(db.Text, nullable=True)

    def get_features(self):
        if not self.features:
            return []

        try:
            return json.loads(self.features)
        except:
            return self.features.split('\n') if self.features else []

    def get_features_en(self):
        if not self.features_en:
            return []

        try:
            return json.loads(self.features_en)
        except:
            return self.features_en.split('\n') if self.features_en else []

    def get_package_includes(self):
        if not self.package_includes:
            return []

        try:
            return json.loads(self.package_includes)
        except:
            return self.package_includes.split('\n') if self.package_includes else []

    def get_package_includes_en(self):
        if not self.package_includes_en:
            return []

        try:
            return json.loads(self.package_includes_en)
        except:
            return self.package_includes_en.split('\n') if self.package_includes_en else []

    def get_gallery(self):
        if not self.gallery:
            return []

        try:
            return json.loads(self.gallery)
        except:
            return []

    def get_related_services(self):
        if not self.related_services:
            return []

        try:
            return json.loads(self.related_services)
        except:
            return []

    def get_related_services_en(self):
        if not self.related_services_en:
            return []

        try:
            return json.loads(self.related_services_en)
        except:
            return []

    def __repr__(self):
        return f'<Service {self.title}>'

class SocialMedia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(50), nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<SocialMedia {self.platform}>'


class Carousel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    title_en = db.Column(db.String(100), nullable=True)
    caption = db.Column(db.String(255), nullable=True)
    caption_en = db.Column(db.String(255), nullable=True)
    image_filename = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<Carousel {self.id}: {self.title or "Untitled"}>'


class ContactMessage(db.Model):
    """نموذج رسائل التواصل والاستفسارات"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    read = db.Column(db.Boolean, default=False)
    starred = db.Column(db.Boolean, default=False)
    replied = db.Column(db.Boolean, default=False)
    telegram_sent = db.Column(db.Boolean, default=False)
    email_sent = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Contact {self.id}: {self.name}>'


class ServiceRequest(db.Model):
    """نموذج طلبات الخدمة"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    service_type = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=False)
    budget = db.Column(db.String(50), nullable=True)
    timeline = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='new')  # new, in_progress, completed, cancelled
    telegram_sent = db.Column(db.Boolean, default=False)
    email_sent = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<Service Request {self.id}: {self.service_type}>'

class Visitor(db.Model):
    """نموذج لتتبع زوار الموقع وعناوين IP الخاصة بهم - محدث 2025-05-04 للتتبع الدقيق"""
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False, index=True)  # يدعم IPv6
    user_agent = db.Column(db.String(255), nullable=True)  # معلومات المتصفح
    # تم تعطيل عمود browser_fingerprint مؤقتًا لتجنب الأخطاء
    # browser_fingerprint = db.Column(db.String(64), nullable=True, index=True)  # بصمة المتصفح الفريدة للتتبع الدقيق
    referrer = db.Column(db.Text, nullable=True)  # الموقع المحيل منه
    country = db.Column(db.String(50), nullable=True)  # الدولة (يمكن استنتاجها من عنوان IP)
    city = db.Column(db.String(100), nullable=True)  # المدينة
    browser = db.Column(db.String(50), nullable=True)  # نوع المتصفح
    os = db.Column(db.String(50), nullable=True)  # نظام التشغيل
    device = db.Column(db.String(20), nullable=True)  # جهاز الزائر (desktop, mobile, tablet)
    first_visit = db.Column(db.DateTime, default=datetime.now)  # تاريخ أول زيارة
    last_visit = db.Column(db.DateTime, default=datetime.now)  # تاريخ آخر زيارة
    visit_count = db.Column(db.Integer, default=1)  # عدد مرات الزيارة
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # للربط بالمستخدم إذا كان مسجلاً
    session_id = db.Column(db.Text, nullable=True, index=True)  # معرف الجلسة للتتبع بين الزيارات
    is_bot = db.Column(db.Boolean, default=False)  # هل هو روبوت؟
    
    # العلاقات
    page_visits = db.relationship('PageVisit', backref='visitor', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Visitor {self.ip_address}>'
    
    def update_visit(self):
        """تحديث بيانات زيارة جديدة"""
        self.last_visit = datetime.now()
        self.visit_count += 1
        
    @classmethod
    def is_ip_anonymous(cls, ip):
        """التحقق مما إذا كان عنوان IP خاص أو محلي"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            return (ip_obj.is_private or 
                    ip_obj.is_loopback or 
                    ip_obj.is_link_local or 
                    ip_obj.is_multicast or 
                    ip == '0.0.0.0')
        except:
            return True  # إذا كان هناك خطأ، نعتبره خاصًا للأمان
            
class PageVisit(db.Model):
    """نموذج لتتبع زيارات الصفحات"""
    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.Integer, db.ForeignKey('visitor.id'), nullable=False)
    page_url = db.Column(db.String(255), nullable=False)  # مسار الصفحة المزارة
    page_title = db.Column(db.String(255), nullable=True)  # عنوان الصفحة
    visited_at = db.Column(db.DateTime, default=datetime.now)  # وقت الزيارة
    time_spent = db.Column(db.Integer, nullable=True)  # الوقت المستغرق بالثواني (اختياري)
    exit_page = db.Column(db.Boolean, default=False)  # هل هي صفحة الخروج من الموقع؟
    
    def __repr__(self):
        return f'<PageVisit {self.page_url} by visitor {self.visitor_id}>'