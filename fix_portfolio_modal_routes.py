"""
إصلاح مسارات النوافذ المنبثقة لمعرض المشاريع
"""
from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user
from sqlalchemy import and_
from datetime import datetime, timedelta

from database import db
from models import PortfolioItem, PortfolioLike, PortfolioView, UserActivity, Visitor

# إنشاء بلوبرنت
portfolio_modal_fix_bp = Blueprint('portfolio_modal_fix', __name__, url_prefix='/portfolio')

# مسار للحصول على تفاصيل المشروع
@portfolio_modal_fix_bp.route('/<int:portfolio_id>/details')
def get_portfolio_item_detail(portfolio_id):
    """الحصول على تفاصيل المشروع"""
    try:
        item = PortfolioItem.query.get_or_404(portfolio_id)
        
        # التحقق من حالة الإعجاب
        user_liked = False
        if current_user.is_authenticated:
            like = PortfolioLike.query.filter_by(portfolio_id=portfolio_id, user_id=current_user.id).first()
            user_liked = like is not None
        else:
            like = PortfolioLike.query.filter_by(portfolio_id=portfolio_id, user_ip=request.remote_addr).first()
            user_liked = like is not None
        
        # تجهيز البيانات
        data = {
            'success': True,
            'item': {
                'id': item.id,
                'title': item.title,
                'category': item.category,
                'description': item.description,
                'image_url': item.image_url,
                'external_url': item.link,
                'created_at': item.created_at.strftime('%Y-%m-%d'),
                'likes_count': item.likes_count or 0,
                'views_count': item.views_count or 0,
                'comments_count': 0,
                'user_liked': user_liked
            }
        }
        
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"خطأ في جلب تفاصيل المشروع: {str(e)}")
        return jsonify({'success': False, 'message': 'فشل في جلب تفاصيل المشروع'}), 500

# مسار لتسجيل مشاهدة للمشروع
@portfolio_modal_fix_bp.route('/<int:portfolio_id>/view', methods=['POST'])
def view_portfolio_item(portfolio_id):
    """تسجيل مشاهدة للمشروع"""
    try:
        item = PortfolioItem.query.get_or_404(portfolio_id)
        
        # تحديث عدد المشاهدات
        if not item.views_count:
            item.views_count = 1
        else:
            item.views_count += 1
            
        # تسجيل مشاهدة جديدة
        view = PortfolioView()
        view.portfolio_id = portfolio_id
        
        if current_user.is_authenticated:
            view.user_id = current_user.id
        else:
            view.visitor_ip = request.remote_addr
            
            # التحقق من وجود زائر مسجل
            visitor = Visitor.query.filter_by(ip_address=request.remote_addr).first()
            if visitor:
                view.visitor_id = visitor.id
                
        view.viewed_at = datetime.utcnow()
        
        db.session.add(view)
        
        # تسجيل نشاط المستخدم
        activity = UserActivity()
        activity.activity_type = 'view'
        activity.activity_data = f'portfolio:{portfolio_id}'
        activity.ip_address = request.remote_addr
        
        if current_user.is_authenticated:
            activity.user_id = current_user.id
        else:
            # التحقق من وجود زائر مسجل
            visitor = Visitor.query.filter_by(ip_address=request.remote_addr).first()
            if visitor:
                activity.visitor_id = visitor.id
                
        activity.created_at = datetime.utcnow()
        
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'views_count': item.views_count
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"خطأ في تسجيل مشاهدة للمشروع: {str(e)}")
        return jsonify({'success': False, 'message': 'فشل في تسجيل المشاهدة'}), 500

# مسار لتبديل حالة الإعجاب بالمشروع
@portfolio_modal_fix_bp.route('/<int:portfolio_id>/like', methods=['POST'])
def like_portfolio_item(portfolio_id):
    """تبديل حالة الإعجاب بالمشروع"""
    try:
        item = PortfolioItem.query.get_or_404(portfolio_id)
        like_added = False
        
        # البحث عن إعجاب موجود
        if current_user.is_authenticated:
            like = PortfolioLike.query.filter_by(portfolio_id=portfolio_id, user_id=current_user.id).first()
        else:
            like = PortfolioLike.query.filter_by(portfolio_id=portfolio_id, user_ip=request.remote_addr).first()
        
        # إذا لم يكن هناك إعجاب مسبق، أضفه
        if not like:
            like = PortfolioLike()
            like.portfolio_id = portfolio_id
            
            if current_user.is_authenticated:
                like.user_id = current_user.id
            else:
                like.user_ip = request.remote_addr
                
                # التحقق من وجود زائر مسجل
                visitor = Visitor.query.filter_by(ip_address=request.remote_addr).first()
                if visitor:
                    like.visitor_id = visitor.id
            
            like.created_at = datetime.utcnow()
            db.session.add(like)
            
            # زيادة عدد الإعجابات
            if not item.likes_count:
                item.likes_count = 1
            else:
                item.likes_count += 1
                
            like_added = True
            
            # تسجيل نشاط المستخدم
            activity = UserActivity()
            activity.activity_type = 'like'
            activity.activity_data = f'portfolio:{portfolio_id}'
            activity.ip_address = request.remote_addr
            
            if current_user.is_authenticated:
                activity.user_id = current_user.id
            else:
                visitor = Visitor.query.filter_by(ip_address=request.remote_addr).first()
                if visitor:
                    activity.visitor_id = visitor.id
                    
            activity.created_at = datetime.utcnow()
            db.session.add(activity)
        else:
            # إزالة الإعجاب
            db.session.delete(like)
            
            # تقليل عدد الإعجابات
            if item.likes_count and item.likes_count > 0:
                item.likes_count -= 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'liked': like_added,
            'likes_count': item.likes_count or 0
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"خطأ في تبديل حالة الإعجاب بالمشروع: {str(e)}")
        return jsonify({'success': False, 'message': 'فشل في تبديل حالة الإعجاب'}), 500

# دالة لتسجيل البلوبرنت في التطبيق
def init_portfolio_modal_fix(app):
    """تسجيل مسارات إصلاح النوافذ المنبثقة"""
    app.register_blueprint(portfolio_modal_fix_bp)
    return app