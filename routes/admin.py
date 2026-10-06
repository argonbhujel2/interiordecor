from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Product, ProductCategory, ProductImage, Service, Project, ProjectImage, QuoteRequest, ContactMessage, Pricing, SiteSetting
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import re

admin_bp = Blueprint('admin', __name__)

def slugify(text):
    text = str(text).lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text

from utils.uploads import save_image, allowed_file

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@login_required
def dashboard():
    stats = {
        'products': Product.query.count(),
        'services': Service.query.count(),
        'projects': Project.query.count(),
        'quotes_new': QuoteRequest.query.filter_by(status='New').count(),
        'quotes_total': QuoteRequest.query.count(),
        'messages_unread': ContactMessage.query.filter_by(is_read=False).count(),
        'messages_total': ContactMessage.query.count(),
    }
    recent_quotes = QuoteRequest.query.order_by(QuoteRequest.created_at.desc()).limit(5).all()
    recent_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats, recent_quotes=recent_quotes, recent_messages=recent_messages)

# ===== PRODUCTS =====
@admin_bp.route('/products')
@login_required
def products():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin/products.html', products=products)

@admin_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
def product_add():
    categories = ProductCategory.query.all()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        slug = slugify(request.form.get('slug') or name)
        p = Product(
            name=name, slug=slug,
            category_id=int(request.form.get('category_id') or 0) or None,
            short_description=request.form.get('short_description', ''),
            description=request.form.get('description', ''),
            specifications=request.form.get('specifications', ''),
            applications=request.form.get('applications', ''),
            available_sizes=request.form.get('available_sizes', ''),
            price=float(request.form.get('price') or 0) or None,
            price_display=request.form.get('price_display', 'Request Price'),
            stock_status=request.form.get('stock_status', 'Available'),
            is_featured=request.form.get('is_featured') == 'on',
            is_active=request.form.get('is_active') == 'on',
        )
        db.session.add(p)
        db.session.flush()
        if 'image' in request.files:
            url = save_image(request.files['image'], 'products')
            if url:
                img = ProductImage(product_id=p.id, image_url=url, is_primary=True, alt_text=name)
                db.session.add(img)
        db.session.commit()
        flash('Product added.', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', product=None, categories=categories)

@admin_bp.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def product_edit(id):
    product = Product.query.get_or_404(id)
    categories = ProductCategory.query.all()
    if request.method == 'POST':
        product.name = request.form.get('name', '').strip()
        product.slug = slugify(request.form.get('slug') or product.name)
        product.category_id = int(request.form.get('category_id') or 0) or None
        product.short_description = request.form.get('short_description', '')
        product.description = request.form.get('description', '')
        product.specifications = request.form.get('specifications', '')
        product.applications = request.form.get('applications', '')
        product.available_sizes = request.form.get('available_sizes', '')
        product.price = float(request.form.get('price') or 0) or None
        product.price_display = request.form.get('price_display', 'Request Price')
        product.stock_status = request.form.get('stock_status', 'Available')
        product.is_featured = request.form.get('is_featured') == 'on'
        product.is_active = request.form.get('is_active') == 'on'
        if 'image' in request.files and request.files['image'].filename:
            url = save_image(request.files['image'], 'products')
            if url:
                for img in product.images:
                    img.is_primary = False
                img = ProductImage(product_id=product.id, image_url=url, is_primary=True, alt_text=product.name)
                db.session.add(img)
        db.session.commit()
        flash('Product updated.', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', product=product, categories=categories)

@admin_bp.route('/products/<int:id>/delete', methods=['POST'])
@login_required
def product_delete(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted.', 'success')
    return redirect(url_for('admin.products'))

# ===== SERVICES =====
@admin_bp.route('/services')
@login_required
def services():
    services = Service.query.order_by(Service.sort_order).all()
    return render_template('admin/services.html', services=services)

@admin_bp.route('/services/add', methods=['GET', 'POST'])
@login_required
def service_add():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        s = Service(
            title=title, slug=slugify(request.form.get('slug') or title),
            short_description=request.form.get('short_description', ''),
            description=request.form.get('description', ''),
            features=request.form.get('features', ''),
            is_active=request.form.get('is_active') == 'on',
        )
        if 'image' in request.files:
            s.image_url = save_image(request.files['image'], 'services')
        db.session.add(s)
        db.session.commit()
        flash('Service added.', 'success')
        return redirect(url_for('admin.services'))
    return render_template('admin/service_form.html', service=None)

@admin_bp.route('/services/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def service_edit(id):
    service = Service.query.get_or_404(id)
    if request.method == 'POST':
        service.title = request.form.get('title', '').strip()
        service.slug = slugify(request.form.get('slug') or service.title)
        service.short_description = request.form.get('short_description', '')
        service.description = request.form.get('description', '')
        service.features = request.form.get('features', '')
        service.is_active = request.form.get('is_active') == 'on'
        if 'image' in request.files and request.files['image'].filename:
            service.image_url = save_image(request.files['image'], 'services')
        db.session.commit()
        flash('Service updated.', 'success')
        return redirect(url_for('admin.services'))
    return render_template('admin/service_form.html', service=service)

@admin_bp.route('/services/<int:id>/delete', methods=['POST'])
@login_required
def service_delete(id):
    service = Service.query.get_or_404(id)
    db.session.delete(service)
    db.session.commit()
    flash('Service deleted.', 'success')
    return redirect(url_for('admin.services'))

# ===== PROJECTS =====
@admin_bp.route('/projects')
@login_required
def projects():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('admin/projects.html', projects=projects)

@admin_bp.route('/projects/add', methods=['GET', 'POST'])
@login_required
def project_add():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        p = Project(
            title=title, slug=slugify(request.form.get('slug') or title),
            category=request.form.get('category', ''),
            location=request.form.get('location', ''),
            description=request.form.get('description', ''),
            materials_used=request.form.get('materials_used', ''),
            is_featured=request.form.get('is_featured') == 'on',
            is_active=request.form.get('is_active') == 'on',
        )
        if request.form.get('completion_date'):
            p.completion_date = datetime.strptime(request.form.get('completion_date'), '%Y-%m-%d').date()
        if 'cover_image' in request.files:
            p.cover_image = save_image(request.files['cover_image'], 'projects')
        db.session.add(p)
        db.session.commit()
        flash('Project added.', 'success')
        return redirect(url_for('admin.projects'))
    return render_template('admin/project_form.html', project=None)

@admin_bp.route('/projects/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def project_edit(id):
    project = Project.query.get_or_404(id)
    if request.method == 'POST':
        project.title = request.form.get('title', '').strip()
        project.slug = slugify(request.form.get('slug') or project.title)
        project.category = request.form.get('category', '')
        project.location = request.form.get('location', '')
        project.description = request.form.get('description', '')
        project.materials_used = request.form.get('materials_used', '')
        project.is_featured = request.form.get('is_featured') == 'on'
        project.is_active = request.form.get('is_active') == 'on'
        if request.form.get('completion_date'):
            project.completion_date = datetime.strptime(request.form.get('completion_date'), '%Y-%m-%d').date()
        if 'cover_image' in request.files and request.files['cover_image'].filename:
            project.cover_image = save_image(request.files['cover_image'], 'projects')
        db.session.commit()
        flash('Project updated.', 'success')
        return redirect(url_for('admin.projects'))
    return render_template('admin/project_form.html', project=project)

@admin_bp.route('/projects/<int:id>/delete', methods=['POST'])
@login_required
def project_delete(id):
    project = Project.query.get_or_404(id)
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted.', 'success')
    return redirect(url_for('admin.projects'))

# ===== QUOTES =====
@admin_bp.route('/quotes')
@login_required
def quotes():
    status = request.args.get('status')
    q = QuoteRequest.query
    if status:
        q = q.filter_by(status=status)
    quotes = q.order_by(QuoteRequest.created_at.desc()).all()
    return render_template('admin/quotes.html', quotes=quotes, active_status=status)

@admin_bp.route('/quotes/<int:id>', methods=['GET', 'POST'])
@login_required
def quote_detail(id):
    quote = QuoteRequest.query.get_or_404(id)
    if request.method == 'POST':
        quote.status = request.form.get('status', quote.status)
        quote.internal_notes = request.form.get('internal_notes', '')
        db.session.commit()
        flash('Quote updated.', 'success')
        return redirect(url_for('admin.quote_detail', id=id))
    return render_template('admin/quote_detail.html', quote=quote)

# ===== MESSAGES =====
@admin_bp.route('/messages')
@login_required
def messages():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin/messages.html', messages=messages)

@admin_bp.route('/messages/<int:id>/read', methods=['POST'])
@login_required
def message_read(id):
    msg = ContactMessage.query.get_or_404(id)
    msg.is_read = True
    db.session.commit()
    return redirect(url_for('admin.messages'))

@admin_bp.route('/messages/<int:id>/delete', methods=['POST'])
@login_required
def message_delete(id):
    msg = ContactMessage.query.get_or_404(id)
    db.session.delete(msg)
    db.session.commit()
    flash('Message deleted.', 'success')
    return redirect(url_for('admin.messages'))

# ===== PRICING =====
@admin_bp.route('/pricing', methods=['GET', 'POST'])
@login_required
def pricing():
    if request.method == 'POST':
        for key in request.form:
            if key.startswith('mat_'):
                pid = int(key.split('_')[1])
                p = Pricing.query.get(pid)
                if p:
                    p.material_price_per_sqft = float(request.form.get(f'mat_{pid}') or 0)
                    p.installation_price_per_sqft = float(request.form.get(f'inst_{pid}') or 0)
        db.session.commit()
        flash('Pricing updated.', 'success')
        return redirect(url_for('admin.pricing'))
    pricing = Pricing.query.all()
    return render_template('admin/pricing.html', pricing=pricing)

# ===== SETTINGS =====
@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        keys = ['business_name', 'tagline', 'phone', 'whatsapp', 'email', 'address', 'opening_hours',
                'facebook', 'instagram', 'tiktok', 'youtube', 'hero_title', 'hero_subtitle',
                'stat_projects', 'stat_customers', 'stat_years', 'stat_support', 'about_who', 'about_mission']
        for k in keys:
            val = request.form.get(k, '')
            s = SiteSetting.query.filter_by(setting_key=k).first()
            if s:
                s.value = val
            else:
                db.session.add(SiteSetting(setting_key=k, value=val))
        # Hero image upload
        if 'hero_image' in request.files and request.files['hero_image'].filename:
            try:
                url = save_image(request.files['hero_image'], 'hero')
            except Exception as e:
                current_app.logger.error(f'Hero upload error: {e}')
                flash(f'Image upload failed: {e}. Set USE_CLOUDINARY=true for Vercel.', 'error')
                url = None
            if url:
                s = SiteSetting.query.filter_by(setting_key='hero_image').first()
                if s:
                    s.value = url
                else:
                    db.session.add(SiteSetting(setting_key='hero_image', value=url))
        # Clear hero image if requested
        if request.form.get('clear_hero_image') == 'on':
            s = SiteSetting.query.filter_by(setting_key='hero_image').first()
            if s:
                s.value = ''
        db.session.commit()
        flash('Settings saved.', 'success')
        return redirect(url_for('admin.settings'))
    settings = {s.setting_key: s.value for s in SiteSetting.query.all()}
    return render_template('admin/settings.html', settings=settings)
