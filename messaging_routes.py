"""
مسارات وواجهات للتعامل مع الرسائل والطلبات
"""

import os
import logging
import traceback
from datetime import datetime
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from database import db
from models import ContactMessage, ServiceRequest
from telegram_service import (
    send_telegram_message, 
    format_contact_message, 
    format_order_notification
)

# إنشاء البلوبرنت
messaging_bp = Blueprint('messaging', __name__, url_prefix='/messaging')

@messaging_bp.route('/admin/messages')
@login_required
def admin_messages():
    """عرض واجهة إدارة الرسائل"""
    # جلب جميع الرسائل، الأحدث أولاً
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    
    # تقسيم الرسائل
    unread_messages = [msg for msg in messages if not msg.read]
    read_messages = [msg for msg in messages if msg.read]
    starred_messages = [msg for msg in messages if msg.starred]
    
    return render_template('admin/messages.html',
                          messages=messages,
                          unread_messages=unread_messages,
                          read_messages=read_messages,
                          starred_messages=starred_messages,
                          active_section='messages')

@messaging_bp.route('/admin/service-requests')
@login_required
def admin_service_requests():
    """عرض واجهة إدارة طلبات الخدمة"""
    # جلب جميع الطلبات، الأحدث أولاً
    requests = ServiceRequest.query.order_by(ServiceRequest.created_at.desc()).all()
    
    # تقسيم الطلبات حسب الحالة
    new_requests = [req for req in requests if req.status == 'new']
    in_progress_requests = [req for req in requests if req.status == 'in_progress']
    completed_requests = [req for req in requests if req.status == 'completed']
    cancelled_requests = [req for req in requests if req.status == 'cancelled']
    
    return render_template('admin/service_requests.html',
                          requests=requests,
                          new_requests=new_requests,
                          in_progress_requests=in_progress_requests,
                          completed_requests=completed_requests,
                          cancelled_requests=cancelled_requests,
                          active_section='service_requests')

