from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), Length(min=3, max=25)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(), Length(min=6)
    ])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), Length(min=3, max=25)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(), Length(min=6)
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.')
    ])
    role = SelectField('Role', choices=[
        ('parent', 'Parent'),
        ('teacher', 'Teacher'),
        ('staff', 'Staff')
    ], validators=[DataRequired()])
    submit = SubmitField('Register')
