"""
نظام تسجيل الدخول والمستخدمين
يتضمن المصادقة الثنائية عبر تيليجرام للمدراء فقط
"""
import os
import json
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from database import db
from models import User, UserRole, UserActivity
from email_service import send_email

# إنشاء blueprint للتعامل مع مسارات المصادقة
auth = Blueprint('auth', __name__, url_prefix='/auth')

# نموذج لتسجيل الدخول
@auth.route('/login', methods=['GET', 'POST'])
def login():
    """واجهة تسجيل الدخول"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # TODO: إضافة خيار تسجيل الدخول عبر Google
    # تم تعطيل هذا مؤقتًا حتى يتم تنفيذ دعم Google OAuth
    google_login_url = "#"
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        # البحث عن المستخدم إما باسم المستخدم أو البريد الإلكتروني
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        # تحقق من وجود المستخدم وكلمة المرور
        if not user or not user.check_password(password):
            if user:
                user.increment_login_attempts()
                
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
            return render_template('auth/login.html', google_login_url=google_login_url)
            
        # تحقق من حالة الحساب
        if user.account_locked:
            flash('تم قفل الحساب بسبب محاولات دخول متكررة. يرجى التواصل مع الإدارة', 'danger')
            return render_template('auth/login.html', google_login_url=google_login_url)
        
        # التحقق من تفعيل البريد الإلكتروني
        if not user.email_verified and not user.from_google:
            flash('يرجى تفعيل بريدك الإلكتروني أولاً. تحقق من بريدك الوارد أو اطلب رمز تفعيل جديد', 'warning')
            return render_template('auth/login.html', google_login_url=google_login_url, user_email=user.email)
                  
        # التحقق مما إذا كان المستخدم مسؤول ويحتاج للمصادقة الثنائية
        if user.is_admin() and user.two_factor_enabled and user.telegram_verified:
            # إنشاء رمز المصادقة الثنائية وتخزينه مؤقتًا في الجلسة
            from telegram_service import generate_2fa_code
            two_factor_code = generate_2fa_code(user.id, user.email)
            
            # تخزين معلومات المستخدم والرمز في الجلسة
            session['two_factor_auth'] = {
                'user_id': user.id,
                'code': two_factor_code,
                'expiry': (datetime.now() + timedelta(minutes=10)).timestamp(),
                'remember': remember,
                'next': request.args.get('next')
            }
            
            # إعادة التوجيه إلى صفحة إدخال رمز المصادقة الثنائية
            return redirect(url_for('auth.two_factor_auth'))
            
        # إعادة تعيين محاولات تسجيل الدخول
        user.reset_login_attempts()
        
        # تسجيل الدخول
        login_user(user, remember=remember)
        
        # تسجيل نشاط تسجيل الدخول
        activity = UserActivity(
            user_id=user.id,
            ip_address=request.remote_addr,
            activity_type='login',
            details=json.dumps({
                'user_agent': request.user_agent.string,
                'method': 'password'
            })
        )
        db.session.add(activity)
        db.session.commit()
        
        # إرسال تنبيه أمني عن تسجيل الدخول إذا كان المستخدم مدير
        if user.is_admin():
            from telegram_service import format_security_alert
            format_security_alert(
                user.email,
                "تسجيل دخول جديد",
                request.remote_addr,
                request.user_agent.string
            )
        
        # إعادة توجيه المستخدم
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        
        # إذا كان المستخدم هو المدير، توجيهه للوحة التحكم
        if user.is_admin():
            return redirect(url_for('admin_dashboard'))
        
        # توجيه المستخدم العادي للصفحة الرئيسية
        flash(f'مرحبًا {user.display_name or user.username}! تم تسجيل دخولك بنجاح.', 'success')
        return redirect(url_for('index'))
        
    return render_template('auth/login.html', google_login_url=google_login_url)


@auth.route('/two-factor-auth', methods=['GET', 'POST'])
def two_factor_auth():
    """المصادقة الثنائية"""
    two_factor_data = session.get('two_factor_auth')
    
    # التحقق من وجود بيانات المصادقة الثنائية
    if not two_factor_data:
        flash('انتهت جلسة المصادقة الثنائية. يرجى تسجيل الدخول مرة أخرى', 'danger')
        return redirect(url_for('auth.login'))
    
    # التحقق من صلاحية الرمز
    expiry_time = datetime.fromtimestamp(two_factor_data['expiry'])
    if datetime.now() > expiry_time:
        # حذف بيانات المصادقة الثنائية إذا انتهت صلاحيتها
        session.pop('two_factor_auth', None)
        flash('انتهت صلاحية رمز المصادقة الثنائية. يرجى تسجيل الدخول مرة أخرى', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # التحقق من الرمز المدخل
        code = request.form.get('code')
        if not code or code != two_factor_data['code']:
            flash('الرمز غير صحيح. يرجى المحاولة مرة أخرى', 'danger')
            return render_template('auth/two_factor_auth.html')
        
        # البحث عن المستخدم
        user = User.query.get(two_factor_data['user_id'])
        if not user:
            session.pop('two_factor_auth', None)
            flash('حدث خطأ. يرجى تسجيل الدخول مرة أخرى', 'danger')
            return redirect(url_for('auth.login'))
        
        # إعادة تعيين محاولات تسجيل الدخول
        user.reset_login_attempts()
        
        # تسجيل الدخول
        login_user(user, remember=two_factor_data.get('remember', False))
        
        # تسجيل نشاط تسجيل الدخول
        activity = UserActivity(
            user_id=user.id,
            ip_address=request.remote_addr,
            activity_type='login',
            details=json.dumps({
                'user_agent': request.user_agent.string,
                'method': 'two_factor_auth'
            })
        )
        db.session.add(activity)
        db.session.commit()
        
        # حذف بيانات المصادقة الثنائية
        session.pop('two_factor_auth', None)
        
        # إعادة توجيه المستخدم
        next_page = two_factor_data.get('next')
        if next_page:
            return redirect(next_page)
        
        # إذا كان المستخدم هو المدير، توجيهه للوحة التحكم
        if user.is_admin():
            return redirect(url_for('admin_dashboard'))
        
        # توجيه المستخدم العادي للصفحة الرئيسية
        flash(f'مرحبًا {user.display_name or user.username}! تم تسجيل دخولك بنجاح.', 'success')
        return redirect(url_for('index'))
    
    return render_template('auth/two_factor_auth.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """واجهة إنشاء حساب جديد"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        display_name = request.form.get('display_name', username)
        
        # التحقق من البيانات
        if not username or not email or not password:
            flash('جميع الحقول مطلوبة', 'danger')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('كلمات المرور غير متطابقة', 'danger')
            return render_template('auth/register.html')
            
        # التحقق من تفرد اسم المستخدم والبريد الإلكتروني
        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم مستخدم بالفعل', 'danger')
            return render_template('auth/register.html')
            
        if User.query.filter_by(email=email).first():
            flash('البريد الإلكتروني مستخدم بالفعل', 'danger')
            return render_template('auth/register.html')
            
        # إنشاء مستخدم جديد
        new_user = User(
            username=username,
            email=email,
            display_name=display_name,
            role=UserRole.VISITOR.value  # مستخدم عادي بشكل افتراضي
        )
        new_user.set_password(password)
        
        # توليد رمز تحقق للبريد الإلكتروني
        verification_token = new_user.generate_verification_token()
        
        # حفظ المستخدم في قاعدة البيانات
        db.session.add(new_user)
        
        # تسجيل نشاط تسجيل حساب جديد
        activity = UserActivity(
            user_id=new_user.id,
            ip_address=request.remote_addr,
            activity_type='register',
            details=json.dumps({'user_agent': request.user_agent.string})
        )
        db.session.add(activity)
        db.session.commit()
        
        # إرسال بريد التحقق
        verify_url = url_for('auth.verify_email', token=verification_token, _external=True)
        send_verification_email(new_user.email, new_user.display_name, verify_url)
        
        flash('تم إنشاء الحساب بنجاح. يرجى التحقق من بريدك الإلكتروني لتفعيل الحساب', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth.route('/verify-email/<token>')
def verify_email(token):
    """تحقق من رمز تفعيل البريد الإلكتروني"""
    user = User.query.filter_by(verification_token=token).first()
    
    if not user:
        flash('رمز التحقق غير صالح', 'danger')
        return redirect(url_for('auth.login'))
        
    if user.verify_email(token):
        db.session.commit()
        flash('تم تفعيل الحساب بنجاح. يمكنك الآن تسجيل الدخول', 'success')
    else:
        flash('رمز التحقق منتهي الصلاحية. يرجى طلب رمز جديد', 'danger')
        
    return redirect(url_for('auth.login'))

@auth.route('/security-settings')
@login_required
def security_settings():
    """إعدادات الأمان والمصادقة الثنائية"""
    # تحقق من أن المستخدم مسجل دخول
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    # إنشاء نماذج تغيير كلمة المرور وتعطيل المصادقة الثنائية
    from flask_wtf import FlaskForm
    from wtforms import PasswordField, SubmitField
    from wtforms.validators import DataRequired, Length, EqualTo
    
    class PasswordForm(FlaskForm):
        current_password = PasswordField('كلمة المرور الحالية', validators=[DataRequired()])
        new_password = PasswordField('كلمة المرور الجديدة', validators=[DataRequired(), Length(min=6)])
        confirm_password = PasswordField('تأكيد كلمة المرور', validators=[DataRequired(), EqualTo('new_password', message='كلمات المرور غير متطابقة')])
        submit = SubmitField('تحديث كلمة المرور')
    
    class DisableTwoFactorForm(FlaskForm):
        submit = SubmitField('تعطيل المصادقة الثنائية')
    
    password_form = PasswordForm()
    disable_2fa_form = DisableTwoFactorForm()
    
    # الحصول على سجل تسجيل الدخول
    login_history = UserActivity.query.filter_by(
        user_id=current_user.id,
        activity_type='login'
    ).order_by(UserActivity.created_at.desc()).limit(5).all()
    
    return render_template('auth/security_settings.html',
                          password_form=password_form,
                          disable_2fa_form=disable_2fa_form,
                          login_history=login_history)

@auth.route('/update-password', methods=['POST'])
@login_required
def update_password():
    """تحديث كلمة المرور"""
    from flask_wtf import FlaskForm
    from wtforms import PasswordField, SubmitField
    from wtforms.validators import DataRequired, Length, EqualTo
    
    class PasswordForm(FlaskForm):
        current_password = PasswordField('كلمة المرور الحالية', validators=[DataRequired()])
        new_password = PasswordField('كلمة المرور الجديدة', validators=[DataRequired(), Length(min=6)])
        confirm_password = PasswordField('تأكيد كلمة المرور', validators=[DataRequired(), EqualTo('new_password', message='كلمات المرور غير متطابقة')])
        submit = SubmitField('تحديث كلمة المرور')
    
    form = PasswordForm()
    
    if form.validate_on_submit():
        # التحقق من كلمة المرور الحالية
        if not current_user.check_password(form.current_password.data):
            flash('كلمة المرور الحالية غير صحيحة', 'danger')
            return redirect(url_for('auth.security_settings'))
        
        # تحديث كلمة المرور
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        # تسجيل نشاط تغيير كلمة المرور
        activity = UserActivity(
            user_id=current_user.id,
            ip_address=request.remote_addr,
            activity_type='password_change',
            details=json.dumps({'user_agent': request.user_agent.string})
        )
        db.session.add(activity)
        db.session.commit()
        
        # إرسال تنبيه أمني عن تغيير كلمة المرور
        if current_user.is_admin():
            from telegram_service import format_security_alert
            format_security_alert(
                current_user.email,
                "تغيير كلمة المرور",
                request.remote_addr,
                request.user_agent.string
            )
        
        flash('تم تحديث كلمة المرور بنجاح', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('auth.security_settings'))

# تم تعريف هذه الوظائف مسبقًا (setup_two_factor و verify_telegram)

@auth.route('/disable-two-factor', methods=['POST'])
@login_required
def disable_two_factor():
    """تعطيل المصادقة الثنائية"""
    # تحقق من أن المستخدم مسجل دخول ومسؤول
    if not current_user.is_authenticated or not current_user.is_admin():
        flash('ميزة المصادقة الثنائية متاحة للمسؤولين فقط', 'warning')
        return redirect(url_for('auth.security_settings'))
    
    # تعطيل المصادقة الثنائية
    current_user.two_factor_enabled = False
    db.session.commit()
    
    # تسجيل نشاط تعطيل المصادقة الثنائية
    activity = UserActivity(
        user_id=current_user.id,
        ip_address=request.remote_addr,
        activity_type='disable_2fa',
        details=json.dumps({'user_agent': request.user_agent.string})
    )
    db.session.add(activity)
    db.session.commit()
    
    # إرسال تنبيه أمني عن تعطيل المصادقة الثنائية
    from telegram_service import format_security_alert
    format_security_alert(
        current_user.email,
        "تعطيل المصادقة الثنائية",
        request.remote_addr,
        request.user_agent.string
    )
    
    flash('تم تعطيل المصادقة الثنائية بنجاح', 'success')
    return redirect(url_for('auth.security_settings'))

@auth.route('/verify-two-factor', methods=['POST'])
def verify_two_factor():
    """التحقق من رمز المصادقة الثنائية"""
    code = request.form.get('code')
    two_factor_data = session.get('two_factor_auth')
    
    if not two_factor_data:
        flash('انتهت جلسة المصادقة الثنائية. يرجى تسجيل الدخول مرة أخرى', 'danger')
        return redirect(url_for('auth.login'))
    
    if not code or code != two_factor_data['code']:
        flash('الرمز غير صحيح. يرجى المحاولة مرة أخرى', 'danger')
        return redirect(url_for('auth.two_factor_auth'))
    
    user = User.query.get(two_factor_data['user_id'])
    if not user:
        session.pop('two_factor_auth', None)
        flash('حدث خطأ. يرجى تسجيل الدخول مرة أخرى', 'danger')
        return redirect(url_for('auth.login'))
    
    # إعادة تعيين محاولات تسجيل الدخول
    user.reset_login_attempts()
    
    # تسجيل الدخول
    login_user(user, remember=two_factor_data.get('remember', False))
    
    # تسجيل نشاط تسجيل الدخول
    activity = UserActivity(
        user_id=user.id,
        ip_address=request.remote_addr,
        activity_type='login',
        details=json.dumps({
            'user_agent': request.user_agent.string,
            'method': 'two_factor_auth'
        })
    )
    db.session.add(activity)
    db.session.commit()
    
    # حذف بيانات المصادقة الثنائية
    session.pop('two_factor_auth', None)
    
    # إرسال تنبيه أمني عن تسجيل الدخول
    from telegram_service import format_security_alert
    format_security_alert(
        user.email,
        "تسجيل دخول باستخدام المصادقة الثنائية",
        request.remote_addr,
        request.user_agent.string
    )
    
    # إعادة توجيه المستخدم
    next_page = two_factor_data.get('next')
    if next_page:
        return redirect(next_page)
    
    flash(f'مرحبًا {user.display_name or user.username}! تم تسجيل دخولك بنجاح.', 'success')
    return redirect(url_for('admin_dashboard'))

@auth.route('/resend-2fa-code')
def resend_two_factor_code():
    """إعادة إرسال رمز المصادقة الثنائية"""
    two_factor_data = session.get('two_factor_auth')
    
    if not two_factor_data:
        flash('انتهت جلسة المصادقة الثنائية. يرجى تسجيل الدخول مرة أخرى', 'danger')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(two_factor_data['user_id'])
    if not user:
        session.pop('two_factor_auth', None)
        flash('حدث خطأ. يرجى تسجيل الدخول مرة أخرى', 'danger')
        return redirect(url_for('auth.login'))
    
    # إنشاء رمز جديد
    from telegram_service import generate_2fa_code
    two_factor_code = generate_2fa_code(user.id, user.email)
    
    # تحديث بيانات الجلسة
    two_factor_data['code'] = two_factor_code
    two_factor_data['expiry'] = (datetime.now() + timedelta(minutes=10)).timestamp()
    session['two_factor_auth'] = two_factor_data
    
    flash('تم إرسال رمز جديد إلى حساب التيليجرام المرتبط بحسابك', 'success')
    return redirect(url_for('auth.two_factor_auth'))

@auth.route('/resend-verification')
@login_required
def resend_verification():
    """إعادة إرسال رمز التحقق"""
    if current_user.email_verified:
        flash('تم تفعيل البريد الإلكتروني بالفعل', 'info')
        return redirect(url_for('index'))
        
    verification_token = current_user.generate_verification_token()
    db.session.commit()
    
    verify_url = url_for('auth.verify_email', token=verification_token, _external=True)
    send_verification_email(current_user.email, current_user.display_name, verify_url)
    
    flash('تم إرسال رمز التحقق إلى بريدك الإلكتروني', 'success')
    return redirect(url_for('index'))

@auth.route('/logout')
@login_required
def logout():
    """تسجيل الخروج"""
    # تسجيل نشاط تسجيل الخروج
    activity = UserActivity(
        user_id=current_user.id,
        ip_address=request.remote_addr,
        activity_type='logout'
    )
    db.session.add(activity)
    db.session.commit()
    
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('index'))

