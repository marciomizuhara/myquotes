from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, func

db = SQLAlchemy()

class Book(db.Model):
    __tablename__ = 'books'
    __table_args__ = (db.Index('idx_book_title', 'title'),)

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    cover = db.Column(db.String(500))
    summary = db.Column(db.Text)
    rating = db.Column(db.Float, nullable=True, default=None)

    quotes = db.relationship('Quote', backref='book', lazy=True, cascade="all, delete")
    characters = db.relationship('Character', backref='book', lazy=True, cascade="all, delete")


class Character(db.Model):
    __tablename__ = 'characters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text, nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    rating = db.Column(db.Float, nullable=True, default=0.0)
    tags = db.Column(db.String, nullable=True)


class Quote(db.Model):
    __tablename__ = 'quotes'
    __table_args__ = (db.Index('idx_quote_book', 'book_id'),)

    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.Integer, nullable=True)
    type = db.Column(db.Integer)
    text = db.Column(db.String(1000), nullable=False)
    notes = db.Column(db.Text)

    is_active = db.Column(db.Integer, nullable=False, default=1)   # ✅ ADICIONAR
    is_favorite = db.Column(db.Integer, nullable=False, default=0)

    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    location_start = db.Column(db.Integer, nullable=True)
    location_end = db.Column(db.Integer, nullable=True)


def fetch_books():
    """Retorna lista [(Book, quote_count)], ordenada por ID desc (mais novos primeiro)."""
    results = (
        db.session.query(
            Book,
            func.count(Quote.id).label('quote_count')
        )
        .outerjoin(Quote, Book.id == Quote.book_id)
        .group_by(
            Book.id,
            Book.title,
            Book.author,
            Book.cover,
            Book.summary,
            Book.rating
        )
        .order_by(desc(Book.id))
        .all()
    )
    return results
