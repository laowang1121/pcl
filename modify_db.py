import sqlite3

# 连接到数据库文件
conn = sqlite3.connect(r'D:\javaxmu\one\前端项目\my_flask_project\flaskProject3\instance\blog.db')
cursor = conn.cursor()

# 添加新列
try:
    cursor.execute("ALTER TABLE articles ADD COLUMN cover_image TEXT;")
    print("Column added successfully.")
except sqlite3.OperationalError as e:
    print(f"Error: {e}")

# 关闭连接
conn.commit()
conn.close()
