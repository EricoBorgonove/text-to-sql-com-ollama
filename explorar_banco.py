
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL

load_dotenv()

url = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(url)
inspetor = inspect(engine)

print("\n=== BANCO DE DADOS DA LOCADORA ===")

with engine.connect() as conexao:
    total = conexao.execute(
        text("SELECT COUNT(*) FROM locacoes")
    ).scalar_one()

    print(f"\nLocações cadastradas: {total}")

print("\n=== TABELAS E RELACIONAMENTOS ===")

for tabela in inspetor.get_table_names():
    print(f"\nTABELA: {tabela}")

    for coluna in inspetor.get_columns(tabela):
        print(f"  {coluna['name']} ({coluna['type']})")

    for fk in inspetor.get_foreign_keys(tabela):
        origem = ", ".join(fk["constrained_columns"])
        destino = ", ".join(fk["referred_columns"])

        print(
            f"  RELACIONAMENTO: {origem} → "
            f"{fk['referred_table']}.{destino}"
        )

print("\n=== VIEWS ===")

for view in inspetor.get_view_names():
    print(view)

print("\nExploração concluída!")
