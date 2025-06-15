from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField
from wtforms.fields.choices import SelectField, SelectMultipleField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileAllowed
from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from models import Category, Tag

def category_choices():
    return Category.query.all()

def tag_choices():
    return Tag.query.all()

class ProfileForm(FlaskForm):
    nickname = StringField('昵称', validators=[DataRequired()])
    gender = StringField('性别', validators=[DataRequired()])
    birthday = DateField('生日', format='%Y-%m-%d', validators=[DataRequired()])
    zodiac = SelectField('星座', choices=[
        ('白羊座', '白羊座'), ('金牛座', '金牛座'), ('双子座', '双子座'),
        ('巨蟹座', '巨蟹座'), ('狮子座', '狮子座'), ('处女座', '处女座'),
        ('天秤座', '天秤座'), ('天蝎座', '天蝎座'), ('射手座', '射手座'),
        ('摩羯座', '摩羯座'), ('水瓶座', '水瓶座'), ('双鱼座', '双鱼座')
    ])
    location = StringField('现居地')
    occupation = StringField('职业')
    bio = TextAreaField('个人介绍')


class EditArticleForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired()])
    summary = TextAreaField('摘要', validators=[DataRequired()])
    content = TextAreaField('内容', validators=[DataRequired()])
    content_images = FileField('上传图片', validators=[FileAllowed(['png', 'jpg', 'jpeg', 'gif', 'bmp'])])
    cover_image = FileField('封面图片', validators=[FileAllowed(['jpg', 'png', 'jpeg'], '仅支持图片文件')])
    category = QuerySelectField('分类', query_factory=category_choices, get_label='name', allow_blank=True)
    tags = QuerySelectMultipleField('标签', query_factory=tag_choices, get_label='name')

class CommentForm(FlaskForm):
    content = TextAreaField('评论内容', validators=[DataRequired(message='评论内容不能为空')])