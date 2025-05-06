# وظائف إدارة الكاروسيل لإضافتها إلى app.py

# ----- إدارة الكاروسيل -----

@app.route('/admin/carousel-management')
@login_required
def admin_carousel_management():
    """واجهة الإدارة لعناصر الكاروسيل"""
    # الحصول على عناصر الكاروسيل (مرتبة حسب ترتيب الكاروسيل)
    carousel_items = PortfolioItem.query.filter(PortfolioItem.carousel_order > 0).order_by(PortfolioItem.carousel_order).all()
    
    # الحصول على جميع عناصر المعرض للإدارة
    portfolio_items = PortfolioItem.query.order_by(PortfolioItem.created_at.desc()).all()
    
    # الحصول على العناصر البارزة
    featured_items = PortfolioItem.query.filter_by(featured=True).all()
    
    # الحصول على الإحصائيات للوحة التحكم
    pending_testimonials = Testimonial.query.filter_by(approved=False).count()
    pending_portfolio_comments = PortfolioComment.query.filter_by(approved=False).count()
    
    return render_template('admin/carousel_management.html',
                          carousel_items=carousel_items,
                          portfolio_items=portfolio_items,
                          featured_items=featured_items,
                          pending_testimonials=pending_testimonials,
                          pending_portfolio_comments=pending_portfolio_comments)

@app.route('/admin/portfolio/update-carousel', methods=['POST'])
@login_required
def update_portfolio_carousel():
    """تحديث إعدادات الكاروسيل والعناصر البارزة لعنصر معرض"""
    try:
        portfolio_id = request.form.get('portfolio_id', type=int)
        if not portfolio_id:
            flash('معرف العنصر مطلوب', 'danger')
            return redirect(url_for('admin_carousel_management'))
            
        portfolio_item = PortfolioItem.query.get_or_404(portfolio_id)
        
        # تحديث الكاروسيل والعناصر البارزة
        carousel_order = request.form.get('carousel_order', type=int, default=0)
        portfolio_item.carousel_order = max(0, min(10, carousel_order))  # التأكد من أن القيمة بين 0 و 10
        portfolio_item.featured = 'featured' in request.form
        
        db.session.commit()
        app.logger.info(f"تم تحديث إعدادات الكاروسيل والعناصر البارزة لعنصر المعرض بنجاح: {portfolio_item.id} - {portfolio_item.title}")
        flash('تم تحديث إعدادات الكاروسيل والعناصر البارزة بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"خطأ في تحديث إعدادات الكاروسيل: {str(e)}")
        flash(f'حدث خطأ أثناء تحديث إعدادات الكاروسيل: {str(e)}', 'danger')
    
    return redirect(url_for('admin_carousel_management'))

@app.route('/admin/carousel/save-order', methods=['POST'])
@login_required
def save_carousel_order():
    """حفظ ترتيب عناصر الكاروسيل بعد السحب والإفلات"""
    try:
        if request.is_json:
            data = request.get_json()
            items = data.get('items', [])
            
            if not items:
                return jsonify({'success': False, 'message': 'لا توجد عناصر للتحديث'})
            
            for item in items:
                item_id = item.get('id')
                order = item.get('order')
                
                if item_id and order is not None:
                    portfolio_item = PortfolioItem.query.get(item_id)
                    if portfolio_item:
                        portfolio_item.carousel_order = order
            
            db.session.commit()
            app.logger.info("تم تحديث ترتيب الكاروسيل بنجاح")
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'البيانات المرسلة غير صالحة'})
            
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"خطأ في حفظ ترتيب الكاروسيل: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})