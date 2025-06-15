import os
from flask import request, redirect, render_template, url_for, flash, session, jsonify, send_from_directory, current_app
from flask_login import login_required, current_user, login_user, LoginManager, logout_user
from werkzeug.utils import secure_filename
from __init__ import create_app, db  # 正确导入db
from models import Article, User, Comment, Tag, Category
from forms import EditArticleForm, ProfileForm, CommentForm
from flask_bcrypt import Bcrypt
from datetime import timedelta
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import random
from flask import make_response




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

@app.route('/captcha')
def captcha():
    # 生成随机验证码文本
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    code = ''.join(random.choices(chars, k=4))
    session['captcha'] = code  # 存入session

    # 创建图片
    img = Image.new('RGB', (100, 40), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    # 尝试使用系统字体
    try:
        font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 28)
    except:
        font = ImageFont.load_default()
    draw.text((10, 5), code, font=font, fill=(0, 0, 0))

    # 干扰线
    for _ in range(5):
        x1 = random.randint(0, 100)
        y1 = random.randint(0, 40)
        x2 = random.randint(0, 100)
        y2 = random.randint(0, 40)
        draw.line(((x1, y1), (x2, y2)), fill=(150, 150, 150), width=1)

    buf = BytesIO()
    img.save(buf, 'PNG')
    buf.seek(0)
    response = make_response(buf.read())
    response.headers['Content-Type'] = 'image/png'
    return response

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
    # 技术类标签名集合
    tech_tags = {'前端', 'HTML', 'CSS', 'JavaScript', 'Vue', 'React', 'Angular', '后端', 'Java', 'Python', 'Node.js',
                 'PHP', 'Go', 'Ruby', '数据库', 'MySQL', 'MongoDB', 'PostgreSQL', 'Redis', '移动开发', 'Android', 'iOS',
                 'Flutter', 'React Native', '人工智能', '机器学习', '深度学习', 'NLP', 'CV', '云计算', 'AWS', 'Azure',
                 '阿里云', 'Docker', 'Kubernetes', '运维与DevOps', 'CI/CD', '自动化', '监控', '日志'}
    # 生活类标签名集合（合并所有生活相关标签）
    life_tags = {'旅行', '美食', '读书', '电影', '摄影', '健身', '情感'}
    # 学习成长类标签名集合
    growth_tags = {'学习方法', '时间管理', '个人成长', '习惯养成'}
    # 创业与职场类集合
    enacar_tags = {'创业', '产品经理', '职业规划', '简历面试', '职场技能'}
    # 设计与创意类
    design_tags = {'UI/UX设计', '平面设计', '插画', '动画', '交互设计'}
    # 其他常用标签类
    other_tags = {'随笔', '日志', '心得体会', '教程', '资源分享', '工具推荐', '新闻', '业界动态'}

    tags = Tag.query.all()
    all_tags = []
    # 分类名映射（可根据实际分类表调整）
    category_map = {
        '技术类': tech_tags,
        '生活类': life_tags,
        '学习成长': growth_tags,
        '创业与职场': enacar_tags,
        '设计与创意': design_tags,
        '其他常用标签': other_tags
    }
    # 查询所有分类
    categories = Category.query.all() if 'Category' in globals() else []
    category_name_dict = {str(c.id): c.name for c in categories}
    for tag in tags:
        # 优先用tag.category_name或tag.category_id
        cat_name = getattr(tag, 'category_name', None)
        if not cat_name and hasattr(tag, 'category_id'):
            cat_name = category_name_dict.get(str(tag.category_id), None)
        # 如果在已知集合，归类，否则用数据库分类或“其它类”
        if tag.name in tech_tags:
            cat = '技术类'
        elif tag.name in life_tags:
            cat = '生活类'
        elif tag.name in growth_tags:
            cat = '学习成长'
        elif tag.name in enacar_tags:
            cat = '创业与职场'
        elif tag.name in design_tags:
            cat = '设计与创意'
        elif tag.name in other_tags:
            cat = '其他常用标签'
        elif cat_name:
            cat = cat_name
        else:
            cat = '其它类'
        all_tags.append({'id': tag.id, 'name': tag.name, 'category_name': cat})

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
            author=current_user,
            category=form.category.data,
            tags=list(form.tags.data)
        )
        db.session.add(article)
        db.session.commit()
        flash('文章添加成功', 'success')
        return redirect(url_for('home'))

    return render_template('add_article.html', form=form, all_tags=all_tags)

