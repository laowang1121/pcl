import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# 创建数据库实例和登录管理器实例
db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    # 配置应用
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "blog.db")}'  # 指定数据库路径
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = '123'  # 设置 Flask 密钥

    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)

    # 导入模型并初始化数据库（避免循环导入）
    with app.app_context():
        db.create_all()  # 创建所有数据库表

    # 设置用户加载函数
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))

    return app

