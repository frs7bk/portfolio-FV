"""
مسارات التعليقات والإعجابات لمعرض الأعمال
"""
import json
import logging
import os
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import desc

from database import db
from models import PortfolioItem, PortfolioComment, PortfolioLike, CommentLike, User, UserActivity
from telegram_service import send_telegram_message, format_comment_notification, format_like_notification
from email_service import send_comment_notification

comments = Blueprint('comments', __name__, url_prefix='/comments')

@comments.route('/api/portfolio/<int:portfolio_id>/comments')
@comments.route('/portfolio/comments/<int:portfolio_id>')
def get_portfolio_comments(portfolio_id):
    """الحصول على قائمة التعليقات لمشروع معين"""
    portfolio_item = PortfolioItem.query.get_or_404(portfolio_id)
    
    # فقط التعليقات المعتمدة تظهر للمستخدمين العاديين
    query = PortfolioComment.query.filter_by(portfolio_id=portfolio_id, parent_id=None)
    
    if not (current_user.is_authenticated and current_user.is_admin()):
        query = query.filter_by(approved=True)
    
    # أحدث التعليقات أولاً    
    comments = query.order_by(desc(PortfolioComment.created_at)).all()
    
    # تحويل التعليقات إلى JSON
    comment_list = []
    for comment in comments:
        comment_data = comment.to_dict()
        
        # إضافة الردود على هذا التعليق (إذا وجدت)
        replies_query = PortfolioComment.query.filter_by(parent_id=comment.id)
        if not (current_user.is_authenticated and current_user.is_admin()):
            replies_query = replies_query.filter_by(approved=True)
            
        replies = replies_query.order_by(PortfolioComment.created_at).all()
        comment_data['replies'] = [reply.to_dict() for reply in replies]
        
        comment_list.append(comment_data)
    
    # إضافة نشاط المشاهدة إذا كان المستخدم مسجلاً
    if current_user.is_authenticated:
        activity = UserActivity(
            user_id=current_user.id,
            ip_address=request.remote_addr,
            activity_type='view_comments',
            resource_type='portfolio_item',
            resource_id=portfolio_id
        )
        db.session.add(activity)
        db.session.commit()
    
    return jsonify({
        'comments': comment_list,
        'total_comments': len(comment_list)
    })

