"""Agente 2: valida e executa SELECT em transacao de leitura.

Didatico, nao e uma sandbox de SQL. Use uma conta PostgreSQL somente de leitura.
"""
import re
import sqlglot
from sqlglot import exp
from sqlalchemy import text
from configuracao import obter_engine, obter_esquema

MAX_LINHAS = 20
FUNCOES_PERMITIDAS = {
    "count", "sum", "avg", "min", "max", "round", "coalesce", "date_trunc",
    "extract", "lower", "upper", "abs", "nullif", "length", "trim", "substring",
    "cast", "date", "greatest", "least"
}


def validar_sql(sql):
    sql = sql.strip()
    # Ponto e virgula FINAL e valido em PostgreSQL; removemos apenas o terminador.
    # Ponto e virgula no meio continua bloqueado (multiplas instrucoes).
    if sql.endswith(";"):
        sql = sql[:-1].rstrip()
    if not sql or ";" in sql or "--" in sql or "/*" in sql or "*/" in sql:
        raise ValueError("SQL vazia, com comentarios ou multiplas instrucoes.")
    arvores = sqlglot.parse(sql, read="postgres")
    if len(arvores) != 1 or not isinstance(arvores[0], exp.Select):
        raise ValueError("Apenas SELECT simples e permitido.")
    raiz = arvores[0]
    # Subconsultas SELECT sao permitidas (NOT EXISTS, IN, comparacoes).
    # DML/DDL, CTEs e combinacoes de conjuntos continuam proibidos.
    banidos = (exp.CTE, exp.With, exp.Union, exp.Intersect,
               exp.Except, exp.Insert, exp.Update, exp.Delete, exp.Drop,
               exp.Create, exp.Alter, exp.Command, exp.Into, exp.Lateral)
    if any(isinstance(no, banidos) for no in raiz.walk()):
        raise ValueError("SQL contem estrutura nao permitida nesta pratica.")
    # Nao permitir SELECT ... FOR UPDATE/SHARE.
    if raiz.args.get("locks"):
        raise ValueError("Bloqueio de linhas nao permitido.")
    # Para esta pratica, toda SELECT deve consultar tabelas da locadora.
    tabelas = list(raiz.find_all(exp.Table))
    if not tabelas:
        raise ValueError("Consulta sem tabela nao permitida.")
    _, permitidos = obter_esquema()
    for tabela in tabelas:
        if tabela.name not in permitidos or (tabela.db and tabela.db != "public") or tabela.catalog:
            raise ValueError(f"Tabela nao autorizada: {tabela.sql()}")
    # exp.Func inclui operadores do AST (como AND em algumas versoes do
    # SQLGlot). Validar todo exp.Func pelo nome rejeita SELECTs legitimos.
    # Aqui bloqueamos somente funcoes genericas / nao reconhecidas pelo parser.
    # Funcoes nativas reconhecidas sao controladas pela conta somente leitura,
    # por timeout e pelo limite de linhas. Nao e uma sandbox completa.
    for funcao in raiz.find_all(exp.Anonymous):
        nome = funcao.name.lower()
        if nome not in FUNCOES_PERMITIDAS:
            raise ValueError(f"Funcao nao autorizada: {nome}")
    # Segunda barreira: roles PostgreSQL sem escrita e transacao READ ONLY.
    return raiz.sql(dialect="postgres")


def executar(sql):
    sql_validada = validar_sql(sql)
    with obter_engine().connect() as conexao:
        with conexao.begin():
            conexao.execute(text("SET TRANSACTION READ ONLY"))
            conexao.execute(text("SET LOCAL statement_timeout = '5000ms'"))
            conexao.execute(text("SET LOCAL search_path TO public, pg_catalog"))
            rows = conexao.execute(
                text(f"SELECT * FROM ({sql_validada}) AS resultado_ia LIMIT {MAX_LINHAS}")
            ).mappings().all()
    return sql_validada, [dict(row) for row in rows]
