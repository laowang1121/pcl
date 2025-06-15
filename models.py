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
    # 关联评论
    comments = db.relationship('Comment', back_populates='article', cascade='all, delete-orphan')
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    category = db.relationship('Category', back_populates='articles')
    tags = db.relationship('Tag', secondary='article_tag', back_populates='articles')

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


# 评论模型
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)  # 修改这里
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='select')
    user = db.relationship('User')
    article = db.relationship('Article', back_populates='comments')

    def __repr__(self):
        return f'<Comment {self.id}>'


# 分类模型
class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    articles = db.relationship('Article', back_populates='category')

    def __repr__(self):
        return f'<Category {self.name}>'


# 标签与文章关联表
article_tag = db.Table('article_tag',
    db.Column('article_id', db.Integer, db.ForeignKey('articles.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)

# 标签模型
class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)
    articles = db.relationship('Article', secondary=article_tag, back_populates='tags')

    def __repr__(self):
        return f'<Tag {self.name}>'


# 初始化数据库
def init_app(app):
    db.init_app(app)