@comments.route('/portfolio/<int:portfolio_id>/comment', methods=['POST'])
@comments.route('/portfolio/comment/<int:portfolio_id>', methods=['POST'])
@comments.route('/api/portfolio/<int:portfolio_id>/comment', methods=['POST'])
@comments.route('/api/portfolio/<int:portfolio_id>/comments', methods=['POST'])
@comments.route('/api/portfolio/comment/add', methods=['POST'])
def add_comment(portfolio_id=None):
    """إضافة تعليق جديد على مشروع"""
    # تسجيل المعلومات للتشخيص
    print("طريقة الطلب:", request.method)
    print("عنوان URL:", request.path)
    print("البيانات المرسلة:", request.form.to_dict() if request.form else "لا توجد بيانات")
    
    # تحويل portfolio_id من المسار إلى رقم إذا كان موجوداً في المسار
    if portfolio_id:
        try:
            portfolio_id = int(portfolio_id)
            print("معرف المشروع من المسار:", portfolio_id)
        except (ValueError, TypeError):
            print("خطأ في تحويل معرف المشروع:", portfolio_id)
            portfolio_id = None
    
    # دعم JSON request body و Form data
    if request.is_json:
        data = request.get_json()
        if portfolio_id is None:
            portfolio_id = data.get('portfolio_id')
        name = data.get('name')
        email = data.get('email')
        content = data.get('content')
        parent_id = data.get('parent_id')
    else:
        name = request.form.get('name')
        email = request.form.get('email')
        content = request.form.get('content')
        parent_id = request.form.get('parent_id')
        
        # استخراج معرف المشروع من نموذج الطلب إذا لم يكن موجوداً في المسار
        if portfolio_id is None:
            try:
                portfolio_id = request.form.get('portfolio_id')
                if portfolio_id:
                    portfolio_id = int(portfolio_id)
            except (ValueError, TypeError):
                pass
    
    # تسجيل القيم المستخرجة للتشخيص
    print("القيم النهائية:")
    print("معرف المشروع:", portfolio_id)
    print("الاسم:", name)
    print("البريد الإلكتروني:", email)
    print("المحتوى:", content)
    
    # التحقق من وجود معرّف المشروع
    if not portfolio_id:
        return jsonify({
            'success': False,
            'message': 'يجب تحديد معرّف المشروع'
        })
    
    portfolio_item = PortfolioItem.query.get_or_404(portfolio_id)
    
    # التحقق من البيانات المدخلة
    if not content or len(content.strip()) < 3:
        return jsonify({
            'success': False,
            'message': 'يجب أن يحتوي التعليق على نص'
        })
    
    # إذا كان المستخدم مسجلاً، استخدم بياناته
    if current_user.is_authenticated:
        name = current_user.display_name or current_user.username
        email = current_user.email
        user_id = current_user.id
        
        # المسؤولون يمكنهم نشر تعليقات معتمدة مباشرة
        approved = current_user.is_admin()
    else:
        # استخدام الاسم الافتراضي إذا لم يوفر المستخدم اسماً
        if not name or name.strip() == '':
            name = 'زائر'
            
        # استخدام البريد الإلكتروني الافتراضي إذا لم يوفر المستخدم بريداً
        if not email or email.strip() == '':
            email = 'visitor@example.com'
            
        # طباعة البيانات للتأكد من استخدامها
        print("استخدام بيانات الزائر:", name, email)
        
        user_id = None
        approved = False
    
    # إنشاء التعليق الجديد
    comment = PortfolioComment(
        portfolio_id=portfolio_id,
        user_id=user_id,
        author_name=name,
        author_email=email,  # حفظ البريد الإلكتروني للتعليق
        content=content,
        approved=approved,
        ip_address=request.remote_addr,
        session_id=request.cookies.get('session', None)
    )
    
    # إذا كان رداً على تعليق آخر
    if parent_id:
        parent_comment = PortfolioComment.query.get(parent_id)
        if parent_comment and parent_comment.portfolio_id == portfolio_id:
            comment.parent_id = parent_id
    
    db.session.add(comment)
    
    # تسجيل نشاط إضافة تعليق
    if current_user.is_authenticated:
        activity = UserActivity(
            user_id=current_user.id,
            ip_address=request.remote_addr,
            activity_type='comment',
            resource_type='portfolio_item',
            resource_id=portfolio_id,
            details=json.dumps({'comment_id': comment.id})
        )
        db.session.add(activity)
    
    db.session.commit()
    
    # إرسال إشعار تليجرام للمسؤول بوجود تعليق جديد
    try:
        user_info = current_user.username if current_user.is_authenticated else name
        portfolio_title = portfolio_item.title
        
        # إذا كان رداً على تعليق آخر
        is_reply = False
        parent_comment_text = None
        if parent_id:
            parent = PortfolioComment.query.get(parent_id)
            if parent:
                is_reply = True
                parent_comment_text = parent.content
        
        # تنسيق الإشعار
        notification = format_comment_notification(
            user_info=user_info,
            portfolio_title=portfolio_title,
            comment_text=content,
            is_reply=is_reply,
            parent_comment=parent_comment_text
        )
        
        # إرسال الإشعار عبر تليجرام
        send_telegram_message(notification)
    except Exception as e:
        # تسجيل الخطأ ولكن السماح باستمرار العملية
        logging.error(f"Error sending Telegram notification for new comment: {str(e)}")
    
    # إرسال بريد إلكتروني للمسؤول بوجود تعليق جديد
    try:
        admin_email = current_app.config.get('ADMIN_EMAIL', 'info@firas-designs.com')
        
        # استخراج عنوان المشروع
        portfolio_title = portfolio_item.title
        
        # إرسال إشعار بالبريد الإلكتروني
        send_comment_notification(
            name=name,
            email=email,
            portfolio_title=portfolio_title,
            comment=content,
            admin_email=admin_email
        )
    except Exception as e:
        # تسجيل الخطأ ولكن السماح باستمرار العملية
        logging.error(f"Error sending email notification for new comment: {str(e)}")
    
    message = 'تم استلام تعليقك وسيتم مراجعته قبل النشر' if not approved else 'تم إضافة تعليقك بنجاح'
    
    # إرجاع استجابة JSON مع رسالة نجاح
    return jsonify({
        'success': True,
        'message': message,
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'approved': approved
        }
    })

