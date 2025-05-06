"""
نظام الإحصائيات وتتبع النشاطات
نظام كامل لعرض إحصائيات الموقع في لوحة تحكم المسؤول، بما في ذلك:
- عدد الزيارات اليومية/الأسبوعية/الشهرية
- عدد الإعجابات المسجلة
- عدد المشاهدات لكل مشروع/منتج
- عدد المستخدمين الجدد (يوميًا، شهريًا)
- رسوم بيانية باستخدام مكتبات Chart.js
- دعم لتصفية البيانات حسب الفترة الزمنية ونوع التفاعل
- تتبع زوار الموقع وعناوين IP الخاصة بهم
- معلومات جغرافية وتقنية عن زوار الموقع
- سجل كامل لزيارات الصفحات
"""
import json
import logging
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, current_app, session
from flask_login import login_required, current_user

from sqlalchemy import func, and_, or_
from sqlalchemy.sql import text

from models import User, PortfolioItem, PortfolioComment, UserActivity, PortfolioLike, CommentLike, Visitor, PageVisit
from database import db
from restricted_actions import admin_required
import user_agents  # لتحليل معلومات المتصفح
from telegram_service import send_telegram_message, format_visit_notification

# إنشاء blueprint للتعامل مع مسارات الإحصائيات
analytics = Blueprint('analytics', __name__)

@analytics.route('/dashboard')
@admin_required
def dashboard():
    """لوحة تحكم الإحصائيات - للمدير فقط"""
    import logging
    logging.debug("Entered analytics.dashboard function")
    logging.info(f"User {current_user.username} (id: {current_user.id}) accessing analytics dashboard")
    # الحصول على الإحصائيات الإجمالية
    try:
        likes_count = PortfolioLike.query.count()
    except:
        likes_count = 0
        
    try:
        comment_likes = CommentLike.query.count()
    except:
        comment_likes = 0
        
    try:
        comments_count = PortfolioComment.query.count()
    except:
        comments_count = 0
    
    total_stats = {
        'views': get_total_views(),
        'likes': likes_count + comment_likes,
        'comments': comments_count,
        'users': User.query.count()
    }
    
    # الحصول على أكثر المشاريع مشاهدة
    top_projects = PortfolioItem.query.order_by(
        PortfolioItem.views_count.desc()
    ).limit(10).all()
    
    # الحصول على آخر النشاطات
    latest_activities = UserActivity.query.order_by(
        UserActivity.created_at.desc()
    ).limit(10).all()
    
    # توليد بيانات الرسوم البيانية
    chart_data = generate_chart_data(days=30)
    
    # إضافة تاريخ ووقت التحديث
    date_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    return render_template(
        'admin/analytics/dashboard.html',
        total_stats=total_stats,
        top_projects=top_projects,
        latest_activities=latest_activities,
        chart_data=chart_data,
        date_time=date_time
    )

@analytics.route('/portfolio')
@admin_required
def portfolio_stats_api():
    """واجهة برمجية لإحصائيات المشاريع - للمدير فقط"""
    days = request.args.get('days', type=int)
    stats = get_portfolio_stats(days)
    return jsonify(stats)

@analytics.route('/activity')
@admin_required
def activity_stats_api():
    """واجهة برمجية لإحصائيات النشاطات - للمدير فقط"""
    days = request.args.get('days', type=int)
    stats = get_activity_stats(days)
    return jsonify(stats)

@analytics.route('/users')
@admin_required
def user_stats_api():
    """واجهة برمجية لإحصائيات المستخدمين - للمدير فقط"""
    days = request.args.get('days', type=int)
    stats = get_user_stats(days)
    return jsonify(stats)

