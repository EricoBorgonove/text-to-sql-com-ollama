"""Agente 3: explica resultados, preservando os valores do PostgreSQL."""
import json
from ollama import conversar


def formatar_dados(linhas):
    """Fallback legivel: exibe os dados, sem criar interpretacoes nao suportadas."""
    if not linhas:
        return "Nenhum registro encontrado."
    if len(linhas) == 1 and len(linhas[0]) == 1:
        chave, valor = next(iter(linhas[0].items()))
        return f"{chave}: {valor}"
    return "Resultados encontrados:\n" + "\n".join(
        "- " + "; ".join(f"{chave}: {valor}" for chave, valor in linha.items())
        for linha in linhas
    )


def interpretar(pergunta, sql, linhas):
    if not linhas:
        return "A consulta foi executada, mas nenhum registro foi retornado."
    dados = json.dumps(linhas, ensure_ascii=False, default=str)
    mensagens = [
        {"role": "system", "content": (
            "Voce explica resultados SQL da locadora em PORTUGUES claro. "
            "Responda em frases normais e nao em JSON, listas Python ou arrays. "
            "Se houver varios registros, apresente cada um com os valores das colunas "
            "(incluindo totais e receitas), em linhas legiveis. "
            "Nao retorne somente nomes quando os dados incluem quantidades. "
            "Use SOMENTE os dados fornecidos. Nunca invente metricas, valores ou conclusoes. "
            "Nao afirme que as 20 linhas sao a lista completa se houver truncamento."
        )},
        {"role": "user", "content": f"PERGUNTA: {pergunta}\nSQL: {sql}\nDADOS: {dados}"},
    ]
    try:
        resposta = conversar(mensagens).strip()
        # Se a IA devolver somente um array ou objeto, nao apresentar dados incompletos.
        if resposta.startswith(("[", "{")):
            return formatar_dados(linhas)
        # Se houver metricas e a IA ignorar todas, preferir os dados verificados.
        if len(linhas) > 1:
            metricas = [str(v) for linha in linhas for v in linha.values()
                        if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.', '', 1).isdigit())]
            if metricas and not any(v in resposta for v in metricas):
                return formatar_dados(linhas)
        return resposta or formatar_dados(linhas)
    except Exception:
        return formatar_dados(linhas)
