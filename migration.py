import pandas as pd
from sqlalchemy import create_engine

# Caminhos e credenciais
# Conexão SQLite local
sqlite_url = 'sqlite:///instance/database.db'

# Conexão Supabase (substitua pela sua URL completa)
supabase_url = 'postgresql+psycopg://postgres:Arahuzim26052300!@db.voibxmtriglolckeomgh.supabase.co:5432/postgres'

# Cria engines
sqlite_engine = create_engine(sqlite_url)
pg_engine = create_engine(supabase_url)

# Lista das tabelas na ordem certa (por causa das chaves estrangeiras)
tables = ['books', 'quotes', 'characters']

# Migração
for table in tables:
    print(f'📦 Migrando tabela: {table}...')
    df = pd.read_sql_table(table, sqlite_engine)
    if not df.empty:
        df.to_sql(table, pg_engine, if_exists='append', index=False)
        print(f'✅ {len(df)} registros inseridos em {table}.')
    else:
        print(f'⚠️ Tabela {table} está vazia, ignorada.')

print('\n🚀 Migração concluída com sucesso!')