@comments.route('/api/comments/<int:comment_id>/like', methods=['POST'])
@comments.route('/comments/like/<int:comment_id>', methods=['POST'])
def like_comment(comment_id):
    """إضافة أو إزالة إعجاب على تعليق"""
    comment = PortfolioComment.query.get_or_404(comment_id)
    
    # تجهيز معلومات المستخدم/الزائر بما في ذلك البصمة الرقمية
    user_id = None
    session_id = None
    fingerprint = None
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    
    # إنشاء بصمة فريدة للمتصفح لتحديد المستخدم
    if user_agent:
        import hashlib
        browser_fingerprint = f"{ip_address}|{user_agent[:100]}"
        fingerprint = hashlib.md5(browser_fingerprint.encode()).hexdigest()
    
    # إعداد الجلسة - الجلسات تدوم 30 يومًا للحفاظ على ثبات أفضل للإعجابات
    if 'user_session_id' not in session:
        import uuid
        session['user_session_id'] = str(uuid.uuid4())
        session.permanent = True  # تفعيل الجلسات طويلة الأمد
    
    # تحديد هوية المستخدم حسب حالة تسجيل الدخول
    if current_user.is_authenticated:
        # المستخدم مسجل الدخول - استخدم معرف المستخدم
        user_id = current_user.id
        session_id = None  # لا نحتاج لحفظ معرف الجلسة للمستخدم المسجل
    else:
        # المستخدم غير مسجل - استخدم معرف الجلسة
        session_id = session['user_session_id']
    
    # البحث عن إعجاب موجود باستخدام كل الوسائل المتاحة
    existing_like = None
    
    # قائمة من الفلاتر البديلة للبحث عن إعجاب سابق
    like_filters = []
    
    # إنشاء مجموعة من الفلاتر المختلفة للبحث بطرق متعددة
    if user_id:
        like_filters.append(db.and_(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == user_id
        ))
    
    if session_id:
        like_filters.append(db.and_(
            CommentLike.comment_id == comment_id,
            CommentLike.session_id == session_id
        ))
        
    if fingerprint:
        like_filters.append(db.and_(
            CommentLike.comment_id == comment_id,
            CommentLike.fingerprint == fingerprint
        ))
        
    if ip_address:
        like_filters.append(db.and_(
            CommentLike.comment_id == comment_id,
            CommentLike.ip_address == ip_address
        ))
    
    # البحث باستخدام أي من الفلاتر المعرّفة
    if like_filters:
        existing_like = CommentLike.query.filter(db.or_(*like_filters)).first()
    
    response = {'success': True}
    
    if existing_like:
        # إذا كان الإعجاب موجوداً بالفعل، قم بإزالته
        db.session.delete(existing_like)
        response['action'] = 'removed'
    else:
        # التأكد من أن عنوان IP غير فارغ
        if not ip_address:
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            if not ip_address:
                ip_address = "127.0.0.1"  # استخدام قيمة افتراضية إذا تعذر الحصول على عنوان IP
        
        # وإلا أضف إعجاب جديد
        new_like = CommentLike(
            comment_id=comment_id,
            user_id=user_id,
            ip_address=ip_address,
            session_id=session_id,
            fingerprint=fingerprint,
            user_ip=ip_address  # إضافة قيمة للحقل القديم للحفاظ على التوافق
        )
        db.session.add(new_like)
        response['action'] = 'added'
        
        # تسجيل نشاط الإعجاب
        if current_user.is_authenticated:
            activity = UserActivity(
                user_id=current_user.id,
                ip_address=request.remote_addr,
                activity_type='like_comment',
                resource_type='comment',
                resource_id=comment_id
            )
            db.session.add(activity)
    
    db.session.commit()
    
    # تحديث عدد الإعجابات في الرد
    response['likes_count'] = comment.likes_count
    
    return jsonify(response)

