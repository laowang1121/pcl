from flask_login import UserMixin
from datetime import datetime
from __init__ import db


# 用户模型
class User(UserMixin, db.Model):
    __tablename__ = 'user'  # 显式指定表名
    __table_args__ = {'extend_existing': True}  # 添加 extend_existing 参数
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    nickname = db.Column(db.String(150))
    gender = db.Column(db.String(10))
    birthday = db.Column(db.Date)
    zodiac = db.Column(db.String(20))
    location = db.Column(db.String(150))
    occupation = db.Column(db.String(150))
    bio = db.Column(db.Text)
    articles = db.relationship('Article', back_populates='author')

    def get_id(self):
        return str(self.id)


# 文章模型
class Article(db.Model):
    __tablename__ = 'articles'  # 显式指定表名
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    summary = db.Column(db.String(250), nullable=False)
    content = db.Column(db.Text, nullable=False)
    content_images = db.Column(db.String(500), nullable=True)  # 保存内容图片路径
    cover_image = db.Column(db.String(255), nullable=True)  # 添加封面图片字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 创建时间
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)  # 更新时间
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)  # 发布日期
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', back_populates='articles')
    # 关联图片
    images = db.relationship('Image', back_populates='article', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Article {self.title}>'


# 图片模型
class Image(db.Model):
    __tablename__ = 'images'  # 显式指定表名
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    article = db.relationship('Article', back_populates='images')

    def __repr__(self):
        return f'<Image {self.filename}>'


# 初始化数据库
def init_app(app):
    db.init_app(app)
