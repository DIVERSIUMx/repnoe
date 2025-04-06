from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired


class UserLogin(FlaskForm):
    name = StringField("Имя пользователя", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField('Войти')


class UpdateUser(FlaskForm):
    name = StringField("Имя пользователя", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    new_password = PasswordField("Новый Пароль", validators=[DataRequired()])
    new_password_two = PasswordField(
        "Повторите Пароль", validators=[DataRequired()])
    submit = SubmitField('Изменить')
