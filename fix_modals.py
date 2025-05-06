"""
إصلاح إضافي للنوافذ المنبثقة في معرض الأعمال
هذا الملف ينشئ مسارًا إضافيًا لإصلاح مشكلة النوافذ المنبثقة
"""

from flask import Blueprint, send_from_directory, render_template, jsonify, request, url_for
import os

fix_modals_bp = Blueprint('fix_modals', __name__)


@fix_modals_bp.route('/portfolio/modal_scripts', methods=['GET'])
def get_modal_scripts():
    """
    إرجاع ملفات JavaScript الخاصة بإصلاح النوافذ المنبثقة
    """
    # لوجود تصحيح مسار القالب
    return jsonify({
        'status': 'success',
        'message': 'Modal fix scripts are ready',
        'scripts': [
            url_for('static', filename='js/load-portfolio-modal.js'),
            url_for('static', filename='js/portfolio-modal-fix.js')
        ]
    })


@fix_modals_bp.route('/portfolio/modal_templates', methods=['GET'])
def get_modal_template():
    """
    إرجاع قالب النافذة المنبثقة
    """
    # لوجود تصحيح مسار القالب بالكامل كـ HTML
    modal_html = """
    <!-- مودال تفاصيل المشروع -->
    <div id="portfolio-modal" class="portfolio-modal">
      <button id="close-modal" class="close-modal">&times;</button>
      
      <div class="modal-container">
        <div class="modal-image">
          <img id="modal-image" src="" alt="صورة المشروع">
        </div>
        
        <div class="modal-content">
          <div class="modal-header">
            <img src="/static/uploads/profile.png" alt="صورة الملف الشخصي">
            <h4>فيراس ديزاين</h4>
          </div>
          
          <div class="modal-details">
            <h3 id="modal-title"></h3>
            <span id="modal-category" class="modal-category"></span>
            <div id="modal-description"></div>
            <div id="modal-link-container" style="display: none;">
              <a id="modal-link" href="#" target="_blank" class="btn btn-primary mt-2">زيارة المشروع</a>
            </div>
            <div class="modal-meta">
              <span id="modal-date"></span>
            </div>
          </div>
          
          <div class="modal-actions">
            <button id="like-button" type="button"><i class="far fa-heart"></i></button>
            <button type="button"><i class="far fa-share-square"></i></button>
          </div>
          
          <div class="modal-stats">
            <p id="modal-likes">0 إعجاب</p>
            <p id="modal-views">0 مشاهدة</p>
          </div>
          
          <input type="hidden" id="modal-item-id" value="">
        </div>
      </div>
    </div>
    """
    
    return jsonify({
        'status': 'success',
        'html': modal_html
    })


def init_fix_modals(app):
    """
    تهيئة مسارات إصلاح النوافذ المنبثقة
    """
    app.register_blueprint(fix_modals_bp)
    
    return app