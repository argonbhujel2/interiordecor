from flask import Blueprint, request, jsonify, current_app
from models import db, Pricing, User

api_bp = Blueprint('api', __name__)

@api_bp.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json(silent=True) or {}
    try:
        length = float(data.get('length', 0))
        width = float(data.get('width', 0))
        unit = data.get('unit', 'feet')
        material = data.get('material', 'Gypsum Board')
        installation = data.get('installation', 'both')
        
        if unit == 'meter':
            length *= 3.28084
            width *= 3.28084
        
        area = length * width
        
        pricing = Pricing.query.filter_by(material_type=material, is_active=True).first()
        mat_price = pricing.material_price_per_sqft if pricing else 50
        inst_price = pricing.installation_price_per_sqft if pricing else 80
        
        material_cost = area * mat_price
        installation_cost = area * inst_price if installation == 'both' else 0
        total = material_cost + installation_cost
        
        return jsonify({
            'success': True,
            'area_sqft': round(area, 2),
            'area_display': f'{round(area, 2)} sq.ft',
            'material_cost': round(material_cost, 2),
            'installation_cost': round(installation_cost, 2),
            'total': round(total, 2),
            'material': material,
            'note': 'Estimated price only. Final price depends on site measurement, material selection and design.'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@api_bp.route('/setup', methods=['GET', 'POST'])
def setup_seed():
    """
    Seed the database with sample data.
    Empty DB: open /api/setup
    Force recreate tables: /api/setup?reset=1
    """
    force_reset = request.args.get('reset') == '1'

    try:
        if force_reset:
            db.drop_all()
            db.create_all()
        else:
            db.create_all()
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Database connection/schema failed: {e}',
            'hint': 'Check DATABASE_URL. Try /api/setup?reset=1 to recreate all tables.'
        }), 500

    try:
        has_users = User.query.first() is not None
    except Exception as e:
        # Schema mismatch — force recreate
        try:
            db.drop_all()
            db.create_all()
            has_users = False
        except Exception as e2:
            return jsonify({
                'success': False,
                'error': f'Cannot fix schema: {e2}',
                'original': str(e)
            }), 500

    if has_users and not force_reset:
        from models import Product, Service, Project
        return jsonify({
            'success': True,
            'message': 'Database already has data. Use /api/setup?reset=1 to wipe and re-seed.',
            'products': Product.query.count(),
            'services': Service.query.count(),
            'projects': Project.query.count(),
            'admin': '/admin'
        })

    try:
        from app import seed_data
        # If force reset, users were wiped so seed will run
        seed_data(current_app)
        from models import Product, Service, Project
        return jsonify({
            'success': True,
            'message': 'Database seeded successfully!',
            'products': Product.query.count(),
            'services': Service.query.count(),
            'projects': Project.query.count(),
            'admin_url': '/admin',
            'login': 'admin / ChangeMe123! (or ADMIN_PASSWORD env)',
            'next': 'Refresh the homepage.'
        })
    except Exception as e:
        # On seed failure due to schema, try full reset once
        err = str(e)
        if 'UndefinedColumn' in err or 'does not exist' in err or 'column' in err.lower():
            try:
                db.drop_all()
                db.create_all()
                from app import seed_data
                seed_data(current_app)
                from models import Product, Service, Project
                return jsonify({
                    'success': True,
                    'message': 'Tables recreated and database seeded successfully!',
                    'products': Product.query.count(),
                    'services': Service.query.count(),
                    'projects': Project.query.count(),
                    'admin_url': '/admin',
                    'login': 'admin / ChangeMe123!'
                })
            except Exception as e2:
                return jsonify({'success': False, 'error': str(e2), 'original': err}), 500
        return jsonify({
            'success': False,
            'error': err,
            'hint': 'Try https://your-site.vercel.app/api/setup?reset=1'
        }), 500


@api_bp.route('/status', methods=['GET'])
def status():
    """Health check."""
    try:
        users = User.query.count()
        from models import Product, Service, Project
        return jsonify({
            'ok': True,
            'users': users,
            'products': Product.query.count(),
            'services': Service.query.count(),
            'projects': Project.query.count(),
            'seeded': users > 0
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e),
            'hint': 'Try /api/setup?reset=1 to recreate tables.'
        }), 500