@messaging_bp.route('/submit-contact', methods=['POST'])
def submit_contact():
    """تلقي وحفظ رسائل نموذج التواصل"""
    try:
        # استخراج البيانات من النموذج
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        phone = request.form.get('phone', '').strip()
        
        # التحقق من البيانات المطلوبة
        if not name:
            return jsonify({'error': 'يرجى إدخال الاسم'}), 400
        
        if not email:
            return jsonify({'error': 'يرجى إدخال البريد الإلكتروني'}), 400
        
        if not message:
            return jsonify({'error': 'يرجى إدخال نص الرسالة'}), 400
        
        # إنشاء وحفظ الرسالة الجديدة
        new_message = ContactMessage(
            name=name,
            email=email,
            subject=subject,
            message=message,
            phone=phone,
            ip_address=request.remote_addr
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        # إرسال إشعار تيليجرام
        formatted_message = format_contact_message(name, email, message, subject)
        telegram_success = send_telegram_message(formatted_message)
        
        # تحديث حالة إرسال التيليجرام
        if telegram_success:
            new_message.telegram_sent = True
            db.session.commit()
            logging.info(f"Telegram notification sent for contact message ID {new_message.id}")
        
        return jsonify({
            'success': True,
            'message': 'تم إرسال رسالتك بنجاح! سنقوم بالرد عليك في أقرب وقت ممكن.'
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in submit_contact: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({'error': 'حدث خطأ أثناء إرسال الرسالة. يرجى المحاولة مرة أخرى لاحقاً.'}), 500

@messaging_bp.route('/submit-service-request', methods=['POST'])
def submit_service_request():
    """تلقي وحفظ طلبات الخدمة"""
    try:
        # استخراج البيانات من النموذج
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        service_type = request.form.get('service_type', '').strip()
        details = request.form.get('details', '').strip()
        budget = request.form.get('budget', '').strip()
        timeline = request.form.get('timeline', '').strip()
        
        # التحقق من البيانات المطلوبة
        if not name:
            return jsonify({'error': 'يرجى إدخال الاسم'}), 400
        
        if not email:
            return jsonify({'error': 'يرجى إدخال البريد الإلكتروني'}), 400
        
        if not service_type:
            return jsonify({'error': 'يرجى تحديد نوع الخدمة المطلوبة'}), 400
        
        if not details:
            return jsonify({'error': 'يرجى إدخال تفاصيل الطلب'}), 400
        
        # إنشاء وحفظ طلب الخدمة الجديد
        new_request = ServiceRequest(
            name=name,
            email=email,
            phone=phone,
            service_type=service_type,
            details=details,
            budget=budget,
            timeline=timeline,
            ip_address=request.remote_addr
        )
        
        db.session.add(new_request)
        db.session.commit()
        
        # إرسال إشعار تيليجرام
        formatted_message = format_order_notification(name, service_type, details, email, phone)
        telegram_success = send_telegram_message(formatted_message)
        
        # تحديث حالة إرسال التيليجرام
        if telegram_success:
            new_request.telegram_sent = True
            db.session.commit()
            logging.info(f"Telegram notification sent for service request ID {new_request.id}")
        
        return jsonify({
            'success': True,
            'message': 'تم إرسال طلبك بنجاح! سنقوم بالتواصل معك قريباً لمناقشة التفاصيل.'
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in submit_service_request: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({'error': 'حدث خطأ أثناء إرسال الطلب. يرجى المحاولة مرة أخرى لاحقاً.'}), 500

@messaging_bp.route('/admin/message/<int:message_id>/toggle-read', methods=['POST'])
@login_required
def toggle_message_read(message_id):
    """تبديل حالة قراءة الرسالة"""
    message = ContactMessage.query.get_or_404(message_id)
    message.read = not message.read
    
    # إذا تم وضع علامة كمقروءة، نحدث تاريخ القراءة
    if message.read:
        message.read_at = datetime.now()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'read': message.read
    })

@messaging_bp.route('/admin/message/<int:message_id>/toggle-star', methods=['POST'])
@login_required
def toggle_message_star(message_id):
    """تبديل حالة تثبيت الرسالة (نجمة)"""
    message = ContactMessage.query.get_or_404(message_id)
    message.starred = not message.starred
    db.session.commit()
    
    return jsonify({
        'success': True,
        'starred': message.starred
    })

@messaging_bp.route('/admin/service-request/<int:request_id>/update-status', methods=['POST'])
@login_required
def update_request_status(request_id):
    """تحديث حالة طلب الخدمة"""
    req = ServiceRequest.query.get_or_404(request_id)
    new_status = request.form.get('status')
    
    # التحقق من صحة الحالة
    valid_statuses = ['new', 'in_progress', 'completed', 'cancelled']
    if new_status not in valid_statuses:
        return jsonify({'error': 'حالة غير صالحة'}), 400
    
    req.status = new_status
    db.session.commit()
    
    return jsonify({
        'success': True,
        'status': new_status
    })

@messaging_bp.route('/admin/message/<int:message_id>/delete', methods=['POST'])
@login_required
def delete_message(message_id):
    """حذف رسالة"""
    message = ContactMessage.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    
    flash('تم حذف الرسالة بنجاح', 'success')
    return redirect(url_for('messaging.admin_messages'))

@messaging_bp.route('/admin/service-request/<int:request_id>/delete', methods=['POST'])
@login_required
def delete_service_request(request_id):
    """حذف طلب خدمة"""
    req = ServiceRequest.query.get_or_404(request_id)
    db.session.delete(req)
    db.session.commit()
    
    flash('تم حذف الطلب بنجاح', 'success')
    return redirect(url_for('messaging.admin_service_requests'))

@messaging_bp.route('/api/unread-messages-count')
@login_required
def unread_messages_count():
    """الحصول على عدد الرسائل غير المقروءة"""
    count = ContactMessage.query.filter_by(read=False).count()
    return jsonify({
        'success': True,
        'count': count
    })

@messaging_bp.route('/api/new-requests-count')
@login_required
def new_requests_count():
    """الحصول على عدد طلبات الخدمة الجديدة"""
    count = ServiceRequest.query.filter_by(status='new').count()
    return jsonify({
        'success': True,
        'count': count
    })