# backend/main.py
import os
from app import create_app

# WSGI entry point
app = create_app()

if __name__ == "__main__":
    # Port 8005 for SCM backend to avoid conflicts
    port = int(os.getenv("PORT", "8005"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
