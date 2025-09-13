# models.py
from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

# Функция для загрузки пользователя Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Ассоциативная таблица для связи многие-ко-многим между Post и Tag
post_tags = db.Table(
    'post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='reader') # Роль пользователя (например, 'reader', 'admin')
    blogs = db.relationship('Blog', backref='owner', lazy=True) # Блоги, принадлежащие пользователю
    comments = db.relationship('Comment', backref='author', lazy=True) # Комментарии, написанные пользователем
    likes = db.relationship('Like', backref='user', lazy=True) # Лайки, поставленные пользователем
    subscriptions = db.relationship('Subscription', backref='user', lazy=True) # Подписки пользователя

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Внешний ключ на пользователя-владельца
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # Дата создания
    posts = db.relationship('Post', backref='blog', lazy=True) # Посты в этом блоге
    subscriptions = db.relationship('Subscription', backref='blog', lazy=True) # Подписки на этот блог

    def __repr__(self):
        return f"Blog('{self.title}', '{self.created_at}')"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False) # Внешний ключ на блог
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # Дата создания
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow) # Дата последнего обновления
    comments = db.relationship('Comment', backref='post', lazy=True) # Комментарии к этому посту
    likes = db.relationship('Like', backref='post', lazy=True) # Лайки к этому посту
    tags = db.relationship('Tag', secondary=post_tags, backref='posts') # Теги, связанные с этим постом

    def __repr__(self):
        return f"Post('{self.title}', '{self.created_at}')"

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # Название тега

    def __repr__(self):
        return f"Tag('{self.name}')"

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False) # Внешний ключ на пост
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Внешний ключ на пользователя-автора
    content = db.Column(db.Text, nullable=False) # Содержание комментария
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # Дата создания

    def __repr__(self):
        return f"Comment('{self.content}', '{self.created_at}')"

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False) # Внешний ключ на пост
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Внешний ключ на пользователя
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # Дата создания лайка

    def __repr__(self):
        return f"Like('{self.user_id}', '{self.post_id}')"

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Внешний ключ на пользователя
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False) # Внешний ключ на блог
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # Дата подписки

    def __repr__(self):
        return f"Subscription('{self.user_id}', '{self.blog_id}')"