from .__init__ import db
from models import Article
from datetime import datetime

articles = Article.query.all()
for article in articles:
    if not article.created_at:
        article.created_at = datetime.utcnow()
        db.session.add(article)
db.session.commit()
