import os
from flask import request, redirect, render_template, url_for, flash, session, jsonify, send_from_directory, current_app
from flask_login import login_required, current_user, login_user, LoginManager, logout_user
from werkzeug.utils import secure_filename
from __init__ import create_app, db  # 正确导入db
from models import Article, User
from forms import EditArticleForm, ProfileForm
from flask_bcrypt import Bcrypt
from datetime import timedelta




# 创建 Flask 应用实例
app = create_app()
bcrypt = Bcrypt(app)

# 创建数据库表
with app.app_context():
    db.create_all()

basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 登录管理器配置
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "请先登录后访问该页面"
MAX_IMAGE_AREA = 2073600

app.config['SECRET_KEY'] = '123'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 自定义过滤器：将 UTC 时间转换为中国时间
@app.template_filter('china_time')
def china_time_filter(dt):
    if dt is None:
        return ''
    return (dt + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')

# 主页路由
@app.route('/')
def home():
    articles = Article.query.all() or []
    cover_images = [article.cover_image for article in articles if article.cover_image]
    return render_template('index.html', articles=articles, cover_images=cover_images)

# 定义 user_loader 函数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['username'] = username
            login_user(user)
            flash('登录成功！', 'success')
            return redirect(url_for('home'))
        else:
            flash('用户名或密码错误', 'danger')
    return render_template('login.html')

# 注册路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if len(username) < 6 or len(password) < 6:
            flash('用户名和密码长度必须至少6位', 'warning')
            return render_template('register.html')

        if password != confirm_password:
            flash('两次输入的密码不一致', 'warning')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return render_template('register.html')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        flash('注册成功！请点击确认后跳转到登录页面。', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# 用户列表查看
@app.route('/users')
@login_required
def view_users():
    if not current_user.is_admin:
        flash('您无权查看此页面', 'danger')
        return redirect(url_for('home'))
    users = User.query.all()
    return render_template('users.html', users=users)

# 登出路由
@app.route('/logout')
@login_required
def logout():
    logout_user()  # 这行必须加
    session.pop('username', None)
    flash('您已登出', 'info')
    return redirect(url_for('home'))

# 添加文章
@app.route('/add_article', methods=['GET', 'POST'])
@login_required
def add_article():
    form = EditArticleForm()
    if form.validate_on_submit():
        cover_image = None
        if form.cover_image.data:
            filename = secure_filename(form.cover_image.data.filename)
            cover_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            form.cover_image.data.save(cover_path)
            cover_image = filename
        article = Article(
            title=form.title.data,
            summary=form.summary.data,
            content=form.content.data,
            cover_image=cover_image,
            author=current_user
        )
        db.session.add(article)
        db.session.commit()
        flash('文章添加成功', 'success')
        return redirect(url_for('home'))

    return render_template('add_article.html', form=form)

# 编辑文章
@app.route('/edit_article/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_article(id):
    article = Article.query.get_or_404(id)
    form = EditArticleForm(obj=article)
    if form.validate_on_submit():
        article.title = form.title.data
        article.summary = form.summary.data
        article.content = form.content.data

        # 处理封面图片
        file = request.files.get('cover_image')
        if file and file.filename and allowed_file(file.filename):
            import uuid
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            cover_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(cover_path)
            # 删除旧封面
            if article.cover_image and article.cover_image != filename:
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], article.cover_image)
                if os.path.exists(old_path):
                    os.remove(old_path)
            article.cover_image = filename

        db.session.commit()
        flash('文章已更新！', 'success')
        return redirect(url_for('view_article', article_id=article.id))

    return render_template('edit_article.html', form=form, article=article)
# 文章显示
@app.route('/view_article/<int:article_id>')
def view_article(article_id):
    article = Article.query.get_or_404(article_id)
    images = getattr(article, 'images', [])
    cover_image = article.cover_image
    return render_template('view_article.html', article=article, images=images, cover_image=cover_image)

# 删除文章的路由
@app.route('/delete_article/<int:id>', methods=['POST'])
@login_required
def delete_article(id):
    article = Article.query.get_or_404(id)
    if article.user_id != current_user.id and not current_user.is_admin:
        flash('您没有权限删除这篇文章！', 'danger')
        return redirect(url_for('view_article', article_id=id))
    db.session.delete(article)
    db.session.commit()
    flash('文章已成功删除！', 'success')
    return redirect(url_for('home'))

# 个人信息更新
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    user = User.query.get(current_user.id)

    if request.method == 'GET':
        form.nickname.data = user.nickname
        form.gender.data = user.gender
        form.birthday.data = user.birthday
        form.zodiac.data = user.zodiac
        form.location.data = user.location
        form.occupation.data = user.occupation
        form.bio.data = user.bio

    if form.validate_on_submit():
        user.nickname = form.nickname.data
        user.gender = form.gender.data
        user.birthday = form.birthday.data
        user.zodiac = form.zodiac.data
        user.location = form.location.data
        user.occupation = form.occupation.data
        user.bio = form.bio.data

        db.session.commit()
        flash('个人信息更新成功！', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', form=form)

# 图片上传
@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({"location": url_for('uploaded_file', filename=filename)}), 200
    else:
        return jsonify({"error": "Invalid file format"}), 400

# 文件路由
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)