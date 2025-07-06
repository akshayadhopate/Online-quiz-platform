from app import create_app, db, bcrypt
from app.models import User

app = create_app()

with app.app_context():
    email = "admin@example.com"
    password = "admin123"
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    admin = User(email=email, password=hashed_password, role="ADMIN")
    db.session.add(admin)
    db.session.commit()
    print(f"Admin user created: {email}")