from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User

class RegistrationForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Register")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("Email already registered.")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")

class QuizForm(FlaskForm):
    title = StringField("Quiz Title", validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField("Description", validators=[Length(max=500)])
    submit = SubmitField("Create Quiz")

class QuestionForm(FlaskForm):
    text = TextAreaField("Question Text", validators=[DataRequired()])
    type = SelectField(
        "Question Type",
        choices=[("MCQ", "Multiple Choice"), ("TRUE_FALSE", "True/False")],
        validators=[DataRequired()],
    )
    option1 = StringField("Option 1", render_kw={"placeholder": "Required for MCQ"})
    option2 = StringField("Option 2", render_kw={"placeholder": "Required for MCQ"})
    option3 = StringField("Option 3", render_kw={"placeholder": "Required for MCQ"})
    option4 = StringField("Option 4", render_kw={"placeholder": "Required for MCQ"})
    correct_answer = StringField(
        "Correct Answer",
        validators=[DataRequired()],
        render_kw={"placeholder": "For MCQ, enter one of the options; for True/False, enter 'True' or 'False'"}
    )
    submit = SubmitField("Add Question")

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False

        if self.type.data == "MCQ":
            # Ensure all options are filled
            if not all([self.option1.data, self.option2.data, self.option3.data, self.option4.data]):
                msg = "All four options are required for MCQ."
                self.option1.errors.append(msg)
                return False

            # Correct answer must be one of the options
            if self.correct_answer.data not in [
                self.option1.data,
                self.option2.data,
                self.option3.data,
                self.option4.data,
            ]:
                self.correct_answer.errors.append("Correct answer must match one of the options.")
                return False

        elif self.type.data == "TRUE_FALSE":
            if self.correct_answer.data not in ["True", "False"]:
                self.correct_answer.errors.append("Correct answer must be 'True' or 'False' for True/False questions.")
                return False

        return True

# class QuestionForm(FlaskForm):
#     text = TextAreaField("Question Text", validators=[DataRequired()])
#     type = SelectField("Question Type", choices=[("MCQ", "Multiple Choice"), ("TRUE_FALSE", "True/False")], validators=[DataRequired()])
#     option1 = StringField("Option 1", validators=[DataRequired()], render_kw={"placeholder": "Required for MCQ"})
#     option2 = StringField("Option 2", validators=[DataRequired()], render_kw={"placeholder": "Required for MCQ"})
#     option3 = StringField("Option 3", validators=[DataRequired()], render_kw={"placeholder": "Required for MCQ"})
#     option4 = StringField("Option 4", validators=[DataRequired()], render_kw={"placeholder": "Required for MCQ"})
#     correct_answer = StringField("Correct Answer", validators=[DataRequired()], render_kw={"placeholder": "For MCQ, enter one of the options; for True/False, enter 'True' or 'False'"})
#     submit = SubmitField("Add Question")

#     def validate(self, extra_validators=None):
#         if not super().validate(extra_validators):
#             return False
#         if self.type.data == "MCQ" and self.correct_answer.data not in [self.option1.data, self.option2.data, self.option3.data, self.option4.data]:
#             self.correct_answer.errors.append("Correct answer must be one of the provided options.")
#             return False
#         if self.type.data == "TRUE_FALSE" and self.correct_answer.data not in ["True", "False"]:
#             self.correct_answer.errors.append("Correct answer must be 'True' or 'False' for True/False questions.")
#             return False
#         return True