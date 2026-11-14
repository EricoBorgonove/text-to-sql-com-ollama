"""Conexao e esquema do PostgreSQL para os tres agentes."""
import os
from functools import lru_cache
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import URL

load_dotenv()

@lru_cache(maxsize=1)
def obter_engine():
    url = URL.create(
        "postgresql+psycopg",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.environ["DB_NAME"],
    )
    return create_engine(url, pool_pre_ping=True)

@lru_cache(maxsize=1)
def obter_esquema():
    inspetor = inspect(obter_engine())
    tabelas = inspetor.get_table_names(schema="public")
    views = inspetor.get_view_names(schema="public")
    if not tabelas:
        raise RuntimeError("Nenhuma tabela encontrada no esquema public.")
    partes = []
    for nome in tabelas + views:
        colunas = inspetor.get_columns(nome, schema="public")
        campos = ", ".join(f"{c['name']} {c['type']}" for c in colunas)
        partes.append(f"{'VIEW' if nome in views else 'TABELA'} {nome}: {campos}")
        if nome in tabelas:
            for fk in inspetor.get_foreign_keys(nome, schema="public"):
                a = ",".join(fk["constrained_columns"])
                b = ",".join(fk["referred_columns"])
                partes.append(f"  FK {nome}.{a} -> {fk['referred_table']}.{b}")
    return "\n".join(partes), set(tabelas + views)
