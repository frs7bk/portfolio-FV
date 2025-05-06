"""
تسجيل مسارات إصلاح النوافذ المنبثقة
"""

from flask import Blueprint, current_app, render_template, jsonify
from fix_modals import fix_modals_bp

def register_fix_modals(app):
    """تسجيل مسارات إصلاح النوافذ المنبثقة"""
    app.register_blueprint(fix_modals_bp)
    
    @app.context_processor
    def inject_modal_fix():
        """إضافة متغيرات إضافية متاحة في كل القوالب"""
        return {
            'modal_fix_enabled': True
        }
    
    return app