# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models import User 
from flask_wtf.file import FileField, FileAllowed  # Убрали MultipleFileField

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6, max=100)])
    confirm_password = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password', message='Пароли должны совпадать')])
    submit = SubmitField('Зарегистрироваться')

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
    # Для множественной загрузки используем обычное FileField
    attachment = FileField('Прикрепить файлы (фото/музыка/видео)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'mp3', 'wav', 'ogg', 'mp4', 'mov', 'avi'], 
                    'Разрешены только файлы изображений, аудио и видео.')
    ])
    submit = SubmitField('Сохранить пост')

class CommentForm(FlaskForm):
    content = TextAreaField('Ваш комментарий', validators=[DataRequired(), Length(min=1, max=500)])
    submit = SubmitField('Оставить комментарий')
