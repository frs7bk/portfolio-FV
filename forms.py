
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, IntegerField, BooleanField, FileField, HiddenField, URLField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, ValidationError, URL
import os

def validate_image(form, field):
    if field.data:
        filename = field.data.filename.lower()
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
        if not ('.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS):
            raise ValidationError('صيغة الملف غير مسموح بها')
        if len(field.data.read()) > 16 * 1024 * 1024:  # 16MB
            field.data.seek(0)  # Reset file pointer
            raise ValidationError('حجم الملف كبير جداً')
        field.data.seek(0)  # Reset file pointer

class LoginForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(message='يجب إدخال اسم المستخدم')])
    password = PasswordField('كلمة المرور', validators=[DataRequired(message='يجب إدخال كلمة المرور')])

class TestimonialForm(FlaskForm):
    name = StringField('الاسم', validators=[
        DataRequired(message='يجب إدخال الاسم'),
        Length(min=2, max=100, message='يجب أن يكون الاسم بين 2 و 100 حرف')
    ])
    company = StringField('الشركة', validators=[Optional(), Length(max=100, message='يجب أن لا يتجاوز اسم الشركة 100 حرف')])
    content = TextAreaField('التعليق', validators=[
        DataRequired(message='يجب إدخال التعليق'),
        Length(min=10, max=1000, message='يجب أن يكون التعليق بين 10 و 1000 حرف')
    ])
    rating = IntegerField('التقييم', validators=[NumberRange(min=1, max=5)], default=5)

class ContentForm(FlaskForm):
    section_id = HiddenField('القسم', validators=[DataRequired()])
    key = StringField('المفتاح', validators=[DataRequired(message='يجب إدخال المفتاح')])
    value = TextAreaField('القيمة', validators=[Optional()])

class ProfileForm(FlaskForm):
    email = StringField('البريد الإلكتروني', validators=[
        DataRequired(message='يجب إدخال البريد الإلكتروني'),
        Email(message='البريد الإلكتروني غير صالح')
    ])
    current_password = PasswordField('كلمة المرور الحالية', validators=[Optional()])
    new_password = PasswordField('كلمة المرور الجديدة', validators=[
        Optional(),
        Length(min=6, message='يجب أن تكون كلمة المرور على الأقل 6 أحرف')
    ])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[Optional()])

class ImageUploadForm(FlaskForm):
    image = FileField('الصورة', validators=[
        DataRequired(message='يجب اختيار صورة'),
        validate_image
    ])
    section = HiddenField('القسم')
    key = HiddenField('المفتاح')
    caption = StringField('التسمية التوضيحية')
    alt_text = StringField('النص البديل')

class PortfolioItemForm(FlaskForm):
    """نموذج إضافة/تعديل مشروع في معرض الأعمال"""
    title = StringField('العنوان', validators=[
        DataRequired(message='يجب إدخال عنوان المشروع'),
        Length(min=3, max=200, message='يجب أن يكون العنوان بين 3 و 200 حرف')
    ])
    title_en = StringField('العنوان (بالإنجليزية)', validators=[
        Optional(),
        Length(max=200, message='يجب أن لا يتجاوز العنوان 200 حرف')
    ])
    description = TextAreaField('الوصف', validators=[
        DataRequired(message='يجب إدخال وصف المشروع'),
        Length(min=10, max=5000, message='يجب أن يكون الوصف بين 10 و 5000 حرف')
    ])
    description_en = TextAreaField('الوصف (بالإنجليزية)', validators=[
        Optional(),
        Length(max=5000, message='يجب أن لا يتجاوز الوصف 5000 حرف')
    ])
    category = StringField('التصنيف', validators=[
        DataRequired(message='يجب إدخال تصنيف المشروع'),
        Length(min=2, max=100, message='يجب أن يكون التصنيف بين 2 و 100 حرف')
    ])
    link = URLField('رابط المشروع', validators=[
        Optional(),
        URL(message='يجب إدخال رابط صحيح')
    ])
    image = FileField('صورة المشروع', validators=[
        DataRequired(message='يجب اختيار صورة للمشروع'),
        validate_image
    ])
    featured = BooleanField('مميز')
    carousel_order = IntegerField('ترتيب في الكاروسيل', validators=[
        Optional(),
        NumberRange(min=0, max=10, message='يجب أن يكون الترتيب بين 0 و 10')
    ], default=0)
    carousel_images = FileField('صور إضافية للكاروسيل', validators=[
        Optional(),
        validate_image
    ])
