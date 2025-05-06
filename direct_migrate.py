from sqlalchemy import text
from app import app, db

# قم بإضافة العمود session_id إلى جدول portfolio_like
with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE portfolio_like ADD COLUMN IF NOT EXISTS session_id VARCHAR(100)"))
        db.session.commit()
        print("تم إضافة عمود session_id إلى جدول portfolio_like بنجاح")
    except Exception as e:
        db.session.rollback()
        print(f"حدث خطأ أثناء إضافة عمود session_id: {str(e)}")

# تعديل قيد NOT NULL لعمود name في جدول portfolio_comment (إذا كان موجوداً)
with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE portfolio_comment ALTER COLUMN name DROP NOT NULL"))
        db.session.commit()
        print("تم تعديل قيود العمود name في جدول portfolio_comment بنجاح")
    except Exception as e:
        db.session.rollback()
        print(f"حدث خطأ أثناء تعديل قيود العمود name: {str(e)}")