from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from app import db
from app.models import Quiz, Question, Attempt, User
from app.forms import QuizForm, QuestionForm
from datetime import datetime
from sqlalchemy.sql import func

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
    page = request.args.get("page", 1, type=int)
    quizzes = Quiz.query.filter_by(created_by=current_user.id).paginate(page=page, per_page=5)
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
            category=form.category.data,
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
            options=[form.option1.data, form.option2.data, form.option3.data, form.option4.data] if form.type.data == "MCQ" else None,
            correct_answer=form.correct_answer.data
        )
        db.session.add(question)
        db.session.commit()
        flash("Question added successfully!", "success")
        return redirect(url_for("quiz.list_questions", quiz_id=quiz.id))
    return render_template("admin_question_create.html", form=form, quiz=quiz)


@quiz_bp.route("/quizzes")
@login_required
def available_quizzes():
    page = request.args.get("page", 1, type=int)
    category = request.args.get("category", None)
    query = Quiz.query
    if category:
        query = query.filter_by(category=category)
    quizzes = query.paginate(page=page, per_page=5)
    categories = db.session.query(Quiz.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    return render_template("quiz_list.html", quizzes=quizzes, categories=categories)

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
    if not answers:
        flash("No answers submitted.", "danger")
        return redirect(url_for("quiz.available_quizzes"))

    # Calculate score
    score = 0
    questions = quiz.questions
    for question in questions:
        user_answer = answers.get(str(question.id))
        if user_answer and user_answer == question.correct_answer:
            score += 1

    # Store attempt
    attempt = Attempt(
        user_id=current_user.id,
        quiz_id=quiz.id,
        score=score,
        answers=answers
    )
    db.session.add(attempt)
    db.session.commit()

    # Clear session
    session.pop("quiz_answers", None)
    session.pop("quiz_id", None)
    session.pop("current_question", None)
    session.pop("timer_start", None)

    return redirect(url_for("quiz.view_results", attempt_id=attempt.id))

@quiz_bp.route("/results/<int:attempt_id>")
@login_required
def view_results(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    if attempt.user_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("main.home"))
    quiz = attempt.quiz
    questions = quiz.questions
    return render_template("results.html", attempt=attempt, quiz=quiz, questions=questions)

@quiz_bp.route("/leaderboard")
@login_required
def leaderboard():
    quiz_id = request.args.get("quiz_id", type=int)
    if quiz_id:
        leaderboard_data = db.session.query(
            User.email,
            Attempt.score,
            func.max(Attempt.timestamp).label("latest")
        ).join(Attempt).filter(Attempt.quiz_id == quiz_id).group_by(User.id).order_by(Attempt.score.desc()).limit(10).all()
        quiz = Quiz.query.get_or_404(quiz_id)
        title = f"Leaderboard for {quiz.title}"
    else:
        leaderboard_data = db.session.query(
            User.email,
            func.sum(Attempt.score).label("total_score")
        ).join(Attempt).group_by(User.id).order_by(func.sum(Attempt.score).desc()).limit(10).all()
        title = "Overall Leaderboard"
    return render_template("leaderboard.html", leaderboard_data=leaderboard_data, title=title)

# from flask import Blueprint, render_template, redirect, url_for, flash, request, session
# from flask_login import login_required, current_user
# from app import db
# from app.models import Quiz, Question, Attempt
# from app.forms import QuizForm, QuestionForm
# from datetime import datetime

# quiz_bp = Blueprint("quiz", __name__)

# def admin_required(func):
#     def wrapper(*args, **kwargs):
#         if not current_user.is_authenticated or current_user.role != "ADMIN":
#             flash("Access denied. Admins only.", "danger")
#             return redirect(url_for("main.home"))
#         return func(*args, **kwargs)
#     wrapper.__name__ = func.__name__
#     return wrapper

# @quiz_bp.route("/admin/quizzes")
# @login_required
# @admin_required
# def list_quizzes():
#     quizzes = Quiz.query.filter_by(created_by=current_user.id).all()
#     return render_template("admin_quiz_list.html", quizzes=quizzes)

# @quiz_bp.route("/admin/quiz/create", methods=["GET", "POST"])
# @login_required
# @admin_required
# def create_quiz():
#     form = QuizForm()
#     if form.validate_on_submit():
#         quiz = Quiz(
#             title=form.title.data,
#             description=form.description.data,
#             created_by=current_user.id
#         )
#         db.session.add(quiz)
#         db.session.commit()
#         flash("Quiz created successfully!", "success")
#         return redirect(url_for("quiz.list_quizzes"))
#     return render_template("admin_quiz_create.html", form=form)

# @quiz_bp.route("/admin/quiz/<int:quiz_id>/questions")
# @login_required
# @admin_required
# def list_questions(quiz_id):
#     quiz = Quiz.query.get_or_404(quiz_id)
#     if quiz.created_by != current_user.id:
#         flash("Access denied.", "danger")
#         return redirect(url_for("quiz.list_quizzes"))
#     return render_template("admin_question_list.html", quiz=quiz)

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
#             options=[form.option1.data, form.option2.data, form.option3.data, form.option4.data]
#             if form.type.data == "MCQ"
#             else None,
#             correct_answer=form.correct_answer.data
#         )
#         db.session.add(question)
#         db.session.commit()
#         flash("Question added successfully!", "success")
#         return redirect(url_for("quiz.list_questions", quiz_id=quiz.id))
    
#     # 👇 Add this block to catch validation issues
#     elif request.method == "POST":
#         print("Form validation failed:", form.errors)
#         flash("Please fix the errors in the form.", "danger")

#     return render_template("admin_question_create.html", form=form, quiz=quiz)

# @quiz_bp.route("/quizzes")
# @login_required
# def available_quizzes():
#     quizzes = Quiz.query.all()
#     return render_template("quiz_list.html", quizzes=quizzes)

# @quiz_bp.route("/quiz/<int:quiz_id>/take", methods=["GET", "POST"])
# @login_required
# def take_quiz(quiz_id):
#     quiz = Quiz.query.get_or_404(quiz_id)
#     if not quiz.questions:
#         flash("This quiz has no questions yet.", "danger")
#         return redirect(url_for("quiz.available_quizzes"))

#     # Initialize session for answers and question index
#     if "quiz_answers" not in session or session["quiz_id"] != quiz_id:
#         session["quiz_id"] = quiz_id
#         session["quiz_answers"] = {}
#         session["current_question"] = 0
#         session["timer_start"] = 0  # Placeholder for timer (seconds)

#     current_question_index = session["current_question"]
#     questions = quiz.questions
#     if current_question_index >= len(questions):
#         return redirect(url_for("quiz.submit_quiz", quiz_id=quiz_id))

#     question = questions[current_question_index]

#     if request.method == "POST":
#         answer = request.form.get("answer")
#         if answer:
#             session["quiz_answers"][str(question.id)] = answer
#             session["current_question"] += 1
#             session.modified = True
#         if "next" in request.form and session["current_question"] < len(questions):
#             return redirect(url_for("quiz.take_quiz", quiz_id=quiz_id))
#         elif "submit" in request.form:
#             return redirect(url_for("quiz.submit_quiz", quiz_id=quiz_id))

#     return render_template(
#         "take_quiz.html",
#         quiz=quiz,
#         question=question,
#         question_number=current_question_index + 1,
#         total_questions=len(questions)
#     )

# @quiz_bp.route("/quiz/<int:quiz_id>/submit")
# @login_required
# def submit_quiz(quiz_id):
#     quiz = Quiz.query.get_or_404(quiz_id)
#     answers = session.get("quiz_answers", {})
#     if not answers:
#         flash("No answers submitted.", "danger")
#         return redirect(url_for("quiz.available_quizzes"))

#     # Calculate score
#     score = 0
#     questions = quiz.questions
#     for question in questions:
#         user_answer = answers.get(str(question.id))
#         if user_answer and user_answer == question.correct_answer:
#             score += 1

#     # Store attempt
#     attempt = Attempt(
#         user_id=current_user.id,
#         quiz_id=quiz.id,
#         score=score,
#         answers=answers
#     )
#     db.session.add(attempt)
#     db.session.commit()

#     # Clear session
#     session.pop("quiz_answers", None)
#     session.pop("quiz_id", None)
#     session.pop("current_question", None)
#     session.pop("timer_start", None)

#     return redirect(url_for("quiz.view_results", attempt_id=attempt.id))

# @quiz_bp.route("/results/<int:attempt_id>")
# @login_required
# def view_results(attempt_id):
#     attempt = Attempt.query.get_or_404(attempt_id)
#     if attempt.user_id != current_user.id:
#         flash("Access denied.", "danger")
#         return redirect(url_for("main.home"))
#     quiz = attempt.quiz
#     questions = quiz.questions
#     return render_template("results.html", attempt=attempt, quiz=quiz, questions=questions)

# @quiz_bp.route("/quiz/<int:quiz_id>/submit")
# @login_required
# def submit_quiz(quiz_id):
#     quiz = Quiz.query.get_or_404(quiz_id)
#     answers = session.get("quiz_answers", {})
#     session.pop("quiz_answers", None)
#     session.pop("quiz_id", None)
#     session.pop("current_question", None)
#     session.pop("timer_start", None)
#     return render_template("quiz_submitted.html", quiz=quiz)

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