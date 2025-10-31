from flask import Flask, render_template, request, redirect, url_for, send_file
from sqlalchemy import desc
from image_utils import generate_quote_image
from models import db, Book, Quote, Character, fetch_books
from sqlalchemy.sql.expression import func
from sqlalchemy.sql import text
import os

app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg://postgres:Arahuzim26052300!@db.voibxmtriglolckeomgh.supabase.co:5432/postgres'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


@app.route('/')
def random_quotes():
    """Exibe citações aleatórias na página inicial."""
    search_query = request.args.get('search')
    if search_query:
        quotes = Quote.query.join(Book).filter(
            (Quote.text.contains(search_query)) |
            (Book.title.contains(search_query)) |
            (Book.author.contains(search_query))
        ).all()
    else:
        quotes = Quote.query.order_by(func.random()).all()
    return render_template('index.html', quotes=quotes)


@app.route('/all')
def all_quotes():
    search_query = request.args.get('search')
    books = db.session.query(
        Book,
        func.count(Quote.id).label('quote_count')
    ).join(Quote, Book.id == Quote.book_id, isouter=True).group_by(Book.id).all()

    if search_query:
        quotes = Quote.query.join(Book).filter(
            (Quote.text.contains(search_query)) |
            (Book.title.contains(search_query)) |
            (Book.author.contains(search_query)) |
            (Quote.notes.contains(search_query))
        ).order_by(desc(Quote.id)).all()  # Ordenação em ordem decrescente
    else:
        quotes = Quote.query.order_by(desc(Quote.id)).all()  # Ordenação em ordem decrescente

    return render_template('index.html', quotes=quotes, books=books)

@app.route('/details')
def book_details():
    search_query = request.args.get('search', '')

    # Base query para buscar livros com resumo, rating e personagens
    query = db.session.query(
        Book.id,
        Book.title,
        Book.author,
        Book.cover,
        Book.summary,
        Book.rating,
        func.group_concat(Character.name, ', ').label('characters')  # Concatena os nomes dos personagens
    ).outerjoin(Character).group_by(Book.id)

    if search_query:
        query = query.filter(
            (Book.title.contains(search_query)) |
            (Book.author.contains(search_query)) |
            (Book.summary.contains(search_query))
        )

    books = query.all()
    return render_template('details.html', books=books)

@app.route('/details/<int:book_id>')
def book_detail_page(book_id):
    """Exibe detalhes de um livro específico."""
    book = Book.query.get_or_404(book_id)
    characters = Character.query.filter_by(book_id=book_id).all()
    return render_template('book_detail.html', book=book, characters=characters)




@app.route('/gallery')
def gallery_view():
    """Exibe uma galeria com as capas dos livros."""
    books = Book.query.all()
    return render_template('gallery.html', books=books)


@app.route('/book_gallery')
def book_gallery():
    books = fetch_books()  # Lista de tuplas (Book, quote_count)
    return render_template('book_gallery.html', books=books)


@app.route('/characters', methods=['GET'])
def characters():
    """Exibe uma lista de personagens, com suporte a busca e ordenação."""
    # Obtém o parâmetro de busca (search) e de ordenação (sort) da URL
    search_query = request.args.get('search', '')
    sort_option = request.args.get('sort', '')

    # Consulta base: relaciona personagens e livros
    query = db.session.query(Character, Book).join(Book)

    # Aplica filtro se houver um termo de busca
    if search_query:
        query = query.filter(
            (Character.name.contains(search_query)) |  # Busca por nome
            (Character.description.contains(search_query)) |  # Busca por descrição
            (Character.tags.contains(search_query))  # Busca por tags
        )

    # Aplica ordenação com base no parâmetro 'sort'
    if sort_option == 'rating_desc':
        query = query.order_by(Character.rating.desc())  # Ordenação por rating decrescente
    else:
        query = query.order_by(func.random())  # Ordenação aleatória padrão

    # Busca os resultados
    characters = query.all()

    # Renderiza o template com os resultados e a opção de ordenação atual
    return render_template('characters.html', characters=characters, sort=sort_option)





@app.route('/type/<int:type_id>')
def filter_by_type(type_id):
    """Filtra citações por tipo respeitando os parâmetros atuais da URL."""
    search_query = request.args.get('search', '')
    view_mode = request.args.get('view', '')

    # Base query com filtro por tipo
    quotes = Quote.query.filter_by(type=type_id)

    # Consulta para obter os livros com contagem de citações
    books = db.session.query(
        Book,
        func.count(Quote.id).label('quote_count')
    ).join(Quote).filter(Quote.type == type_id).group_by(Book.id).all()

    # Aplicar busca, se existir
    if search_query:
        quotes = quotes.join(Book).filter(
            (Quote.text.contains(search_query)) |
            (Book.title.contains(search_query)) |
            (Book.author.contains(search_query))
        )

    # Buscar citações filtradas
    quotes = quotes.all()

    # Respeitar a visualização atual (gallery ou table)
    if view_mode == 'gallery':
        return render_template('index.html', books=books, view='gallery')

    return render_template('index.html', quotes=quotes, books=books, view='table')





@app.route('/add_quote', methods=['GET', 'POST'])
def add_quote():
    if request.method == 'POST':
        page = request.form['page']
        type = request.form['type']
        text = request.form['text']
        book_title = request.form['book']
        author = request.form['author']
        cover = request.form['cover']

        # Buscar ou criar livro
        book = Book.query.filter_by(title=book_title).first()
        if not book:
            book = Book(title=book_title, author=author, cover=cover)
            db.session.add(book)
            db.session.commit()

        # Adicionar quote
        new_quote = Quote(
            page=page,
            type=type,
            text=text,
            book_id=book.id
        )
        db.session.add(new_quote)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_quote.html')


@app.route('/update_note', methods=['POST'])
def update_note():
    data = request.get_json()
    quote_id = data.get('quote_id')
    new_note = data.get('note')

    if quote_id is None:
        return {'status': 'error', 'message': 'ID da citação não fornecido'}, 400

    quote = Quote.query.get(quote_id)
    if not quote:
        return {'status': 'error', 'message': 'Citação não encontrada'}, 404

    if new_note == '':  # Exclusão de nota
        quote.notes = None
        message = 'Nota removida com sucesso'
    else:  # Edição ou Salvamento de nota
        quote.notes = new_note.strip()
        message = 'Nota atualizada com sucesso'

    db.session.commit()
    return {'status': 'success', 'message': message}




@app.route('/sql-query', methods=['GET', 'POST'])
def sql_query():
    if request.method == 'POST':
        query = request.form.get('sql_query')
        try:
            result = db.session.execute(text(query))
            results = [dict(row) for row in result]
        except Exception as e:
            return f"Erro: {e}"
    return render_template('index.html', sql_results=results)


@app.route('/download_quote/<int:quote_id>')
def download_quote(quote_id):
    # Busca a citação no banco de dados pelo ID
    quote = Quote.query.get_or_404(quote_id)

    # Usa as propriedades do objeto SQLAlchemy
    file_path = generate_quote_image(quote.text, quote.book.author, quote.book.title)

    # Retorna a imagem gerada para download
    return send_file(file_path, as_attachment=True)



if __name__ == '__main__':
    app.run(debug=True, port=5001)