@analytics.route('/data')
@admin_required
def chart_data_api():
    """واجهة برمجية لبيانات الرسوم البيانية - للمدير فقط"""
    days = request.args.get('days', type=int, default=30)
    chart_data = generate_chart_data(days)
    
    # إحصائيات إجمالية
    total_stats = {
        'views': get_total_views(days),
        'likes': get_total_likes(days),
        'comments': get_total_comments(days),
        'users': get_total_users(days)
    }
    
    # أكثر المشاريع مشاهدة
    top_projects_query = PortfolioItem.query
    
    if days:
        date_filter = datetime.now() - timedelta(days=days)
        # نحتاج إلى تحسين هذا الاستعلام ليعكس المشاهدات والإعجابات في الفترة المحددة
        # هذا يتطلب تعديلًا في هيكل قاعدة البيانات ليتضمن تواريخ للعدادات
        top_projects_query = top_projects_query.filter(
            PortfolioItem.created_at >= date_filter
        )
    
    top_projects = top_projects_query.order_by(
        PortfolioItem.views_count.desc()
    ).limit(10).all()
    
    # تحويل النتائج إلى JSON
    top_projects_json = []
    for item in top_projects:
        top_projects_json.append({
            'id': item.id,
            'title': item.title,
            'views_count': item.views_count,
            'likes_count': item.likes_count,
            'comments_count': PortfolioComment.query.filter_by(portfolio_id=item.id).count()
        })
    
    return jsonify({
        'chart_data': chart_data,
        'total_stats': total_stats,
        'top_projects': top_projects_json
    })

