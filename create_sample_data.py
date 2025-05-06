"""
Script para crear datos de muestra para el sitio web.
Esto crea elementos de portfolio para poder probar la funcionalidad.
"""

from app import app, db
from models import PortfolioItem, Section, Image, Content, User
from datetime import datetime

def create_sample_portfolio():
    """Crear elementos de portfolio de muestra"""
    print("Creando elementos de portfolio de muestra...")
    
    # Verificar si ya existen elementos
    if PortfolioItem.query.count() > 0:
        print(f"Ya existen {PortfolioItem.query.count()} elementos en el portfolio.")
        return
    
    # Datos de muestra para el portfolio
    portfolio_items = [
        {
            'title': 'تصميم هوية شركة تقنية',
            'title_en': 'Tech Company Brand Identity',
            'description': 'تصميم شعار وهوية بصرية متكاملة لشركة متخصصة في تطوير البرمجيات والحلول التقنية.',
            'description_en': 'Logo and complete brand identity design for a software development and tech solutions company.',
            'image_url': '/static/uploads/20250420203624_ig.jpg',
            'category': 'هوية بصرية, تصميم شعار',
            'year': 2025,
            'featured': True,
            'client': 'شركة تك سوليوشنز',
            'client_en': 'Tech Solutions Corp',
            'tools': 'Adobe Illustrator, Adobe Photoshop',
            'external_url': 'https://example.com/project1'
        },
        {
            'title': 'تصميم منشورات انستجرام',
            'title_en': 'Instagram Posts Design',
            'description': 'سلسلة تصاميم لمنشورات انستجرام لعلامة تجارية في مجال الأزياء والموضة.',
            'description_en': 'A series of Instagram posts designs for a fashion brand.',
            'image_url': '/static/uploads/20250420203643_IMG_20240616_225008_798.jpg',
            'category': 'سوشيال ميديا, تصميم منشورات',
            'year': 2025,
            'featured': True,
            'client': 'ماركة فاشون',
            'client_en': 'Fashion Brand',
            'tools': 'Adobe Photoshop, Canva',
            'external_url': 'https://example.com/project2'
        },
        {
            'title': 'تصميم موقع ويب لشركة استشارات',
            'title_en': 'Consulting Firm Website Design',
            'description': 'تصميم واجهة مستخدم لموقع ويب لشركة استشارات مالية وإدارية.',
            'description_en': 'UI design for a financial and management consulting firm website.',
            'image_url': '/static/uploads/20250420203815_profile.png',
            'category': 'تصميم ويب, تجربة المستخدم',
            'year': 2025,
            'featured': False,
            'client': 'شركة كونسلت برو',
            'client_en': 'ConsultPro',
            'tools': 'Figma, Adobe XD, Sketch',
            'external_url': 'https://example.com/project3'
        },
        {
            'title': 'إعلانات حملة تسويقية',
            'title_en': 'Marketing Campaign Ads',
            'description': 'تصميم إعلانات لحملة تسويقية شاملة تتضمن وسائط مطبوعة ورقمية.',
            'description_en': 'Ad designs for a comprehensive marketing campaign including print and digital media.',
            'image_url': '/static/uploads/20250420205529_djezzy_final.jpg',
            'category': 'تصميم إعلاني, تسويق',
            'year': 2024,
            'featured': True,
            'client': 'شركة مشروبات',
            'client_en': 'Beverage Company',
            'tools': 'Adobe Illustrator, Adobe Photoshop, Adobe InDesign',
            'external_url': 'https://example.com/project4'
        },
        {
            'title': 'تصميم تطبيق جوال',
            'title_en': 'Mobile App Design',
            'description': 'تصميم واجهات مستخدم لتطبيق جوال لخدمات توصيل الطعام.',
            'description_en': 'UI design for a food delivery mobile application.',
            'image_url': '/static/uploads/20250420224146_profile.png',
            'category': 'تصميم تطبيقات, تجربة المستخدم',
            'year': 2024,
            'featured': False,
            'client': 'فودكس',
            'client_en': 'FoodX',
            'tools': 'Figma, Adobe XD, Sketch',
            'external_url': 'https://example.com/project5'
        },
        {
            'title': 'تصميم كتاب وغلاف',
            'title_en': 'Book and Cover Design',
            'description': 'تصميم غلاف وصفحات داخلية لكتاب في مجال التنمية الذاتية.',
            'description_en': 'Cover and interior page design for a self-development book.',
            'image_url': '/static/uploads/20250420225626_ig.jpg',
            'category': 'تصميم مطبوعات, غلاف كتاب',
            'year': 2024,
            'featured': True,
            'client': 'دار النشر المتميزة',
            'client_en': 'Premium Publishing House',
            'tools': 'Adobe InDesign, Adobe Illustrator, Adobe Photoshop',
            'external_url': 'https://example.com/project6'
        }
    ]
    
    # Crear los elementos en la base de datos
    for item_data in portfolio_items:
        portfolio_item = PortfolioItem(
            title=item_data['title'],
            title_en=item_data['title_en'],
            description=item_data['description'],
            description_en=item_data['description_en'],
            image_url=item_data['image_url'],
            category=item_data['category'],
            featured=item_data['featured'],
            link=item_data['external_url'],
            created_at=datetime.now(),
            views_count=0,
            likes_count_value=0
        )
        db.session.add(portfolio_item)
    
    # Guardar cambios
    db.session.commit()
    print(f"Se han creado {len(portfolio_items)} elementos de portfolio.")

if __name__ == '__main__':
    with app.app_context():
        create_sample_portfolio()