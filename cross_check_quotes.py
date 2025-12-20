import re
import time
from pathlib import Path
from rapidfuzz import fuzz, process
from tqdm import tqdm
from app import db, app
from models import Quote, Book

# -------------------------------
# 🔧 Caminhos principais
# -------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DB_QUOTES_FILE = OUTPUT_DIR / "quotes_do_db.txt"
NEW_QUOTES_FILE = OUTPUT_DIR / "quotes_que_nao_estao_no_db.txt"
CLIPPINGS_FILE = INPUT_DIR / "My Clippings.txt"

# -------------------------------
# 1️⃣ Coleta de citações do banco
# -------------------------------
def fetch_quotes_from_db():
    print("📡 Acessando banco de dados remoto...")
    db_quotes = []

    with app.app_context():
        quotes = (
            db.session.query(Quote.text, Book.title)
            .join(Book, Quote.book_id == Book.id)
            .all()
        )

    for text, book in quotes:
        db_quotes.append(text.strip())

    with open(DB_QUOTES_FILE, "w", encoding="utf-8") as f:
        for text, book in quotes:
            f.write(f"[{book}] {text.strip()}\n")

    print(f"✅ {len(db_quotes)} citações carregadas do banco e salvas em {DB_QUOTES_FILE}\n")
    return db_quotes


# -------------------------------
# 2️⃣ Processamento do My Clippings
# -------------------------------
def parse_clippings():
    print("📘 Lendo e processando My Clippings.txt...\n")

    with open(CLIPPINGS_FILE, "r", encoding="utf-8") as f:
        raw_data = f.read()

    blocks = raw_data.split("==========")
    valid_quotes = []
    color_prefixes = ("verde", "amarelo", "azul", "vermelho")

    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 3:
            continue

        header = lines[0]
        meta = lines[1].lower()
        content = " ".join(lines[2:]).strip()

        # Apenas blocos de destaque (highlight)
        if "highlight" not in meta:
            continue

        # Ignorar notas coloridas e vazias
        if not content or content.lower().startswith(color_prefixes):
            continue

        # Extrair título e autor
        if "(" in header and ")" in header:
            book_title = header.split("(")[0].strip()
            author = header.split("(")[-1].replace(")", "").strip()
        else:
            book_title = header.strip()
            author = "Unknown"

        # Extrair página, se houver
        page_match = re.search(r"page\s+(\d+)", meta, re.IGNORECASE)
        page = int(page_match.group(1)) if page_match else None

        valid_quotes.append({
            "book": book_title,
            "author": author,
            "page": page,
            "quote": content
        })

    print(f"✅ {len(valid_quotes)} citações válidas extraídas do My Clippings.\n")
    return valid_quotes


# -------------------------------
# 3️⃣ Cross-check com barra de progresso
# -------------------------------
def cross_check_quotes(db_quotes, kindle_quotes, threshold=90):
    print("⚡ Iniciando comparação com RapidFuzz + barra de progresso...\n")
    new_quotes = []

    for item in tqdm(kindle_quotes, desc="Comparando citações", unit="quote"):
        text = item["quote"]
        match = process.extractOne(text, db_quotes, scorer=fuzz.ratio, score_cutoff=threshold)
        if not match:
            new_quotes.append(item)

    print(f"\n🆕 {len(new_quotes)} citações novas detectadas.")
    with open(NEW_QUOTES_FILE, "w", encoding="utf-8") as f:
        for q in new_quotes:
            f.write(f"📖 {q['book']} ({q['author']})\n")
            if q["page"]:
                f.write(f"📄 Página: {q['page']}\n")
            f.write(f"💬 {q['quote']}\n")
            f.write("---\n\n")

    print(f"💾 Salvas em {NEW_QUOTES_FILE}\n")


# -------------------------------
# 🚀 Execução principal
# -------------------------------
if __name__ == "__main__":
    start = time.time()

    db_quotes = fetch_quotes_from_db()
    kindle_quotes = parse_clippings()
    cross_check_quotes(db_quotes, kindle_quotes, threshold=90)

    elapsed = round(time.time() - start, 2)
    print(f"✅ Concluído em {elapsed}s.")
