"""Image upload helper — Cloudinary preferred, /tmp fallback on Vercel."""
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app, url_for


def allowed_file(filename):
    if not filename or '.' not in filename:
        return False
    return filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_EXTENSIONS', set())


def save_image(file, folder='uploads'):
    """
    Save uploaded image.
    1. Cloudinary if USE_CLOUDINARY=true and credentials set
    2. Local static/uploads if writable
    3. /tmp/zypsom_uploads on read-only FS (Vercel) — ephemeral but works
    Returns public URL string or None.
    """
    if not file or not getattr(file, 'filename', None) or file.filename == '':
        return None
    if not allowed_file(file.filename):
        return None

    use_cloudinary = (
        current_app.config.get('USE_CLOUDINARY')
        and current_app.config.get('CLOUDINARY_CLOUD_NAME')
        and current_app.config.get('CLOUDINARY_API_KEY')
    )

    if use_cloudinary:
        try:
            import cloudinary
            import cloudinary.uploader
            cloudinary.config(
                cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
                api_key=current_app.config['CLOUDINARY_API_KEY'],
                api_secret=current_app.config['CLOUDINARY_API_SECRET'],
            )
            result = cloudinary.uploader.upload(
                file,
                folder=f"zypsom/{folder}",
                resource_type='image',
            )
            return result.get('secure_url')
        except Exception as e:
            current_app.logger.error(f'Cloudinary upload failed: {e}')
            # fall through to local/tmp

    filename = secure_filename(file.filename)
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    filename = f'{timestamp}_{filename}'

    # Try configured upload folder
    upload_root = current_app.config.get('UPLOAD_FOLDER')
    target_dir = os.path.join(upload_root, folder) if upload_root else None

    if target_dir:
        try:
            os.makedirs(target_dir, exist_ok=True)
            filepath = os.path.join(target_dir, filename)
            file.seek(0)
            file.save(filepath)
            return f'/static/uploads/{folder}/{filename}'
        except OSError as e:
            current_app.logger.warning(f'Local upload failed ({e}), trying /tmp')

    # Vercel read-only: use /tmp (works but files don't persist across cold starts)
    tmp_dir = os.path.join('/tmp', 'zypsom_uploads', folder)
    try:
        os.makedirs(tmp_dir, exist_ok=True)
        filepath = os.path.join(tmp_dir, filename)
        file.seek(0)
        file.save(filepath)
        return f'/media/{folder}/{filename}'
    except Exception as e:
        current_app.logger.error(f'Tmp upload failed: {e}')
        return None
