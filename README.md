# Web Blog Platform

A simple and powerful blogging platform built with Flask.

## Quick Start

### 1. Install Requirements

```bash
pip install -r requirements.txt
```

### 2. Set Up Database

```bash
python create_tables.py
```

### 3. Run the Application

```bash
python run.py
```

The app will be available at: **http://localhost:5000**

## How to Use

### Register & Login
- Go to `/register` to create an account
- Use `/login` to sign in with your email and password

### Create a Blog
1. Click "Create Blog" in the navigation
2. Fill in title and description
3. Click "Save Blog"

### Write Posts
1. Go to your blog
2. Click "New Post"
3. Add title, content, and optional files
4. Click "Save Post"

### Manage Your Profile
- Click "My Profile" in the navigation
- Update your username/email
- Change your password

## Features

✅ **User System** - Register, login, profile management
✅ **Blogs** - Create, edit, delete blogs
✅ **Posts** - Write posts with file attachments
✅ **Comments** - Discuss posts with other users
✅ **Likes** - Like your favorite posts
✅ **Subscriptions** - Follow blogs you like
✅ **File Uploads** - Images, audio, video, documents

## Configuration

Edit `config.py` to customize:
- Database settings
- File upload limits
- Secret keys

## Deployment

For production, use Gunicorn:

```bash
pip install gunicorn
gunicorn -c gunicorn_config.py run:app
```

Or use Docker:

```bash
docker-compose up -d
```

## Need Help?

Check the error pages for troubleshooting:
- 404 Not Found
- 500 Server Error
- 403 Forbidden
- 413 Request Too Large

Enjoy blogging! 🚀
