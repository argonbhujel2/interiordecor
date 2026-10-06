from app import app

# For Vercel / WSGI servers
application = app

if __name__ == "__main__":
    app.run()
