# routes.py
import os
import mimetypes
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from app.models import User, Blog, Post, Comment, db, Subscription, Like, Attachment 
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.forms import RegistrationForm, LoginForm, BlogForm, PostForm, CommentForm, UpdateProfileForm, ChangePasswordForm
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

# Множество разрешенных MIME-типов для дополнительной безопасности
ALLOWED_MIME_TYPES = {
    # Изображения
    'image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp',
    # Аудио
    'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/ogg', 'audio/flac', 'audio/x-m4a',
    # Видео
    'video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska', 'video/webm',
    # Документы
    'application/pdf', 'application/msword', 
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain', 'application/rtf', 'application/vnd.oasis.opendocument.text'
}

def is_safe_mime_type(mimetype):
    """Проверяет, что MIME-тип разрешен"""
    if not mimetype:
        return False
    # Нормализуем MIME-тип (убираем кодировку и параметры)
    mimetype = mimetype.split(';')[0].strip().lower()
    return mimetype in ALLOWED_MIME_TYPES

def validate_file_upload(file):
    """Проверяет файл на безопасность"""
    if not file or not file.filename:
        return False, "Файл не выбран"
    
    # Проверка расширения
    if not allowed_file(file.filename):
        return False, "Недопустимый тип файла"
    
    # Проверка MIME-типа
    mimetype = file.mimetype
    if not is_safe_mime_type(mimetype):
        # Дополнительная проверка через mimetypes модуль
        guessed_type, _ = mimetypes.guess_type(file.filename)
        if not guessed_type or guessed_type not in ALLOWED_MIME_TYPES:
            return False, "Недопустимый MIME-тип файла"
        mimetype = guessed_type
    
    return True, mimetype

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
    
    # Статистика для главной страницы
    from app.models import User, Post
    users_count = User.query.count()
    posts_count = Post.query.count()
    
    return render_template('index.html', 
                         title='Главная', 
                         blogs=blogs,
                         users_count=users_count,
                         posts_count=posts_count)

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
        
    return render_template('blog_form.html', title=f'Редактировать блог: {blog.title}', form=form, blog=blog)

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
        db.session.flush()  # Чтобы получить ID поста
        
        # Обработка тегов
        tags_input = request.form.get('tags', '').strip()
        if tags_input:
            from app.models import Tag
            tag_names = [tag.strip().lower() for tag in tags_input.split(',') if tag.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                    db.session.flush()
                if tag not in post.tags:
                    post.tags.append(tag)
        
        # Обработка прикрепленного файла с улучшенной валидацией
        if form.attachment.data:
            file = form.attachment.data
            is_valid, validation_result = validate_file_upload(file)
            
            if not is_valid:
                flash(f'Ошибка загрузки файла: {validation_result}', 'danger')
            else:
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
                
                try:
                    file.save(file_path)
                    
                    extension = unique_filename.rsplit('.', 1)[1].lower()
                    file_type = get_file_type(extension)
                    
                    attachment = Attachment(
                        post=post,
                        user_id=current_user.id,
                        filename=unique_filename,
                        original_filename=original_filename,
                        mimetype=validation_result,  # Используем проверенный MIME-тип
                        file_type=file_type
                    )
                    db.session.add(attachment)
                except Exception as e:
                    flash(f'Ошибка при сохранении файла: {str(e)}', 'danger')
                    # Удаляем файл, если он был частично сохранен
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except:
                            pass

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
        
    # Навигация между постами (предыдущий и следующий)
    all_posts = Post.query.filter_by(blog_id=post.blog_id).order_by(Post.created_at.desc()).all()
    post_index = next((i for i, p in enumerate(all_posts) if p.id == post.id), None)
    prev_post = all_posts[post_index + 1] if post_index is not None and post_index + 1 < len(all_posts) else None
    next_post = all_posts[post_index - 1] if post_index is not None and post_index > 0 else None
    
    return render_template('post.html', 
                           title=post.title, 
                           post=post, 
                           comments=comments, 
                           form=form, 
                           is_liked=is_liked,
                           like_count=like_count,
                           prev_post=prev_post,
                           next_post=next_post)

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
        
        # Обработка тегов
        tags_input = request.form.get('tags', '').strip()
        post.tags.clear()  # Очищаем существующие теги
        if tags_input:
            from app.models import Tag
            tag_names = [tag.strip().lower() for tag in tags_input.split(',') if tag.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                    db.session.flush()
                post.tags.append(tag)
        
        db.session.commit()
        flash('Ваш пост был успешно обновлен!', 'success')
        return redirect(url_for('main.post', post_id=post.id))
        
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
        
    return render_template('post_form.html', title=f'Редактировать пост: {post.title}', form=form, post=post, blog=post.blog)

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
    """Маршрут для отдачи загруженных файлов"""
    from flask import send_from_directory, abort
    import os
    from werkzeug.utils import secure_filename

    # Безопасная проверка пути
    upload_folder = current_app.config['UPLOAD_FOLDER']

    # Проверяем, что файл существует и находится в разрешенной директории
    try:
        # Используем secure_filename для дополнительной безопасности
        safe_filename = secure_filename(filename)

        # Проверяем, что файл существует
        file_path = os.path.join(upload_folder, safe_filename)
        if not os.path.exists(file_path):
            abort(404)

        # Проверяем, что путь находится внутри upload_folder
        if not os.path.abspath(file_path).startswith(os.path.abspath(upload_folder)):
            abort(403)

        # Получаем MIME-тип файла из базы данных
        mimetype = None
        attachment = Attachment.query.filter_by(filename=safe_filename).first()
        if attachment:
            mimetype = attachment.mimetype

        return send_from_directory(upload_folder, safe_filename, mimetype=mimetype)

    except Exception as e:
        current_app.logger.error(f"Error serving file {filename}: {str(e)}")
        abort(500)

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

# ---------------- Пользовательский профиль ----------------

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()
    password_form = ChangePasswordForm()

    # Заполняем форму текущими данными пользователя
    if request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    # Обработка обновления профиля
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Ваш профиль успешно обновлен!', 'success')
        return redirect(url_for('main.profile'))

    # Обработка изменения пароля
    if password_form.validate_on_submit():
        if not check_password_hash(current_user.password, password_form.current_password.data):
            flash('Текущий пароль введен неверно.', 'danger')
        else:
            current_user.password = generate_password_hash(password_form.new_password.data)
            db.session.commit()
            flash('Ваш пароль успешно изменен!', 'success')
            return redirect(url_for('main.profile'))

    return render_template('profile.html', form=form, password_form=password_form)
