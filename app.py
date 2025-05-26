import os
from flask import request, redirect, render_template, url_for, flash, session, jsonify, send_from_directory, current_app
from flask_login import login_required, current_user, login_user, LoginManager
from sqlalchemy.testing import db
from werkzeug.utils import secure_filename
from .__init__ import create_app  # 使用相对导入修复路径问题
from models import Article, User
from forms import EditArticleForm, ProfileForm
from flask_bcrypt import Bcrypt  # 使用 bcrypt 加密密码


# 创建 Flask 应用实例
app = create_app()
bcrypt = Bcrypt(app)

# 创建数据库表
with app.app_context():
    db.create_all()


basedir = os.path.abspath(os.path.dirname(__file__))
# 配置上传目录
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
UPLOAD_FOLDER = os.path.join(basedir, 'pcf', 'uploads')  # 指定完整路径
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 登录管理器配置
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
MAX_IMAGE_AREA = 2073600

app.config['SECRET_KEY'] = '123'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# 主页路由
@app.route('/')
def home():
    articles = Article.query.all() or []
    cover_images = [article.cover_image for article in articles if article.cover_image]
    return render_template('index.html', articles=articles, cover_images=cover_images)


# 定义 user_loader 函数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # 根据用户 ID 查找用户对象


# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):  # 使用 bcrypt 校验密码
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

        if len(username) < 6 or len(password) < 6:
            flash('用户名和密码长度必须至少6位', 'warning')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return render_template('register.html')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')  # 使用 bcrypt 加密密码
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
    session.pop('username', None)
    flash('您已登出', 'info')
    return redirect(url_for('home'))


# 添加文章
@app.route('/add_article', methods=['GET', 'POST'])
@login_required
def add_article():
    form = EditArticleForm()
    if form.validate_on_submit():
        # 处理封面图片上传
        cover_image = None
        if form.cover_image.data:
            filename = secure_filename(form.cover_image.data.filename)
            cover_path = os.path.join(basedir,'uploads', filename)  # 保存到 pcf/uploads 目录
            form.cover_image.data.save(cover_path)  # 保存图片
            cover_image = filename
        # 创建文章
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
        # 确保重定向到主页
        return redirect(url_for('home'))

    return render_template('add_article.html', form=form)


# 编辑文章
@app.route('/edit_article/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_article(id):
    article = Article.query.get_or_404(id)
    form = EditArticleForm(obj=article)

    if form.validate_on_submit():
        # 更新文章标题、摘要和内容
        article.title = form.title.data
        article.summary = form.summary.data
        article.content = form.content.data

        # 处理封面图片上传
        if 'cover_image' in request.files:
            cover_image = request.files['cover_image']
            if cover_image and cover_image.filename != '':
                filename = secure_filename(cover_image.filename)
                cover_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                cover_image.save(cover_path)
                article.cover_image = filename  # 更新封面图片路径

        db.session.commit()
        flash('文章已更新！', 'success')
        return redirect(url_for('view_article', article_id=article.id))

    return render_template('edit_article.html', form=form, article=article)


# 文章显示
@app.route('/view_article/<int:article_id>')
def view_article(article_id):
    article = Article.query.get_or_404(article_id)

    # 获取与文章相关的图片
    images = article.images
    # 获取封面图片路径
    cover_image = article.cover_image

    return render_template('view_article.html', article=article, images=images, cover_image=cover_image)


# 删除文章的路由
@app.route('/delete_article/<int:id>', methods=['POST'])
@login_required
def delete_article(id):
    article = Article.query.get_or_404(id)

    # 确保当前用户是文章的作者或者是管理员
    if article.user_id != current_user.id and not current_user.is_admin:
        flash('您没有权限删除这篇文章！', 'danger')
        return redirect(url_for('view_article', article_id=id))

    # 删除文章
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