@comments.route('/api/portfolio/<int:portfolio_id>/like', methods=['POST'])
def like_portfolio_item(portfolio_id):
    """إضافة أو إزالة إعجاب على مشروع"""
    portfolio_item = PortfolioItem.query.get_or_404(portfolio_id)
    
    # تجهيز معلومات المستخدم/الزائر بما في ذلك البصمة الرقمية
    user_id = None
    session_id = None
    fingerprint = None
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    
    # إنشاء بصمة فريدة للمتصفح لتحديد المستخدم
    if user_agent:
        import hashlib
        browser_fingerprint = f"{ip_address}|{user_agent[:100]}"
        fingerprint = hashlib.md5(browser_fingerprint.encode()).hexdigest()
    
    # إعداد الجلسة - الجلسات تدوم 30 يومًا للحفاظ على ثبات أفضل للإعجابات
    if 'user_session_id' not in session:
        import uuid
        session['user_session_id'] = str(uuid.uuid4())
        session.permanent = True  # تفعيل الجلسات طويلة الأمد
    
    # تحديد هوية المستخدم حسب حالة تسجيل الدخول
    if current_user.is_authenticated:
        # المستخدم مسجل الدخول - استخدم معرف المستخدم
        user_id = current_user.id
        session_id = None  # لا نحتاج لحفظ معرف الجلسة للمستخدم المسجل
    else:
        # المستخدم غير مسجل - استخدم معرف الجلسة
        session_id = session['user_session_id']
    
    # البحث عن إعجاب موجود باستخدام كل الوسائل المتاحة
    existing_like = None
    
    # قائمة من الفلاتر البديلة للبحث عن إعجاب سابق
    like_filters = []
    
    # إنشاء مجموعة من الفلاتر المختلفة للبحث بطرق متعددة
    if user_id:
        like_filters.append(db.and_(
            PortfolioLike.portfolio_id == portfolio_id,
            PortfolioLike.user_id == user_id
        ))
    
    if session_id:
        like_filters.append(db.and_(
            PortfolioLike.portfolio_id == portfolio_id,
            PortfolioLike.session_id == session_id
        ))
        
    if fingerprint:
        like_filters.append(db.and_(
            PortfolioLike.portfolio_id == portfolio_id,
            PortfolioLike.fingerprint == fingerprint
        ))
        
    if ip_address:
        like_filters.append(db.and_(
            PortfolioLike.portfolio_id == portfolio_id,
            PortfolioLike.ip_address == ip_address
        ))
    
    # البحث باستخدام أي من الفلاتر المعرّفة
    if like_filters:
        existing_like = PortfolioLike.query.filter(db.or_(*like_filters)).first()
    
    response = {'success': True}
    
    if existing_like:
        # إذا كان الإعجاب موجوداً بالفعل، قم بإزالته
        db.session.delete(existing_like)
        response['action'] = 'removed'
    else:
        # التأكد من أن عنوان IP غير فارغ
        if not ip_address:
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            if not ip_address:
                ip_address = "127.0.0.1"  # استخدام قيمة افتراضية إذا تعذر الحصول على عنوان IP
        
        # وإلا أضف إعجاب جديد
        new_like = PortfolioLike(
            portfolio_id=portfolio_id,
            user_id=user_id,
            ip_address=ip_address,
            session_id=session_id,
            fingerprint=fingerprint,
            user_ip=ip_address  # إضافة قيمة للحقل القديم للحفاظ على التوافق
        )
        db.session.add(new_like)
        response['action'] = 'added'
        
        # تسجيل نشاط الإعجاب
        if current_user.is_authenticated:
            activity = UserActivity(
                user_id=current_user.id,
                ip_address=request.remote_addr,
                activity_type='like',
                resource_type='portfolio_item',
                resource_id=portfolio_id
            )
            db.session.add(activity)
    
    db.session.commit()
    
    # إرسال إشعار تليجرام عن الإعجاب الجديد
    if response['action'] == 'added':
        try:
            user_info = current_user.username if current_user.is_authenticated else "زائر"
            content_title = portfolio_item.title
            
            # تنسيق الإشعار
            notification = format_like_notification(
                user_info=user_info,
                content_type="مشروع",
                content_title=content_title
            )
            
            # إرسال الإشعار عبر تليجرام
            send_telegram_message(notification)
        except Exception as e:
            # تسجيل الخطأ ولكن السماح باستمرار العملية
            logging.error(f"Error sending Telegram notification for new like: {str(e)}")
    
    # تحديث عدد الإعجابات في الرد
    response['likes_count'] = portfolio_item.likes_count
    
    return jsonify(response)

