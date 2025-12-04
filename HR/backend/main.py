from app import create_app
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask application
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8003))
    app.run(host='0.0.0.0', port=port, debug=True)
