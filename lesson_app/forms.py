from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, ValidationError
from lesson_app.models import User

class LoginForm(FlaskForm):
    username = StringField('שם משתמש', validators=[DataRequired()])
    password = PasswordField('סיסמה', validators=[DataRequired()])
    remember_me = BooleanField('זכור אותי')
    submit = SubmitField('התחבר')

class RegistrationForm(FlaskForm):
    username = StringField('שם משתמש חדש', validators=[DataRequired()])
    password = PasswordField('סיסמה חדשה', validators=[DataRequired()])
    password2 = PasswordField(
        'הזן סיסמה שוב', validators=[DataRequired(), EqualTo('password', message='הסיסמאות חייבות להיות זהות')])
    submit = SubmitField('הוסף מאמן')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('שם המשתמש הזה כבר קיים. אנא בחר שם אחר.')

# --- טופס חדש להוספת משחק ---
class GameForm(FlaskForm):
    category = SelectField('קטגוריה', choices=[('חימום', 'חימום'), ('עיקרי', 'עיקרי'), ('סיום', 'סיום')], validators=[DataRequired()])
    title = StringField('שם המשחק', validators=[DataRequired()])
    bullets = TextAreaField('נקודות להסבר (כל נקודה בשורה חדשה)', validators=[DataRequired()])
    image = FileField('העלה תמונה (אופציונלי)', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('הוסף משחק')