"""
نظام الإجراءات المقيدة
يتضمن مسارات ودوال للتعامل مع الإجراءات التي تتطلب تسجيل الدخول
ويحتوي على:
- مطالبة المستخدم بتسجيل الدخول قبل تنفيذ بعض الإجراءات
- تسجيل تفاعلات المستخدم مع محتويات الموقع
- صلاحيات مختلفة للمستخدمين العاديين والمديرين
"""
import json
from functools import wraps

from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify, current_app
from flask_login import login_required, current_user

from models import User, PortfolioItem, PortfolioLike, PortfolioComment, CommentLike, UserActivity
from database import db

# إنشاء blueprint للتعامل مع مسارات الإجراءات المقيدة
restricted = Blueprint('restricted', __name__, url_prefix='/restricted')

# الوظائف المساعدة

def admin_required(f):
    """وظيفة مساعدة للتحقق من أن المستخدم مدير"""
    import logging
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logging.debug(f"admin_required check for endpoint: {request.endpoint}")
        if not current_user.is_authenticated:
            logging.debug("User is not authenticated, redirecting to admin_login")
            flash('يجب تسجيل الدخول للوصول إلى هذه الصفحة', 'warning')
            return redirect(url_for('admin_login', next=request.url))
        
        logging.debug(f"User authenticated: {current_user.username}, role: {current_user.role}, is_admin: {current_user.is_admin()}")
        if not current_user.is_admin():
            logging.debug("User is not admin, redirecting to home page")
            flash('غير مسموح بالوصول. هذه الصفحة للمديرين فقط', 'danger')
            return redirect(url_for('index'))
        
        logging.debug("Admin check passed, proceeding to view")
        return f(*args, **kwargs)
    return decorated_function

def logged_in_or_session_id():
    """استرجاع معرف المستخدم المسجل أو معرف الجلسة"""
    if current_user.is_authenticated:
        return str(current_user.id), True
    
    # استخدام معرف الجلسة للزوار
    if 'session_id' not in session:
        import secrets
        session['session_id'] = f"session_{secrets.token_hex(16)}"
    
    return session['session_id'], False

def track_activity(activity_type, resource_type=None, resource_id=None, details=None):
    """تسجيل نشاط المستخدم"""
    if current_user.is_authenticated:
        activity = UserActivity(
            user_id=current_user.id,
            ip_address=request.remote_addr,
            activity_type=activity_type,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details or {})
        )
        db.session.add(activity)
        db.session.commit()

# المسارات

@restricted.route('/like-portfolio/<int:portfolio_id>', methods=['POST'])
def like_portfolio_item(portfolio_id):
    """إضافة/إزالة إعجاب على مشروع (متاح للزوار)"""
    portfolio_item = PortfolioItem.query.get_or_404(portfolio_id)
    user_id, is_user = logged_in_or_session_id()
    
    # البحث عن إعجاب سابق
    existing_like = None
    if is_user:
        existing_like = PortfolioLike.query.filter_by(
            portfolio_id=portfolio_id, 
            user_id=user_id
        ).first()
    else:
        existing_like = PortfolioLike.query.filter_by(
            portfolio_id=portfolio_id, 
            session_id=user_id
        ).first()
    
    result = {}
    
    # إذا كان هناك إعجاب سابق، قم بإزالته
    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
        
        # تحديث عدد الإعجابات
        portfolio_item.likes_count = PortfolioLike.query.filter_by(portfolio_id=portfolio_id).count()
        db.session.commit()
        
        result = {
            'status': 'removed',
            'likes_count': portfolio_item.likes_count
        }
        
        if is_user:
            track_activity('unlike', 'portfolio', portfolio_id)
    else:
        # إنشاء إعجاب جديد
        new_like = PortfolioLike(portfolio_id=portfolio_id)
        
        if is_user:
            new_like.user_id = user_id
        else:
            new_like.session_id = user_id
        
        db.session.add(new_like)
        db.session.commit()
        
        # تحديث عدد الإعجابات
        portfolio_item.likes_count = PortfolioLike.query.filter_by(portfolio_id=portfolio_id).count()
        db.session.commit()
        
        result = {
            'status': 'added',
            'likes_count': portfolio_item.likes_count
        }
        
        if is_user:
            track_activity('like', 'portfolio', portfolio_id)
    
    return jsonify(result)

