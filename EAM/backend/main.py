# backend/main.py
import os
from app import create_app

# WSGI entry point
app = create_app()

if __name__ == "__main__":
    # Port 8008 for EAM backend
    port = int(os.getenv("PORT", "8008"))
    app.run(host="0.0.0.0", port=port, debug=True)
