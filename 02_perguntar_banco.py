"""Aula 8 - Prática 2: perguntas em linguagem natural ao PostgreSQL local."""
import json
import os

import requests
import sqlglot
from sqlglot import exp
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL

load_dotenv()

url = URL.create(
    "postgresql+psycopg",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.environ["DB_NAME"],
)
engine = create_engine(url)
inspector = inspect(engine)

# Somente objetos do schema public foram disponibilizados ao agente.
tabelas = inspector.get_table_names(schema="public")
views = inspector.get_view_names(schema="public")
permitidos = set(tabelas + views)


def descrever_esquema():
    partes = []
    for nome in tabelas + views:
        colunas = inspector.get_columns(nome, schema="public")
        campos = ", ".join(f"{c['name']} {c['type']}" for c in colunas)
        partes.append(f"{nome}: {campos}")
        if nome in tabelas:
            for fk in inspector.get_foreign_keys(nome, schema="public"):
                origem = ",".join(fk["constrained_columns"])
                destino = ",".join(fk["referred_columns"])
                partes.append(f"  FK {nome}.{origem} -> {fk['referred_table']}.{destino}")
    return "\n".join(partes)


def consultar_ollama(mensagens, formato="json"):
    resposta = requests.post(
        os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat"),
        json={
            "model": os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
            "messages": mensagens,
            "format": formato,
            "stream": False,
            "options": {"temperature": 0},
        },
        timeout=120,
    )
    resposta.raise_for_status()
    return resposta.json()["message"]["content"]


def gerar_sql(pergunta, esquema):
    prompt = (
        "Voce gera SQL PostgreSQL apenas de leitura. "
        "Use exclusivamente as tabelas e colunas do esquema fornecido. "
        "Retorne SOMENTE um objeto JSON com a propriedade 'sql'. "
        "A SQL deve ser uma unica consulta SELECT, sem comentarios, sem ponto e virgula, "
        "sem DDL, DML, WITH, UNION ou funcoes administrativas. "
        "Nao invente tabelas ou colunas. Inclua LIMIT 20 quando fizer sentido.\n\n"
        f"ESQUEMA:\n{esquema}\n\nPERGUNTA:\n{pergunta}"
    )
    texto_resposta = consultar_ollama([
        {"role": "system", "content": "Responda unicamente em JSON valido."},
        {"role": "user", "content": prompt},
    ])
    dado = json.loads(texto_resposta)
    return dado["sql"]


def validar_sql(sql):
    # Um parser evita confiar apenas em palavras-chave e expressões regulares.
    instrucoes = sqlglot.parse(sql, read="postgres")
    if len(instrucoes) != 1 or not isinstance(instrucoes[0], exp.Select):
        raise ValueError("Somente uma instrucao SELECT simples e permitida.")
    arvore = instrucoes[0]
    bloqueados = (
        exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create,
        exp.Alter, exp.Command, exp.Union, exp.Intersect, exp.Except,
        exp.With, exp.Into,
    )
    if any(arvore.find(tipo) is not None for tipo in bloqueados):
        raise ValueError("Consulta contem operacao nao permitida.")
    # Evita subconsultas e tabelas externas para manter o exemplo simples.
    if any(not isinstance(tabela, exp.Table) for tabela in arvore.find_all(exp.Table)):
        raise ValueError("Referencia de tabela invalida.")
    for tabela in arvore.find_all(exp.Table):
        if tabela.name not in permitidos or (tabela.db and tabela.db != "public"):
            raise ValueError(f"Tabela nao permitida: {tabela.name}")
    return arvore.sql(dialect="postgres")


def executar(sql):
    # O usuario do PostgreSQL deve ter somente SELECT, independentemente do parser.
    with engine.connect() as conexao:
        with conexao.begin():
            conexao.execute(text("SET TRANSACTION READ ONLY"))
            conexao.execute(text("SET LOCAL statement_timeout = '5000ms'"))
            resultado = conexao.execute(text(f"SELECT * FROM ({sql}) AS resultado_ia LIMIT 20"))
            return [dict(linha) for linha in resultado.mappings().all()]


def main():
    esquema = descrever_esquema()
    print("Banco conectado. Tabelas:", ", ".join(tabelas))
    print("Views:", ", ".join(views))
    while True:
        pergunta = input("\nPergunte sobre a locadora (ou 'sair'): ").strip()
        if pergunta.lower() in {"sair", "exit", "quit"}:
            break
        if not pergunta:
            continue
        try:
            sql = validar_sql(gerar_sql(pergunta, esquema))
            print("\nSQL validada:\n", sql)
            linhas = executar(sql)
            print("\nResultado (ate 20 linhas):")
            print(json.dumps(linhas, ensure_ascii=False, indent=2, default=str))
            # Na prática inicial, dados brutos evitam uma segunda chamada ao modelo.
        except Exception as erro:
            print(f"Nao foi possivel responder: {erro}")


if __name__ == "__main__":
    main()