@restricted.route('/like-comment/<int:comment_id>', methods=['POST'])
def like_comment(comment_id):
    """إضافة/إزالة إعجاب على تعليق (متاح للزوار)"""
    comment = PortfolioComment.query.get_or_404(comment_id)
    user_id, is_user = logged_in_or_session_id()
    
    # البحث عن إعجاب سابق
    existing_like = None
    if is_user:
        existing_like = CommentLike.query.filter_by(
            comment_id=comment_id, 
            user_id=user_id
        ).first()
    else:
        existing_like = CommentLike.query.filter_by(
            comment_id=comment_id, 
            session_id=user_id
        ).first()
    
    result = {}
    
    # إذا كان هناك إعجاب سابق، قم بإزالته
    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
        
        # تحديث عدد الإعجابات
        comment.likes_count = CommentLike.query.filter_by(comment_id=comment_id).count()
        db.session.commit()
        
        result = {
            'status': 'removed',
            'likes_count': comment.likes_count
        }
        
        if is_user:
            track_activity('unlike', 'comment', comment_id)
    else:
        # إنشاء إعجاب جديد
        new_like = CommentLike(comment_id=comment_id)
        
        if is_user:
            new_like.user_id = user_id
        else:
            new_like.session_id = user_id
        
        db.session.add(new_like)
        db.session.commit()
        
        # تحديث عدد الإعجابات
        comment.likes_count = CommentLike.query.filter_by(comment_id=comment_id).count()
        db.session.commit()
        
        result = {
            'status': 'added',
            'likes_count': comment.likes_count
        }
        
        if is_user:
            track_activity('like', 'comment', comment_id)
    
    return jsonify(result)

@restricted.route('/add-comment/<int:portfolio_id>', methods=['POST'])
def add_comment(portfolio_id):
    """إضافة تعليق على مشروع - يتم تحويل المستخدم لتسجيل الدخول أولاً"""
    # التحقق من تسجيل الدخول
    if not current_user.is_authenticated:
        flash('يجب تسجيل الدخول لإضافة تعليق', 'warning')
        # تخزين نص التعليق في الجلسة للعودة إليه بعد تسجيل الدخول
        session['pending_comment'] = {
            'portfolio_id': portfolio_id,
            'content': request.form.get('content', '')
        }
        return redirect(url_for('auth.login', next=request.referrer or url_for('portfolio')))
    
    content = request.form.get('content', '').strip()
    if not content:
        flash('يجب إدخال محتوى للتعليق', 'danger')
        return redirect(request.referrer or url_for('portfolio'))
    
    # إضافة التعليق
    new_comment = PortfolioComment(
        portfolio_id=portfolio_id,
        user_id=current_user.id,
        content=content,
        approved=current_user.is_admin()  # الموافقة التلقائية على تعليقات المدير
    )
    db.session.add(new_comment)
    db.session.commit()
    
    # تسجيل النشاط
    track_activity('comment', 'portfolio', portfolio_id, {'content': content})
    
    if new_comment.approved:
        flash('تمت إضافة التعليق بنجاح', 'success')
    else:
        flash('تم إرسال التعليق وسيظهر بعد الموافقة عليه', 'info')
    
    return redirect(request.referrer or url_for('portfolio'))

@restricted.route('/submit-contact-form', methods=['POST'])
def submit_contact_form():
    """إرسال نموذج الاتصال - يمكن للزوار الإرسال ولكن يتم تسجيل المعلومات"""
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    subject = request.form.get('subject', '').strip()
    message = request.form.get('message', '').strip()
    
    # التحقق من صحة البيانات
    if not all([name, email, message]):
        flash('جميع الحقول المطلوبة يجب ملؤها', 'danger')
        return redirect(request.referrer or url_for('index'))
    
    # إنشاء رسالة جديدة
    from models import ContactMessage
    new_message = ContactMessage(
        name=name,
        email=email,
        subject=subject,
        message=message
    )
    
    # ربط الرسالة بالمستخدم إذا كان مسجلاً
    if current_user.is_authenticated:
        new_message.user_id = current_user.id
        track_activity('contact_form', 'message', None, {'subject': subject})
    
    db.session.add(new_message)
    db.session.commit()
    
    # إرسال بريد إلكتروني للإدارة
    try:
        from email_service import send_contact_form_notification
        admin_email = current_app.config.get('ADMIN_EMAIL', 'admin@example.com')
        send_contact_form_notification(name, email, subject, message, admin_email)
    except Exception as e:
        current_app.logger.error(f"Error sending contact form notification: {str(e)}")
    
    flash('تم إرسال رسالتك بنجاح وسنتواصل معك قريباً', 'success')
    return redirect(request.referrer or url_for('index'))

@restricted.route('/view-portfolio/<int:portfolio_id>')
def view_portfolio_item(portfolio_id):
    """تسجيل مشاهدة لمشروع (متاح للزوار)"""
    portfolio_item = PortfolioItem.query.get_or_404(portfolio_id)
    user_id, is_user = logged_in_or_session_id()
    
    # زيادة عدد المشاهدات
    portfolio_item.views_count += 1
    db.session.commit()
    
    if is_user:
        track_activity('view_portfolio', 'portfolio', portfolio_id)
    
    return jsonify({'status': 'success', 'views_count': portfolio_item.views_count})

