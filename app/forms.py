# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models import User # Импортируем модель User для проверки уникальности

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6, max=100)])
    confirm_password = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password', message='Пароли должны совпадать')])
    submit = SubmitField('Зарегистрироваться')

    # Пользовательские валидаторы для проверки уникальности имени пользователя и email
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя пользователя уже занято. Пожалуйста, выберите другое.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже зарегистрирован. Пожалуйста, используйте другой или войдите.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class BlogForm(FlaskForm):
    title = StringField('Название блога', validators=[DataRequired(), Length(min=1, max=150)])
    description = TextAreaField('Описание блога', validators=[DataRequired()])
    submit = SubmitField('Сохранить блог')

class PostForm(FlaskForm):
    title = StringField('Название поста', validators=[DataRequired(), Length(min=1, max=150)])
    content = TextAreaField('Содержание поста', validators=[DataRequired()])
    submit = SubmitField('Сохранить пост')