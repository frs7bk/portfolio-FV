"""
مسارات معرض الأعمال والتفاعلات
"""

from flask import Blueprint, jsonify, request, render_template, session, abort, current_app as app
from flask_login import current_user, login_required
from models import db, PortfolioItem, PortfolioComment, PortfolioLike, CommentLike, User, PortfolioView, Visitor
from datetime import datetime, timedelta
import json
import uuid
import hashlib
import logging

portfolio_bp = Blueprint('portfolio', __name__)

@portfolio_bp.route('/api/portfolio/categories')
def get_portfolio_categories():
    """واجهة برمجية للحصول على قائمة الفئات المتاحة في معرض الأعمال"""
    try:
        # استعلام للحصول على جميع الفئات الفريدة
        distinct_categories = db.session.query(PortfolioItem.category)\
            .filter(PortfolioItem.category.isnot(None))\
            .filter(PortfolioItem.category != '')\
            .distinct()\
            .all()
        
        # تحويل النتائج إلى قائمة
        categories = [cat[0] for cat in distinct_categories if cat[0]]
        
        # فرز الفئات أبجديًا
        categories.sort()
        
        # إضافة فئة "الكل" في البداية
        categories.insert(0, "الكل")
        
        return jsonify({
            'success': True,
            'categories': categories
        })
    except Exception as e:
        app.logger.error(f"خطأ في الحصول على فئات المعرض: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@portfolio_bp.route('/api/portfolio/filter/<category>')
def filter_portfolio_by_category(category):
    """واجهة برمجية للحصول على مشاريع معرض الأعمال مفلترة حسب الفئة"""
    try:
        # التحقق مما إذا كانت الفئة هي "الكل"
        if category == "الكل":
            # إرجاع جميع المشاريع بدون فلترة
            portfolio_items = PortfolioItem.query.order_by(PortfolioItem.created_at.desc()).all()
        else:
            # فلترة المشاريع حسب الفئة
            portfolio_items = PortfolioItem.query\
                .filter(PortfolioItem.category == category)\
                .order_by(PortfolioItem.created_at.desc())\
                .all()
        
        # تحويل المشاريع إلى قائمة قواميس
        items_data = []
        for item in portfolio_items:
            # حساب عدد التعليقات
            comments_count = PortfolioComment.query.filter_by(
                portfolio_id=item.id, 
                approved=True
            ).count()
            
            # إضافة بيانات المشروع
            items_data.append({
                'id': item.id,
                'title': item.title,
                'description': item.description,
                'image_url': item.image_url,
                'category': item.category,
                'link': item.link,
                'created_at': item.created_at.isoformat() if item.created_at else None,
                'likes_count': item.likes_count_value or 0,
                'views_count': item.views_count or 0,
                'comments_count': comments_count
            })
        
        return jsonify({
            'success': True,
            'items': items_data,
            'count': len(items_data),
            'category': category
        })
    except Exception as e:
        app.logger.error(f"خطأ في فلترة المشاريع حسب الفئة: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@portfolio_bp.route('/portfolio')
def portfolio():
    """عرض صفحة معرض الأعمال الافتراضية"""
    # الحصول على إجمالي عدد الإعجابات لجميع المشاريع
    total_likes = db.session.query(db.func.sum(PortfolioItem.likes_count_value)).scalar() or 0
    
    # الحصول على إجمالي عدد المشاهدات لجميع المشاريع
    total_views = db.session.query(db.func.sum(PortfolioItem.views_count)).scalar() or 0
    
    # الحصول على قائمة المشاريع مع إحصائياتها
    portfolio_items = PortfolioItem.query.order_by(PortfolioItem.created_at.desc()).all()
    
    # حساب عدد التعليقات لكل مشروع
    for item in portfolio_items:
        item.comments_count = PortfolioComment.query.filter_by(
            portfolio_id=item.id, 
            approved=True
        ).count()
    
    # التحقق مما إذا كان هناك المزيد من المشاريع للتحميل (للتمرير اللانهائي)
    has_more = len(portfolio_items) > 12
    
    return render_template(
        'portfolio.html',
        portfolio_items=portfolio_items[:12],  # إعرض فقط أول 12 مشروع في البداية
        total_likes=total_likes,
        total_views=total_views,
        has_more=has_more
    )

@portfolio_bp.route('/api/portfolio/page/<int:page>')
def get_portfolio_page(page):
    """واجهة برمجية للحصول على قائمة المشاريع بالصفحات للتحميل التدريجي"""
    try:
        # حجم الصفحة - عدد المشاريع في كل طلب
        page_size = 12
        
        # حساب الـ offset للصفحة
        offset = (page - 1) * page_size
        
        # الحصول على المشاريع للصفحة المطلوبة
        portfolio_items = PortfolioItem.query.order_by(PortfolioItem.created_at.desc()).offset(offset).limit(page_size).all()
        
        # تحويل إلى قائمة من القواميس
        items_data = []
        for item in portfolio_items:
            # حساب عدد التعليقات
            comments_count = PortfolioComment.query.filter_by(
                portfolio_id=item.id, 
                approved=True
            ).count()
            
            # إضافة بيانات المشروع
            items_data.append({
                'id': item.id,
                'title': item.title,
                'description': item.description,
                'image_url': item.image_url,
                'category': item.category,
                'link': item.link,
                'created_at': item.created_at.isoformat() if item.created_at else None,
                'likes_count': item.likes_count_value,
                'views_count': item.views_count,
                'comments_count': comments_count
            })
        
        # التحقق من وجود المزيد من المشاريع للتحميل
        total_count = PortfolioItem.query.count()
        has_more = total_count > (offset + page_size)
        
        return jsonify({
            'success': True,
            'items': items_data,
            'has_more': has_more,
            'total_count': total_count,
            'page': page,
            'page_size': page_size
        })
    except Exception as e:
        app.logger.error(f"خطأ في الحصول على المشاريع بالصفحات: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@portfolio_bp.route('/portfolio/<int:portfolio_id>/detail')
def get_portfolio_item_detail(portfolio_id):
    """الحصول على تفاصيل عنصر معرض الأعمال لعرضه في النافذة المنبثقة"""
    try:
        portfolio_item = PortfolioItem.query.get_or_404(portfolio_id)
        comments = PortfolioComment.query.filter_by(portfolio_id=portfolio_id, approved=True).order_by(PortfolioComment.created_at.desc()).all()
        
        # التحقق مما إذا كان المستخدم الحالي قد أعجب بالمشروع
        user_liked = False
        if current_user.is_authenticated:
            like = PortfolioLike.query.filter_by(portfolio_id=portfolio_id, user_id=current_user.id).first()
            user_liked = like is not None
        
        # تحويل التعليقات إلى تنسيق JSON
        comments_data = []
        for comment in comments:
            # التحقق مما إذا كان المستخدم الحالي قد أعجب بالتعليق
            comment_user_liked = False
            if current_user.is_authenticated:
                comment_like = CommentLike.query.filter_by(comment_id=comment.id, user_id=current_user.id).first()
                comment_user_liked = comment_like is not None
            
            # إضافة معلومات التعليق
            comment_data = {
                'id': comment.id,
                'content': comment.content,
                'created_at': comment.created_at.isoformat() if comment.created_at else None,
                'author_name': comment.author_name,
                'likes_count': comment.likes_count or 0,
                'user_liked': comment_user_liked
            }
            comments_data.append(comment_data)
        
        # إنشاء كائن البيانات للاستجابة
        data = {
            'id': portfolio_item.id,
            'title': portfolio_item.title,
            'title_en': portfolio_item.title_en,
            'description': portfolio_item.description,
            'description_en': portfolio_item.description_en,
            'image_url': portfolio_item.image_url,
            'category': portfolio_item.category,
            'link': portfolio_item.link,
            'views_count': portfolio_item.views_count or 0,
            'likes_count': portfolio_item.likes_count or 0,
            'comments_count': len(comments),
            'created_at': portfolio_item.created_at.isoformat() if portfolio_item.created_at else None,
            'comments': comments_data,
            'user_liked': user_liked
        }
        
        # إضافة معلومات الصور المتعددة إذا كانت موجودة
        if portfolio_item.carousel_images:
            try:
                carousel_images = json.loads(portfolio_item.carousel_images)
                data['carousel_images'] = carousel_images
            except:
                data['carousel_images'] = []
        else:
            data['carousel_images'] = []
        
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"Error fetching portfolio item details: {str(e)}")
        return jsonify({'error': True, 'message': str(e)}), 500

@portfolio_bp.route('/api/update-visitor', methods=['POST'])
def update_visitor():
    """تحديث بيانات الزائر في قاعدة البيانات باستخدام المعلومات المستلمة من جافاسكريبت"""
    if not request.is_json:
        return jsonify({'success': False, 'message': 'طلب غير صالح'}), 400
        
    data = request.json
    fingerprint = data.get('fingerprint')
    session_id = data.get('session_id')
    
    if not fingerprint or not session_id:
        return jsonify({'success': False, 'message': 'بيانات غير كافية'}), 400
        
    try:
        # الحصول على معلومات الزائر
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # البحث عن سجل زائر موجود مسبقًا
        visitor = None
        
        # البحث بناءً على معرف الجلسة أو عنوان IP
        if session_id:
            visitor = Visitor.query.filter(Visitor.session_id == session_id).first()
            
        if not visitor and ip_address:
            visitor = Visitor.query.filter(Visitor.ip_address == ip_address).first()
        
        if visitor:
            # تحديث السجل الموجود
            visitor.last_visit = datetime.now()
            visitor.visit_count += 1
            
            # تحديث معرف الجلسة إذا كان فارغًا
            if session_id and not visitor.session_id:
                visitor.session_id = session_id
                
        else:
            # إنشاء سجل جديد للزائر
            new_visitor = Visitor(
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                first_visit=datetime.now(),
                last_visit=datetime.now()
            )
            db.session.add(new_visitor)
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"خطأ في تحديث بيانات الزائر: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@portfolio_bp.route('/portfolio/<int:portfolio_id>/view', methods=['POST'])
def view_portfolio_item(portfolio_id):
    """زيادة عدد مشاهدات عنصر معرض الأعمال مع ضمان عدم تكرار المشاهدة لنفس المستخدم (آخر تحديث 2025-05-04)"""
    # استخدام البيانات المرسلة من JavaScript لتحسين دقة تتبع المشاهدات
    try:
        # استيراد دالة إشعارات تيليجرام والمكتبات المطلوبة
        from telegram_service import send_telegram_message, format_visit_notification
        from datetime import datetime, timedelta
        import logging
        
        app.logger.info(f"معالجة مشاهدة للعنصر {portfolio_id} في معرض الأعمال")
        portfolio_item = PortfolioItem.query.get_or_404(portfolio_id)
        
        # الحصول على معلومات المستخدم/الزائر
        user_id = None
        visitor_id = None
        session_id = None
        fingerprint = None
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # إنشاء بصمة فريدة للمتصفح باستخدام مزيج من IP والمتصفح
        if user_agent:
            browser_fingerprint = f"{ip_address}|{user_agent[:100]}"  # تقليل طول البصمة لتحسين الأداء
            fingerprint = hashlib.md5(browser_fingerprint.encode()).hexdigest()
        
        # إعداد الجلسة - الجلسات تدوم 30 يومًا للحفاظ على ثبات أفضل للمشاهدات والإعجابات
        if 'user_session_id' not in session:
            session['user_session_id'] = str(uuid.uuid4())
            session.permanent = True  # جلسات طويلة الأمد
        
        # تخصيص معرف المستخدم حسب حالة تسجيل الدخول
        if current_user.is_authenticated:
            user_id = current_user.id
            user_info = current_user.username
        else:
            # استخدام معرف الجلسة للمستخدمين غير المسجلين
            session_id = session['user_session_id']
            user_info = f"زائر من {ip_address}"
            
            # البحث عن سجل الزائر أو إنشاء سجل جديد
            visitor = Visitor.query.filter_by(ip_address=ip_address).first()
            if visitor:
                # تحديث معلومات الزائر الموجود
                visitor_id = visitor.id
                visitor.last_visit = datetime.now()
                visitor.visit_count += 1
                
                # تحديث معرف الجلسة إذا كان فارغًا
                if not visitor.session_id:
                    visitor.session_id = session_id
            else:
                # إنشاء سجل زائر جديد
                new_visitor = Visitor(
                    ip_address=ip_address,
                    user_agent=user_agent,
                    session_id=session_id,
                    first_visit=datetime.now(),
                    last_visit=datetime.now()
                )
                db.session.add(new_visitor)
                db.session.flush()  # لإنشاء معرف للزائر الجديد
                visitor_id = new_visitor.id
        
        # التحقق من وجود سجل مشاهدة سابق بأي طريقة من طرق التعرف
        existing_view = None
        
        # قائمة من الفلاتر البديلة للبحث عن مشاهدة سابقة
        all_filters = []
        
        # إنشاء مجموعة من الفلاتر المختلفة للبحث بطرق متعددة
        if user_id:
            all_filters.append(db.and_(
                PortfolioView.portfolio_id == portfolio_id,
                PortfolioView.user_id == user_id
            ))
        
        if session_id:
            all_filters.append(db.and_(
                PortfolioView.portfolio_id == portfolio_id,
                PortfolioView.session_id == session_id
            ))
            
        if fingerprint:
            all_filters.append(db.and_(
                PortfolioView.portfolio_id == portfolio_id,
                PortfolioView.fingerprint == fingerprint
            ))
            
        if visitor_id:
            all_filters.append(db.and_(
                PortfolioView.portfolio_id == portfolio_id,
                PortfolioView.visitor_id == visitor_id
            ))
            
        if ip_address:
            all_filters.append(db.and_(
                PortfolioView.portfolio_id == portfolio_id,
                PortfolioView.ip_address == ip_address
            ))
        
        # القفل الزمني: البحث عن مشاهدة في آخر 24 ساعة للحد من المشاهدات المتكررة
        time_lock = datetime.now() - timedelta(hours=24)
        time_filter = PortfolioView.created_at >= time_lock

        # البحث باستخدام أي من الفلاتر المعرّفة مع شرط الوقت
        if all_filters:
            existing_view = PortfolioView.query.filter(
                db.or_(*all_filters), 
                time_filter
            ).first()
        
        is_new_view = False
        
        # مشاهدة جديدة (لم يسبق للمستخدم مشاهدة هذا المشروع)
        if not existing_view:
            is_new_view = True
            app.logger.info(f"إنشاء مشاهدة جديدة للعنصر {portfolio_id}")
            
            # إنشاء سجل مشاهدة جديد
            new_view = PortfolioView(
                portfolio_id=portfolio_id,
                user_id=user_id,
                visitor_id=visitor_id,
                session_id=session_id,
                fingerprint=fingerprint,
                ip_address=ip_address,
                created_at=datetime.now()
            )
            db.session.add(new_view)
            db.session.flush()
            
            # تحديث عداد المشاهدات في جدول المشروع
            if portfolio_item.views_count is None:
                portfolio_item.views_count = 1
            else:
                portfolio_item.views_count += 1
            
            # إرسال إشعار تيليجرام عند مشاهدة مشروع جديد
            try:
                telegram_message = format_visit_notification(
                    user_info=user_info,
                    project_title=portfolio_item.title,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                send_telegram_message(telegram_message)
            except Exception as telegram_error:
                app.logger.error(f"خطأ في إرسال إشعار تيليجرام: {str(telegram_error)}")
        else:
            # مشاهدة متكررة - لا يتم احتسابها
            app.logger.info(f"مشاهدة متكررة للعنصر {portfolio_id} من نفس المستخدم - لم تحتسب")
        
        db.session.commit()
        
        # تحديث عدد المشاهدات الكلي من قاعدة البيانات
        try:
            portfolio_item.update_views_count()
            db.session.commit()
        except Exception as update_error:
            app.logger.error(f"خطأ في تحديث العدد الكلي للمشاهدات: {str(update_error)}")
        
        # سجل حالة المشاهدة
        if is_new_view:
            app.logger.info(f"مشاهدة فريدة جديدة للعنصر {portfolio_id}، الإجمالي: {portfolio_item.views_count}")
        else:
            app.logger.info(f"مشاهدة متكررة للعنصر {portfolio_id} من نفس المستخدم - لم تحتسب")
        
        return jsonify({
            'success': True,
            'views_count': portfolio_item.views_count,
            'is_new_view': is_new_view
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"خطأ في تحديث عدد المشاهدات: {str(e)}")
        return jsonify({'error': True, 'message': str(e)}), 500

@portfolio_bp.route('/portfolio/<int:portfolio_id>/like', methods=['POST'])
def like_portfolio_item(portfolio_id):
    """تبديل حالة الإعجاب لعنصر معرض الأعمال (إضافة أو إزالة) مع ضمان فاصل زمني أدنى"""
    try:
        from telegram_service import send_telegram_message, format_like_notification
        from datetime import datetime, timedelta
        
        app.logger.info(f"معالجة إعجاب للعنصر {portfolio_id} في معرض الأعمال")
        portfolio_item = PortfolioItem.query.get_or_404(portfolio_id)
        
        # الحصول على معلومات المستخدم/الزائر
        user_id = None
        user_info = "زائر"  # متغير لتخزين معلومات المستخدم لإشعار التلغرام
        fingerprint = None
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # إنشاء بصمة فريدة للمتصفح لتحديد المستخدم
        if user_agent:
            browser_fingerprint = f"{ip_address}|{user_agent[:100]}"
            fingerprint = hashlib.md5(browser_fingerprint.encode()).hexdigest()
        
        # إعداد الجلسة - الجلسات تدوم 30 يومًا للحفاظ على ثبات أفضل للإعجابات
        if 'user_session_id' not in session:
            session['user_session_id'] = str(uuid.uuid4())
            session.permanent = True  # تفعيل الجلسات طويلة الأمد
        
        # تحديد هوية المستخدم حسب حالة تسجيل الدخول
        if current_user.is_authenticated:
            # المستخدم مسجل الدخول - استخدم معرف المستخدم
            user_id = current_user.id
            user_info = current_user.name if hasattr(current_user, 'name') else current_user.username
            session_id = None  # لا نحتاج لحفظ معرف الجلسة للمستخدم المسجل
        else:
            # المستخدم غير مسجل - استخدم معرف الجلسة
            session_id = session['user_session_id']
            user_info = f"زائر من {ip_address}"
        
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
        
        # تحسين التحقق من الإعجابات بإضافة قيود زمنية للحماية من التبديل السريع
        # فترة 15 دقيقة لحماية الخادم من طلبات التبديل المتكررة
        time_lock = datetime.now() - timedelta(minutes=15)
        time_filter = PortfolioLike.created_at >= time_lock

        # البحث باستخدام أي من الفلاتر المعرّفة
        if like_filters:
            # أولاً، نبحث عن أي إعجاب بغض النظر عن الوقت
            existing_like = PortfolioLike.query.filter(db.or_(*like_filters)).first()
            
            # ثانياً، نبحث عن إعجاب حديث (خلال الـ 15 دقيقة الماضية) لمنع التبديل السريع
            recent_like = PortfolioLike.query.filter(
                db.or_(*like_filters),
                time_filter
            ).first()
            
            # إذا كان هناك إعجاب حديث، نتحقق إذا كان هذا محاولة لإزالة إعجاب تم مؤخراً
            if recent_like and existing_like:
                # هذا يعني أن المستخدم يحاول إزالة إعجاب وضعه خلال الـ 15 دقيقة الماضية
                # نقرر السماح بالإزالة إذا مر وقت معين (مثلاً 30 ثانية) وإلا نمنع الإزالة
                min_toggle_time = datetime.now() - timedelta(seconds=30)
                
                if recent_like.created_at < min_toggle_time:
                    # مر أكثر من 30 ثانية، نسمح بإزالة الإعجاب
                    pass
                else:
                    # أقل من 30 ثانية، إخبار المستخدم بالانتظار
                    return jsonify({
                        'success': False,
                        'liked': True,  # لم يتغير
                        'likes_count': portfolio_item.likes_count_value,
                        'message': 'يرجى الانتظار قبل تغيير الإعجاب مرة أخرى'
                    })
        
        # تبديل حالة الإعجاب (إضافة أو إزالة)
        if existing_like:
            # إزالة الإعجاب الموجود
            db.session.delete(existing_like)
            
            # تحديث عدد الإعجابات في جدول المشروع
            if portfolio_item.likes_count_value and portfolio_item.likes_count_value > 0:
                portfolio_item.likes_count_value -= 1
            
            liked = False
            app.logger.info(f"تمت إزالة الإعجاب للعنصر {portfolio_id}")
        else:
            # إضافة إعجاب جديد مع كل المعلومات المتاحة لتعزيز الثبات
            new_like = PortfolioLike(
                portfolio_id=portfolio_id,
                user_id=user_id if current_user.is_authenticated else None,
                session_id=session_id if not current_user.is_authenticated else None,
                fingerprint=fingerprint,
                ip_address=ip_address,
                user_ip=ip_address,  # إضافة user_ip لحل مشكلة NOT NULL constraint
                created_at=datetime.now()
            )
            
            db.session.add(new_like)
            
            # تحديث عدد الإعجابات في جدول المشروع
            if portfolio_item.likes_count_value is None:
                portfolio_item.likes_count_value = 1
            else:
                portfolio_item.likes_count_value += 1
            
            liked = True
            app.logger.info(f"تمت إضافة إعجاب جديد للعنصر {portfolio_id}")
            
            # إرسال إشعار تيليجرام للإعجاب الجديد
            try:
                telegram_message = format_like_notification(
                    user_info=user_info,
                    content_type="مشروع",
                    content_title=portfolio_item.title
                )
                send_telegram_message(telegram_message)
            except Exception as telegram_error:
                app.logger.error(f"خطأ في إرسال إشعار تيليجرام: {str(telegram_error)}")
        
        db.session.commit()
        
        # تخزين حالة الإعجاب في الجلسة للعرض والاستخدام المستقبلي
        liked_items_key = 'liked_portfolio_items'
        if liked_items_key not in session:
            session[liked_items_key] = []
            
        liked_items = session[liked_items_key]
        
        if liked:
            if portfolio_id not in liked_items:
                liked_items.append(portfolio_id)
        else:
            if portfolio_id in liked_items:
                liked_items.remove(portfolio_id)
                
        session[liked_items_key] = liked_items
        
        return jsonify({
            'success': True,
            'liked': liked,
            'likes_count': portfolio_item.likes_count_value
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"خطأ في تبديل حالة الإعجاب: {str(e)}")
        return jsonify({'error': True, 'message': str(e)}), 500

@portfolio_bp.route('/portfolio/<int:portfolio_id>/comment', methods=['POST'])
def add_portfolio_comment(portfolio_id):
    """إضافة تعليق جديد على عنصر معرض الأعمال"""
    try:
        from telegram_service import send_telegram_message, format_comment_notification
        
        portfolio_item = PortfolioItem.query.get_or_404(portfolio_id)
        content = request.form.get('content')
        author_name = request.form.get('author')  # الاسم من النموذج الجديد
        
        if not content or not content.strip():
            return jsonify({'error': True, 'message': 'التعليق لا يمكن أن يكون فارغًا'}), 400
            
        if not author_name or not author_name.strip():
            return jsonify({'error': True, 'message': 'يرجى إدخال اسمك'}), 400
        
        # إنشاء التعليق الجديد
        new_comment = PortfolioComment(
            portfolio_id=portfolio_id,
            content=content,
            created_at=datetime.now(),
            likes_count=0,
            approved=False  # جميع التعليقات تحتاج إلى موافقة
        )
        
        # متغير لتخزين معلومات المستخدم لإشعار التلغرام
        user_info = author_name
        
        # إضافة معلومات المستخدم إذا كان مسجل الدخول
        if current_user.is_authenticated:
            new_comment.user_id = current_user.id
            # إذا كان المستخدم مسجل الدخول، نستخدم اسمه من قاعدة البيانات مع السماح بتغييره
            new_comment.author_name = author_name if author_name else (current_user.name if hasattr(current_user, 'name') else current_user.username)
            user_info = new_comment.author_name
            # جعل تعليقات المسؤول معتمدة تلقائيًا
            if current_user.is_admin:
                new_comment.approved = True
        else:
            # إذا لم يكن مسجل الدخول، استخدم معرف الجلسة
            if 'user_session_id' not in session:
                import uuid
                session['user_session_id'] = str(uuid.uuid4())
            new_comment.session_id = session['user_session_id']
            new_comment.author_name = author_name
        
        db.session.add(new_comment)
        db.session.commit()
        
        # إرسال إشعار تلغرام بالتعليق الجديد
        telegram_message = format_comment_notification(
            user_info=user_info,
            portfolio_title=portfolio_item.title,
            comment_text=content
        )
        send_telegram_message(telegram_message)
        
        # الحصول على جميع التعليقات المعتمدة لهذا العنصر
        comments = PortfolioComment.query.filter_by(portfolio_id=portfolio_id, approved=True).order_by(PortfolioComment.created_at.desc()).all()
        
        # تحويل التعليقات إلى تنسيق JSON
        comments_data = []
        for comment in comments:
            # التحقق مما إذا كان المستخدم الحالي قد أعجب بالتعليق
            comment_user_liked = False
            if current_user.is_authenticated:
                comment_like = CommentLike.query.filter_by(comment_id=comment.id, user_id=current_user.id).first()
                comment_user_liked = comment_like is not None
            
            comment_data = {
                'id': comment.id,
                'content': comment.content,
                'created_at': comment.created_at.isoformat() if comment.created_at else None,
                'author_name': comment.author_name,
                'likes_count': comment.likes_count or 0,
                'user_liked': comment_user_liked
            }
            comments_data.append(comment_data)
        
        return jsonify({
            'success': True,
            'comments': comments_data,
            'comments_count': len(comments),
            'message': 'تم إضافة التعليق بنجاح' if new_comment.approved else 'تم إرسال التعليق وسيتم مراجعته قبل النشر'
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding portfolio comment: {str(e)}")
        return jsonify({'error': True, 'message': str(e)}), 500

@portfolio_bp.route('/comment/<int:comment_id>/like', methods=['POST'])
def like_comment(comment_id):
    """تبديل حالة الإعجاب للتعليق (إضافة أو إزالة) مع تحسين الثبات عبر الجلسات"""
    try:
        from telegram_service import send_telegram_message, format_like_notification
        import logging
        
        app.logger.info(f"Processing like for comment {comment_id}")
        comment = PortfolioComment.query.get_or_404(comment_id)
        
        # التحقق من المستخدم
        user_id = None
        user_info = "زائر"  # متغير لتخزين معلومات المستخدم لإشعار التلغرام
        fingerprint = None
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # إنشاء بصمة فريدة للمتصفح لحفظها مع الإعجاب
        if user_agent:
            browser_fingerprint = f"{ip_address}|{user_agent[:100]}"
            fingerprint = hashlib.md5(browser_fingerprint.encode()).hexdigest()
        
        if current_user.is_authenticated:
            # المستخدم مسجل الدخول - استخدم معرف المستخدم
            user_id = current_user.id
            user_info = current_user.name if hasattr(current_user, 'name') else current_user.username
        else:
            # المستخدم غير مسجل - استخدم معرف الجلسة
            if 'user_session_id' not in session:
                session['user_session_id'] = str(uuid.uuid4())
                # حفظ معرف الجلسة في كوكيز بمدة طويلة (30 يومًا) لثبات أكبر
                session.permanent = True
            user_id = session['user_session_id']
        
        # البحث عن إعجاب موجود بطرق متعددة
        existing_like = None
        
        # قائمة من الفلاتر البديلة للبحث عن إعجاب سابق
        comment_like_filters = []
        
        # إنشاء مجموعة من الفلاتر المختلفة للبحث بطرق متعددة
        if current_user.is_authenticated and user_id:
            comment_like_filters.append(db.and_(
                CommentLike.comment_id == comment_id,
                CommentLike.user_id == user_id
            ))
        
        if not current_user.is_authenticated and user_id:
            comment_like_filters.append(db.and_(
                CommentLike.comment_id == comment_id,
                CommentLike.session_id == user_id
            ))
            
        if fingerprint:
            comment_like_filters.append(db.and_(
                CommentLike.comment_id == comment_id,
                CommentLike.fingerprint == fingerprint
            ))
            
        if ip_address:
            comment_like_filters.append(db.and_(
                CommentLike.comment_id == comment_id,
                CommentLike.ip_address == ip_address
            ))
        
        # البحث باستخدام أي من الفلاتر المعرّفة
        if comment_like_filters:
            existing_like = CommentLike.query.filter(db.or_(*comment_like_filters)).first()
        
        # تبديل حالة الإعجاب
        if existing_like:
            # إزالة الإعجاب
            db.session.delete(existing_like)
            if comment.likes_count and comment.likes_count > 0:
                comment.likes_count -= 1
            liked = False
            app.logger.info(f"Removed like from comment {comment_id}")
        else:
            # إضافة إعجاب جديد
            new_like = CommentLike(
                comment_id=comment_id,
                created_at=datetime.now(),
                fingerprint=fingerprint,
                ip_address=ip_address
            )
            
            if current_user.is_authenticated:
                new_like.user_id = user_id
            else:
                new_like.session_id = user_id
            
            db.session.add(new_like)
            
            if comment.likes_count is None:
                comment.likes_count = 1
            else:
                comment.likes_count += 1
            
            liked = True
            app.logger.info(f"Added new like to comment {comment_id}")
            
            # إرسال إشعار تلغرام بالإعجاب الجديد
            try:
                # الحصول على معلومات المشروع من خلال التعليق للإشعار
                portfolio_item = PortfolioItem.query.get(comment.portfolio_id)
                if portfolio_item:
                    telegram_message = format_like_notification(
                        user_info=user_info,
                        content_type="تعليق على مشروع",
                        content_title=f"{portfolio_item.title} - {comment.content[:50]}..."
                    )
                    send_telegram_message(telegram_message)
            except Exception as telegram_error:
                app.logger.error(f"Telegram notification error: {str(telegram_error)}")
        
        db.session.commit()
        
        # تخزين حالة الإعجاب في الجلسة للعرض
        liked_comments_key = 'liked_comments'
        if liked_comments_key not in session:
            session[liked_comments_key] = []
            
        liked_comments = session[liked_comments_key]
        
        if liked:
            if comment_id not in liked_comments:
                liked_comments.append(comment_id)
        else:
            if comment_id in liked_comments:
                liked_comments.remove(comment_id)
                
        session[liked_comments_key] = liked_comments
        
        return jsonify({
            'success': True,
            'liked': liked,
            'likes_count': comment.likes_count
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error toggling comment like: {str(e)}")
        return jsonify({'error': True, 'message': str(e)}), 500