from app import db
from app.models import User
with app.app_context():
    print(User.query.all())