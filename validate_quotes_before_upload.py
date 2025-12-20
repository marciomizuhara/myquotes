import re
import sys
import time
from pathlib import Path
from rapidfuzz import fuzz, process
from app import db, app
from models import Book, Quote

# -------------------------------
# 🔧 Caminhos principais
# -------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output"
INPUT_FILE = OUTPUT_DIR / "quotes_a_subir.txt"

# -------------------------------
# ⚙️ Modo (dry-run ou commit)
# -------------------------------
commit_mode = len(sys.argv) > 1 and sys.argv[1].lower() == "commit"

# -------------------------------
# 🎨 Tipagem (mesma do import_excel)
# -------------------------------
def get_type_and_note(note):
    note = note.strip()
    lower_note = note.lower()
    if lower_note.startswith('vermelho'):
        return 1, note[8:].strip()
    if lower_note.startswith('amarelo'):
        return 2, note[7:].strip()
    if lower_note.startswith('verde'):
        return 3, note[5:].strip()
    if lower_note.startswith('azul'):
        note_body = note[4:].strip()
        if 'hahaha' in lower_note or 'haha' in lower_note:
            return 4, note_body
        else:
            return 6, note_body
    if lower_note.startswith('ciano'):
        return 5, note[5:].strip()
    if lower_note.isdigit():
        return int(lower_note), ''
    return 0, note.strip()

# -------------------------------
# 📘 Parser do arquivo
# -------------------------------
def parse_quotes_to_upload():
    print("📖 Lendo arquivo quotes_a_subir.txt...\n")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        raw = f.read()

    blocks = raw.split('---')
    quotes = []

    for block in blocks:
        lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
        if len(lines) < 3:
            continue

        book_line = lines[0]
        page_line = lines[1]
        quote_line = lines[2]
        type_line = lines[3] if len(lines) >= 4 else "0"

        # Extrair título e autor
        match = re.match(r"📖 (.+?) \((.+)\)", book_line)
        if match:
            book_title, author = match.groups()
        else:
            book_title, author = "Unknown", "Unknown"

        # Extrair página (tratar Página: sem número → None)
        page_match = re.search(r"Página:\s*(\d+)?", page_line)
        page = int(page_match.group(1)) if page_match and page_match.group(1) else None

        # Converter tipo e nota
        tipo, note = get_type_and_note(type_line)

        quotes.append({
            "book": book_title.strip(),
            "author": author.strip(),
            "page": page,
            "quote": quote_line.strip("💬 ").strip(),
            "type": tipo,
            "note": note
        })

    print(f"✅ {len(quotes)} citações carregadas para validação.\n")
    return quotes

# -------------------------------
# 🔍 Validação e commit opcional
# -------------------------------
def validate_and_maybe_commit(quotes_to_upload, threshold=90):
    print("⚡ Iniciando validação...\n")
    if commit_mode:
        print("🚀 MODO COMMIT ATIVO — alterações serão salvas no banco!\n")
    else:
        print("🧪 MODO DRY-RUN — nenhuma alteração será salva.\n")

    new_quotes_total = 0
    new_books_total = 0

    with app.app_context():
        for q in quotes_to_upload:
            book = (
                Book.query.filter(Book.title.ilike(q["book"]))
                .filter(Book.author.ilike(q["author"]))
                .first()
            )

            if not book:
                print(f"📘 Novo livro detectado: '{q['book']}' ({q['author']})")
                if commit_mode:
                    book = Book(title=q["book"], author=q["author"])
                    db.session.add(book)
                    db.session.flush()
                    new_books_total += 1
                else:
                    print("   → Livro seria criado no modo commit.\n")

            if not book:
                continue

            existing_quotes = Quote.query.filter(Quote.book_id == book.id).all()
            db_texts = [e.text.strip() for e in existing_quotes]

            match = process.extractOne(q["quote"], db_texts, scorer=fuzz.ratio, score_cutoff=threshold)

            if match:
                print(f"✅ Já existe em '{q['book']}' (similaridade {match[1]:.1f}%)")
                print(f"   → {q['quote'][:80]}...\n")
            else:
                print(f"🆕 Nova citação detectada: '{q['book']}' — página {q['page'] or 'NULL'}")
                print(f"💬 {q['quote'][:120]}...")
                print(f"   Tipo: {q['type']} | Nota: {q['note'] or '—'}\n")

                if commit_mode:
                    new_quote = Quote(
                        page=q["page"],  # None vira NULL automaticamente
                        type=q["type"],
                        text=q["quote"],
                        notes=q["note"],
                        book_id=book.id,
                        is_favorite=0
                    )
                    db.session.add(new_quote)
                    new_quotes_total += 1

        if commit_mode:
            db.session.commit()
            print(f"✅ Commit concluído: {new_books_total} livros novos, {new_quotes_total} citações adicionadas.")
        else:
            print("🧪 Nenhum dado foi salvo (modo dry-run).")

# -------------------------------
# 🚀 Execução principal
# -------------------------------
if __name__ == "__main__":
    start = time.time()
    quotes = parse_quotes_to_upload()
    validate_and_maybe_commit(quotes, threshold=90)
    elapsed = round(time.time() - start, 2)
    print(f"\n✅ Processo concluído em {elapsed}s.")
