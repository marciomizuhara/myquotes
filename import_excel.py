import os
import shutil
import pandas as pd
import json
import time
import re
from sqlalchemy import func
from openpyxl import Workbook
from app import db, app
from models import Book, Quote
from pathlib import Path
import win32com.client

# -------------------------------
# 0️⃣ Caminhos principais
# -------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"

BACKUP_DIR = Path(r"C:\Users\marci\Desktop\myclippings_backup")
INPUT_FILE = INPUT_DIR / "My Clippings.txt"
EXCEL_FILE = OUTPUT_DIR / "quotes.xlsx"
CACHE_FILE = DATA_DIR / "quote_cache.json"

# -------------------------------
# 🔁 Etapa de cópia do Kindle (INALTERADA)
# -------------------------------
def find_kindle_file():
    print("🔍 Procurando o Kindle conectado...")

    possible_drives = [f"{chr(c)}:" for c in range(65, 91)]
    for drive in possible_drives:
        kindle_path = Path(f"{drive}\\documents\\My Clippings.txt")
        if kindle_path.exists():
            print(f"📗 Kindle detectado via unidade ({drive})")
            return kindle_path

    shell = win32com.client.Dispatch("Shell.Application")
    for item in shell.NameSpace(17).Items():
        if "Kindle" in item.Name:
            print(f"📘 Kindle detectado via MTP: {item.Name}")
            try:
                kindle_ns = item.GetFolder
                docs_folder = kindle_ns.ParseName("Internal storage").GetFolder
                documents = docs_folder.ParseName("documents").GetFolder
                my_clippings = documents.ParseName("My Clippings.txt")
                if my_clippings:
                    print("✅ Arquivo My Clippings.txt encontrado (modo MTP)!")
                    return my_clippings
            except Exception:
                pass

    print("❌ Kindle não encontrado.")
    return None


def copy_from_kindle():
    print("📥 Iniciando cópia do My Clippings do Kindle...\n")

    kindle_item = find_kindle_file()
    if not kindle_item:
        print("❌ Arquivo My Clippings.txt não encontrado. Conecte o Kindle e tente novamente.")
        return False

    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        INPUT_DIR.mkdir(parents=True, exist_ok=True)

        backup_path = BACKUP_DIR / "My Clippings.txt"
        input_path = INPUT_FILE

        if isinstance(kindle_item, Path):
            shutil.copy2(kindle_item, backup_path)
            shutil.copy2(kindle_item, input_path)
            print(f"✅ Copiado via unidade: {kindle_item}")
        else:
            shell = win32com.client.Dispatch("Shell.Application")
            target_ns = shell.NameSpace(str(INPUT_DIR))
            print("📄 Copiando via MTP (isso pode levar alguns segundos)...")
            target_ns.CopyHere(kindle_item, 16)
            time.sleep(2)
            copied_path = INPUT_DIR / "My Clippings.txt"
            if copied_path.exists():
                shutil.copy2(copied_path, backup_path)
            else:
                raise FileNotFoundError("Falha ao copiar via MTP")

        print(f"✅ Backup criado em: {backup_path}")
        print(f"✅ Arquivo atualizado no diretório de input: {input_path}")
        print("📚 Cópia concluída com sucesso! Prosseguindo para o processamento...\n")
        return True

    except Exception as e:
        print(f"❌ Erro ao copiar arquivo: {e}")
        return False


# -------------------------------
# 1️⃣ Lógica de Processamento
# -------------------------------
def get_type_and_note(note):
    note = note.strip()
    lower_note = note.lower()
    if lower_note.startswith('nota'):
        return -1, note
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
    return 0, ''


def extract_rating_from_note(text):
    if not text:
        return None

    match = re.search(r'(\d+(?:\.\d+)?)', text)
    if not match:
        return None

    try:
        value = float(match.group(1))
        if 0.0 <= value <= 5.0:
            return round(value, 1)
    except ValueError:
        pass

    return None


