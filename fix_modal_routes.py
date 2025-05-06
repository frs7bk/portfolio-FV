"""
إصلاح النوافذ المنبثقة في معرض الأعمال
ملف منفصل يمكن استدعاؤه من الملف الرئيسي
"""
from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user
from sqlalchemy import and_

from database import db
from models import PortfolioItem, PortfolioLike, PortfolioView, UserActivity, Visitor

# إنشاء البلوبرنت
portfolio_modal_fix_bp = Blueprint('portfolio_modal_fix', __name__, url_prefix='/portfolio')

def init_portfolio_modal_fix(app):
    """تسجيل البلوبرنت في التطبيق"""
    # تسجيل الطرق
    @portfolio_modal_fix_bp.route('/<int:portfolio_id>/detail')
    def get_portfolio_item_detail(portfolio_id):
        """الحصول على تفاصيل عنصر المعرض"""
        try:
            # الحصول على بيانات المشروع
            item = PortfolioItem.query.get_or_404(portfolio_id)
            
            # التحقق مما إذا كان المستخدم قد أعجب بالمشروع
            user_liked = False
            if current_user.is_authenticated:
                like = PortfolioLike.query.filter_by(
                    portfolio_id=portfolio_id,
                    user_id=current_user.id
                ).first()
                user_liked = like is not None
            else:
                # للمستخدمين غير المسجلين، نتحقق باستخدام عنوان IP
                like = PortfolioLike.query.filter_by(
                    portfolio_id=portfolio_id,
                    user_ip=request.remote_addr
                ).first()
                user_liked = like is not None
            
            # تحضير البيانات
            data = {
                'id': item.id,
                'title': item.title,
                'category': item.category,
                'description': item.description,
                'image_url': item.image_url,
                'link': item.link,
                'created_at': item.created_at.strftime('%Y-%m-%d'),
                'likes_count': item.likes_count_value,
                'views_count': item.views_count,
                'comments_count': 0,
                'user_liked': user_liked
            }
            
            return jsonify(data)
        except Exception as e:
            current_app.logger.error(f"خطأ في جلب تفاصيل المشروع: {str(e)}")
            return jsonify({
                'error': 'حدث خطأ أثناء جلب تفاصيل المشروع'
            }), 500

    @portfolio_modal_fix_bp.route('/<int:portfolio_id>/view', methods=['POST'])
    def view_portfolio_item(portfolio_id):
        """تسجيل مشاهدة للمشروع"""
        try:
            # التحقق من وجود المشروع
            portfolio_item = PortfolioItem.query.get_or_404(portfolio_id)
            
            # الحصول على معرف الزائر الحالي
            visitor_id = None
            visitor = None
            
            if current_user.is_authenticated:
                # المستخدم المسجل دخوله
                user_id = current_user.id
                visitor = Visitor.query.filter_by(user_id=user_id).first()
            else:
                # الزائر غير المسجل دخوله - استخدام عنوان IP
                ip_address = request.remote_addr
                user_agent = request.headers.get('User-Agent', '')
                visitor = Visitor.query.filter_by(ip_address=ip_address, user_agent=user_agent).first()
            
            if visitor:
                visitor_id = visitor.id
            
            # التحقق مما إذا كان الزائر قد شاهد هذا المشروع مسبقًا في آخر 24 ساعة
            existing_view = None
            if visitor_id:
                from datetime import datetime, timedelta
                last_24h = datetime.now() - timedelta(hours=24)
                
                existing_view = PortfolioView.query.filter(
                    and_(
                        PortfolioView.portfolio_id == portfolio_id,
                        PortfolioView.visitor_id == visitor_id,
                        PortfolioView.viewed_at >= last_24h
                    )
                ).first()
            
            # إذا لم يكن هناك مشاهدة مسجلة في آخر 24 ساعة، سجل مشاهدة جديدة
            if not existing_view:
                # إنشاء سجل مشاهدة جديد
                new_view = PortfolioView(
                    portfolio_id=portfolio_id,
                    visitor_id=visitor_id if visitor_id else None,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', '')
                )
                db.session.add(new_view)
                
                # زيادة عداد المشاهدات للمشروع
                portfolio_item.views_count += 1
                
                # تسجيل النشاط للمستخدم المسجل إذا كان متاحًا
                if current_user.is_authenticated:
                    activity = UserActivity(
                        user_id=current_user.id,
                        activity_type='view',
                        target_type='portfolio',
                        target_id=portfolio_id
                    )
                    db.session.add(activity)
                
                db.session.commit()
            
            return jsonify({
                'success': True,
                'views_count': portfolio_item.views_count
            })
        except Exception as e:
            current_app.logger.error(f"خطأ في تسجيل مشاهدة المشروع: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'حدث خطأ أثناء تسجيل المشاهدة'
            }), 500

    @portfolio_modal_fix_bp.route('/<int:portfolio_id>/like', methods=['POST'])
    def like_portfolio_item(portfolio_id):
        """تبديل حالة الإعجاب بالمشروع"""
        try:
            # التحقق من وجود المشروع
            portfolio_item = PortfolioItem.query.get_or_404(portfolio_id)
            
            # التحقق مما إذا كان المستخدم قد أعجب بالمشروع من قبل
            existing_like = None
            
            if current_user.is_authenticated:
                # المستخدم المسجل دخوله
                existing_like = PortfolioLike.query.filter_by(
                    portfolio_id=portfolio_id,
                    user_id=current_user.id
                ).first()
            else:
                # الزائر غير المسجل دخوله - استخدام عنوان IP
                existing_like = PortfolioLike.query.filter_by(
                    portfolio_id=portfolio_id,
                    user_ip=request.remote_addr
                ).first()
            
            # تبديل حالة الإعجاب (إضافة أو إزالة)
            liked = False
            
            if existing_like:
                # إزالة الإعجاب
                db.session.delete(existing_like)
                portfolio_item.likes_count_value = max(0, portfolio_item.likes_count_value - 1)
            else:
                # إضافة إعجاب جديد
                new_like = PortfolioLike(
                    portfolio_id=portfolio_id,
                    user_id=current_user.id if current_user.is_authenticated else None,
                    user_ip=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', '')
                )
                db.session.add(new_like)
                portfolio_item.likes_count_value += 1
                liked = True
                
                # تسجيل النشاط للمستخدم المسجل إذا كان متاحًا
                if current_user.is_authenticated:
                    activity = UserActivity(
                        user_id=current_user.id,
                        activity_type='like',
                        target_type='portfolio',
                        target_id=portfolio_id
                    )
                    db.session.add(activity)
                    
                # إرسال إشعار عن الإعجاب عبر تيليجرام
                try:
                    from telegram_service import send_telegram_message, format_like_notification
                    
                    # تحضير معلومات المستخدم
                    if current_user.is_authenticated:
                        user_info = current_user.username
                    else:
                        user_info = f"زائر ({request.remote_addr})"
                    
                    # إرسال إشعار التيليجرام
                    message = format_like_notification(user_info, 'مشروع', portfolio_item.title)
                    send_telegram_message(message)
                except Exception as e:
                    current_app.logger.error(f"خطأ في إرسال إشعار تيليجرام للإعجاب: {str(e)}")
                    # لا نريد وقف عملية الإعجاب إذا فشل الإشعار
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'liked': liked,
                'likes_count': portfolio_item.likes_count_value
            })
        except Exception as e:
            current_app.logger.error(f"خطأ في تبديل حالة الإعجاب: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'حدث خطأ أثناء تبديل حالة الإعجاب'
            }), 500

    # تسجيل البلوبرنت
    app.register_blueprint(portfolio_modal_fix_bp)
    current_app.logger.info("تم تسجيل مسارات إصلاح النوافذ المنبثقة بنجاح")
    
    return app
