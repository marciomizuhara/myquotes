from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from sqlalchemy import desc, func, text
from image_utils import generate_quote_image
from models import db, Book, Quote, Character, fetch_books
import os

app = Flask(__name__)

# ✅ Conexão com PostgreSQL (Supabase)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'postgresql+psycopg://postgres:Arahuzim26052300!@db.voibxmtriglolckeomgh.supabase.co:5432/postgres'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


# ==============================
# 🔹 HOME / RANDOM QUOTES
# ==============================
@app.route('/')
def random_quotes():
    """Página inicial: exibe citações aleatórias ou resultado de busca."""
    search_query = request.args.get('search')

    if search_query:
        quotes = (
            db.session.query(Quote)
            .join(Book)
            .filter(
                (Quote.text.ilike(f"%{search_query}%")) |
                (Book.title.ilike(f"%{search_query}%")) |
                (Book.author.ilike(f"%{search_query}%")) |
                (Quote.notes.ilike(f"%{search_query}%"))
            )
            .order_by(desc(Quote.id))
            .all()
        )
    else:
        quotes = db.session.query(Quote).order_by(func.random()).limit(100).all()

    books = fetch_books()

    return render_template('index.html', quotes=quotes, books=books)


# ==============================
# 🔹 ALL QUOTES
# ==============================
@app.route('/all')
def all_quotes():
    """Lista todas as citações, com busca e ordenação decrescente."""
    search_query = request.args.get('search')

    if search_query:
        quotes = (
            db.session.query(Quote)
            .join(Book)
            .filter(
                (Quote.text.ilike(f"%{search_query}%")) |
                (Book.title.ilike(f"%{search_query}%")) |
                (Book.author.ilike(f"%{search_query}%")) |
                (Quote.notes.ilike(f"%{search_query}%"))
            )
            .order_by(desc(Quote.id))
            .all()
        )
    else:
        quotes = db.session.query(Quote).order_by(desc(Quote.id)).all()

    books = fetch_books()
    return render_template('index.html', quotes=quotes, books=books)


# ==============================
# 🔹 BOOK DETAILS
# ==============================
@app.route('/details')
def book_details():
    """Exibe lista de livros com personagens agregados e resumo."""
    search_query = request.args.get('search', '')

    query = (
        db.session.query(
            Book.id,
            Book.title,
            Book.author,
            Book.cover,
            Book.summary,
            Book.rating,
            func.coalesce(
                func.string_agg(
                    Character.name,
                    text("', '")
                ),
                ''
            ).label('characters')
        )
        .outerjoin(Character, Character.book_id == Book.id)
        .group_by(
            Book.id,
            Book.title,
            Book.author,
            Book.cover,
            Book.summary,
            Book.rating
        )
        .order_by(desc(Book.id))
    )

    if search_query:
        query = query.filter(
            (Book.title.ilike(f"%{search_query}%")) |
            (Book.author.ilike(f"%{search_query}%")) |
            (Book.summary.ilike(f"%{search_query}%"))
        )

    books = query.all()
    return render_template('details.html', books=books)


@app.route('/details/<int:book_id>')
def book_detail_page(book_id):
    """Página individual de um livro."""
    book = Book.query.get_or_404(book_id)
    characters = (
        Character.query.filter_by(book_id=book_id)
        .order_by(desc(Character.rating))
        .all()
    )
    return render_template('book_detail.html', book=book, characters=characters)


# ==============================
# 🔹 BOOK GALLERY
# ==============================
@app.route('/gallery')
def gallery_view():
    books = fetch_books()
    return render_template('book_gallery.html', books=books)


@app.route('/book_gallery')
def book_gallery():
    books = fetch_books()
    return render_template('book_gallery.html', books=books)


# ==============================
# 🔹 CHARACTERS
# ==============================
@app.route('/characters', methods=['GET'])
def characters_view():
    """Exibe personagens, com busca e ordenação por rating."""
    search_query = request.args.get('search', '')
    sort_option = request.args.get('sort', '')

    query = db.session.query(Character, Book).join(Book)

    if search_query:
        query = query.filter(
            (Character.name.ilike(f"%{search_query}%")) |
            (Character.description.ilike(f"%{search_query}%")) |
            (Character.tags.ilike(f"%{search_query}%"))
        )

    if sort_option == 'rating_desc':
        query = query.order_by(desc(Character.rating))
    else:
        query = query.order_by(func.random())

    characters = query.all()
    return render_template('characters.html', characters=characters, sort=sort_option)


# ==============================
# 🔹 FILTER BY TYPE (color)
# ==============================
@app.route('/type/<int:type_id>')
def filter_by_type(type_id):
    """Filtra citações por tipo (cor)."""
    search_query = request.args.get('search', '')
    view_mode = request.args.get('view', '')

    quotes_query = db.session.query(Quote).filter(Quote.type == str(type_id))

    if search_query:
        quotes_query = quotes_query.join(Book).filter(
            (Quote.text.ilike(f"%{search_query}%")) |
            (Book.title.ilike(f"%{search_query}%")) |
            (Book.author.ilike(f"%{search_query}%")) |
            (Quote.notes.ilike(f"%{search_query}%"))
        )

    quotes = quotes_query.order_by(desc(Quote.id)).all()

    books = (
        db.session.query(Book, func.count(Quote.id).label('quote_count'))
        .join(Quote, Quote.book_id == Book.id)
        .filter(Quote.type == str(type_id))
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

    if view_mode == 'gallery':
        return render_template('index.html', books=books, view='gallery')

    return render_template('index.html', quotes=quotes, books=books, view='table')


# ==============================
# 🔹 UPDATE NOTE (AJAX)
# ==============================
@app.route('/update_note', methods=['POST'])
def update_note():
    data = request.get_json()
    quote_id = data.get('quote_id')
    new_note = data.get('note')

    if not quote_id:
        return jsonify({'status': 'error', 'message': 'ID da citação não fornecido'}), 400

    quote = Quote.query.get(quote_id)
    if not quote:
        return jsonify({'status': 'error', 'message': 'Citação não encontrada'}), 404

    if new_note == '':
        quote.notes = None
        message = 'Nota removida com sucesso'
    else:
        quote.notes = new_note.strip()
        message = 'Nota atualizada com sucesso'

    db.session.commit()
    return jsonify({'status': 'success', 'message': message})


# ==============================
# 🔹 DOWNLOAD QUOTE IMAGE
# ==============================
@app.route('/download_quote/<int:quote_id>')
def download_quote(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    file_path = generate_quote_image(quote.text, quote.book.author, quote.book.title)
    return send_file(file_path, as_attachment=True)


# ==============================
# 🔹 RUN APP
# ==============================
if __name__ == '__main__':
    app.run(debug=True, port=5001)