# 编辑文章
@app.route('/edit_article/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_article(id):
    article = Article.query.get_or_404(id)
    form = EditArticleForm(obj=article)
    # 以下为 all_tags 处理逻辑，参考 add_article 路由
    tech_tags = {'前端', 'HTML', 'CSS', 'JavaScript', 'Vue', 'React', 'Angular', '后端', 'Java', 'Python', 'Node.js',
                 'PHP', 'Go', 'Ruby', '数据库', 'MySQL', 'MongoDB', 'PostgreSQL', 'Redis', '移动开发', 'Android', 'iOS',
                 'Flutter', 'React Native', '人工智能', '机器学习', '深度学习', 'NLP', 'CV', '云计算', 'AWS', 'Azure',
                 '阿里云', 'Docker', 'Kubernetes', '运维与DevOps', 'CI/CD', '自动化', '监控', '日志'}
    life_tags = {'旅行', '美食', '读书', '电影', '摄影', '健身', '情感'}
    growth_tags = {'学习方法', '时间管理', '个人成长', '习惯养成'}
    enacar_tags = {'创业', '产品经理', '职业规划', '简历面试', '职场技能'}
    design_tags = {'UI/UX设计', '平面设计', '插画', '动画', '交互设计'}
    other_tags = {'随笔', '日志', '心得体会', '教程', '资源分享', '工具推荐', '新闻', '业界动态'}
    tags = Tag.query.all()
    all_tags = []
    category_map = {
        '技术类': tech_tags,
        '生活类': life_tags,
        '学习成长': growth_tags,
        '创业与职场': enacar_tags,
        '设计与创意': design_tags,
        '其他常用标签': other_tags
    }
    categories = Category.query.all() if 'Category' in globals() else []
    category_name_dict = {str(c.id): c.name for c in categories}
    for tag in tags:
        cat_name = getattr(tag, 'category_name', None)
        if not cat_name and hasattr(tag, 'category_id'):
            cat_name = category_name_dict.get(str(tag.category_id), None)
        if tag.name in tech_tags:
            cat = '技术类'
        elif tag.name in life_tags:
            cat = '生活类'
        elif tag.name in growth_tags:
            cat = '学习成长'
        elif tag.name in enacar_tags:
            cat = '创业与职场'
        elif tag.name in design_tags:
            cat = '设计与创意'
        elif tag.name in other_tags:
            cat = '其他常用标签'
        elif cat_name:
            cat = cat_name
        else:
            cat = '其它类'
        all_tags.append({'id': tag.id, 'name': tag.name, 'category_name': cat})
    if form.validate_on_submit():
        article.title = form.title.data
        article.summary = form.summary.data
        article.content = form.content.data
        article.category = form.category.data
        article.tags = list(form.tags.data)
        file = request.files.get('cover_image')
        if file and file.filename and allowed_file(file.filename):
            import uuid
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            cover_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(cover_path)
            if article.cover_image and article.cover_image != filename:
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], article.cover_image)
                if os.path.exists(old_path):
                    os.remove(old_path)
            article.cover_image = filename
        db.session.commit()
        flash('文章已更新！', 'success')
        return redirect(url_for('view_article', article_id=article.id))
    return render_template('edit_article.html', form=form, article=article, all_tags=all_tags)
# 文章显示
@app.route('/view_article/<int:article_id>', methods=['GET', 'POST'])
def view_article(article_id):
    article = Article.query.get_or_404(article_id)
    images = getattr(article, 'images', [])
    cover_image = article.cover_image
    form = CommentForm()
    # 处理评论提交
    if form.validate_on_submit() and current_user.is_authenticated:
        comment = Comment(
            content=form.content.data,
            user_id=current_user.id,
            article_id=article.id
        )
        db.session.add(comment)
        db.session.commit()
        flash('评论发布成功！', 'success')
        return redirect(url_for('view_article', article_id=article.id))
    # 只查主评论
    comments = Comment.query.filter_by(article_id=article.id, parent_id=None).order_by(Comment.created_at.desc()).all()
    return render_template('view_article.html', article=article, images=images, cover_image=cover_image, form=form, comments=comments)

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

# 文章详情路由
@app.route('/article/<int:article_id>', methods=['GET', 'POST'])
def article_detail(article_id):
    article = Article.query.get_or_404(article_id)
    images = getattr(article, 'images', [])
    cover_image = article.cover_image
    form = CommentForm()
    # 处理评论提交
    if form.validate_on_submit() and current_user.is_authenticated:
        comment = Comment(
            content=form.content.data,
            user_id=current_user.id,
            article_id=article.id
        )
        db.session.add(comment)
        db.session.commit()
        flash('评论发布成功！', 'success')
        return redirect(url_for('article_detail', article_id=article_id) + '#comment-section')
    # 只查主评论
    comments = Comment.query.filter_by(article_id=article.id, parent_id=None).order_by(Comment.created_at.desc()).all()
    return render_template('view_article.html', article=article, images=images, cover_image=cover_image, form=form, comments=comments)

# 删除评论的路由
@app.route('/delete_comment/<int:comment_id>/<int:article_id>', methods=['POST'])
@login_required
def delete_comment(comment_id, article_id):
    comment = Comment.query.get_or_404(comment_id)
    article = Article.query.get_or_404(article_id)
    # 只有评论作者或文章作者可以删除
    if current_user.id == comment.user_id or current_user.id == article.user_id:
        # 删除主评论及其所有子评论
        def delete_with_replies(comment):
            for reply in comment.replies:
                delete_with_replies(reply)
            db.session.delete(comment)
        delete_with_replies(comment)
        db.session.commit()
        flash('评论及其子评论已删除', 'success')
    else:
        flash('无权限删除该评论', 'danger')
    return redirect(url_for('article_detail', article_id=article_id) + '#comment-section')

#评论回复路由
@app.route('/reply_comment/<int:comment_id>/<int:article_id>', methods=['POST'])
@login_required
def reply_comment(comment_id, article_id):
    from models import Comment
    reply_content = request.form.get('reply_content', '').strip()
    if not reply_content:
        flash('回复内容不能为空', 'danger')
        return redirect(url_for('article_detail', article_id=article_id) + '#comment-section')
    parent_comment = Comment.query.get_or_404(comment_id)
    reply = Comment(
        content=reply_content,
        user_id=current_user.id,
        article_id=article_id,
        parent_id=comment_id
    )
    db.session.add(reply)
    db.session.commit()
    flash('回复成功', 'success')
    return redirect(url_for('article_detail', article_id=article_id) + '#comment-section')

if __name__ == '__main__':
    app.run(debug=True)