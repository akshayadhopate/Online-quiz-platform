from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="USER")  # USER or ADMIN
    quizzes = db.relationship("Quiz", backref="creator", lazy=True)
    attempts = db.relationship("Attempt", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.email}>"

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    questions = db.relationship("Question", backref="quiz", lazy=True, cascade="all, delete-orphan")
    attempts = db.relationship("Attempt", backref="quiz", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Quiz {self.title}>"

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # MCQ or TRUE_FALSE
    options = db.Column(db.JSON, nullable=True)  # For MCQ: list of options
    correct_answer = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Question {self.text}>"

class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    answers = db.Column(db.JSON, nullable=False)  # {question_id: user_answer}
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<Attempt User:{self.user_id} Quiz:{self.quiz_id} Score:{self.score}>"
