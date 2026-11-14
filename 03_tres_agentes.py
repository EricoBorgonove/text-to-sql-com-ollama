"""Aula 8 — Pratica 3: memoria de sessao e autocorrecao."""
import json
from sqlalchemy.exc import SQLAlchemyError
from configuracao import obter_esquema
from agente_planejador import planejar, corrigir
from agente_executor import executar
from agente_interpretador import interpretar
from memoria import MemoriaConversa

MAX_TENTATIVAS = 3


def diagnostico_curto(erro):
    """Nao repassa SQLAlchemy connection URLs ou parametros secretos para o modelo."""
    if isinstance(erro, SQLAlchemyError):
        origem = getattr(erro, "orig", None)
        if origem is not None:
            # PostgreSQL (psycopg) fornece SQLSTATE e mensagem, sem credenciais.
            codigo = getattr(origem, "sqlstate", None)
            mensagem = getattr(getattr(origem, "diag", None), "message_primary", None)
            if mensagem:
                return f"PostgreSQL {codigo or ''}: {mensagem}"[:350]
        return "Erro de banco de dados ao executar SELECT; confira aliases, tabelas e colunas."
    return str(erro)[:350]


def responder(pergunta, esquema, memoria):
    """Ate 3 tentativas TOTAIS, inclusive quando o JSON de planejamento falha."""
    historico = memoria.contexto()  # congelado durante as tentativas
    plano = None
    sql_anterior = "(nenhuma SQL valida foi gerada)"
    diagnostico = ""
    sql_anteriores = set()

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        print(f"\n[1] PLANEJADOR — tentativa {tentativa}/{MAX_TENTATIVAS}")
        try:
            if tentativa == 1:
                plano = planejar(pergunta, esquema, historico=historico)
            else:
                plano = corrigir(pergunta, esquema, sql_anterior, diagnostico, tentativa, historico=historico)
        except ValueError as erro:
            diagnostico = diagnostico_curto(erro)
            print("[1] PLANEJADOR — resposta invalida:", diagnostico)
            sql_anterior = "(resposta anterior sem SQL valida)"
            continue

        print("Objetivo:", plano["objetivo"])
        print("SQL proposta:\n", plano["sql"])
        try:
            sql_gerada = plano["sql"].strip()
            if sql_gerada in sql_anteriores:
                raise ValueError("A SQL repetiu uma tentativa anterior sem correcao.")
            sql_anteriores.add(sql_gerada)
            sql, linhas = executar(sql_gerada)
        except (ValueError, SQLAlchemyError) as erro:
            sql_anterior = plano["sql"]
            diagnostico = diagnostico_curto(erro)
            print("[2] EXECUTOR — consulta nao executada com sucesso:", diagnostico)
            continue

        print("\n[2] EXECUTOR — consulta autorizada")
        print(sql)
        print("Linhas retornadas:", len(linhas))
        print(json.dumps(linhas, indent=2, ensure_ascii=False, default=str))
        print("\n[3] INTERPRETADOR")
        resposta = interpretar(pergunta, sql, linhas)
        print(resposta)
        memoria.registrar(pergunta, sql, linhas, resposta)
        print(f"[MEMORIA] {len(memoria)} interacao(oes) guardada(s) nesta sessao.")
        return

    print("Limite de 3 tentativas atingido. Nao foi possivel responder com confianca.")


def main():
    try:
        esquema, permitidos = obter_esquema()
    except Exception as erro:
        print("Falha ao conectar no banco:", diagnostico_curto(erro))
        return
    memoria = MemoriaConversa()
    print("\n=== LOCADORA: 3 AGENTES — MEMORIA DE SESSAO ===")
    print("Objetos identificados:", ", ".join(sorted(permitidos)))
    print("Digite uma pergunta, 'limpar' (zera a memoria) ou 'sair'.")
    while True:
        try:
            pergunta = input("\nVoce: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrado.")
            return
        if pergunta.lower() in {"sair", "exit", "quit"}:
            return
        if not pergunta:
            continue
        if pergunta.lower() in {"limpar", "limpar memoria", "limpar memória"}:
            memoria.limpar()
            print("Memoria da sessao apagada.")
            continue
        try:
            responder(pergunta, esquema, memoria)
        except Exception as erro:
            print("Nao foi possivel concluir a pergunta:", diagnostico_curto(erro))


if __name__ == "__main__":
    main()
