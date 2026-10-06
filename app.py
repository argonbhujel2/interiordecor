import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import re

from config import Config
from models import db, User, Product, ProductCategory, ProductImage, Service, Project, ProjectImage, QuoteRequest, ContactMessage, Pricing, SiteSetting

login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    
    login_manager.login_view = 'admin.login'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes.main import main_bp
    from routes.admin import admin_bp
    from routes.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Calculator API is JSON-only; exempt from CSRF
    csrf.exempt(api_bp)
    
    # Context processors
    @app.context_processor
    def inject_settings():
        settings = {}
        try:
            for s in SiteSetting.query.all():
                settings[s.setting_key] = s.value
        except Exception:
            pass
        defaults = {
            'business_name': 'Urlabari Interior Decor',
            'tagline': 'Premium Gypsum & Ceiling Solutions',
            'phone': '+977 981-1348243',
            'whatsapp': '9779811348243',
            'email': 'info@urlabariinterior.com',
            'address': 'Urlabari, Morang, Nepal',
            'opening_hours': 'Sun - Fri: 9:00 AM - 6:00 PM',
            'facebook': '#',
            'instagram': '#',
            'tiktok': '#',
            'youtube': '#',
            'hero_title': 'Premium Gypsum & Ceiling Solutions',
            'hero_subtitle': 'Quality materials, professional installation and modern ceiling solutions for homes, offices and commercial spaces.',
            'hero_image': '',
            'stat_projects': '500+',
            'stat_customers': '100+',
            'stat_years': '5+',
            'stat_support': '100%',
        }
        for k, v in defaults.items():
            if k not in settings or not settings[k]:
                settings[k] = v
        return dict(settings=settings)
    
    @app.template_filter('slugify')
    def slugify_filter(text):
        text = str(text).lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_-]+', '-', text)
        return text
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return render_template('500.html'), 500
    
    # Create tables and seed on first run
    with app.app_context():
        try:
            db.create_all()
            seed_data(app)
        except Exception as e:
            print(f'[WARN] Database init error: {e}')
            print('  Make sure DATABASE_URL is correct, or leave it empty to use SQLite.')
    
    return app