@auth.route('/profile')
@login_required
def profile():
    """الملف الشخصي للمستخدم"""
    # استرجاع أنشطة المستخدم
    activities = UserActivity.query.filter_by(user_id=current_user.id).order_by(UserActivity.created_at.desc()).limit(10).all()
    
    return render_template('auth/profile.html', user=current_user, activities=activities)


# تم تعريف وظيفة security_settings مسبقاً


@auth.route('/setup-two-factor', methods=['GET', 'POST'])
@login_required
def setup_two_factor():
    """إعداد المصادقة الثنائية"""
    # التحقق من أن المستخدم مسؤول (مدير) - فقط المدراء يمكنهم إعداد المصادقة الثنائية
    if not current_user.is_admin():
        flash('غير مسموح بالوصول. ميزة المصادقة الثنائية متاحة فقط للمسؤولين', 'danger')
        return redirect(url_for('auth.profile'))
        
    if request.method == 'POST':
        # التحقق من كلمة المرور للتأكيد
        password = request.form.get('password')
        if not current_user.check_password(password):
            flash('كلمة المرور غير صحيحة', 'danger')
            return redirect(url_for('auth.security_settings'))
        
        action = request.form.get('action')
        
        if action == 'enable':
            # توليد رمز التحقق للتليجرام
            from telegram_service import setup_telegram_2fa
            verification_code = current_user.generate_telegram_verification_code()
            
            # حفظ الرمز في قاعدة البيانات
            db.session.commit()
            
            # إرسال الرمز عبر التليجرام
            setup_telegram_2fa(current_user.id, current_user.username, current_user.email)
            
            flash('تم إرسال رمز التحقق إلى بوت التيليجرام. يرجى إدخال الرمز لربط حسابك', 'success')
            return redirect(url_for('auth.verify_telegram'))
            
        elif action == 'disable':
            # تعطيل المصادقة الثنائية
            current_user.two_factor_enabled = False
            db.session.commit()
            
            # تسجيل نشاط تعطيل المصادقة الثنائية
            activity = UserActivity(
                user_id=current_user.id,
                ip_address=request.remote_addr,
                activity_type='disable_2fa'
            )
            db.session.add(activity)
            db.session.commit()
            
            flash('تم تعطيل المصادقة الثنائية بنجاح', 'success')
            return redirect(url_for('auth.security_settings'))
    
    return render_template('auth/setup_two_factor.html', user=current_user)


