# Urlabari Interior Decor — Website

Premium gypsum, false ceiling & interior materials website.

## Local (Windows)

```powershell
cd path\to\project
python -m pip install -r requirements.txt
python -m flask --app app run --debug --port 5000
```

Open http://127.0.0.1:5000  
Admin: http://127.0.0.1:5000/admin → **admin** / **ChangeMe123!**

SQLite is used automatically if `DATABASE_URL` is not set.

---

## Vercel Deploy (IMPORTANT)

**SQLite does NOT work on Vercel** (filesystem is temporary). You need a free Postgres database.

### 1. Create free Postgres (Neon)

1. Go to https://neon.tech → Sign up
2. Create a project
3. Copy the connection string (looks like):
   ```
   postgresql://user:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require
   ```

### 2. Vercel Environment Variables

In Vercel project → Settings → Environment Variables, add:

| Name | Value |
|------|-------|
| `SECRET_KEY` | any long random string |
| `DATABASE_URL` | your Neon connection string |
| `ADMIN_USERNAME` | admin |
| `ADMIN_PASSWORD` | your secure password |
| `ADMIN_EMAIL` | your email |

Optional Cloudinary:
| `USE_CLOUDINARY` | true |
| `CLOUDINARY_CLOUD_NAME` | ... |
| `CLOUDINARY_API_KEY` | ... |
| `CLOUDINARY_API_SECRET` | ... |

### 3. Redeploy

After setting env vars, Redeploy the project.

### 4. Seed the database

Visit once (replace YOUR_SECRET_KEY with the same value as SECRET_KEY):

```
https://your-site.vercel.app/api/setup?key=YOUR_SECRET_KEY
```

You should see: `{"success": true, "message": "Database seeded successfully..."}`

Then open the site — products, services, projects will appear.

Admin login: `/admin` with the credentials you set.

---

## Calculator

Works after CSRF fix. If you still see network error, hard-refresh (Ctrl+Shift+R).

## Admin

- Products / Services / Projects — CRUD + images
- Quotes & Messages
- Pricing (calculator rates)
- Settings — name, phone, WhatsApp, **hero image**, about text, stats
