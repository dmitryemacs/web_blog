# routes.py
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from app.models import User, Blog, Post, Comment, db, Subscription, Like, Attachment 
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.forms import RegistrationForm, LoginForm, BlogForm, PostForm, CommentForm
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from datetime import datetime

bp = Blueprint('main', __name__)

# ---------------- Вспомогательные функции для файлов ----------------
def allowed_file(filename):
    allowed_extensions = {
        'png', 'jpg', 'jpeg', 'gif',  # изображения
        'mp3', 'wav', 'ogg', 'flac',  # аудио
        'mp4', 'mov', 'avi', 'mkv', 'webm',  # видео
        'pdf', 'doc', 'docx', 'txt', 'rtf'  # документы
    }
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_type(extension):
    image_ext = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    audio_ext = {'mp3', 'wav', 'ogg', 'flac', 'm4a'}
    video_ext = {'mp4', 'mov', 'avi', 'mkv', 'webm', 'flv'}
    doc_ext = {'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt'}
    
    if extension in image_ext:
        return 'image'
    elif extension in audio_ext:
        return 'audio'
    elif extension in video_ext:
        return 'video'
    elif extension in doc_ext:
        return 'document'
    return 'other'
# ---------------- Регистрация и логин ----------------

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        try:
            db.session.commit()
            flash('Регистрация успешна! Теперь вы можете войти.', 'success')
            return redirect(url_for('main.login'))
        except IntegrityError:
            db.session.rollback()
            flash('Ошибка регистрации. Имя пользователя или email уже заняты.', 'danger')
            
    return render_template('register.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            flash('Вход выполнен успешно!', 'success')
            return redirect(next_page or url_for('main.index'))
        else:
            flash('Ошибка входа. Проверьте email или пароль.', 'danger')
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('main.index'))

# ---------------- Главная страница и блоги ----------------

@bp.route('/')
def index():
    blogs = Blog.query.order_by(Blog.created_at.desc()).all()
    return render_template('index.html', title='Главная', blogs=blogs)

@bp.route('/new_blog', methods=['GET', 'POST'])
@login_required
def new_blog():
    form = BlogForm()
    if form.validate_on_submit():
        blog = Blog(title=form.title.data, description=form.description.data, owner=current_user)
        db.session.add(blog)
        db.session.commit()
        flash('Ваш новый блог успешно создан!', 'success')
        return redirect(url_for('main.blog', blog_id=blog.id))
        
    return render_template('blog_form.html', title='Создать блог', form=form)

@bp.route('/blog/<int:blog_id>')
def blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    posts = Post.query.filter_by(blog_id=blog.id).order_by(Post.created_at.desc()).all()
    
    is_subscribed = False
    if current_user.is_authenticated:
        is_subscribed = Subscription.query.filter_by(user_id=current_user.id, blog_id=blog.id).first() is not None
        
    return render_template('blog.html', blog=blog, posts=posts, is_subscribed=is_subscribed)

@bp.route('/blog/<int:blog_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    
    if blog.owner != current_user:
        flash('Вы не являетесь владельцем этого блога и не можете его редактировать.', 'danger')
        return redirect(url_for('main.blog', blog_id=blog.id))

    form = BlogForm()
    
    if form.validate_on_submit():
        blog.title = form.title.data
        blog.description = form.description.data
        db.session.commit()
        flash('Ваш блог был успешно обновлен!', 'success')
        return redirect(url_for('main.blog', blog_id=blog.id))
        
    elif request.method == 'GET':
        form.title.data = blog.title
        form.description.data = blog.description
        
    return render_template('blog_form.html', title=f'Редактировать блог: {blog.title}', form=form)

@bp.route('/blog/<int:blog_id>/delete', methods=['POST'])
@login_required
def delete_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    
    if blog.owner != current_user:
        flash('Вы не являетесь владельцем этого блога.', 'danger')
        return redirect(url_for('main.index'))
    
    db.session.delete(blog)
    db.session.commit()
    flash(f'Блог "{blog.title}" успешно удален.', 'success')
    return redirect(url_for('main.index'))

# ---------------- Функции подписки ----------------

@bp.route('/blog/<int:blog_id>/subscribe', methods=['POST'])
@login_required
def subscribe_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if blog.owner == current_user:
        flash('Вы являетесь владельцем этого блога.', 'warning')
        return redirect(url_for('main.blog', blog_id=blog.id))

    if not Subscription.query.filter_by(user_id=current_user.id, blog_id=blog.id).first():
        subscription = Subscription(user_id=current_user.id, blog_id=blog.id)
        db.session.add(subscription)
        db.session.commit()
        flash(f'Вы успешно подписались на блог "{blog.title}"!', 'success')
    else:
        flash(f'Вы уже подписаны на блог "{blog.title}".', 'info')
        
    return redirect(url_for('main.blog', blog_id=blog.id))

@bp.route('/blog/<int:blog_id>/unsubscribe', methods=['POST'])
@login_required
def unsubscribe_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    subscription = Subscription.query.filter_by(user_id=current_user.id, blog_id=blog.id).first()
    
    if subscription:
        db.session.delete(subscription)
        db.session.commit()
        flash(f'Вы отписались от блога "{blog.title}".', 'info')
    else:
        flash('Вы не были подписаны на этот блог.', 'warning')
        
    return redirect(url_for('main.blog', blog_id=blog.id))

# ---------------- Функции постов ----------------

@bp.route('/blog/<int:blog_id>/post/new', methods=['GET', 'POST'])
@login_required
def new_post(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if blog.owner != current_user:
        flash('Вы можете создавать посты только в своих блогах.', 'danger')
        return redirect(url_for('main.blog', blog_id=blog.id))
        
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, blog=blog)
        db.session.add(post)
        
        # Обработка прикрепленного файла - ИСПРАВЛЕНО: form.attachment.data вместо form.attachments.data
        if form.attachment.data:
            file = form.attachment.data
            if file and allowed_file(file.filename):
                original_filename = file.filename
                filename = secure_filename(original_filename)
                
                upload_path = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_path, exist_ok=True)
                
                file_path = os.path.join(upload_path, filename)
                
                counter = 1
                unique_filename = filename
                while os.path.exists(file_path):
                    name, ext = os.path.splitext(filename)
                    unique_filename = f"{name}_{counter}{ext}"
                    file_path = os.path.join(upload_path, unique_filename)
                    counter += 1
                
                file.save(file_path)
                
                extension = unique_filename.rsplit('.', 1)[1].lower()
                file_type = get_file_type(extension)
                
                attachment = Attachment(
                    post=post,
                    user_id=current_user.id,
                    filename=unique_filename,
                    original_filename=original_filename,
                    mimetype=file.mimetype,
                    file_type=file_type
                )
                db.session.add(attachment)

        db.session.commit()
        flash('Ваш пост успешно создан!', 'success')
        return redirect(url_for('main.post', post_id=post.id))
        
    return render_template('post_form.html', title=f'Новый пост в {blog.title}', form=form, blog=blog)