@auth.route('/verify-telegram', methods=['GET', 'POST'])
@login_required
def verify_telegram():
    """التحقق من رمز ربط التيليجرام"""
    # التحقق من أن المستخدم مسؤول (مدير) - فقط المدراء يمكنهم استخدام المصادقة الثنائية
    if not current_user.is_admin():
        flash('غير مسموح بالوصول. ميزة المصادقة الثنائية متاحة فقط للمسؤولين', 'danger')
        return redirect(url_for('auth.profile'))
    
    if request.method == 'POST':
        verification_code = request.form.get('code')
        
        if current_user.verify_telegram(verification_code):
            # تفعيل المصادقة الثنائية
            current_user.two_factor_enabled = True
            db.session.commit()
            
            # تسجيل نشاط تفعيل المصادقة الثنائية
            activity = UserActivity(
                user_id=current_user.id,
                ip_address=request.remote_addr,
                activity_type='enable_2fa',
                details=json.dumps({'method': 'telegram'})
            )
            db.session.add(activity)
            db.session.commit()
            
            flash('تم تفعيل المصادقة الثنائية بنجاح', 'success')
            return redirect(url_for('auth.security_settings'))
        else:
            flash('رمز التحقق غير صحيح أو منتهي الصلاحية', 'danger')
    
    return render_template('auth/verify_telegram.html', user=current_user)

