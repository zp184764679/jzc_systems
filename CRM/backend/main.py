# backend/main.py
import os
from app import create_app

# WSGI entry point
app = create_app()

if __name__ == "__main__":
    # Port 8002 for CRM backend to avoid conflicts
    port = int(os.getenv("PORT", "8002"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
