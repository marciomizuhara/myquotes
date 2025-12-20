import pandas as pd
from supabase import create_client, Client

# 🔹 CONFIGURAÇÕES DO SUPABASE
SUPABASE_URL = "https://voibxmtriglolckeomgh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZvaWJ4bXRyaWdsb2xja2VvbWdoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE5MzQ4MjYsImV4cCI6MjA3NzUxMDgyNn0.P8bmGR87sW_q8EVCQxJQKiGwZ_i7-kh47pQVnokjQQQ"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🔹 LER PLANILHA
excel_path = "data/input/characters_to_update.xlsx"
df = pd.read_excel(excel_path)

# 🔹 REMOVER COLUNA ID (se existir)
if "id" in df.columns:
    df = df.drop(columns=["id"])

rows = df.to_dict(orient="records")

print(f"📘 Iniciando importação de {len(rows)} personagens...\n")

for i, row in enumerate(rows, start=1):
    try:
        name = row.get("name")
        book_id = int(row.get("book_id")) if pd.notna(row.get("book_id")) else None

        if not name or not book_id:
            print(f"⚠️ ({i}) Ignorado: dados insuficientes → name='{name}', book_id={book_id}")
            continue

        # 🔹 Checa se já existe no DB (mesmo nome + mesmo livro)
        existing = supabase.table("characters") \
            .select("id") \
            .eq("name", name.strip()) \
            .eq("book_id", book_id) \
            .execute()

        if existing.data:
            print(f"⏩ ({i}) Já existe no banco: {name} (book_id={book_id})")
            continue

        # 🔹 Insere se não existir
        data = {
            "name": name.strip(),
            "description": row.get("description"),
            "book_id": book_id,
            "tags": row.get("tags"),
            "rating": float(row.get("rating")) if pd.notna(row.get("rating")) else None,
        }

        supabase.table("characters").insert(data).execute()
        print(f"✅ ({i}) Inserido: {name}")

    except Exception as e:
        print(f"❌ ({i}) Erro ao processar {row.get('name')}: {e}")

print("\n🎯 Importação concluída!")