@auth.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    """تحديث بيانات الملف الشخصي"""
    display_name = request.form.get('display_name')
    bio = request.form.get('bio')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # تحديث بيانات المستخدم
    current_user.display_name = display_name
    current_user.bio = bio
    
    # تحديث كلمة المرور إذا تم تقديمها
    if current_password and new_password:
        if not current_user.check_password(current_password):
            flash('كلمة المرور الحالية غير صحيحة', 'danger')
            return redirect(url_for('auth.profile'))
            
        if new_password != confirm_password:
            flash('كلمات المرور الجديدة غير متطابقة', 'danger')
            return redirect(url_for('auth.profile'))
            
        current_user.set_password(new_password)
        
    # حفظ التغييرات
    db.session.commit()
    
    # تسجيل نشاط تحديث الملف الشخصي
    activity = UserActivity(
        user_id=current_user.id,
        ip_address=request.remote_addr,
        activity_type='update_profile'
    )
    db.session.add(activity)
    db.session.commit()
    
    flash('تم تحديث الملف الشخصي بنجاح', 'success')
    return redirect(url_for('auth.profile'))

@auth.route('/upload-avatar', methods=['POST'])
@login_required
def upload_avatar():
    """رفع صورة شخصية جديدة"""
    if 'avatar' not in request.files:
        flash('لم يتم اختيار صورة', 'danger')
        return redirect(url_for('auth.profile'))
        
    avatar_file = request.files['avatar']
    
    if avatar_file.filename == '':
        flash('لم يتم اختيار صورة', 'danger')
        return redirect(url_for('auth.profile'))
        
    # التحقق من امتداد الملف وحجمه
    if not allowed_avatar_file(avatar_file.filename):
        flash('صيغة الملف غير مدعومة. يرجى استخدام JPG أو PNG أو GIF فقط', 'danger')
        return redirect(url_for('auth.profile'))
        
    # حفظ الصورة
    from app import secure_file_save
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(8)}_{avatar_file.filename}"
    
    try:
        avatar_path = secure_file_save(avatar_file, filename, 'avatars')
        current_user.avatar_url = avatar_path
        db.session.commit()
        
        # تسجيل نشاط تحديث الصورة الشخصية
        activity = UserActivity(
            user_id=current_user.id,
            ip_address=request.remote_addr,
            activity_type='update_avatar'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('تم تحديث الصورة الشخصية بنجاح', 'success')
    except Exception as e:
        flash(f'حدث خطأ أثناء رفع الصورة: {str(e)}', 'danger')
        
    return redirect(url_for('auth.profile'))

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """استعادة كلمة المرور"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('لا يوجد حساب مرتبط بهذا البريد الإلكتروني', 'danger')
            return render_template('auth/forgot_password.html')
            
        # توليد رمز إعادة تعيين كلمة المرور
        reset_token = user.generate_verification_token()
        db.session.commit()
        
        # إرسال بريد إعادة تعيين كلمة المرور
        reset_url = url_for('auth.reset_password', token=reset_token, _external=True)
        send_password_reset_email(user.email, user.display_name, reset_url)
        
        flash('تم إرسال تعليمات إعادة تعيين كلمة المرور إلى بريدك الإلكتروني', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/forgot_password.html')

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """إعادة تعيين كلمة المرور باستخدام الرمز"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    # البحث عن المستخدم بواسطة الرمز
    user = User.query.filter_by(verification_token=token).first()
    
    if not user or not user.token_expiry or user.token_expiry < datetime.now():
        flash('رمز إعادة تعيين كلمة المرور غير صالح أو منتهي الصلاحية', 'danger')
        return redirect(url_for('auth.forgot_password'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('كلمات المرور غير متطابقة', 'danger')
            return render_template('auth/reset_password.html', token=token)
            
        # تحديث كلمة المرور وإلغاء الرمز
        user.set_password(password)
        user.verification_token = None
        user.token_expiry = None
        
        # تسجيل نشاط إعادة تعيين كلمة المرور
        activity = UserActivity(
            user_id=user.id,
            ip_address=request.remote_addr,
            activity_type='password_reset'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('تم إعادة تعيين كلمة المرور بنجاح. يمكنك الآن تسجيل الدخول', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html', token=token)

# وظائف مساعدة
def allowed_avatar_file(filename):
    """التحقق من امتداد ملف الصورة الشخصية"""
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_verification_email(email, name, verify_url):
    """إرسال بريد التحقق"""
    subject = 'تفعيل حسابك'
    text_content = f'''
    مرحباً {name}،
    
    شكراً لتسجيلك في موقعنا!
    
    لتفعيل حسابك، يرجى النقر على الرابط التالي:
    {verify_url}
    
    إذا لم تقم بإنشاء هذا الحساب، يرجى تجاهل هذا البريد.
    
    مع تحيات،
    فريق الموقع
    '''
    
    html_content = f'''
    <div dir="rtl" style="font-family: 'Cairo', Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #f59e0b; text-align: center;">تفعيل حسابك</h2>
        <p>مرحباً {name}،</p>
        <p>شكراً لتسجيلك في موقعنا!</p>
        <p>لتفعيل حسابك، يرجى النقر على الزر أدناه:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{verify_url}" style="background-color: #f59e0b; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">تفعيل الحساب</a>
        </div>
        <p>أو يمكنك نسخ الرابط التالي ولصقه في متصفحك:</p>
        <p style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; word-break: break-all;">{verify_url}</p>
        <p>إذا لم تقم بإنشاء هذا الحساب، يرجى تجاهل هذا البريد.</p>
        <p>مع تحيات،<br>فريق الموقع</p>
    </div>
    '''
    
    return send_email(to_email=email, from_email=current_app.config.get('MAIL_DEFAULT_SENDER', 'info@firas-designs.com'), 
                     subject=subject, text_content=text_content, html_content=html_content)

def send_password_reset_email(email, name, reset_url):
    """إرسال بريد إعادة تعيين كلمة المرور"""
    subject = 'إعادة تعيين كلمة المرور'
    text_content = f'''
    مرحباً {name}،
    
    لقد تلقينا طلباً لإعادة تعيين كلمة المرور الخاصة بك.
    
    لإعادة تعيين كلمة المرور، يرجى النقر على الرابط التالي:
    {reset_url}
    
    إذا لم تطلب إعادة تعيين كلمة المرور، يرجى تجاهل هذا البريد وستبقى كلمة المرور دون تغيير.
    
    مع تحيات،
    فريق الموقع
    '''
    
    html_content = f'''
    <div dir="rtl" style="font-family: 'Cairo', Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #f59e0b; text-align: center;">إعادة تعيين كلمة المرور</h2>
        <p>مرحباً {name}،</p>
        <p>لقد تلقينا طلباً لإعادة تعيين كلمة المرور الخاصة بك.</p>
        <p>لإعادة تعيين كلمة المرور، يرجى النقر على الزر أدناه:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}" style="background-color: #f59e0b; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">إعادة تعيين كلمة المرور</a>
        </div>
        <p>أو يمكنك نسخ الرابط التالي ولصقه في متصفحك:</p>
        <p style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; word-break: break-all;">{reset_url}</p>
        <p>إذا لم تطلب إعادة تعيين كلمة المرور، يرجى تجاهل هذا البريد وستبقى كلمة المرور دون تغيير.</p>
        <p>مع تحيات،<br>فريق الموقع</p>
    </div>
    '''
    
    return send_email(to_email=email, from_email=current_app.config.get('MAIL_DEFAULT_SENDER', 'info@firas-designs.com'), 
                     subject=subject, text_content=text_content, html_content=html_content)