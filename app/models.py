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
    db.Column('post_id', db.Integer, db.ForeignKey('post.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id', ondelete='CASCADE'), primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='reader') # Роль пользователя
    
    # ИСПРАВЛЕНО: Добавлено cascade='all, delete-orphan'
    blogs = db.relationship('Blog', backref='owner', lazy=True, cascade='all, delete-orphan') 
    
    # ИСПРАВЛЕНО: Добавлены ondelete='CASCADE' для зависимых моделей, чтобы удаление пользователя работало
    comments = db.relationship('Comment', backref='author', lazy=True, cascade='all, delete-orphan') 
    likes = db.relationship('Like', backref='user', lazy=True, cascade='all, delete-orphan') 
    subscriptions = db.relationship('Subscription', backref='subscriber', lazy=True, cascade='all, delete-orphan') 
    uploaded_attachments = db.relationship('Attachment', backref='uploader', lazy=True, foreign_keys='Attachment.user_id', cascade='all, delete-orphan')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', 'Role: {self.role}')"

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # ИСПРАВЛЕНО: Добавлено ondelete='CASCADE'
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False) # Внешний ключ на владельца блога
    title = db.Column(db.String(150), nullable=False) # Название блога
    description = db.Column(db.Text, nullable=False) # Описание блога
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # Дата создания
    posts = db.relationship('Post', backref='blog', lazy=True, cascade='all, delete-orphan') # Посты в этом блоге
    subscribers = db.relationship('Subscription', backref='blog', lazy=True, cascade='all, delete-orphan') # Подписчики блога

    def __repr__(self):
        return f"Blog('{self.title}', 'Owner ID: {self.owner_id}')"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # ИСПРАВЛЕНО: Добавлено ondelete='CASCADE'
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id', ondelete='CASCADE'), nullable=False) # Внешний ключ на блог
    title = db.Column(db.String(150), nullable=False) # Заголовок поста
    content = db.Column(db.Text, nullable=False) # Содержание поста
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # Дата создания
    
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan') # Комментарии к посту
    likes = db.relationship('Like', backref='post', lazy=True, cascade='all, delete-orphan') # Лайки к посту
    tags = db.relationship('Tag', secondary=post_tags, lazy='subquery', backref=db.backref('posts', lazy=True))
    
    # Новое отношение для прикрепленных файлов
    attachments = db.relationship('Attachment', backref='post', lazy=True, cascade='all, delete-orphan', foreign_keys='Attachment.post_id') 

    def __repr__(self):
        return f"Post('{self.title}', '{self.created_at}')"

# ... (Остальные классы Tag, Attachment, Comment, Like, Subscription) ...

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # ИСПРАВЛЕНО: Добавлено ondelete='CASCADE'
    post_id = db.Column(db.Integer, db.ForeignKey('post.id', ondelete='CASCADE'), nullable=False) # К какому посту относится
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False) # Кто загрузил файл
    filename = db.Column(db.String(255), nullable=False) # Имя файла, под которым он сохранен на сервере (secure_filename)
    original_filename = db.Column(db.String(255)) # Исходное имя файла
    mimetype = db.Column(db.String(100), nullable=False) # MIME-тип файла
    file_type = db.Column(db.String(10), nullable=False) # Тип: 'image', 'video', 'audio', 'other'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"Attachment('{self.filename}', 'Post ID: {self.post_id}', 'Type: {self.file_type}')"


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # Название тега

    def __repr__(self):
        return f"Tag('{self.name}')"

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id', ondelete='CASCADE'), nullable=False) # Внешний ключ на пост
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False) # Внешний ключ на пользователя-автора
    content = db.Column(db.Text, nullable=False) # Содержание комментария
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # Дата создания

    def __repr__(self):
        return f"Comment('{self.content}', '{self.created_at}')"

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id', ondelete='CASCADE'), nullable=False) # Внешний ключ на пост
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False) # Внешний ключ на пользователя
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # Дата создания лайка

    def __repr__(self):
        return f"Like('{self.user_id}', '{self.post_id}')"

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False) # Внешний ключ на пользователя
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id', ondelete='CASCADE'), nullable=False) # Внешний ключ на блог
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # Дата подписки

    def __repr__(self):
        return f"Subscription('User: {self.user_id}', 'Blog: {self.blog_id}')"