@analytics.route('/activity-list')
@admin_required
def activity_list():
    """قائمة جميع النشاطات - للمدير فقط"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # الحصول على جميع النشاطات مع التصفح
    activities = UserActivity.query.order_by(
        UserActivity.created_at.desc()
    ).paginate(page=page, per_page=per_page)
    
    # إضافة تاريخ ووقت التحديث
    date_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    return render_template(
        'admin/analytics/activity_list.html',
        activities=activities,
        date_time=date_time
    )

@analytics.route('/user/<int:user_id>')
@admin_required
def user_activity(user_id):
    """عرض نشاطات مستخدم محدد - للمدير فقط"""
    user = User.query.get_or_404(user_id)
    
    # الحصول على نشاطات المستخدم
    activities = UserActivity.query.filter_by(
        user_id=user_id
    ).order_by(UserActivity.created_at.desc()).all()
    
    # إضافة تاريخ ووقت التحديث
    date_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    return render_template(
        'admin/analytics/user_activity.html',
        user=user,
        activities=activities,
        date_time=date_time
    )
    
@analytics.route('/visitors')
@admin_required
def visitors_dashboard():
    """لوحة تحكم إحصائيات الزوار - للمدير فقط"""
    days = request.args.get('days', 30, type=int)
    
    # الحصول على إحصائيات الزوار
    stats = get_visitor_stats(days)
    
    # الحصول على قائمة الزوار الأخيرة
    latest_visitors = Visitor.query.order_by(
        Visitor.last_visit.desc()
    ).limit(20).all()
    
    # إضافة تاريخ ووقت التحديث
    date_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    return render_template(
        'admin/analytics/visitors.html',
        stats=stats,
        latest_visitors=latest_visitors,
        date_time=date_time,
        days=days
    )
    
@analytics.route('/visitors/data')
@admin_required
def visitors_data_api():
    """واجهة برمجية لبيانات الزوار - للمدير فقط"""
    days = request.args.get('days', 30, type=int)
    stats = get_visitor_stats(days)
    return jsonify(stats)
    
@analytics.route('/visitors/<int:visitor_id>')
@admin_required
def visitor_detail(visitor_id):
    """تفاصيل زائر محدد - للمدير فقط"""
    visitor = Visitor.query.get_or_404(visitor_id)
    
    # الحصول على سجل زيارات الصفحات
    page_visits = PageVisit.query.filter_by(
        visitor_id=visitor_id
    ).order_by(PageVisit.visited_at.desc()).all()
    
    # معلومات المستخدم المرتبط (إن وجد)
    user = None
    if visitor.user_id:
        user = User.query.get(visitor.user_id)
    
    # إضافة تاريخ ووقت التحديث
    date_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    return render_template(
        'admin/analytics/visitor_detail.html',
        visitor=visitor,
        page_visits=page_visits,
        user=user,
        date_time=date_time
    )
    
@analytics.route('/ip-lookup')
@admin_required
def ip_lookup():
    """البحث عن معلومات عنوان IP - للمدير فقط"""
    ip = request.args.get('ip', '')
    result = {}
    
    if ip:
        # هنا يمكن إضافة كود للبحث عن معلومات IP باستخدام API خارجي
        # مثل ipinfo.io أو ip-api.com
        # لكن حاليًا سنعرض المعلومات المخزنة في قاعدة البيانات فقط
        visitors = Visitor.query.filter_by(ip_address=ip).all()
        result = {
            'ip': ip,
            'visitors': visitors,
            'count': len(visitors)
        }
    
    # إضافة تاريخ ووقت التحديث
    date_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    return render_template(
        'admin/analytics/ip_lookup.html',
        result=result,
        ip=ip,
        date_time=date_time
    )

@analytics.route('/api/page-visits')
@admin_required
def api_page_visits():
    """واجهة برمجية للحصول على زيارات الصفحات لزائر محدد أو مجموعة زوار - للمدير فقط"""
    visitor_ids = request.args.get('visitor_ids', '')
    
    if not visitor_ids:
        return jsonify({'error': 'لم يتم تحديد معرف الزائر', 'visits': []}), 400
    
    # تحليل قائمة المعرفات
    try:
        ids = [int(id.strip()) for id in visitor_ids.split(',') if id.strip()]
    except ValueError:
        return jsonify({'error': 'معرفات الزوار غير صالحة', 'visits': []}), 400
    
    if not ids:
        return jsonify({'error': 'معرفات الزوار غير صالحة', 'visits': []}), 400
    
    # الحصول على زيارات الصفحات
    page_visits = PageVisit.query.filter(
        PageVisit.visitor_id.in_(ids)
    ).order_by(PageVisit.visited_at.desc()).all()
    
    # تحويل البيانات إلى تنسيق JSON
    visits_data = []
    for visit in page_visits:
        visits_data.append({
            'id': visit.id,
            'url': visit.page_url,
            'title': visit.page_title or visit.page_url,
            'time': visit.visited_at.strftime('%Y-%m-%d %H:%M:%S'),
            'visitor_id': visit.visitor_id
        })
    
    return jsonify({'visits': visits_data})

# الوظائف المساعدة

def get_total_views(days=None):
    """الحصول على مجموع المشاهدات لجميع المشاريع"""
    if days:
        date_filter = datetime.now() - timedelta(days=days)
        return db.session.query(func.sum(PortfolioItem.views_count))\
            .filter(PortfolioItem.created_at >= date_filter).scalar() or 0
    return db.session.query(func.sum(PortfolioItem.views_count)).scalar() or 0

def get_total_likes(days=None):
    """الحصول على مجموع الإعجابات"""
    try:
        if days:
            date_filter = datetime.now() - timedelta(days=days)
            try:
                portfolio_likes = PortfolioLike.query.filter(
                    PortfolioLike.created_at >= date_filter
                ).count()
            except:
                portfolio_likes = 0
            
            try:
                comment_likes = CommentLike.query.filter(
                    CommentLike.created_at >= date_filter
                ).count()
            except:
                comment_likes = 0
                
            return portfolio_likes + comment_likes
            
        # إجمالي الإعجابات
        try:
            portfolio_likes = PortfolioLike.query.count()
        except:
            portfolio_likes = 0
            
        try:
            comment_likes = CommentLike.query.count()
        except:
            comment_likes = 0
            
        return portfolio_likes + comment_likes
    except Exception as e:
        print(f"Error in get_total_likes: {str(e)}")
        return 0

def get_total_comments(days=None):
    """الحصول على مجموع التعليقات"""
    if days:
        date_filter = datetime.now() - timedelta(days=days)
        return PortfolioComment.query.filter(
            PortfolioComment.created_at >= date_filter
        ).count()
    return PortfolioComment.query.count()

def get_total_users(days=None):
    """الحصول على مجموع المستخدمين"""
    if days:
        date_filter = datetime.now() - timedelta(days=days)
        return User.query.filter(
            User.created_at >= date_filter
        ).count()
    return User.query.count()

def get_portfolio_stats(days=None):
    """الحصول على إحصائيات المشاريع"""
    # استعلام قاعدة البيانات
    query = db.session.query(
        PortfolioItem.id,
        PortfolioItem.title,
        PortfolioItem.views_count,
        PortfolioItem.likes_count,
        func.count(PortfolioComment.id).label('comments_count')
    ).outerjoin(
        PortfolioComment, PortfolioComment.portfolio_id == PortfolioItem.id
    ).group_by(
        PortfolioItem.id
    )
    
    # تطبيق فلتر التاريخ إذا تم تحديده
    if days:
        date_filter = datetime.now() - timedelta(days=days)
        query = query.filter(PortfolioItem.created_at >= date_filter)
    
    # تنفيذ الاستعلام
    results = query.all()
    
    # تحويل النتائج إلى قائمة قواميس
    stats = []
    for result in results:
        stats.append({
            'id': result.id,
            'title': result.title,
            'views_count': result.views_count,
            'likes_count': result.likes_count,
            'comments_count': result.comments_count
        })
    
    return stats

def get_activity_stats(days=None):
    """الحصول على إحصائيات النشاطات"""
    # استعلام قاعدة البيانات
    query = db.session.query(
        UserActivity.activity_type,
        func.count(UserActivity.id).label('count')
    ).group_by(
        UserActivity.activity_type
    )
    
    # تطبيق فلتر التاريخ إذا تم تحديده
    if days:
        date_filter = datetime.now() - timedelta(days=days)
        query = query.filter(UserActivity.created_at >= date_filter)
    
    # تنفيذ الاستعلام
    results = query.all()
    
    # تحويل النتائج إلى قاموس
    stats = {}
    for result in results:
        stats[result.activity_type] = result.count
    
    return stats

def get_user_stats(days=None):
    """الحصول على إحصائيات المستخدمين"""
    # عدد المستخدمين الجدد
    new_users_query = db.session.query(
        func.count(User.id)
    )
    
    if days:
        date_filter = datetime.now() - timedelta(days=days)
        new_users_query = new_users_query.filter(User.created_at >= date_filter)
    
    new_users_count = new_users_query.scalar() or 0
    
    # المستخدمين النشطين (الذين لديهم نشاطات)
    active_users_query = db.session.query(
        func.count(func.distinct(UserActivity.user_id))
    )
    
    if days:
        date_filter = datetime.now() - timedelta(days=days)
        active_users_query = active_users_query.filter(UserActivity.created_at >= date_filter)
    
    active_users_count = active_users_query.scalar() or 0
    
    return {
        'new_users': new_users_count,
        'active_users': active_users_count
    }

def generate_chart_data(days=30):
    """توليد بيانات الرسوم البيانية"""
    # تحديد الفترة الزمنية
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # توليد التواريخ
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    # بيانات المشاهدات
    views_data = []
    for date in dates:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        next_date = date_obj + timedelta(days=1)
        
        # احتساب عدد النشاطات من نوع view في هذا اليوم
        views_count = UserActivity.query.filter(
            UserActivity.activity_type.like('view%'),
            UserActivity.created_at >= date_obj,
            UserActivity.created_at < next_date
        ).count()
        
        views_data.append(views_count)
    
    # بيانات الإعجابات
    likes_data = []
    for date in dates:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        next_date = date_obj + timedelta(days=1)
        
        # احتساب عدد النشاطات من نوع like في هذا اليوم
        likes_count = UserActivity.query.filter(
            UserActivity.activity_type.like('like%'),
            UserActivity.created_at >= date_obj,
            UserActivity.created_at < next_date
        ).count()
        
        likes_data.append(likes_count)
    
    # بيانات التعليقات
    comments_data = []
    for date in dates:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        next_date = date_obj + timedelta(days=1)
        
        # احتساب عدد النشاطات من نوع comment في هذا اليوم
        comments_count = UserActivity.query.filter(
            UserActivity.activity_type.like('comment%'),
            UserActivity.created_at >= date_obj,
            UserActivity.created_at < next_date
        ).count()
        
        comments_data.append(comments_count)
    
    # تجميع البيانات
    chart_data = {
        'labels': dates,
        'views': views_data,
        'likes': likes_data,
        'comments': comments_data
    }
    
    return chart_data
    
# وظائف تتبع الزوار

def track_visitor(request):
    """تتبع زائر جديد أو تحديث بيانات زائر موجود"""
    from user_agents import parse  # استيراد داخلي لتجنب مشاكل دورة الاستيراد
    import logging
    
    logging.debug("Starting visitor tracking")
    
    # الحصول على عنوان IP الحقيقي للزائر (مع مراعاة وجود بروكسي)
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip_address:
        # إذا كان العنوان يحتوي على عناوين متعددة، نأخذ الأول
        ip_address = ip_address.split(',')[0].strip()
    
    # معلومات عن المتصفح
    user_agent_string = request.headers.get('User-Agent', '')
    user_agent = parse(user_agent_string)
    
    logging.debug(f"Visitor info - IP: {ip_address}, UA: {user_agent_string}")
    
    # معلومات إضافية
    referrer = request.headers.get('Referer', '')
    
    # استخدام Flask session بدلاً من قراءة الكوكيز مباشرة
    try:
        session_id = session.get('session_id', '')
    except Exception as e:
        logging.warning(f"Error getting session_id: {str(e)}")
        session_id = request.cookies.get('session', '')
    
    # التحقق من وجود الزائر
    visitor = None
    
    # تحقق أولاً باستخدام session_id (للزوار المتكررين)
    if session_id:
        visitor = Visitor.query.filter_by(session_id=session_id).first()
    
    # إذا لم نجد الزائر بمعرف الجلسة، نبحث عنه بعنوان IP
    if not visitor and ip_address:
        # البحث فقط إذا كان IP ليس خاصًا (مثل localhost)
        if not Visitor.is_ip_anonymous(ip_address):
            visitor = Visitor.query.filter_by(ip_address=ip_address).first()
    
    # استخراج معلومات الجهاز من وكيل المستخدم
    device_type = 'unknown'
    if user_agent.is_mobile:
        device_type = 'mobile'
    elif user_agent.is_tablet:
        device_type = 'tablet'
    elif user_agent.is_pc:
        device_type = 'desktop'
    elif user_agent.is_bot:
        device_type = 'bot'
    
    # إنشاء زائر جديد إذا لم يكن موجودًا
    is_new_visitor = False
    if not visitor:
        is_new_visitor = True
        visitor = Visitor(
            ip_address=ip_address,
            user_agent=user_agent_string,
            referrer=referrer,
            browser=user_agent.browser.family,
            os=user_agent.os.family,
            device=device_type,
            session_id=session_id,
            is_bot=user_agent.is_bot,
            # إذا كان المستخدم مسجلاً، نربط الزائر بحسابه
            user_id=current_user.id if current_user.is_authenticated else None
        )
        db.session.add(visitor)
    else:
        # تحديث بيانات الزائر الموجود
        visitor.update_visit()
        visitor.user_agent = user_agent_string
        visitor.referrer = referrer
        visitor.browser = user_agent.browser.family
        visitor.os = user_agent.os.family
        visitor.device = device_type
        # تحديث معرف المستخدم إذا قام بتسجيل الدخول
        if current_user.is_authenticated and not visitor.user_id:
            visitor.user_id = current_user.id
    
    # حفظ التغييرات
    db.session.commit()
    
    # إرسال إشعار عن زائر جديد عبر تلغرام
    if is_new_visitor and not visitor.is_bot and not Visitor.is_ip_anonymous(ip_address):
        try:
            visitor_name = f"المستخدم {current_user.username}" if current_user.is_authenticated else "زائر جديد"
            notification_message = format_visit_notification(visitor_name, "الصفحة الرئيسية", ip_address, user_agent_string)
            send_telegram_message(notification_message)
            logging.info(f"Sent Telegram notification for new visitor: {visitor.id} from IP: {ip_address}")
        except Exception as e:
            logging.error(f"Failed to send Telegram notification for new visitor: {str(e)}")
    
    return visitor

def track_page_visit(visitor, request):
    """تسجيل زيارة صفحة"""
    import logging
    
    page_url = request.path
    page_title = request.args.get('page_title', '')
    
    logging.debug(f"Tracking page visit - URL: {page_url}, Title: {page_title}, Visitor ID: {visitor.id}")
    
    # إنشاء سجل زيارة جديد
    page_visit = PageVisit(
        visitor_id=visitor.id,
        page_url=page_url,
        page_title=page_title
    )
    
    # تعليم زيارات الصفحة السابقة كغير خروج
    previous_visits = PageVisit.query.filter_by(
        visitor_id=visitor.id,
        exit_page=True
    ).all()
    
    for visit in previous_visits:
        visit.exit_page = False
    
    # اعتبار هذه الزيارة هي صفحة الخروج مبدئيًا
    page_visit.exit_page = True
    
    # حفظ البيانات
    db.session.add(page_visit)
    db.session.commit()
    
    return page_visit

def get_visitor_stats(days=None):
    """إحصائيات الزوار"""
    # تحديد الفترة الزمنية
    date_filter = None
    if days:
        date_filter = datetime.now() - timedelta(days=days)
    
    # إجمالي عدد الزوار
    visitors_query = db.session.query(Visitor)
    if date_filter:
        visitors_query = visitors_query.filter(Visitor.first_visit >= date_filter)
    total_visitors = visitors_query.count()
    
    # عدد الزوار المميزين (غير البوتات)
    non_bot_visitors_query = visitors_query.filter(Visitor.is_bot == False)
    non_bot_visitors = non_bot_visitors_query.count()
    
    # عدد مشاهدات الصفحات
    page_views_query = db.session.query(PageVisit)
    if date_filter:
        page_views_query = page_views_query.filter(PageVisit.visited_at >= date_filter)
    total_page_views = page_views_query.count()
    
    # متوسط عدد الصفحات لكل زائر
    pages_per_visitor = 0
    if non_bot_visitors > 0:
        pages_per_visitor = round(total_page_views / non_bot_visitors, 2)
    
    # تصنيف الزوار حسب الأجهزة
    devices_stats = {}
    devices = db.session.query(
        Visitor.device,
        func.count(Visitor.id).label('count')
    ).group_by(Visitor.device)
    
    if date_filter:
        devices = devices.filter(Visitor.first_visit >= date_filter)
    
    for device in devices.all():
        device_name = device.device or 'unknown'
        devices_stats[device_name] = device.count
    
    # تصنيف الزوار حسب المتصفح
    browser_stats = {}
    browsers = db.session.query(
        Visitor.browser,
        func.count(Visitor.id).label('count')
    ).group_by(Visitor.browser)
    
    if date_filter:
        browsers = browsers.filter(Visitor.first_visit >= date_filter)
    
    for browser in browsers.all():
        browser_name = browser.browser or 'unknown'
        browser_stats[browser_name] = browser.count
    
    # تصنيف الزوار حسب نظام التشغيل
    os_stats = {}
    operating_systems = db.session.query(
        Visitor.os,
        func.count(Visitor.id).label('count')
    ).group_by(Visitor.os)
    
    if date_filter:
        operating_systems = operating_systems.filter(Visitor.first_visit >= date_filter)
    
    for os in operating_systems.all():
        os_name = os.os or 'unknown'
        os_stats[os_name] = os.count
    
    # الصفحات الأكثر زيارة
    top_pages = db.session.query(
        PageVisit.page_url,
        PageVisit.page_title,
        func.count(PageVisit.id).label('count')
    ).group_by(
        PageVisit.page_url,
        PageVisit.page_title
    )
    
    if date_filter:
        top_pages = top_pages.filter(PageVisit.visited_at >= date_filter)
    
    top_pages_list = []
    for page in top_pages.order_by(text('count DESC')).limit(10).all():
        top_pages_list.append({
            'url': page.page_url,
            'title': page.page_title or page.page_url,
            'count': page.count
        })
    
    return {
        'total_visitors': total_visitors,
        'non_bot_visitors': non_bot_visitors,
        'total_page_views': total_page_views,
        'pages_per_visitor': pages_per_visitor,
        'devices': devices_stats,
        'browsers': browser_stats,
        'operating_systems': os_stats,
        'top_pages': top_pages_list
    }