@restricted.route('/request-service/<service_type>', methods=['POST'])
def request_service(service_type):
    """طلب خدمة - يجب تسجيل الدخول أولاً"""
    # التحقق من تسجيل الدخول
    if not current_user.is_authenticated:
        flash('يجب تسجيل الدخول لطلب الخدمة', 'warning')
        # تخزين بيانات الطلب في الجلسة للعودة إليها بعد تسجيل الدخول
        session['pending_service_request'] = {
            'service_type': service_type,
            'details': request.form.get('details', ''),
            'contact_method': request.form.get('contact_method', ''),
            'budget': request.form.get('budget', '')
        }
        return redirect(url_for('auth.login', next=request.referrer or url_for('index')))
    
    details = request.form.get('details', '').strip()
    contact_method = request.form.get('contact_method', '').strip()
    budget = request.form.get('budget', '').strip()
    
    if not details:
        flash('يجب إدخال تفاصيل الطلب', 'danger')
        return redirect(request.referrer or url_for(f'service_detail', service_type=service_type))
    
    # إنشاء طلب خدمة جديد
    from models import ServiceRequest
    new_request = ServiceRequest(
        user_id=current_user.id,
        service_type=service_type,
        details=details,
        contact_method=contact_method,
        budget=budget,
        status='pending'
    )
    db.session.add(new_request)
    db.session.commit()
    
    # تسجيل النشاط
    track_activity('service_request', 'service', service_type, {'details': details})
    
    # إرسال إشعار للإدارة عبر تيليجرام
    try:
        from telegram_service import send_service_request_notification
        send_service_request_notification(
            current_user.username,
            current_user.email,
            service_type,
            details,
            contact_method,
            budget
        )
    except Exception as e:
        current_app.logger.error(f"Error sending service request notification: {str(e)}")
    
    flash('تم إرسال طلب الخدمة بنجاح وسنتواصل معك قريباً', 'success')
    return redirect(url_for('service_detail', service_type=service_type))

@restricted.route('/check-pending')
def check_pending_actions():
    """التحقق من وجود إجراءات معلقة بعد تسجيل الدخول"""
    result = {'has_pending': False}
    
    if 'pending_comment' in session:
        result['has_pending'] = True
        result['type'] = 'comment'
        result['data'] = session.pop('pending_comment')
    
    elif 'pending_service_request' in session:
        result['has_pending'] = True
        result['type'] = 'service_request'
        result['data'] = session.pop('pending_service_request')
    
    return jsonify(result)

@restricted.route('/process-pending', methods=['POST'])
@login_required
def process_pending_action():
    """معالجة الإجراءات المعلقة بعد تسجيل الدخول"""
    action_type = request.form.get('type')
    
    if action_type == 'comment':
        portfolio_id = request.form.get('portfolio_id')
        content = request.form.get('content')
        
        if portfolio_id and content:
            # إضافة التعليق
            new_comment = PortfolioComment(
                portfolio_id=int(portfolio_id),
                user_id=current_user.id,
                content=content,
                approved=current_user.is_admin()
            )
            db.session.add(new_comment)
            db.session.commit()
            
            # تسجيل النشاط
            track_activity('comment', 'portfolio', portfolio_id, {'content': content})
            
            if new_comment.approved:
                flash('تمت إضافة التعليق بنجاح', 'success')
            else:
                flash('تم إرسال التعليق وسيظهر بعد الموافقة عليه', 'info')
    
    elif action_type == 'service_request':
        service_type = request.form.get('service_type')
        details = request.form.get('details')
        contact_method = request.form.get('contact_method')
        budget = request.form.get('budget')
        
        if service_type and details:
            # إنشاء طلب خدمة جديد
            from models import ServiceRequest
            new_request = ServiceRequest(
                user_id=current_user.id,
                service_type=service_type,
                details=details,
                contact_method=contact_method,
                budget=budget,
                status='pending'
            )
            db.session.add(new_request)
            db.session.commit()
            
            # تسجيل النشاط
            track_activity('service_request', 'service', service_type, {'details': details})
            
            # إرسال إشعار للإدارة عبر تيليجرام
            try:
                from telegram_service import send_service_request_notification
                send_service_request_notification(
                    current_user.username,
                    current_user.email,
                    service_type,
                    details,
                    contact_method,
                    budget
                )
            except Exception as e:
                current_app.logger.error(f"Error sending service request notification: {str(e)}")
            
            flash('تم إرسال طلب الخدمة بنجاح وسنتواصل معك قريباً', 'success')
    
    return redirect(request.referrer or url_for('index'))