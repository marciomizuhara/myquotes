from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from sqlalchemy.sql.expression import func

db = SQLAlchemy()

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    cover = db.Column(db.String(200))  # Caminho para a imagem da capa
    quotes = db.relationship('Quote', backref='book', lazy=True, cascade="all, delete")
    summary = db.Column(db.Text)
    rating = db.Column(db.Integer)
    characters = db.relationship('Character', backref='book', lazy=True)

class Character(db.Model):
    __tablename__ = 'characters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text, nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    rating = db.Column(db.String, nullable=True, default=0)  # Permite inteiros ou floats, com valor padrão 0
    tags = db.Column(db.String, nullable=True)  # Para armazenar as tags como uma string separada por vírgulas


class Quote(db.Model):
    __tablename__ = 'quotes'
    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.Integer, nullable=True)
    type = db.Column(db.String(50))
    text = db.Column(db.String(500), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    notes = db.Column(db.Text)  # Novo campo para anotações


# Função para buscar livros
def fetch_books():
    books_with_quotes = db.session.query(
        Book,
        func.count(Quote.id).label('quote_count')  # Conta as citações por livro
    ).outerjoin(Quote, Book.id == Quote.book_id).group_by(Book.id).order_by(desc(Book.id)).all()

    return books_with_quotes

