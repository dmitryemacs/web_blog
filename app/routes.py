# routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import User, Blog, Post, Comment, db, Subscription # Добавлен Subscription
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.forms import RegistrationForm, LoginForm, BlogForm, PostForm, CommentForm # Добавлен CommentForm

bp = Blueprint('main', __name__)

# ---------------- Регистрация и логин ----------------
@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Вы успешно вошли!', 'success')
            # Перенаправление на страницу, которую пользователь пытался посетить, или на главную
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        flash('Неверный логин или пароль', 'danger')
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта.', 'info')
    return redirect(url_for('main.index'))

# ---------------- Главная и просмотр ----------------
@bp.route('/')
def index():
    blogs = Blog.query.all()
    return render_template('index.html', blogs=blogs)

@bp.route('/blog/<int:blog_id>')
def blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    posts = Post.query.filter_by(blog_id=blog.id).order_by(Post.created_at.desc()).all()
    is_subscribed = False
    if current_user.is_authenticated:
        # Проверяем, подписан ли текущий пользователь на этот блог
        is_subscribed = Subscription.query.filter_by(user_id=current_user.id, blog_id=blog.id).first() is not None
    return render_template('blog.html', blog=blog, posts=posts, is_subscribed=is_subscribed) # Передаем is_subscribed

@bp.route('/post/<int:post_id>', methods=['GET', 'POST']) # Добавлен POST метод
def post(post_id):
    post = Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post.id).order_by(Comment.created_at.asc()).all()
    comment_form = CommentForm() # Инициализируем форму комментария

    if comment_form.validate_on_submit() and current_user.is_authenticated:
        comment = Comment(content=comment_form.content.data, post=post, author=current_user)
        db.session.add(comment)
        db.session.commit()
        flash('Ваш комментарий успешно добавлен!', 'success')
        return redirect(url_for('main.post', post_id=post.id))
    
    # Если форма была отправлена, но не прошла валидацию (например, пользователь не аутентифицирован, но форма отображается)
    # или это GET запрос, просто отображаем страницу.
    return render_template('post.html', post=post, comments=comments, comment_form=comment_form)

# ---------------- CRUD для блогов ----------------
@bp.route('/blog/new', methods=['GET', 'POST'])
@login_required
def new_blog():
    form = BlogForm()
    if form.validate_on_submit():
        blog = Blog(title=form.title.data, description=form.description.data, owner=current_user)
        db.session.add(blog)
        db.session.commit()
        flash('Блог успешно создан!', 'success')
        return redirect(url_for('main.blog', blog_id=blog.id))
    return render_template('blog_form.html', form=form, title='Создать новый блог')

@bp.route('/blog/<int:blog_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if blog.owner != current_user:
        flash('У вас нет прав для редактирования этого блога.', 'warning')
        return redirect(url_for('main.index'))
    form = BlogForm(obj=blog) # Заполнение формы существующими данными блога
    if form.validate_on_submit():
        blog.title = form.title.data
        blog.description = form.description.data
        db.session.commit()
        flash('Блог успешно обновлен!', 'success')
        return redirect(url_for('main.blog', blog_id=blog.id))
    return render_template('blog_form.html', form=form, title='Редактировать блог')

@bp.route('/blog/<int:blog_id>/delete', methods=['POST'])
@login_required
def delete_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if blog.owner != current_user:
        flash('У вас нет прав для удаления этого блога.', 'warning')
        return redirect(url_for('main.index'))
    db.session.delete(blog)
    db.session.commit()
    flash('Блог успешно удален!', 'info')
    return redirect(url_for('main.index'))

# ---------------- CRUD для постов ----------------
@bp.route('/blog/<int:blog_id>/post/new', methods=['GET', 'POST'])
@login_required
def new_post(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if blog.owner != current_user:
        flash('У вас нет прав для создания поста в этом блоге.', 'warning')
        return redirect(url_for('main.index'))
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, blog=blog)
        db.session.add(post)
        db.session.commit()
        flash('Пост успешно создан!', 'success')
        return redirect(url_for('main.post', post_id=post.id))
    return render_template('post_form.html', form=form, title='Создать новый пост')

@bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    # Проверяем, является ли текущий пользователь владельцем блога, к которому принадлежит пост
    if post.blog.owner != current_user:
        flash('У вас нет прав для редактирования этого поста.', 'warning')
        return redirect(url_for('main.index'))
    form = PostForm(obj=post) # Заполнение формы существующими данными поста
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Пост успешно обновлен!', 'success')
        return redirect(url_for('main.post', post_id=post.id))
    return render_template('post_form.html', form=form, title='Редактировать пост')

@bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    # Проверяем, является ли текущий пользователь владельцем блога, к которому принадлежит пост
    if post.blog.owner != current_user:
        flash('У вас нет прав для удаления этого поста.', 'warning')
        return redirect(url_for('main.index'))
    db.session.delete(post)
    db.session.commit()
    flash('Пост успешно удален!', 'info')
    return redirect(url_for('main.blog', blog_id=post.blog.id))

# ---------------- Функции подписки ----------------
@bp.route('/blog/<int:blog_id>/subscribe', methods=['POST'])
@login_required
def subscribe_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    # Проверяем, не подписан ли пользователь уже
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
        flash(f'Вы не были подписаны на блог "{blog.title}".', 'warning')
    return redirect(url_for('main.blog', blog_id=blog.id))