def process_clippings():
    wb = Workbook()
    ws = wb.active
    ws.title = "Valid Quotes"

    ws.append([
        'Page', 'Type', 'Quote', 'Author', 'Book', 'Note',
        'LocationStart', 'LocationEnd'
    ])

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        raw_data = f.read()

    blocks = [b.strip() for b in raw_data.split('==========') if b.strip()]

    highlights = {}
    notes_by_location = {}
    ratings_detected = []

    skipped_clippings = 0

    for block in blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if len(lines) < 2:
            continue

        book_info = lines[0]
        if '(' in book_info and ')' in book_info:
            book_title = book_info.split('(')[0].strip()
            author = book_info.split('(')[-1].replace(')', '').strip()
        else:
            book_title = book_info.strip()
            author = 'Unknown'

        meta_info = lines[1]
        meta_lower = meta_info.lower()

        page = None
        if 'page' in meta_lower:
            parts = [p for p in meta_info.split('|') if 'page' in p.lower()]
            if parts:
                try:
                    page = int(parts[0].split()[-1])
                except ValueError:
                    page = None

        loc_match = re.search(r'location\s+(\d+)(?:-(\d+))?', meta_lower)
        if not loc_match:
            continue

        loc_start = int(loc_match.group(1))
        loc_end = int(loc_match.group(2)) if loc_match.group(2) else loc_start

        content = '\n'.join(lines[2:]).strip()

        if content.startswith("<You have reached") or "<You have reached" in content:
            skipped_clippings += 1
            continue

        # ⭐ BLOCO ANTIGO DE RATING POR HIGHLIGHT (NEUTRALIZADO)
        # Mantido propositalmente para preservar o script
        if 'highlight' in meta_lower and content.lower().startswith('nota'):
            continue

        key = (book_title, author, loc_start, loc_end)

        if 'highlight' in meta_lower:
            highlights[key] = {
                'page': page,
                'quote': content,
                'author': author,
                'book': book_title,
                'location_start': loc_start,
                'location_end': loc_end
            }

        elif 'note' in meta_lower:
            note_type, note_text = get_type_and_note(content)
            if note_type == 0:
                continue

            notes_by_location[(book_title, author, loc_start)] = {
                'type': note_type,
                'note': note_text
            }

    for (book, author, h_start, h_end), h in highlights.items():
        final_type = 0
        final_note = ''

        for (nb, na, n_loc), note in notes_by_location.items():
            if nb != book or na != author:
                continue
            if h_start <= n_loc <= h_end:
                final_type = note['type']
                final_note = note['note']
                break

        # ⭐ RATING: NOTE "Nota X" após associação canônica
        if final_note.lower().startswith('nota'):
            rating = extract_rating_from_note(final_note)
            if rating is not None:
                ratings_detected.append({
                    'book': book,
                    'author': author,
                    'rating': rating
                })
                print(
                    f"⭐ Rating detectado via NOTE | "
                    f"Livro: {book} | "
                    f"Location: {h_start}-{h_end} | "
                    f"Valor: {rating}"
                )
            continue

        if final_type == 0:
            continue

        ws.append([
            h['page'],
            final_type,
            h['quote'].strip(),
            author,
            book,
            final_note.strip(),
            h['location_start'],
            h['location_end']
        ])

    wb.save(EXCEL_FILE)
    print(f"✅ Arquivo Excel salvo com sucesso: {EXCEL_FILE}")
    print(f"📘 Ratings detectados: {len(ratings_detected)}")

    return ratings_detected


# -------------------------------
# 2️⃣ Importação para o banco
# -------------------------------
def load_cache():
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            print("⚠️ Cache corrompido — recriando...")
    return {}


def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def import_from_excel(ratings_detected):
    with app.app_context():
        df = pd.read_excel(EXCEL_FILE)
        cache = load_cache()

        inserted = 0
        updated = 0
        skipped = 0

        CUTOFF_BOOK_ID = 63

        existing_books = {
            b.title.lower(): b
            for b in Book.query.all()
        }

        # ⭐ Aplicação dos ratings
        for item in ratings_detected:
            book = existing_books.get(item['book'].lower())
            if not book or book.id < CUTOFF_BOOK_ID:
                continue

            rating = item['rating']

            if book.rating is None:
                book.rating = rating
                print(f"🟢 Rating definido | {book.title} = {rating}")
            elif abs(book.rating - rating) >= 0.1:
                old = book.rating
                book.rating = rating
                print(f"🟡 Rating atualizado | {book.title}: {old} → {rating}")
            else:
                print(f"⚪ Rating ignorado | {book.title}")

        for idx, row in df.iterrows():
            if pd.isna(row['Book']) or pd.isna(row['Quote']):
                continue

            book_title = row['Book'].strip()
            book_key = book_title.lower()

            book = existing_books.get(book_key)
            if not book:
                book = Book(
                    title=book_title,
                    author=row['Author'].strip() if pd.notna(row['Author']) else 'Unknown'
                )
                db.session.add(book)
                db.session.flush()
                existing_books[book_key] = book

            if book.id < CUTOFF_BOOK_ID:
                skipped += 1
                continue

            quote_text = row['Quote'].strip()
            note_text = row['Note'].strip() if isinstance(row['Note'], str) else ''
            quote_type = int(row['Type']) if not pd.isna(row['Type']) else 0

            if quote_type == 0:
                skipped += 1
                continue

            loc_start = int(row['LocationStart']) if not pd.isna(row['LocationStart']) else None
            loc_end = int(row['LocationEnd']) if not pd.isna(row['LocationEnd']) else None

            cache_key = f"{book.id}|{loc_start}"
            if cache_key in cache:
                skipped += 1
                continue

            existing_quote = Quote.query.filter(
                Quote.book_id == book.id,
                Quote.location_start == loc_start
            ).first()

            if existing_quote:
                changed = False

                if len(quote_text) > len(existing_quote.text):
                    existing_quote.text = quote_text
                    changed = True

                if note_text and (not existing_quote.notes or existing_quote.notes.strip() == ''):
                    existing_quote.notes = note_text
                    changed = True

                if existing_quote.type != quote_type:
                    existing_quote.type = quote_type
                    changed = True

                if changed:
                    updated += 1

                cache[cache_key] = True
                skipped += 1
                continue

            new_quote = Quote(
                book_id=book.id,
                text=quote_text,
                notes=note_text,
                type=quote_type,
                page=row['Page'] if not pd.notna(row['Page']) else None,
                location_start=loc_start,
                location_end=loc_end
            )

            db.session.add(new_quote)
            cache[cache_key] = True
            inserted += 1

        db.session.commit()
        save_cache(cache)

        print("✅ Commit realizado com sucesso.")
        print(f"🟢 Inseridas: {inserted}")
        print(f"🟡 Atualizadas: {updated}")
        print(f"⚪ Ignoradas: {skipped}")


# -------------------------------
# 3️⃣ Execução principal
# -------------------------------
if __name__ == '__main__':
    if copy_from_kindle():
        print("🔄 Processando My Clippings...")
        ratings = process_clippings()
        time.sleep(1)
        print("📥 Importando para o banco...")
        import_from_excel(ratings)
    else:
        print("❌ Operação cancelada — Kindle não encontrado.")
