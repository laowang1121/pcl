from .__init__ import db, create_app

app = create_app()

# 使用 app.app_context() 进入应用上下文，这样就可以访问数据库了
with app.app_context():
    # 创建数据库表
    db.create_all()
