from flask import Blueprint, render_template, redirect, url_for, flash, request, session
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

@quiz_bp.route("/quizzes")
@login_required
def available_quizzes():
    quizzes = Quiz.query.all()
    return render_template("quiz_list.html", quizzes=quizzes)

@quiz_bp.route("/quiz/<int:quiz_id>/take", methods=["GET", "POST"])
@login_required
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if not quiz.questions:
        flash("This quiz has no questions yet.", "danger")
        return redirect(url_for("quiz.available_quizzes"))

    # Initialize session for answers and question index
    if "quiz_answers" not in session or session["quiz_id"] != quiz_id:
        session["quiz_id"] = quiz_id
        session["quiz_answers"] = {}
        session["current_question"] = 0
        session["timer_start"] = 0  # Placeholder for timer (seconds)

    current_question_index = session["current_question"]
    questions = quiz.questions
    if current_question_index >= len(questions):
        return redirect(url_for("quiz.submit_quiz", quiz_id=quiz_id))

    question = questions[current_question_index]

    if request.method == "POST":
        answer = request.form.get("answer")
        if answer:
            session["quiz_answers"][str(question.id)] = answer
            session["current_question"] += 1
            session.modified = True
        if "next" in request.form and session["current_question"] < len(questions):
            return redirect(url_for("quiz.take_quiz", quiz_id=quiz_id))
        elif "submit" in request.form:
            return redirect(url_for("quiz.submit_quiz", quiz_id=quiz_id))

    return render_template(
        "take_quiz.html",
        quiz=quiz,
        question=question,
        question_number=current_question_index + 1,
        total_questions=len(questions)
    )

@quiz_bp.route("/quiz/<int:quiz_id>/submit")
@login_required
def submit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    answers = session.get("quiz_answers", {})
    session.pop("quiz_answers", None)
    session.pop("quiz_id", None)
    session.pop("current_question", None)
    session.pop("timer_start", None)
    return render_template("quiz_submitted.html", quiz=quiz)

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