# ---------------- Функция просмотра поста и комментариев ----------------
@bp.route('/post/<int:post_id>', methods=['GET', 'POST']) # <-- ИСПРАВЛЕННЫЙ МАРШРУТ
def post(post_id):
    post = Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post.id).order_by(Comment.created_at.desc()).all()
    
    # ИСПРАВЛЕНИЕ ОШИБКИ: Используем len() для подсчета элементов в Python-списке
    like_count = len(post.likes)
    
    is_liked = False
    if current_user.is_authenticated:
        is_liked = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first() is not None
        
    form = CommentForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Войдите, чтобы оставить комментарий.', 'warning')
            return redirect(url_for('main.login', next=request.url))
            
        comment = Comment(content=form.content.data, post=post, author=current_user)
        db.session.add(comment)
        db.session.commit()
        flash('Ваш комментарий добавлен!', 'success')
        
        # КЛЮЧЕВОЙ МОМЕНТ: РЕДИРЕКТ
        return redirect(url_for('main.post', post_id=post.id)) 
        
    return render_template('post.html', 
                           title=post.title, 
                           post=post, 
                           comments=comments, 
                           form=form, 
                           is_liked=is_liked,
                           like_count=like_count)

# ---------------- Функции редактирования и удаления ----------------

@bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if post.blog.owner != current_user:
        flash('Вы можете редактировать только посты в своих блогах.', 'danger')
        return redirect(url_for('main.post', post_id=post.id))

    form = PostForm()
    
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Ваш пост был успешно обновлен!', 'success')
        return redirect(url_for('main.post', post_id=post.id))
        
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
        
    return render_template('post_form.html', title=f'Редактировать пост: {post.title}', form=form, post=post)

@bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if post.blog.owner != current_user:
        flash('Вы можете удалять только посты в своих блогах.', 'danger')
        return redirect(url_for('main.post', post_id=post.id))
    
    blog_id = post.blog.id
    
    for attachment in post.attachments:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], attachment.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    db.session.delete(post)
    db.session.commit()
    flash(f'Пост "{post.title}" успешно удален.', 'success')
    return redirect(url_for('main.blog', blog_id=blog_id))

# ---------------- Функции лайков ----------------

@bp.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    like = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    
    if like:
        db.session.delete(like)
        db.session.commit()
        flash(f'Вы убрали лайк с поста "{post.title}".', 'info')
    else:
        new_like = Like(user_id=current_user.id, post_id=post.id)
        db.session.add(new_like)
        db.session.commit()
        flash(f'Вы лайкнули пост "{post.title}"!', 'success')
        
    return redirect(url_for('main.post', post_id=post.id))

# ---------------- Функции комментариев ----------------

@bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    post_id = comment.post.id
    
    is_owner = current_user == comment.author
    is_post_owner = current_user == comment.post.blog.owner
    is_admin = getattr(current_user, 'role', 'reader') == 'admin' # Используем getattr на случай, если role не определена
    
    if is_owner or is_post_owner or is_admin:
        db.session.delete(comment)
        db.session.commit()
        flash('Комментарий удален.', 'success')
    else:
        flash('У вас нет прав для удаления этого комментария.', 'danger')
        
    return redirect(url_for('main.post', post_id=post_id))

# ---------------- Служебные маршруты ----------------

@bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

# delete attachment
@bp.route('/attachment/<int:attachment_id>/delete', methods=['POST'])
@login_required
def delete_attachment(attachment_id):
    attachment = Attachment.query.get_or_404(attachment_id)
    post_id = attachment.post.id
    
    # Проверяем права: владелец поста или администратор
    if attachment.post.blog.owner != current_user and current_user.role != 'admin':
        flash('Вы не можете удалить это вложение.', 'danger')
        return redirect(url_for('main.post', post_id=post_id))
    
    # Удаляем файл с диска
    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], attachment.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        flash(f'Ошибка при удалении файла: {str(e)}', 'warning')
    
    # Удаляем запись из базы
    db.session.delete(attachment)
    db.session.commit()
    
    flash('Вложение удалено.', 'success')
    return redirect(url_for('main.post', post_id=post_id))
