from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user
from sqlalchemy import and_
from datetime import datetime

from database import db
from models import PortfolioItem, PortfolioLike, PortfolioView, UserActivity, Visitor

# إنشاء بلوبرنت
portfolio_instagram_bp = Blueprint('portfolio_instagram', __name__, url_prefix='/portfolio/api')

@portfolio_instagram_bp.route('/item/<int:portfolio_id>', methods=['GET'])
def get_portfolio_item(portfolio_id):
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
        
        # عدد التعليقات
        comments_count = 0  # سنضيف دعم التعليقات لاحقاً
        
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
                'likes': item.likes_count or 0,
                'views': item.views_count or 0,
                'comments_count': comments_count,
                'user_liked': user_liked
            }
        }
        
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"خطأ في جلب تفاصيل المشروع: {str(e)}")
        return jsonify({'success': False, 'message': 'فشل في جلب تفاصيل المشروع'}), 500

@portfolio_instagram_bp.route('/view/<int:portfolio_id>', methods=['POST'])
def view_portfolio_item(portfolio_id):
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
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'views': item.views_count
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"خطأ في تسجيل مشاهدة للمشروع: {str(e)}")
        return jsonify({'success': False, 'message': 'فشل في تسجيل المشاهدة'}), 500

@portfolio_instagram_bp.route('/like/<int:portfolio_id>', methods=['POST'])
def like_portfolio_item(portfolio_id):
    try:
        item = PortfolioItem.query.get_or_404(portfolio_id)
        user_liked = False
        
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
                
            user_liked = True
        else:
            # إزالة الإعجاب
            db.session.delete(like)
            
            # تقليل عدد الإعجابات
            if item.likes_count and item.likes_count > 0:
                item.likes_count -= 1
            
            user_liked = False
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user_liked': user_liked,
            'likes': item.likes_count or 0
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"خطأ في تبديل حالة الإعجاب بالمشروع: {str(e)}")
        return jsonify({'success': False, 'message': 'فشل في تبديل حالة الإعجاب'}), 500

# دالة لتسجيل البلوبرنت في التطبيق
def init_portfolio_instagram(app):
    app.register_blueprint(portfolio_instagram_bp)
    app.logger.info("تم تسجيل مسارات النافذة المنبثقة بنمط إنستغرام")
    return app