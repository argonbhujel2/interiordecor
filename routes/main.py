from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from models import db, Product, ProductCategory, Service, Project, QuoteRequest, ContactMessage, Pricing, SiteSetting
from werkzeug.utils import secure_filename
import os
from datetime import datetime

main_bp = Blueprint('main', __name__)

from utils.uploads import save_image, allowed_file

@main_bp.route('/')
def home():
    products = Product.query.filter_by(is_active=True, is_featured=True).limit(6).all()
    services = Service.query.filter_by(is_active=True).order_by(Service.sort_order).limit(6).all()
    projects = Project.query.filter_by(is_active=True, is_featured=True).limit(6).all()
    return render_template('home.html', products=products, services=services, projects=projects)

@main_bp.route('/products')
def products():
    category_slug = request.args.get('category')
    q = Product.query.filter_by(is_active=True)
    if category_slug:
        cat = ProductCategory.query.filter_by(slug=category_slug).first()
        if cat:
            q = q.filter_by(category_id=cat.id)
    products = q.order_by(Product.sort_order, Product.name).all()
    categories = ProductCategory.query.filter_by(is_active=True).order_by(ProductCategory.sort_order).all()
    return render_template('products.html', products=products, categories=categories, active_category=category_slug)

@main_bp.route('/products/<slug>')
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    related = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True
    ).limit(4).all()
    return render_template('product_detail.html', product=product, related=related)

@main_bp.route('/services')
def services():
    services = Service.query.filter_by(is_active=True).order_by(Service.sort_order).all()
    return render_template('services.html', services=services)

@main_bp.route('/services/<slug>')
def service_detail(slug):
    service = Service.query.filter_by(slug=slug, is_active=True).first_or_404()
    return render_template('service_detail.html', service=service)

@main_bp.route('/projects')
def projects():
    category = request.args.get('category')
    q = Project.query.filter_by(is_active=True)
    if category:
        q = q.filter_by(category=category)
    projects = q.order_by(Project.sort_order, Project.created_at.desc()).all()
    categories = db.session.query(Project.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    return render_template('projects.html', projects=projects, categories=categories, active_category=category)

@main_bp.route('/projects/<slug>')
def project_detail(slug):
    project = Project.query.filter_by(slug=slug, is_active=True).first_or_404()
    return render_template('project_detail.html', project=project)

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        if not name or not message:
            flash('Name and message are required.', 'error')
            return redirect(url_for('main.contact'))
        msg = ContactMessage(name=name, phone=phone, email=email, message=message)
        db.session.add(msg)
        db.session.commit()
        flash('Thank you. Our team will contact you shortly.', 'success')
        return redirect(url_for('main.contact'))
    return render_template('contact.html')

@main_bp.route('/quote', methods=['GET', 'POST'])
def quote():
    if request.method == 'POST':
        photo_url = None
        if 'photo' in request.files:
            photo_url = save_image(request.files['photo'], 'quotes')
        
        qr = QuoteRequest(
            customer_name=request.form.get('customer_name', '').strip(),
            phone=request.form.get('phone', '').strip(),
            email=request.form.get('email', '').strip(),
            address=request.form.get('address', '').strip(),
            project_location=request.form.get('project_location', '').strip(),
            project_type=request.form.get('project_type', '').strip(),
            required_service=request.form.get('required_service', '').strip(),
            ceiling_type=request.form.get('ceiling_type', '').strip(),
            room_length=float(request.form.get('room_length') or 0) or None,
            room_width=float(request.form.get('room_width') or 0) or None,
            estimated_area=float(request.form.get('estimated_area') or 0) or None,
            unit=request.form.get('unit', 'feet'),
            material_preference=request.form.get('material_preference', '').strip(),
            installation_required=request.form.get('installation_required') == 'yes',
            preferred_date=datetime.strptime(request.form.get('preferred_date'), '%Y-%m-%d').date() if request.form.get('preferred_date') else None,
            budget=request.form.get('budget', '').strip(),
            message=request.form.get('message', '').strip(),
            photo_url=photo_url,
            status='New'
        )
        if not qr.customer_name or not qr.phone:
            flash('Name and phone are required.', 'error')
            return redirect(url_for('main.quote'))
        db.session.add(qr)
        db.session.commit()
        flash('Thank you. Our team will contact you shortly.', 'success')
        return redirect(url_for('main.quote'))
    
    services = Service.query.filter_by(is_active=True).all()
    return render_template('quote.html', services=services)

@main_bp.route('/calculator')
def calculator():
    pricing = {p.material_type: {'material': p.material_price_per_sqft, 'installation': p.installation_price_per_sqft} 
               for p in Pricing.query.filter_by(is_active=True).all()}
    return render_template('calculator.html', pricing=pricing)


@main_bp.route('/media/<path:filepath>')
def media_file(filepath):
    """Serve files from /tmp uploads (Vercel ephemeral storage)."""
    from flask import send_from_directory, abort
    import os
    base = os.path.join('/tmp', 'zypsom_uploads')
    full = os.path.join(base, filepath)
    if not os.path.isfile(full):
        abort(404)
    directory = os.path.dirname(full)
    filename = os.path.basename(full)
    return send_from_directory(directory, filename)

@main_bp.route('/robots.txt')
def robots():
    return current_app.send_static_file('robots.txt')

@main_bp.route('/sitemap.xml')
def sitemap():
    from flask import make_response
    products = Product.query.filter_by(is_active=True).all()
    services = Service.query.filter_by(is_active=True).all()
    projects = Project.query.filter_by(is_active=True).all()
    xml = render_template('sitemap.xml', products=products, services=services, projects=projects)
    response = make_response(xml)
    response.headers['Content-Type'] = 'application/xml'
    return response