@comments.route('/admin/comments')
@login_required
def admin_comments():
    """إدارة التعليقات (للمسؤول فقط)"""
    if not current_user.is_admin():
        flash('ليس لديك صلاحية الوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
    
    status = request.args.get('status', 'pending')
    
    if status == 'pending':
        comments = PortfolioComment.query.filter_by(approved=False, status='pending').order_by(desc(PortfolioComment.created_at)).all()
    elif status == 'approved':
        comments = PortfolioComment.query.filter_by(approved=True).order_by(desc(PortfolioComment.created_at)).all()
    elif status == 'rejected':
        comments = PortfolioComment.query.filter_by(status='rejected').order_by(desc(PortfolioComment.created_at)).all()
    else:
        comments = PortfolioComment.query.order_by(desc(PortfolioComment.created_at)).all()
    
    return render_template('admin/comments.html', comments=comments, status=status)

@comments.route('/admin/comments/<int:comment_id>/approve', methods=['POST'])
@login_required
def approve_comment(comment_id):
    """اعتماد تعليق (للمسؤول فقط)"""
    if not current_user.is_admin():
        return jsonify({'error': 'غير مصرح'}), 403
    
    comment = PortfolioComment.query.get_or_404(comment_id)
    comment.approved = True
    comment.status = 'approved'
    db.session.commit()
    
    return jsonify({'success': True})

@comments.route('/admin/comments/<int:comment_id>/reject', methods=['POST'])
@login_required
def reject_comment(comment_id):
    """رفض تعليق (للمسؤول فقط)"""
    if not current_user.is_admin():
        return jsonify({'error': 'غير مصرح'}), 403
    
    comment = PortfolioComment.query.get_or_404(comment_id)
    comment.approved = False
    comment.status = 'rejected'
    db.session.commit()
    
    return jsonify({'success': True})

@comments.route('/admin/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    """حذف تعليق (للمسؤول فقط)"""
    if not current_user.is_admin():
        return jsonify({'error': 'غير مصرح'}), 403
    
    comment = PortfolioComment.query.get_or_404(comment_id)
    
    # حذف الإعجابات المرتبطة بهذا التعليق
    CommentLike.query.filter_by(comment_id=comment_id).delete()
    
    # حذف الردود على هذا التعليق
    PortfolioComment.query.filter_by(parent_id=comment_id).delete()
    
    # حذف التعليق نفسه
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({'success': True})

@comments.route('/admin/comments/<int:comment_id>/reply', methods=['POST'])
@login_required
def admin_reply_to_comment(comment_id):
    """رد المسؤول على تعليق"""
    if not current_user.is_admin():
        return jsonify({'error': 'غير مصرح'}), 403
    
    parent_comment = PortfolioComment.query.get_or_404(comment_id)
    content = request.form.get('content')
    
    if not content or len(content.strip()) < 3:
        return jsonify({'error': 'يجب أن يحتوي الرد على نص'}), 400
    
    # إنشاء رد جديد (معتمد تلقائياً لأنه من المسؤول)
    reply = PortfolioComment(
        portfolio_id=parent_comment.portfolio_id,
        user_id=current_user.id,
        author_name=current_user.display_name or current_user.username,
        content=content,
        parent_id=comment_id,
        approved=True,
        ip_address=request.remote_addr,
        session_id=request.cookies.get('session', None)
    )
    
    db.session.add(reply)
    
    # تسجيل نشاط إضافة رد
    activity = UserActivity(
        user_id=current_user.id,
        ip_address=request.remote_addr,
        activity_type='reply',
        resource_type='comment',
        resource_id=comment_id,
        details=json.dumps({'reply_id': reply.id})
    )
    db.session.add(activity)
    
    db.session.commit()
    
    # إعداد بيانات الرد لإرجاعها
    reply_data = reply.to_dict()
    
    return jsonify({'success': True, 'reply': reply_data})

@comments.route('/api/check-spam', methods=['POST'])
@login_required
def check_spam():
    """فحص التعليق للكشف عن البريد المزعج (للمسؤول فقط)"""
    if not current_user.is_admin():
        return jsonify({'error': 'غير مصرح'}), 403
    
    comment_id = request.form.get('comment_id')
    comment = PortfolioComment.query.get_or_404(comment_id)
    
    # هنا يمكنك تنفيذ منطق فحص البريد المزعج
    # يمكنك استخدام خدمة خارجية أو قواعد بسيطة
    # هذا مثال بسيط يبحث عن كلمات معينة
    
    spam_words = ['viagra', 'casino', 'lottery', 'prize', 'win money', 'cialis', 'free iphone']
    is_spam = any(word in comment.content.lower() for word in spam_words)
    
    if is_spam:
        comment.status = 'spam'
        db.session.commit()
    
    return jsonify({'success': True, 'is_spam': is_spam})

@comments.route('/api/most-commented-items')
def most_commented_items():
    """الحصول على قائمة المشاريع الأكثر تعليقًا"""
    from sqlalchemy import func
    
    # الحصول على عدد التعليقات لكل مشروع
    query = db.session.query(
        PortfolioItem.id,
        PortfolioItem.title,
        PortfolioItem.image_url,
        func.count(PortfolioComment.id).label('comments_count')
    ).join(
        PortfolioComment, PortfolioItem.id == PortfolioComment.portfolio_id
    ).filter(
        PortfolioComment.approved == True
    ).group_by(
        PortfolioItem.id, PortfolioItem.title, PortfolioItem.image_url
    ).order_by(
        func.count(PortfolioComment.id).desc()
    ).limit(5)
    
    items = query.all()
    
    result = [{
        'id': item.id,
        'title': item.title,
        'image_url': item.image_url,
        'comments_count': item.comments_count
    } for item in items]
    
    return jsonify(result)