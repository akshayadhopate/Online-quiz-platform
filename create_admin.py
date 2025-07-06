from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# Minimal setup to bypass circular import
app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///quiz_platform.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Redefine User model directly here
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="USER")

with app.app_context():
    db.create_all()

    email = "admin@example.com"
    password = "admin123"

    existing_admin = User.query.filter_by(email=email).first()
    if existing_admin:
        print("Admin already exists.")
    else:
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        admin = User(email=email, password=hashed_password, role="ADMIN")
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user created: {email}")
