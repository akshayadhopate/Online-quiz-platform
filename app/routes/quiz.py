from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Quiz, Question
from app.forms import QuizForm, QuestionForm

quiz_bp = Blueprint("quiz", __name__)

def admin_required(func):
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "ADMIN":
            flash("Access denied. Admins only.", "danger")
            return redirect(url_for("main.home"))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@quiz_bp.route("/admin/quizzes")
@login_required
@admin_required
def list_quizzes():
    quizzes = Quiz.query.filter_by(created_by=current_user.id).all()
    return render_template("admin_quiz_list.html", quizzes=quizzes)

@quiz_bp.route("/admin/quiz/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_quiz():
    form = QuizForm()
    if form.validate_on_submit():
        quiz = Quiz(
            title=form.title.data,
            description=form.description.data,
            created_by=current_user.id
        )
        db.session.add(quiz)
        db.session.commit()
        flash("Quiz created successfully!", "success")
        return redirect(url_for("quiz.list_quizzes"))
    return render_template("admin_quiz_create.html", form=form)

@quiz_bp.route("/admin/quiz/<int:quiz_id>/questions")
@login_required
@admin_required
def list_questions(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.created_by != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("quiz.list_quizzes"))
    return render_template("admin_question_list.html", quiz=quiz)

@quiz_bp.route("/admin/quiz/<int:quiz_id>/question/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.created_by != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("quiz.list_quizzes"))

    form = QuestionForm()

    if form.validate_on_submit():
        question = Question(
            quiz_id=quiz.id,
            text=form.text.data,
            type=form.type.data,
            options=[form.option1.data, form.option2.data, form.option3.data, form.option4.data]
            if form.type.data == "MCQ"
            else None,
            correct_answer=form.correct_answer.data
        )
        db.session.add(question)
        db.session.commit()
        flash("Question added successfully!", "success")
        return redirect(url_for("quiz.list_questions", quiz_id=quiz.id))
    
    # 👇 Add this block to catch validation issues
    elif request.method == "POST":
        print("Form validation failed:", form.errors)
        flash("Please fix the errors in the form.", "danger")

    return render_template("admin_question_create.html", form=form, quiz=quiz)

# @quiz_bp.route("/admin/quiz/<int:quiz_id>/question/create", methods=["GET", "POST"])
# @login_required
# @admin_required
# def create_question(quiz_id):
#     quiz = Quiz.query.get_or_404(quiz_id)
#     if quiz.created_by != current_user.id:
#         flash("Access denied.", "danger")
#         return redirect(url_for("quiz.list_quizzes"))
#     form = QuestionForm()
#     if form.validate_on_submit():
#         question = Question(
#             quiz_id=quiz.id,
#             text=form.text.data,
#             type=form.type.data,
#             options=[form.option1.data, form.option2.data, form.option3.data, form.option4.data] if form.type.data == "MCQ" else None,
#             correct_answer=form.correct_answer.data
#         )
#         db.session.add(question)
#         db.session.commit()
#         flash("Question added successfully!", "success")
#         return redirect(url_for("quiz.list_questions", quiz_id=quiz.id))
#     return render_template("admin_question_create.html", form=form, quiz=quiz)