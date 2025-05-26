from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileAllowed

class ProfileForm(FlaskForm):
    nickname = StringField('昵称', validators=[DataRequired()])
    gender = StringField('性别', validators=[DataRequired()])
    birthday = DateField('生日', format='%Y-%m-%d', validators=[DataRequired()])
    zodiac = StringField('星座')
    location = StringField('现居地')
    occupation = StringField('职业')
    bio = TextAreaField('个人介绍')


class EditArticleForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired()])
    summary = TextAreaField('摘要', validators=[DataRequired()])
    content = TextAreaField('内容', validators=[DataRequired()])
    content_images = FileField('上传图片', validators=[FileAllowed(['png', 'jpg', 'jpeg', 'gif', 'bmp'])])
    cover_image = FileField('封面图片', validators=[FileAllowed(['jpg', 'png', 'jpeg'], '仅支持图片文件')])