def seed_data(app):
    """Seed initial data if empty"""
    try:
        existing = User.query.first()
        if existing:
            print('[INFO] Database already has data, skip seed.')
            return
        print('[INFO] Empty database — seeding sample data...')
    except Exception as e:
        print(f'[WARN] Could not check users: {e}')
        return
    
    # Admin user
    admin = User(
        username=os.environ.get('ADMIN_USERNAME', 'admin'),
        email=os.environ.get('ADMIN_EMAIL', 'admin@urlabariinterior.com'),
        is_admin=True
    )
    admin.set_password(os.environ.get('ADMIN_PASSWORD', 'ChangeMe123!'))
    db.session.add(admin)
    
    # Categories
    cats = [
        ('Gypsum Products', 'gypsum-products'),
        ('Ceiling Products', 'ceiling-products'),
        ('Accessories', 'accessories'),
    ]
    cat_objs = {}
    for name, slug in cats:
        c = ProductCategory(name=name, slug=slug)
        db.session.add(c)
        cat_objs[slug] = c
    db.session.flush()
    
    # Products
    products_data = [
        ('Gypsum Board', 'gypsum-board', 'gypsum-products', 'Standard gypsum plasterboard for walls and ceilings.', 'Available', None),
        ('Moisture Resistant Gypsum Board', 'moisture-resistant-gypsum-board', 'gypsum-products', 'Ideal for bathrooms and high-humidity areas.', 'Available', None),
        ('Fire Resistant Gypsum Board', 'fire-resistant-gypsum-board', 'gypsum-products', 'Enhanced fire protection for commercial spaces.', 'Available', None),
        ('Acoustic Gypsum Board', 'acoustic-gypsum-board', 'gypsum-products', 'Sound absorption for offices and studios.', 'Available', None),
        ('False Ceiling', 'false-ceiling', 'ceiling-products', 'Modern suspended false ceiling systems.', 'Available', None),
        ('Gypsum Ceiling', 'gypsum-ceiling', 'ceiling-products', 'Classic gypsum ceiling solutions.', 'Available', None),
        ('PVC Ceiling', 'pvc-ceiling', 'ceiling-products', 'Waterproof and easy-to-maintain PVC panels.', 'Available', None),
        ('Decorative Ceiling Panels', 'decorative-ceiling-panels', 'ceiling-products', 'Designer panels for premium interiors.', 'Available', None),
        ('GI Channel', 'gi-channel', 'accessories', 'Galvanized iron channels for framing.', 'Available', None),
        ('Metal Stud', 'metal-stud', 'accessories', 'Light gauge steel studs for partitions.', 'Available', None),
        ('Ceiling Channel', 'ceiling-channel', 'accessories', 'Main and cross channels for false ceilings.', 'Available', None),
        ('Corner Bead', 'corner-bead', 'accessories', 'Protective corner reinforcement.', 'Available', None),
        ('Screws', 'screws', 'accessories', 'Drywall screws for secure fixing.', 'Available', None),
        ('Joint Tape', 'joint-tape', 'accessories', 'Paper or fiberglass joint tape.', 'Available', None),
        ('Joint Compound', 'joint-compound', 'accessories', 'Finishing compound for seamless joints.', 'Available', None),
        ('Insulation Materials', 'insulation-materials', 'accessories', 'Thermal and acoustic insulation.', 'Available', None),
    ]
    product_images = {
        'gypsum-board': 'https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=600&h=400&fit=crop',
        'moisture-resistant-gypsum-board': 'https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=600&h=400&fit=crop',
        'fire-resistant-gypsum-board': 'https://images.unsplash.com/photo-1541888946425-d81bb19240f5?w=600&h=400&fit=crop',
        'acoustic-gypsum-board': 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=600&h=400&fit=crop',
        'false-ceiling': 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=600&h=400&fit=crop',
        'gypsum-ceiling': 'https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=600&h=400&fit=crop',
        'pvc-ceiling': 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600&h=400&fit=crop',
        'decorative-ceiling-panels': 'https://images.unsplash.com/photo-1600573472592-401b489a3cdc?w=600&h=400&fit=crop',
        'gi-channel': 'https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?w=600&h=400&fit=crop',
        'metal-stud': 'https://images.unsplash.com/photo-1581094794329-c8112a89af12?w=600&h=400&fit=crop',
        'ceiling-channel': 'https://images.unsplash.com/photo-1504328345606-18bbc8c9d7d1?w=600&h=400&fit=crop',
        'corner-bead': 'https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=600&h=400&fit=crop',
        'screws': 'https://images.unsplash.com/photo-1563453397534-6e041f96d3d6?w=600&h=400&fit=crop',
        'joint-tape': 'https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=600&h=400&fit=crop',
        'joint-compound': 'https://images.unsplash.com/photo-1589939705384-5185137a7f0f?w=600&h=400&fit=crop',
        'insulation-materials': 'https://images.unsplash.com/photo-1621905251189-08b45d6a269e?w=600&h=400&fit=crop',
    }
    for name, slug, cat_slug, desc, stock, price in products_data:
        p = Product(
            name=name, slug=slug, category_id=cat_objs[cat_slug].id,
            short_description=desc, description=desc + ' High quality materials sourced for Nepalese climate and construction standards.',
            specifications='Standard sizes available. Contact for bulk pricing.',
            stock_status=stock, price=price, price_display='Request Price' if not price else f'Rs. {price}',
            is_featured=True if 'Board' in name or 'Ceiling' in name else False
        )
        db.session.add(p)
        db.session.flush()
        img_url = product_images.get(slug, 'https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=600&h=400&fit=crop')
        db.session.add(ProductImage(product_id=p.id, image_url=img_url, is_primary=True, alt_text=name))
    
    # Services
    services_data = [
        ('Gypsum Ceiling Installation', 'gypsum-ceiling-installation', 'Professional gypsum ceiling installation for residential and commercial spaces.', 'Quality materials\nSkilled technicians\nTimely completion\nClean site finish'),
        ('False Ceiling Installation', 'false-ceiling-installation', 'Modern false ceiling solutions with customized designs and lighting.', 'Custom designs\nLED integration\nAcoustic options\nPremium finishes'),
        ('Gypsum Partition', 'gypsum-partition', 'Professional gypsum wall and partition installation.', 'Lightweight\nFire resistant options\nSound insulation\nQuick installation'),
        ('Interior Ceiling Design', 'interior-ceiling-design', 'Custom ceiling designs according to room size and customer requirements.', '3D concepts\nMaterial selection\nLighting plans\nBudget optimization'),
        ('Repair & Renovation', 'repair-renovation', 'Repair, replacement and renovation of existing ceiling systems.', 'Damage assessment\nMatching materials\nMinimal disruption\nWarranty support'),
        ('Site Measurement', 'site-measurement', 'On-site measurement and consultation before installation.', 'Free consultation\nAccurate measurements\nMaterial estimation\nDesign advice'),
    ]
    service_images = {
        'gypsum-ceiling-installation': 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=600&h=400&fit=crop',
        'false-ceiling-installation': 'https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=600&h=400&fit=crop',
        'gypsum-partition': 'https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=600&h=400&fit=crop',
        'interior-ceiling-design': 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600&h=400&fit=crop',
        'repair-renovation': 'https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=600&h=400&fit=crop',
        'site-measurement': 'https://images.unsplash.com/photo-1581094794329-c8112a89af12?w=600&h=400&fit=crop',
    }
    for title, slug, short, features in services_data:
        s = Service(
            title=title, slug=slug, short_description=short, description=short, features=features,
            image_url=service_images.get(slug, 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=600&h=400&fit=crop')
        )
        db.session.add(s)
    
    # Projects
    projects_data = [
        ('Modern Office Ceiling - Thamel', 'modern-office-thamel', 'Office', 'Thamel, Kathmandu', 'Complete false ceiling with LED integration for a corporate office.'),
        ('Residential Gypsum Ceiling - Lalitpur', 'residential-lalitpur', 'Residential', 'Lalitpur', 'Elegant gypsum ceiling design for a modern home.'),
        ('Hotel Lobby Ceiling - Pokhara', 'hotel-lobby-pokhara', 'Hotel', 'Pokhara', 'Premium decorative ceiling for boutique hotel lobby.'),
        ('Restaurant False Ceiling - Baneshwor', 'restaurant-baneshwor', 'Restaurant', 'Baneshwor, Kathmandu', 'Acoustic and aesthetic false ceiling solution.'),
        ('School Auditorium - Bhaktapur', 'school-auditorium-bhaktapur', 'School', 'Bhaktapur', 'Fire-resistant and acoustic ceiling system.'),
        ('Commercial Shop Fit-out - New Road', 'shop-new-road', 'Shop', 'New Road, Kathmandu', 'Quick-install PVC and gypsum combination ceiling.'),
    ]
    project_images = [
        'https://images.unsplash.com/photo-1497366216548-37526070297c?w=600&h=400&fit=crop',
        'https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=600&h=400&fit=crop',
        'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600&h=400&fit=crop',
        'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=600&h=400&fit=crop',
        'https://images.unsplash.com/photo-1580582932707-520aed937b7b?w=600&h=400&fit=crop',
        'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=600&h=400&fit=crop',
    ]
    for i, (title, slug, cat, loc, desc) in enumerate(projects_data):
        p = Project(title=title, slug=slug, category=cat, location=loc, description=desc,
                    materials_used='Gypsum Board, GI Channels, Joint Compound', is_featured=True,
                    cover_image=project_images[i % len(project_images)])
        db.session.add(p)
    
    # Pricing
    pricing_data = [
        ('Gypsum Board', 45, 80),
        ('False Ceiling', 55, 100),
        ('PVC Ceiling', 35, 60),
        ('Custom Design', 80, 150),
    ]
    for mat, mat_p, inst_p in pricing_data:
        pr = Pricing(material_type=mat, material_price_per_sqft=mat_p, installation_price_per_sqft=inst_p)
        db.session.add(pr)
    
    # Site settings
    defaults = {
        'business_name': 'Urlabari Interior Decor',
        'tagline': 'Premium Gypsum & Ceiling Solutions',
        'phone': '+977 981-1348243',
        'whatsapp': '9779811348243',
        'email': 'info@urlabariinterior.com',
        'address': 'Urlabari, Morang, Nepal',
        'opening_hours': 'Sun - Fri: 9:00 AM - 6:00 PM',
        'hero_title': 'Premium Gypsum & Ceiling Solutions',
        'hero_subtitle': 'Quality materials, professional installation and modern ceiling solutions for homes, offices and commercial spaces.',
        'hero_image': '',
        'stat_projects': '500+',
        'stat_customers': '100+',
        'stat_years': '5+',
        'stat_support': '100%',
        'about_who': 'Professional gypsum and ceiling material supplier and installation service provider based in Nepal. Serving Urlabari and surrounding areas.',
        'about_mission': 'Provide quality materials, professional workmanship and reliable customer service.',
    }
    for k, v in defaults.items():
        db.session.add(SiteSetting(setting_key=k, value=v))
    
    db.session.commit()
    print('Database seeded successfully.')

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
