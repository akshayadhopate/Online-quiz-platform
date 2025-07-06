from flask import Flask
from app.routes.main import main_bp

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "your-secret-key"  # Change in production

    # Register Blueprints
    app.register_blueprint(main_bp)

    return app