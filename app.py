from flask import Flask
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from mongoengine import connect
from dotenv import load_dotenv
import os
from datetime import timedelta
from routes.admin_routes import admin_bp

# Load environment variables from .env
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# JWT configuration
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

# Initialize extensions
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Connect to MongoDB
connect(host=os.getenv("MONGODB_URI"))

# Register blueprints (ensure these files are created)
try:
    from routes.auth_routes import auth_bp
    from routes.wallet_routes import wallet_bp
    from routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(wallet_bp, url_prefix="/wallet")
    app.register_blueprint(admin_bp, url_prefix="/admin")
except ImportError as e:
    print(f"Blueprint import error: {e}")
    print("Make sure all route files (auth_routes, wallet_routes, admin_routes) exist.")

# Root route for basic health check
@app.route("/")
def home():
    return {"message": "Digital Wallet System API is running."}, 200

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
